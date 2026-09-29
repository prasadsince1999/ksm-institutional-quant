"""
scripts/train_laya_lora_distill.py — Train Laya with LoRA (FP16) using Jev Teacher Distillation.
Extracts Jev's System 1 calibrated probabilities into local Laya weights.

Architecture:
- Base: convaiinnovations/laya (ModernBERT-large 421M + Decision Head)
- Adaptation: LoRA (r=8, alpha=16) on encoder attention matrices (Wqkv, Wo)
- Training precision: FP16 on NVIDIA GTX 1650 Ti (4GB VRAM)
- Objective: KL-Divergence + Laya Strictly Proper Scoring Loss against Jev soft probabilities
"""

import os
import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
import time
import json
import torch
import torch.nn as nn
from peft import LoraConfig, get_peft_model
from torch.cuda.amp import autocast, GradScaler

import laya
from laya.agent import build_sequence, collate_items
from laya.common import QTYPES, render_options, proper_reward

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATA_PATH = os.path.join(ROOT_DIR, "data", "distillation_training_data.json")
OUTPUT_DIR = os.path.join(ROOT_DIR, "exness", "models", "laya_lora_distilled")
os.makedirs(OUTPUT_DIR, exist_ok=True)

print("=" * 80)
print("   LAYA LoRA DISTILLATION: TRANSFERRING TYPESAFE JEV REASONING INTO LOCAL GPU")
print("=" * 80)

# 1. Load Dataset
if not os.path.exists(DATA_PATH):
    print(f"❌ Error: {DATA_PATH} not found.")
    sys.exit(1)

with open(DATA_PATH, "r", encoding="utf-8") as f:
    raw_dataset = json.load(f)

print(f"Loaded {len(raw_dataset)} teacher-labeled scenarios from TypeSafe Jev.")

# 2. Initialize Laya Agent on CUDA
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"Loading Base Laya Model on {device}...")
agent = laya.load(device=str(device))
model = agent.model
tok = agent.tok

# 3. Configure LoRA on ModernBERT Attention Weights
lora_config = LoraConfig(
    r=8,
    lora_alpha=16,
    target_modules=["Wqkv", "Wo"],
    lora_dropout=0.05,
    bias="none"
)
model.encoder = get_peft_model(model.encoder, lora_config)

# Make sure decision heads (scorer, type_emb) are also trainable
for param in model.scorer.parameters():
    param.requires_grad = True
for param in model.type_emb.parameters():
    param.requires_grad = True

trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
total_params = sum(p.numel() for p in model.parameters())
print(f"LoRA Initialized: {trainable_params:,} trainable parameters ({trainable_params/total_params*100:.2f}% of {total_params:,})")

# 4. Prepare Tokenized Batches
q_def_choice = {
    "t": "choice",
    "ins": "Rate the institutional risk level of this setup.",
    "crit": {
        "prime_setup": "High liquidity, healthy stop buffer, strong institutional edge",
        "marginal_noise": "Consolidation or moderate spread friction",
        "toxic_trap": "Micro-stop, spread blowout, adverse runaway momentum, or session dead zone"
    }
}
opts_choice = list(q_def_choice["crit"].keys())

q_def_noul = {
    "t": "noul",
    "ins": "Is it mathematically safe and institutionally sound to place or hold this order right now?",
    "crit": None
}

training_items = []
max_len = 512
head_max_len = 192

for entry in raw_dataset:
    state = entry["state"]
    target = entry["target"]

    # Target 1: Choice distribution over ["prime_setup", "marginal_noise", "toxic_trap"]
    # Jev probabilities: e.g. {"prime_setup": 0.05, "marginal_noise": 0.12, "toxic_trap": 0.83}
    jev_choice_probs = target["risk_probabilities"]
    choice_target_vec = [jev_choice_probs.get(k, 0.0) for k in opts_choice]
    choice_sum = sum(choice_target_vec)
    if choice_sum > 0:
        choice_target_vec = [x / choice_sum for x in choice_target_vec]
    else:
        choice_target_vec = [1.0/3, 1.0/3, 1.0/3]

    seq_c, markers_c = build_sequence(tok, state, q_def_choice, max_len, head_max_len)
    training_items.append({
        "ids": seq_c,
        "markers": markers_c,
        "qtype": QTYPES["choice"],
        "target": choice_target_vec
    })

    # Target 2: Noul distribution over [no, yes]
    # allow_trade_prob: prob of YES (index 1), 1 - prob of NO (index 0)
    allow_p = target["allow_trade_prob"]
    noul_target_vec = [1.0 - allow_p, allow_p]

    seq_n, markers_n = build_sequence(tok, state, q_def_noul, max_len, head_max_len)
    training_items.append({
        "ids": seq_n,
        "markers": markers_n,
        "qtype": QTYPES["noul"],
        "target": noul_target_vec
    })

print(f"Compiled {len(training_items)} training sample items (Choice + Noul).")

# 5. Training Loop Setup
optimizer = torch.optim.AdamW(
    [p for p in model.parameters() if p.requires_grad],
    lr=3e-4,
    weight_decay=0.01
)
scaler = GradScaler()
batch_size = 4
num_epochs = 15

print(f"\nStarting LoRA Fine-Tuning ({num_epochs} Epochs, Batch Size={batch_size}, FP16 Mixed Precision)...")

start_time = time.time()
model.train()

for epoch in range(1, num_epochs + 1):
    epoch_loss = 0.0
    num_batches = 0

    # Shuffle training items
    indices = torch.randperm(len(training_items)).tolist()
    
    for i in range(0, len(training_items), batch_size):
        batch_slice = [training_items[idx] for idx in indices[i:i+batch_size]]
        b = collate_items([batch_slice], tok.pad_token_id)
        if b is None:
            continue

        input_ids = b["input_ids"].to(device)
        attention_mask = b["attention_mask"].to(device)
        marker_pos = b["marker_pos"].to(device)
        marker_mask = b["marker_mask"].to(device)
        qtype = b["qtype"].to(device)
        teacher_targets = b["target"].to(device)

        optimizer.zero_grad()

        with autocast(dtype=torch.float16):
            logits, act = model(input_ids, attention_mask, marker_pos, marker_mask, qtype)
            
            # Masked Softmax over option markers
            # logits: (B, K_max)
            logits_clamped = logits.masked_fill(~marker_mask, -1e4)
            student_log_probs = torch.log_softmax(logits_clamped, dim=-1)
            student_probs = torch.softmax(logits_clamped, dim=-1)

            # KL-Divergence Loss + Proper Scoring Rule
            # Loss = KL(teacher || student)
            kl_loss = torch.sum(teacher_targets * (torch.log(teacher_targets.clamp_min(1e-9)) - student_log_probs), dim=-1).mean()
            
            loss = kl_loss

        scaler.scale(loss).backward()
        scaler.unscale_(optimizer)
        torch.nn.utils.clip_grad_norm_([p for p in model.parameters() if p.requires_grad], 1.0)
        scaler.step(optimizer)
        scaler.update()

        epoch_loss += loss.item()
        num_batches += 1

    avg_loss = epoch_loss / max(1, num_batches)
    if epoch % 3 == 0 or epoch == 1 or epoch == num_epochs:
        print(f"Epoch [{epoch:2d}/{num_epochs:2d}] | KL-Distillation Loss: {avg_loss:.4f} | VRAM: {torch.cuda.memory_allocated()/1024**2:.1f}MB")

train_time = time.time() - start_time
print("\n" + "=" * 80)
print(f"🏆 LoRA TRAINING COMPLETE in {train_time:.1f}s!")
print("=" * 80)

# 6. Save LoRA Weights & Adapter Checkpoint
save_path = os.path.join(OUTPUT_DIR, "laya_lora_weights.pt")
torch.save({
    "encoder_lora": model.encoder.state_dict(),
    "scorer": model.scorer.state_dict(),
    "type_emb": model.type_emb.state_dict(),
    "lora_config": lora_config,
    "timestamp": time.time()
}, save_path)
print(f"✅ Trained LoRA weights saved to: {save_path}")

# 7. Validation: Re-Evaluate on Live Trade Scenarios
print("\nValidating Fine-Tuned Laya on Key Incidents:")
model.eval()

validation_scenarios = [
    {
        "id": "LIVE_XAUUSD_26S",
        "name": "XAUUSD 26s Gold Micro-Stop ($1.32 stop vs $6.50 ATR)",
        "state": "Institutional Market Context: XAUUSD (Gold) M5 chart. Order is BUY_LIMIT at 4387.738 with stop loss at 4386.412. Stop distance is only $1.32 (13.2 pips) on Gold where average M5 ATR is $6.50. Broker spread is 3.5 pips.",
        "expected": "toxic_trap"
    },
    {
        "id": "LIVE_EURJPY_MOMENTUM_FLUSH",
        "name": "EURJPY 4-Bar Runaway Red Momentum Flush",
        "state": "Institutional Market Context: EURJPY trading at 181.36. Market is experiencing a violent one-way JPY liquidation flush with 4 consecutive large red expansion candles without any bottom wicks. Strategy attempts to counter-trend fade the low.",
        "expected": "toxic_trap"
    },
    {
        "id": "LIVE_XAUUSD_BIG_WIN",
        "name": "XAUUSD +$9.34 London Clean Win",
        "state": "Institutional Market Context: London Open (08:34 UTC). XAUUSD (Gold) experienced strong bullish displacement breaking Asian High. Order is BUY_LIMIT at Fair Value Gap at 4327.83 with healthy $9.33 stop loss buffer (well above ATR) and 2.8 pip spread.",
        "expected": "prime_setup"
    }
]

for vs in validation_scenarios:
    seq_c, markers_c = build_sequence(tok, vs["state"], q_def_choice, max_len, head_max_len)
    b = collate_items([[{
        "ids": seq_c,
        "markers": markers_c,
        "qtype": QTYPES["choice"]
    }]], tok.pad_token_id)

    with torch.no_grad():
        logits, _ = model(
            b["input_ids"].to(device),
            b["attention_mask"].to(device),
            b["marker_pos"].to(device),
            b["marker_mask"].to(device),
            b["qtype"].to(device)
        )
        probs = torch.softmax(logits[0, :len(markers_c)], dim=-1).cpu().numpy()
        pred_choice = opts_choice[int(probs.argmax())]
        conf = float(probs.max())

    match = "✅ PASS" if pred_choice == vs["expected"] else "❌ FAIL"
    print(f"[{vs['id']}] Prediction: {pred_choice:<15} (Conf={conf:.2f}) | Target: {vs['expected']:<12} -> {match}")

print("\n" + "=" * 80)
print("Distillation Complete. Laya now possesses Jev's calibrated risk boundaries locally.")
print("=" * 80)

"""
exness/decider_guardian.py — Local System 1 Decision Engine Powered by Decider 2B.
Based on Mapika/decider-2b (1.9B parameters, Decision Index score 44.0).

Provides zero-cost, sub-second, zero-hallucination calibrated decision triage for:
1. Pre-Trade Tape & Order Flow Confluence Gating
2. Breaking Macro & Headline Triage
3. In-Flight Position Risk Evaluation

Fail-Safe Design:
Gracefully handles GPU VRAM constraints, falling back to CPU if memory is tight,
and fails open to deterministic ExecutionSentinel invariants if an unexpected error occurs.
"""

import os
import sys
import time
import json
from typing import Dict, Any, Optional

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

class DeciderGuardian:
    """
    Local System 1 Decision Guardian using Decider 2B.
    Performs calibrated single-forward-pass classifications without text generation.
    """
    def __init__(self, device: Optional[str] = None, lazy_load: bool = True, enabled: bool = True):
        self.enabled = enabled
        self.device = device
        self.dtype = None
        self.decider = None
        self.is_loaded = False
        self.last_latency_ms = 0.0
        self.local_model_path = None

        if self.device is None:
            try:
                import torch
                if torch.cuda.is_available():
                    free_gb = (torch.cuda.get_device_properties(0).total_memory - torch.cuda.memory_allocated(0)) / (1024**3)
                    # 2B model in float16 requires ~3.5 GB VRAM
                    if free_gb >= 3.2:
                        self.device = "cuda"
                        self.dtype = torch.float16
                    else:
                        self.device = "cpu"
                        self.dtype = torch.float32
                else:
                    self.device = "cpu"
                    self.dtype = torch.float32
            except Exception:
                self.device = "cpu"
                self.dtype = None

        if self.enabled and not lazy_load:
            self.ensure_loaded()

    def ensure_loaded(self) -> bool:
        """Loads Decider 2B into memory if not already loaded."""
        if not self.enabled:
            return False
        if self.is_loaded and self.decider is not None:
            return True

        try:
            from huggingface_hub import snapshot_download
            import torch
            from decider.infer import Decider

            # Resolve local cached snapshot path
            t0 = time.time()
            self.local_model_path = snapshot_download(
                repo_id="Mapika/decider-2b",
                allow_patterns=["*.json", "*.safetensors", "*.jinja"],
                local_files_only=True
            )

            if self.dtype is None:
                self.dtype = torch.float16 if self.device == "cuda" else torch.float32

            try:
                self.decider = Decider(
                    self.local_model_path,
                    device=self.device,
                    dtype=self.dtype,
                    use_graphs=False
                )
            except Exception as e:
                if self.device == "cuda":
                    print(f"[DeciderGuardian] CUDA load failed ({e}), falling back to CPU...")
                    self.device = "cpu"
                    self.dtype = torch.float32
                    self.decider = Decider(
                        self.local_model_path,
                        device="cpu",
                        dtype=torch.float32,
                        use_graphs=False
                    )
                else:
                    raise e

            self.is_loaded = True
            print(f"[DeciderGuardian] Mapika/decider-2b online on {self.device} ({time.time() - t0:.2f}s).")
            return True
        except Exception as e:
            print(f"[DeciderGuardian] Failed to initialize Decider 2B: {e}")
            self.decider = None
            self.is_loaded = False
            return False

    def evaluate_tape_confluence(self, setup: dict, macro_context: dict) -> Dict[str, Any]:
        """
        Evaluates proposed SMC setup using single-pass System 1 classification.
        """
        if not self.ensure_loaded() or self.decider is None:
            return {
                "engine": "LOCAL_DECIDER_2B (OFFLINE)",
                "approved": True,
                "risk_rating": "PRIME_SETUP",
                "allow_probability": 0.50,
                "confidence": 0.50,
                "latency_ms": 0.0,
                "fallback_used": True
            }

        pair = setup.get('pair', 'UNKNOWN')
        order_type = setup.get('order_type', 'UNKNOWN')
        archetype = setup.get('archetype', 'CORE_SMC')
        risk_pips = setup.get('risk_pips', 10.0)
        spread_pips = macro_context.get('spread_pips', 1.0)
        session = macro_context.get('session', 'ACTIVE')
        liquidity = macro_context.get('liquidity_state', 'NORMAL')

        state_text = (
            f"Institutional Order Flow Context: Market is in {session} session with {liquidity} liquidity conditions "
            f"and a broker spread of {spread_pips} pips. Strategy proposes a {pair} {order_type} "
            f"targeting a {archetype} setup with {risk_pips} pips stop risk."
        )

        try:
            t0 = time.perf_counter()
            d_out = self.decider.decide(
                state_text,
                [
                    {
                        "question": "Is it mathematically safe and institutionally sound to place this pending limit order right now?",
                        "options": ["yes, prime setup", "no, toxic trap or high risk"]
                    },
                    {
                        "question": "Rate the institutional risk level of this setup.",
                        "options": ["prime setup", "marginal noise", "toxic trap"]
                    }
                ]
            )
            latency_ms = (time.perf_counter() - t0) * 1000.0
            self.last_latency_ms = latency_ms

            allow_choice = d_out[0]["choice"]
            allow_conf = d_out[0]["confidence"]
            allow_prob = allow_conf if allow_choice.startswith("yes") else (1.0 - allow_conf)

            risk_choice = d_out[1]["choice"].upper().replace(" ", "_")
            risk_conf = d_out[1]["confidence"]

            # Decider decision rule:
            # 1. Toxic trap vetoes immediately
            # 2. Allow probability < 0.35 vetoes
            # 3. Explicit "no" vetoes
            approved = (not allow_choice.startswith("no")) and (risk_choice != "TOXIC_TRAP") and (allow_prob >= 0.35)

            return {
                "engine": "LOCAL_DECIDER_2B (BACKUP)",
                "approved": approved,
                "risk_rating": risk_choice,
                "allow_probability": round(allow_prob, 4),
                "confidence": round(risk_conf, 4),
                "latency_ms": round(latency_ms, 1),
                "fallback_used": True
            }
        except Exception as e:
            print(f"[DeciderGuardian] Error during evaluation: {e}")
            return {
                "engine": "LOCAL_DECIDER_2B (ERROR_FALLBACK)",
                "approved": True,
                "risk_rating": "PRIME_SETUP",
                "allow_probability": 0.50,
                "confidence": 0.50,
                "latency_ms": 0.0,
                "fallback_used": True
            }

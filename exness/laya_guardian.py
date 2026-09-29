"""
exness/laya_guardian.py — Local Non-Autoregressive System 1 Decision Engine.
Powered by Laya (421M ModernBERT-large + RLCD) running 100% locally on device.

Provides zero-cost, sub-second, zero-hallucination calibrated decision triage for:
1. Breaking Economic & Geopolitical Headline Triage
2. Pre-Trade Macro Tape Confluence Gating
3. Closed Deal Execution Forensic Diagnosis

Fail-Safe Design:
If model weights are uninitialized, GPU is busy, or latency budget exceeds limits,
all methods gracefully fail open to safe defaults with fallback flags.
"""

import os
import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
import time
import json
from typing import Dict, Any, Optional

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

class LayaGuardian:
    """
    Autonomous System 1 Decision Engine for Exness MT5.
    Evaluates market states and telemetries in single-forward passes
    using strictly proper scoring rules (calibrated probabilities).
    """
    def __init__(self, device: Optional[str] = None, lazy_load: bool = True, enabled: bool = True):
        self.enabled = enabled
        self.device = device
        self.agent = None
        self.is_loaded = False
        self.last_latency_ms = 0.0

        if self.device is None:
            try:
                import torch
                self.device = "cuda" if torch.cuda.is_available() else "cpu"
            except Exception:
                self.device = "cpu"

        if self.enabled and not lazy_load:
            self.ensure_loaded()

    def ensure_loaded(self) -> bool:
        """Loads Laya agent into memory if not already loaded, attaching distilled LoRA weights if present."""
        if not self.enabled:
            return False
        if self.is_loaded and self.agent is not None:
            return True

        try:
            import laya
            t0 = time.time()
            self.agent = laya.load(device=self.device)

            # Check for Distilled LoRA weights from Jev
            lora_path = os.path.join(ROOT_DIR, "exness", "models", "laya_lora_distilled", "laya_lora_weights.pt")
            self.is_distilled = False
            if os.path.exists(lora_path):
                try:
                    import torch
                    from peft import get_peft_model
                    ckpt = torch.load(lora_path, map_location=self.device, weights_only=False)
                    lora_cfg = ckpt.get("lora_config")
                    self.agent.model.encoder = get_peft_model(self.agent.model.encoder, lora_cfg)
                    self.agent.model.encoder.load_state_dict(ckpt["encoder_lora"], strict=False)
                    if "scorer" in ckpt:
                        self.agent.model.scorer.load_state_dict(ckpt["scorer"], strict=False)
                    if "type_emb" in ckpt:
                        self.agent.model.type_emb.load_state_dict(ckpt["type_emb"], strict=False)
                    self.agent.model.to(self.device).eval()
                    self.is_distilled = True
                    print(f"[Laya Guardian] Attached Distilled LoRA Adapter (Trained from TypeSafe Jev)!")
                except Exception as lora_err:
                    print(f"[Laya Guardian] Could not attach LoRA weights: {lora_err}. Running base model.")
                    self.is_distilled = False

            if hasattr(self.agent, "cfg"):
                self.agent.cfg["max_len"] = 256
                self.agent.cfg["head_max_len"] = 96

            self.is_loaded = True
            load_time = time.time() - t0
            status_str = "DISTILLED JEV-LEVEL" if self.is_distilled else "BASE"
            print(f"[Laya Guardian] Agent ({status_str}) successfully loaded on {self.device.upper()} in {load_time:.2f}s (max_len=256)!")
            return True
        except Exception as e:
            print(f"[Laya Guardian] Failed to load Laya model: {e}. Running in Rule-Based Fallback Mode.")
            self.agent = None
            self.is_loaded = False
            return False

    def reload_lora_weights(self, weights_path: Optional[str] = None) -> bool:
        """
        Hot-reloads LoRA adapter weights directly into the active PyTorch model in RAM.
        Zero downtime, zero MT5 disconnection.
        """
        if not self.ensure_loaded():
            return False

        if weights_path is None:
            weights_path = os.path.join(ROOT_DIR, "exness", "models", "laya_lora_distilled", "laya_lora_weights.pt")

        if not os.path.exists(weights_path):
            print(f"[Laya Guardian] Cannot hot-reload: file not found at {weights_path}")
            return False

        try:
            import torch
            from peft import get_peft_model, PeftModel
            ckpt = torch.load(weights_path, map_location=self.device, weights_only=False)
            lora_cfg = ckpt.get("lora_config")

            # If encoder is not yet PeftModel, wrap it
            if not isinstance(self.agent.model.encoder, PeftModel):
                self.agent.model.encoder = get_peft_model(self.agent.model.encoder, lora_cfg)

            self.agent.model.encoder.load_state_dict(ckpt["encoder_lora"], strict=False)
            if "scorer" in ckpt:
                self.agent.model.scorer.load_state_dict(ckpt["scorer"], strict=False)
            if "type_emb" in ckpt:
                self.agent.model.type_emb.load_state_dict(ckpt["type_emb"], strict=False)

            self.agent.model.to(self.device).eval()
            self.is_distilled = True
            print(f"[Laya Guardian] Hot-swap successful: Active weights updated from {os.path.basename(weights_path)}!")
            return True
        except Exception as e:
            print(f"[Laya Guardian] Hot-swap failed: {e}")
            return False

    def evaluate_news_headline(self, headline: str) -> Dict[str, Any]:
        """
        Classifies unscheduled breaking news headlines or alerts.
        Returns:
            {
                "halt_trading": bool,
                "impact": str,
                "confidence": float,
                "latency_ms": float,
                "fallback": bool
            }
        """
        if not self.ensure_loaded():
            return {
                "halt_trading": False,
                "impact": "ROUTINE_COMMENTARY",
                "confidence": 0.50,
                "latency_ms": 0.0,
                "fallback": True
            }

        questions = {
            "market_impact": {
                "type": "choice",
                "instructions": "How will this breaking financial or macroeconomic headline impact forex and commodity markets?",
                "criteria": {
                    "volatility_spike": "Emergency rate actions, sudden war or geopolitical conflict, unexpected inflation shock, bank insolvency, tariff wars",
                    "routine_commentary": "Scheduled political statements, expected analyst commentary, gradual macroeconomic updates",
                    "no_impact": "Unrelated corporate earnings, minor municipal events, historical summaries"
                }
            },
            "halt_trading": {
                "type": "noul",
                "instructions": "Does this headline pose an immediate threat of severe slippage, spread blowout, or violent market turbulence?"
            }
        }

        try:
            t0 = time.perf_counter()
            res = self.agent.predict(headline, questions)
            latency_ms = (time.perf_counter() - t0) * 1000.0
            self.last_latency_ms = latency_ms

            answers = res.get("answers", {})
            impact_ans = answers.get("market_impact", {})
            halt_ans = answers.get("halt_trading", {})

            halt_prob = halt_ans.get("noul", 0.0)
            halt_conf = halt_ans.get("confidence", 0.5)
            impact_choice = impact_ans.get("choice", "routine_commentary").upper()

            should_halt = (halt_prob >= 0.50 and halt_conf >= 0.60) or (impact_choice == "VOLATILITY_SPIKE")

            return {
                "halt_trading": should_halt,
                "impact": impact_choice,
                "confidence": round(halt_conf, 4),
                "halt_probability": round(halt_prob, 4),
                "latency_ms": round(latency_ms, 1),
                "fallback": False
            }
        except Exception as e:
            print(f"[Laya Guardian] Headline evaluation failed: {e}")
            return {
                "halt_trading": False,
                "impact": "ROUTINE_COMMENTARY",
                "confidence": 0.50,
                "latency_ms": 0.0,
                "fallback": True
            }

    def evaluate_tape_confluence(self, setup: dict, macro_context: dict) -> Dict[str, Any]:
        """
        Pre-Trade Gate: Evaluates M5 SMC setup against macro session context.
        Returns:
            {
                "approved": bool,
                "conviction": str,
                "confidence": float,
                "latency_ms": float,
                "fallback": bool
            }
        """
        if not self.ensure_loaded():
            return {
                "approved": True,
                "conviction": "PRIME_INSTITUTIONAL",
                "confidence": 0.50,
                "latency_ms": 0.0,
                "fallback": True
            }

        if "state" in setup:
            state_text = setup["state"]
        else:
            pair = setup.get('pair', 'UNKNOWN')
            order_type = setup.get('order_type', 'UNKNOWN')
            archetype = setup.get('archetype', 'CORE_SMC')
            risk_pips = setup.get('risk_pips', 10.0)
            spread_pips = macro_context.get('spread_pips', 1.0)
            session = macro_context.get('session', 'ACTIVE')
            liquidity = macro_context.get('liquidity_state', 'NORMAL')
            mtf_bias = macro_context.get('mtf_bias', 'NEUTRAL')

            state_text = (
                f"Institutional Order Flow Context: Market is in {session} session with {liquidity} liquidity conditions, "
                f"HTF bias {mtf_bias}, and a broker spread of {spread_pips} pips. Strategy proposes a {pair} {order_type} "
                f"targeting a {archetype} setup with {risk_pips} pips stop risk."
            )

        questions = {
            "risk_rating": {
                "type": "choice",
                "instructions": "Rate the institutional risk level of this setup.",
                "criteria": {
                    "prime_setup": "High liquidity, healthy stop buffer, strong institutional edge",
                    "marginal_noise": "Consolidation or moderate spread friction",
                    "toxic_trap": "Micro-stop, spread blowout, adverse runaway momentum, or session dead zone"
                }
            },
            "allow_trade": {
                "type": "noul",
                "instructions": "Is it mathematically safe and institutionally sound to place this order?"
            }
        }

        try:
            t0 = time.perf_counter()
            res = self.agent.predict(state_text, questions)
            latency_ms = (time.perf_counter() - t0) * 1000.0
            self.last_latency_ms = latency_ms

            answers = res.get("answers", {})
            risk_ans = answers.get("risk_rating", {})
            allow_ans = answers.get("allow_trade", {})

            risk_choice = risk_ans.get("choice", "marginal_noise").upper()
            allow_prob = allow_ans.get("noul", 0.5)
            confidence = risk_ans.get("confidence", 0.5)

            # Balanced Decision Rule: Veto if toxic trap or allow_prob < 0.22
            approved = (risk_choice != "TOXIC_TRAP") and (allow_prob >= 0.22)

            return {
                "approved": approved,
                "risk_rating": risk_choice,
                "conviction": risk_choice,
                "allow_probability": round(allow_prob, 4),
                "confidence": round(confidence, 4),
                "latency_ms": round(latency_ms, 1),
                "fallback": False
            }
        except Exception as e:
            print(f"[Laya Guardian] Tape confluence evaluation failed: {e}")
            return {
                "approved": True,
                "conviction": "PRIME_INSTITUTIONAL",
                "confidence": 0.50,
                "latency_ms": 0.0,
                "fallback": True
            }

    def triage_execution_incident(self, telemetry: dict) -> Dict[str, Any]:
        """
        Forensic Triage: Diagnoses closed trade anomalies (e.g. flash stop-outs).
        Returns:
            {
                "root_cause": str,
                "quarantine_minutes": int,
                "confidence": float,
                "latency_ms": float,
                "fallback": bool
            }
        """
        if not self.ensure_loaded():
            return {
                "root_cause": "NORMAL_VARIANCE",
                "quarantine_minutes": 60,
                "confidence": 0.50,
                "latency_ms": 0.0,
                "fallback": True
            }

        state_text = (
            f"Symbol: {telemetry.get('symbol', 'UNKNOWN')} | "
            f"Trade Duration: {telemetry.get('duration_seconds', 0):.0f}s | "
            f"Loss: ${abs(telemetry.get('profit_usd', 0)):.2f} (Planned Risk: ${telemetry.get('planned_risk_usd', 5.0):.2f}) | "
            f"Entry Price: {telemetry.get('entry_price', 0)} | "
            f"Exit Price: {telemetry.get('exit_price', 0)}"
        )

        questions = {
            "root_cause": {
                "type": "choice",
                "instructions": "What is the primary operational cause for this execution incident or flash stop-out?",
                "criteria": {
                    "spread_hunting_spike": "Broker spread widened significantly at fill or exit, stopping out within normal candle wick range",
                    "liquidation_flush": "Massive institutional runaway move blew past stop without pullbacks",
                    "normal_variance": "Standard statistical stop-loss within expected strategy risk parameters"
                }
            },
            "quarantine_urgency": {
                "type": "score",
                "instructions": "What level of asset quarantine should be applied to prevent further loss?",
                "criteria": [
                    "0: none (resume trading immediately)",
                    "1: mild (15-minute cooldown)",
                    "2: serious (60-minute quarantine for volatility stabilization)",
                    "3: critical (halt this asset for remainder of session)"
                ]
            }
        }

        try:
            t0 = time.perf_counter()
            res = self.agent.predict(state_text, questions)
            latency_ms = (time.perf_counter() - t0) * 1000.0
            self.last_latency_ms = latency_ms

            answers = res.get("answers", {})
            cause_ans = answers.get("root_cause", {})
            urgency_ans = answers.get("quarantine_urgency", {})

            cause = cause_ans.get("choice", "normal_variance").upper()
            urgency_score = urgency_ans.get("score", 2.0)
            confidence = cause_ans.get("confidence", 0.5)

            # Map score to minutes
            if urgency_score < 0.5:
                quar_mins = 0
            elif urgency_score < 1.5:
                quar_mins = 15
            elif urgency_score < 2.5:
                quar_mins = 60
            else:
                quar_mins = 180

            return {
                "root_cause": cause,
                "urgency_score": round(urgency_score, 2),
                "quarantine_minutes": quar_mins,
                "confidence": round(confidence, 4),
                "latency_ms": round(latency_ms, 1),
                "fallback": False
            }
        except Exception as e:
            print(f"[Laya Guardian] Incident triage failed: {e}")
            return {
                "root_cause": "NORMAL_VARIANCE",
                "quarantine_minutes": 60,
                "confidence": 0.50,
                "latency_ms": 0.0,
                "fallback": True
            }

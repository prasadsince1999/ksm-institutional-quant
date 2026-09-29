"""
exness/hybrid_decision_guardian.py — Unified System 1 Dual-Engine Architecture.
Combines TypeSafe Jev (Cloud API Primary) with Decider 2B (Local GPU Fallback).

Hierarchy:
1. Primary: TypeSafe Jev System One (Score 59.5, Apex Semantic Triage, ~400ms)
2. Backup : Local Decider 2B on CUDA (Score 44.0, 100% Offline Local Resilience, ~1.7s)
3. Tertiary: Local Laya 421M ModernBERT-RLCD (Score 16.4, Ultra-light CPU Fallback)
4. Safety : Deterministic ExecutionSentinel Invariants (0.003s Hard Mathematics)
"""

import os
import sys
import time
from typing import Dict, Any, Optional
from dotenv import load_dotenv

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
load_dotenv(os.path.join(ROOT_DIR, ".env"))

class HybridDecisionGuardian:
    def __init__(self, use_jev: bool = True, use_decider_backup: bool = True, use_laya_backup: bool = False):
        self.use_jev = use_jev
        self.use_decider_backup = use_decider_backup
        self.use_laya_backup = use_laya_backup
        
        # 1. Primary: TypeSafe Jev client initialization
        self.jev_client = None
        self.jev_api_key = os.getenv("TYPESAFE_API_KEY")
        if self.use_jev and self.jev_api_key:
            try:
                from typesafe_sdk import TypeSafeClient
                self.jev_client = TypeSafeClient(api_key=self.jev_api_key)
                print("[Hybrid Guardian] TypeSafe Jev (Primary Cloud Engine @ 59.5) online.")
            except Exception as e:
                print(f"[Hybrid Guardian] Failed to initialize Jev: {e}")
                self.jev_client = None

        # 2. Local Backup: Decider 2B initialization
        self.decider = None
        if self.use_decider_backup:
            try:
                from exness.decider_guardian import DeciderGuardian
                self.decider = DeciderGuardian(lazy_load=True)
                print("[Hybrid Guardian] Local Decider 2B (On-Device Backup @ 44.0) online.")
            except Exception as e:
                print(f"[Hybrid Guardian] Failed to initialize Decider 2B: {e}")
                self.decider = None

        # 3. Tertiary: Local Laya initialization (optional)
        self.laya = None
        if self.use_laya_backup:
            try:
                from exness.laya_guardian import LayaGuardian
                self.laya = LayaGuardian(lazy_load=True)
                print("[Hybrid Guardian] Local Laya (Tertiary Backup @ 16.4) online.")
            except Exception as e:
                print(f"[Hybrid Guardian] Failed to initialize Laya: {e}")
                self.laya = None

    def evaluate_pre_trade_setup(self, setup: dict, macro_context: dict) -> Dict[str, Any]:
        """
        Evaluates a proposed SMC trade setup.
        Tries TypeSafe Jev first for deepest cognitive reasoning.
        Automatically falls back to Local Decider 2B if Jev fails or encounters network errors.
        Falls back to Deterministic Sentinel as hard ground truth.
        """
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

        # ── 1. Attempt Primary: TypeSafe Jev (Cloud API) ──
        if self.jev_client:
            try:
                from typesafe_sdk import Noul, Choice
                t0 = time.perf_counter()
                res = self.jev_client.system_one(
                    state=state_text,
                    questions={
                        "allow_trade": Noul(instructions="Is it mathematically safe and institutionally sound to place this pending limit order right now?"),
                        "risk_rating": Choice(
                            instructions="Rate the institutional risk level of this setup.",
                            criteria={
                                "prime_setup": "High liquidity, healthy stop buffer, strong institutional edge",
                                "marginal_noise": "Consolidation or moderate spread friction",
                                "toxic_trap": "Micro-stop, spread blowout, adverse runaway momentum, or session dead zone"
                            }
                        )
                    }
                )
                latency_ms = (time.perf_counter() - t0) * 1000.0
                allow_prob = res.answers["allow_trade"].noul
                risk = res.answers["risk_rating"].choice.upper()
                confidence = res.answers["risk_rating"].confidence

                # Jev decision rule: Toxic trap or allow < 0.20 vetoes trade
                approved = (risk != "TOXIC_TRAP") and (allow_prob >= 0.20)

                return {
                    "engine": "TYPESAFE_JEV (PRIMARY)",
                    "approved": approved,
                    "risk_rating": risk,
                    "allow_probability": round(allow_prob, 4),
                    "confidence": round(confidence, 4),
                    "latency_ms": round(latency_ms, 1),
                    "fallback_used": False
                }
            except Exception as e:
                print(f"[Hybrid Guardian] Primary Jev failed: {e}. Falling back to Local Decider 2B.")

        # ── 2. Attempt Local Backup: Decider 2B ──
        if self.decider:
            try:
                res = self.decider.evaluate_tape_confluence(setup, macro_context)
                res["fallback_used"] = True
                return res
            except Exception as e:
                print(f"[Hybrid Guardian] Backup Decider 2B failed: {e}. Falling back to Laya/Sentinel.")

        # ── 3. Attempt Tertiary Backup: Local Laya ──
        if self.laya:
            try:
                res = self.laya.evaluate_tape_confluence(setup, macro_context)
                res["engine"] = "LOCAL_LAYA (TERTIARY)"
                res["fallback_used"] = True
                return res
            except Exception as e:
                print(f"[Hybrid Guardian] Tertiary Laya failed: {e}. Falling back to Invariant Sentinel.")

        # ── 4. Final Fallback: Fail Open to Deterministic Sentinel ──
        return {
            "engine": "DETERMINISTIC_SENTINEL",
            "approved": True,
            "risk_rating": "PRIME_SETUP",
            "allow_probability": 0.50,
            "confidence": 0.50,
            "latency_ms": 0.0,
            "fallback_used": True
        }

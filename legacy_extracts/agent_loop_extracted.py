"""
agent_loop.py — Self-Improving Overnight Loop
Calls Claude API → proposes param change → backtests → keeps if better

Run before sleeping. Wake up to 50–100 experiments.
Requires: ANTHROPIC_API_KEY in environment
"""

import os
import json
import copy
import time
import requests
from datetime import datetime
from backtest import score
from strategy import PARAMS

LOG_FILE = "experiments.json"

# ── Prompt for Claude ────────────────────────────────────
SYSTEM_PROMPT = """You are an expert quantitative trader specializing in Smart Money Concepts (SMC/ICT) for binary options.

You are improving a 4-step IBT strategy:
  Step 1: Swing Liquidity Sweep OR Extreme FVG Mitigated  
  Step 2: Sharp Turn OR Inverse FVG
  Step 3: C-FVG / BAG / FVG + FVG Mitigated
  Step 4: Clear Target → Enter

You will be given:
- Current parameters (JSON)
- Current score and metrics
- History of experiments

Your task: suggest ONE specific parameter change that may improve the score.
The score = win_rate × profit_factor × (1 - max_drawdown). Higher is better.
Binary breakeven at 1.80x payout = 55.6% win rate.

Rules:
- Change ONLY ONE parameter at a time
- Keep changes small and logical (e.g. sweep_lookback from 5 to 7, not 5 to 50)
- Explain WHY this change may improve the score in one sentence
- Output ONLY valid JSON: {"param": "name", "value": new_value, "reason": "one sentence"}
- No markdown, no extra text
"""

def ask_claude(current_params, current_metrics, history):
    recent = history[-5:] if len(history) > 5 else history
    user_msg = f"""Current parameters:
{json.dumps(current_params, indent=2)}

Current score: {current_metrics.get('score', 0)}
Win rate: {current_metrics.get('win_rate', 0)}
Profit factor: {current_metrics.get('profit_factor', 0)}
Max drawdown: {current_metrics.get('max_drawdown', 0)}
Total trades: {current_metrics.get('total_trades', 0)}

Recent experiment history (last 5):
{json.dumps(recent, indent=2)}

Suggest ONE parameter change to improve the score."""

    resp = requests.post(
        "https://api.anthropic.com/v1/messages",
        headers={
            "x-api-key": os.environ["ANTHROPIC_API_KEY"],
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
        json={
            "model": "claude-sonnet-4-20250514",
            "max_tokens": 200,
            "system": SYSTEM_PROMPT,
            "messages": [{"role": "user", "content": user_msg}],
        },
        timeout=30,
    )
    resp.raise_for_status()
    text = resp.json()["content"][0]["text"].strip()
    return json.loads(text)


def run_experiment(params):
    """Score a given set of parameters."""
    return score(params)


def save_log(history):
    with open(LOG_FILE, "w") as f:
        json.dump(history, f, indent=2)


def main(max_experiments=100, sleep_between=30):
    print(f"\n{'═'*50}")
    print(f"IBT AutoResearch — {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"Max experiments: {max_experiments}")
    print(f"{'═'*50}\n")

    # Load existing log if present
    history = []
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE) as f:
            history = json.load(f)

    # Baseline score
    best_params  = copy.deepcopy(PARAMS)
    best_metrics = run_experiment(best_params)
    best_score   = best_metrics["score"]

    print(f"Baseline score: {best_score}")
    print(f"Baseline metrics: {best_metrics}\n")

    history.append({
        "experiment": 0,
        "change": "baseline",
        "params": copy.deepcopy(best_params),
        "metrics": best_metrics,
        "kept": True,
        "timestamp": datetime.now().isoformat(),
    })

    for exp in range(1, max_experiments + 1):
        print(f"── Experiment {exp}/{max_experiments} ──")

        try:
            # Ask Claude for a parameter change
            suggestion = ask_claude(best_params, best_metrics, history)
            param_name = suggestion["param"]
            new_value  = suggestion["value"]
            reason     = suggestion["reason"]
            print(f"  Suggestion: {param_name} → {new_value} | {reason}")

            # Apply change
            test_params = copy.deepcopy(best_params)
            if "." in param_name:
                # nested key e.g. "pair_weights.EURJPY"
                outer, inner = param_name.split(".", 1)
                test_params[outer][inner] = new_value
            else:
                test_params[param_name] = new_value

            # Score it
            test_metrics = run_experiment(test_params)
            test_score   = test_metrics["score"]
            print(f"  Score: {test_score} (best: {best_score})")

            # Keep or revert
            kept = test_score > best_score
            if kept:
                best_params  = test_params
                best_metrics = test_metrics
                best_score   = test_score
                print(f"  ✓ KEPT — new best: {best_score}")

                # Write best params to strategy.py PARAMS
                _update_strategy_params(best_params)
            else:
                print(f"  ✗ reverted")

            history.append({
                "experiment": exp,
                "change": f"{param_name} → {new_value}",
                "reason": reason,
                "score": test_score,
                "best_score": best_score,
                "metrics": test_metrics,
                "kept": kept,
                "timestamp": datetime.now().isoformat(),
            })

        except Exception as e:
            print(f"  Error: {e}")
            history.append({
                "experiment": exp,
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            })

        save_log(history)
        time.sleep(sleep_between)

    print(f"\n{'═'*50}")
    print(f"Done. Best score: {best_score}")
    print(f"Best params: {json.dumps(best_params, indent=2)}")
    print(f"Full log saved to: {LOG_FILE}")


def _update_strategy_params(params):
    """Overwrites PARAMS in strategy.py with the current best."""
    with open("strategy.py", "r") as f:
        content = f.read()

    # Find and replace the PARAMS dict
    import re
    new_params_str = f"PARAMS = {json.dumps(params, indent=4)}\n"
    content = re.sub(
        r"PARAMS\s*=\s*\{.*?\}\n",
        new_params_str,
        content,
        flags=re.DOTALL,
        count=1,
    )
    with open("strategy.py", "w") as f:
        f.write(content)


if __name__ == "__main__":
    main(max_experiments=100, sleep_between=30)

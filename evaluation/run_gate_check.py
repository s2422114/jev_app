"""門の検証を実行する。

- backend の questions.py / judge.py をそのまま使う（本番と同じ質問文・閾値・合成）。
- 門で落ちても早期終了せず、7問すべての値を記録する。
- repeat が 3 の材料は3回投げ、3回分をすべて残す。

実行: cd backend && uv run python ../evaluation/run_gate_check.py
"""

from __future__ import annotations

import asyncio
import json
import sys
import time
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
sys.path.insert(0, str(ROOT / "evaluation"))

from dotenv import load_dotenv  # noqa: E402

load_dotenv(ROOT / ".env")

from typesafe_sdk import AsyncTypeSafeClient  # noqa: E402

from app.judge import ask_jev, evaluate  # noqa: E402
from app.questions import (  # noqa: E402
    GATE_THRESHOLDS,
    MIN_CONFIDENCE,
    SCORE_KEYS,
    SCORE_THRESHOLD,
    WEIGHTS,
)
from gate_materials import MATERIALS, PREDICTIONS  # noqa: E402

RESULTS_DIR = Path(__file__).with_name("demo_results")  # 架空の材料なのでコミットする
SLEEP_SECONDS = 0.5  # 連続で叩かないための間隔


async def main() -> None:
    records: list[dict] = []
    async with AsyncTypeSafeClient() as client:
        for material in MATERIALS:
            for run_index in range(1, material["repeat"] + 1):
                answers = await ask_jev(client, material["state"])
                result = evaluate(answers, material["state"])
                records.append(
                    {
                        "no": material["no"],
                        "run": run_index,
                        "title": material["title"],
                        "aim": material["aim"],
                        "style": material["style"],
                        "criteria_flag": material["criteria_flag"],
                        "note": material.get("note"),
                        "has_expectation": bool(
                            material["state"]["事前の予想"]["会社予想"]
                        ),
                        "answers": {k: v.model_dump() for k, v in answers.items()},
                        "blocked_by": result.blocked_by,
                        "low_confidence": result.low_confidence,
                        "score": result.score,
                        "listed": result.listed,
                    }
                )
                gates = " ".join(
                    f"{k[:4]}={answers[k].normalized:.2f}" for k in GATE_THRESHOLDS
                )
                print(
                    f"{material['no']:>2}-{run_index} {gates} "
                    f"blocked={result.blocked_by} lowconf={result.low_confidence} "
                    f"score={result.score}"
                )
                time.sleep(SLEEP_SECONDS)

    RESULTS_DIR.mkdir(exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    path = RESULTS_DIR / f"gate_check_{stamp}.json"
    path.write_text(
        json.dumps(
            {
                "run_at": stamp,
                # 使った閾値と重みを必ず残す（後から再集計できるように）
                "settings": {
                    "gate_thresholds": GATE_THRESHOLDS,
                    "min_confidence": MIN_CONFIDENCE,
                    "score_keys": list(SCORE_KEYS),
                    "weights": WEIGHTS,
                    "score_threshold": SCORE_THRESHOLD,
                },
                "predictions": PREDICTIONS,
                "records": records,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print(f"\n記録: {path}")


if __name__ == "__main__":
    asyncio.run(main())

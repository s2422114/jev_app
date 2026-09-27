"""門の検証の結果を、判定デモが配るデータに変換する。

画面からは毎回 Jev を呼ばず、ここで作った JSON を配る。
値はすべて実測（evaluation/results/gate_check_*.json）。

実行: uv run python evaluation/build_demo_data.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "evaluation"))

from gate_materials import MATERIALS  # noqa: E402

RESULTS_DIR = ROOT / "evaluation" / "demo_results"
OUT_PATH = ROOT / "backend" / "data" / "demo.json"


def latest_result() -> dict:
    files = sorted(RESULTS_DIR.glob("gate_check_*.json"))
    if not files:
        raise SystemExit("gate_check の結果がありません")
    return json.loads(files[-1].read_text(encoding="utf-8"))


def build() -> dict:
    source = latest_result()
    by_no: dict[int, list[dict]] = {}
    for record in source["records"]:
        by_no.setdefault(record["no"], []).append(record)

    materials = []
    for material in MATERIALS:
        runs = sorted(by_no[material["no"]], key=lambda r: r["run"])
        first = runs[0]
        materials.append(
            {
                "no": material["no"],
                "title": material["title"],
                "aim": material["aim"],
                "style": material["style"],
                "criteria_flag": material["criteria_flag"],
                "note": material.get("note"),
                "has_expectation": first["has_expectation"],
                "state": material["state"],
                "result": {
                    "answers": first["answers"],
                    "blocked_by": first["blocked_by"],
                    "low_confidence": first["low_confidence"],
                    "score": first["score"],
                    "listed": first["listed"],
                },
                # 3回投げたものは、ぶれの幅を画面で見せるために全回を残す
                "runs": [
                    {
                        "run": r["run"],
                        "answers": {k: v["normalized"] for k, v in r["answers"].items()},
                        "blocked_by": r["blocked_by"],
                        "low_confidence": r["low_confidence"],
                        "score": r["score"],
                    }
                    for r in runs
                ],
            }
        )

    usages = [r.get("usage") for r in source["records"] if r.get("usage")]
    total_usage = None
    if usages:
        total_usage = {
            "input_tokens": sum(u.get("input_tokens") or 0 for u in usages),
            "output_tokens": sum(u.get("output_tokens") or 0 for u in usages),
        }

    return {
        "source": f"evaluation/demo_results/gate_check_{source['run_at']}.json",
        "usage": total_usage,
        "measured_at": source["run_at"],
        "model": "jev-1.13.0",
        "settings": source["settings"],
        "materials": materials,
    }


def main() -> None:
    data = build()
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"wrote {OUT_PATH} ({len(data['materials'])} materials)")


if __name__ == "__main__":
    main()

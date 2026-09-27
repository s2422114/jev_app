"""判定デモが配るデータ（実測値）の読み込み。

evaluation/build_demo_data.py が作った backend/data/demo.json を読むだけ。
画面から毎回 Jev を呼ばないのは、公開後の呼び出し回数を抑えるため。
値はすべて実測なので、表示される確率は本物。
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from app.models import DemoJudgement, JudgeResult, MaterialSummary

DEMO_PATH = Path(__file__).resolve().parents[1] / "data" / "demo.json"


@lru_cache(maxsize=1)
def _demo() -> dict:
    return json.loads(DEMO_PATH.read_text(encoding="utf-8"))


def settings() -> dict:
    """判定に使った閾値と重み。画面に出すため。"""
    demo = _demo()
    return {
        **{k: v for k, v in demo["settings"].items() if k != "score_keys"},
        "measured_at": demo["measured_at"],
        "model": demo["model"],
    }


def list_materials() -> list[MaterialSummary]:
    return [
        MaterialSummary(
            no=m["no"],
            title=m["title"],
            style=m["style"],
            criteria_flag=m["criteria_flag"],
            aim=m["aim"],
            listed=m["result"]["listed"],
            values={k: v["normalized"] for k, v in m["result"]["answers"].items()},
            score=m["result"]["score"],
            blocked_by=m["result"]["blocked_by"],
        )
        for m in _demo()["materials"]
    ]


def get_judgement(no: int) -> DemoJudgement | None:
    for m in _demo()["materials"]:
        if m["no"] == no:
            return DemoJudgement(
                no=m["no"],
                title=m["title"],
                aim=m["aim"],
                style=m["style"],
                criteria_flag=m["criteria_flag"],
                note=m.get("note"),
                has_expectation=m["has_expectation"],
                result=JudgeResult(material=m["state"], **m["result"]),
                runs=m["runs"],
            )
    return None

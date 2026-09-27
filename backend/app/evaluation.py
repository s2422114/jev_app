"""評価結果（デモ）の読み込み。

画面に出すのは5つの集計だけ。残り13本は JSON に残しているが、
ここでは返さない（読み切れない量を画面に出さないため、かつ payload を小さく保つため）。

本番データは backend/data/real/ に置き、リポジトリには含めない。
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parents[1] / "data"
DEMO_PATH = DATA_DIR / "evaluation.demo.json"
REAL_PATH = DATA_DIR / "real" / "evaluation.json"


@lru_cache(maxsize=1)
def _raw() -> dict | None:
    """本番があればそちらを、無ければデモを読む。"""
    path = REAL_PATH if REAL_PATH.exists() else DEMO_PATH
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _stat(row: dict) -> dict:
    return {
        "count": row["件数"],
        "cumulative": row["累積リターン"],
        "mean": row["平均リターン"],
        "median": row.get("中央値", 0.0),
        "win_rate": row["勝率"],
        "stdev": row.get("標準偏差", 0.0),
        "max_drawdown": row.get("最大ドローダウン", 0.0),
    }


def evaluation() -> dict | None:
    raw = _raw()
    if raw is None:
        return None

    permutation = raw["10_並べ替え検定"]
    return {
        "demo": raw["デモ"],
        "notice": raw.get("注意"),
        "period": raw["期間"],
        "count": raw["件数"],
        "settings": raw["設定"],
        "comparison": {name: _stat(row) for name, row in raw["1_比較"].items()},
        "score_sweep": [
            {"threshold": row["閾値"], "count": row["件数"], "mean": row["平均リターン"]}
            for row in raw["2_スコア閾値"]
        ],
        "permutation": {
            "listed": permutation.get("通過件数", 0),
            "observed": permutation.get("Jev の平均リターン"),
            "trials": permutation.get("試行回数"),
            "random_at_least": permutation.get("ランダムが同等以上だった割合"),
            "p5": permutation.get("ランダムの5%点"),
            "p95": permutation.get("ランダムの95%点"),
            "histogram": permutation.get("分布"),
        },
        "confidence_bands": [
            {"band": row["confidence"], "count": row["件数"], "mean": row["平均リターン"], "win_rate": row["勝率"]}
            for row in raw["9a_confidence別"]
        ],
        "blocked": {
            key: {"count": row["落とした件数"], "mean": row["平均リターン"]}
            for key, row in raw["8_落ちた門の内訳"].items()
        },
    }

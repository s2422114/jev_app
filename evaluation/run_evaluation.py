"""評価を実行して、集計18本＋ペア（集計19）を書き出す。

  uv run python evaluation/run_evaluation.py --period tuning
  uv run python evaluation/run_evaluation.py --period holdout --confirm-holdout

**検証期間（holdout）は最後に1回だけ実行する。**
そのため、holdout は --confirm-holdout が無いと動かず、
すでに実行済みなら（結果ファイルがあれば）拒否する。自制に頼らない作りにしている。

いまは架空のリターン（--source demo）で動かしている。
本番では --source real に差し替える。集計の形は変えない。
"""

from __future__ import annotations

import argparse
import json
import random
import sys
import time
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "evaluation"))

import pipeline as P  # noqa: E402

DEMO_PATH = ROOT / "backend" / "data" / "demo.json"
# 本番の集計は evaluation/results/（.gitignore 済み）。
# デモの集計だけ backend/data/evaluation.demo.json に置き、コミットする。
# 同じパスに本番データを上書きして、気づかずコミットするのを防ぐため名前を分けている。
RESULTS_DIR = ROOT / "evaluation" / "results"
DEMO_OUT = ROOT / "backend" / "data" / "evaluation.demo.json"
REAL_OUT = ROOT / "backend" / "data" / "real" / "evaluation.json"

SEED = 20260928  # 架空のリターンを引く乱数のシード
DAILY_SIGMA = 0.02
START = date(2026, 6, 1)
TUNING_RATIO = 2 / 3  # 最初の2/3が調整期間、残りが検証期間


def build_demo_records(rng: random.Random) -> list[P.Record]:
    """デモ用の記録。判定は実測値、リターンだけ乱数で作る。

    **リターンは判定と無関係に引く。** 相関させると自作自演になり、
    本番データで回したときに気づけない。
    """
    demo = json.loads(DEMO_PATH.read_text(encoding="utf-8"))
    materials = demo["materials"]

    days: list[date] = []
    day = START
    while len(days) < len(materials):
        if day.weekday() < 5:
            days.append(day)
        day += timedelta(days=7)

    records = []
    for material, day in zip(materials, days):
        answers = material["result"]["answers"]
        open_next = round(1000 * (1 + rng.uniform(-0.3, 0.3)), 1)
        close_next = round(open_next * (1 + rng.gauss(0, DAILY_SIGMA)), 1)
        records.append(
            P.Record(
                no=material["no"],
                date=day.isoformat(),
                code=material["state"]["銘柄"]["コード"],
                title=material["title"],
                text=material["state"]["ニュース"]["本文"],
                values={k: v["normalized"] for k, v in answers.items()},
                confidences={k: v["confidence"] for k, v in answers.items()},
                open_next=open_next,
                close_next=close_next,
            )
        )
    return records, demo["settings"]


def split(records: list[P.Record]) -> tuple[list[P.Record], list[P.Record]]:
    """日付順に並べて、最初の2/3を調整期間、残りを検証期間にする。"""
    ordered = sorted(records, key=lambda r: r.date)
    cut = int(len(ordered) * TUNING_RATIO)
    return ordered[:cut], ordered[cut:]


def aggregate(records: list[P.Record], settings: P.Settings, topix: list[float], demo: bool) -> dict:
    steps = [round(0.50 + 0.05 * i, 2) for i in range(9)]  # 0.50〜0.90 を 0.05 刻み
    return {
        "デモ": demo,
        "注意": "リターンはすべて乱数で作った架空の値です。数字に意味はありません。" if demo else None,
        "期間": f"{records[0].date} 〜 {records[-1].date}",
        "件数": len(records),
        "設定": {
            "門の閾値": settings.gate_thresholds,
            "confidence 下限": settings.min_confidence,
            "重み": settings.weights,
            "スコア閾値": settings.score_threshold,
        },
        "1_比較": P.compare_all(records, settings, topix),
        "2_スコア閾値": P.sweep_score_threshold(records, settings, steps),
        "3_門の閾値_一括": P.sweep_gate_all(records, settings, steps),
        "4_門の閾値_個別": P.sweep_gate_each(records, settings, steps),
        "5_confidence下限": P.sweep_min_confidence(records, settings, steps),
        "6_重み": P.sweep_weights(records, settings),
        "7_質問ごとの分位": P.question_quantiles(records),
        "8_落ちた門の内訳": P.blocked_breakdown(records, settings),
        "9a_confidence別": P.confidence_bands(
            records, [(0.0, 0.3), (0.3, 0.5), (0.5, 0.7), (0.7, 0.9), (0.9, 1.01)]
        ),
        "9b_校正_5群": {k: P.calibration(records, k, 5) for k in P.ALL_KEYS},
        "9b_校正_10群": {k: P.calibration(records, k, 10) for k in P.ALL_KEYS},
        "10_並べ替え検定": P.permutation_test(records, settings, trials=10_000, seed=SEED),
        "11_種類別": P.by_category(records, settings),
        "12_期間別_月": P.by_period(records, settings, "月"),
        "12_期間別_週": P.by_period(records, settings, "週"),
        "13_本文長別": P.by_text_length(records),
        "14_キーワード内訳": P.keyword_breakdown(records),
        "15_順位相関": P.rank_correlation(records, settings),
        "16_値の分布": P.value_histograms(records),
        "17_サンプリングの振れ": P.sampling_variation(
            records, settings, size=500, seeds=[1, 2, 3, 4, 5]
        ),
        "18_実行コスト": P.cost_summary(None, request_count=len(records), seconds=None),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--period", choices=["tuning", "holdout"], required=True)
    parser.add_argument("--source", choices=["demo", "real"], default="demo")
    parser.add_argument(
        "--confirm-holdout",
        action="store_true",
        help="検証期間を開く。閾値の調整が終わってから1回だけ使う",
    )
    parser.add_argument("--force", action="store_true", help="検証期間の再実行を許す")
    args = parser.parse_args()

    out_dir = RESULTS_DIR / args.period
    out_path = out_dir / "aggregates.json"

    if args.period == "holdout":
        if not args.confirm_holdout:
            raise SystemExit(
                "検証期間は --confirm-holdout を付けたときだけ実行できます。\n"
                "閾値の調整が終わっていますか。"
            )
        if out_path.exists() and not args.force:
            raise SystemExit(
                f"すでに実行済みです（{out_path}）。\n"
                "検証期間は1回だけ見る約束なので、やり直すなら --force を明示してください。"
            )

    if args.source == "real":
        raise SystemExit("本番データの読み込みはまだ実装していません（フェーズ6）")

    started = time.time()
    rng = random.Random(SEED)
    records, raw_settings = build_demo_records(rng)
    settings = P.Settings(
        gate_thresholds=raw_settings["gate_thresholds"],
        min_confidence=raw_settings["min_confidence"],
        weights=raw_settings["weights"],
        score_threshold=raw_settings["score_threshold"],
    )

    tuning, holdout = split(records)
    target = tuning if args.period == "tuning" else holdout
    topix = [rng.gauss(0.0002, DAILY_SIGMA * 0.4) for _ in target]

    output = aggregate(target, settings, topix, demo=args.source == "demo")
    output["18_実行コスト"]["所要秒"] = round(time.time() - started, 2)
    output["seed"] = SEED

    out_dir.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    # 集計19：ペア。公開しない（.gitignore に入れてある）。
    (out_dir / "pairs.json").write_text(
        json.dumps(P.pairs(target), ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    # 画面が読むのは調整期間のほう。デモと本番でファイルを分ける。
    if args.period == "tuning":
        screen_path = DEMO_OUT if args.source == "demo" else REAL_OUT
        screen_path.parent.mkdir(parents=True, exist_ok=True)
        screen_path.write_text(
            json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        print(f"画面用: {screen_path}")

    print(f"[{args.period}] {output['期間']} / {output['件数']}件")
    for name, v in output["1_比較"].items():
        print(f"  {name:<12} 件数 {v['件数']:>2} / 累積 {v['累積リターン']:+.2%} / 平均 {v['平均リターン']:+.2%}")
    print(f"\n書き出し: {out_path}\n          {out_dir / 'pairs.json'}")


if __name__ == "__main__":
    main()

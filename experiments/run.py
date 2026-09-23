"""実験定義を読み込んで実行し、結果と usage を記録する。

  uv run python experiments/run.py a_numbers_and_labels --dry-run   # 投げずに state と質問を確認
  uv run python experiments/run.py a_numbers_and_labels             # 実行して results/ に記録
  uv run python experiments/run.py a_numbers_and_labels --only exp1 # id の前方一致で絞る

予想（PREDICTIONS）が空のケースがあると実行しない。先に予想を書くため。
"""

from __future__ import annotations

import argparse
import importlib
import json
import sys
from datetime import datetime
from pathlib import Path

EXPERIMENTS_DIR = Path(__file__).parent
sys.path.insert(0, str(EXPERIMENTS_DIR))

from dotenv import load_dotenv  # noqa: E402

load_dotenv(EXPERIMENTS_DIR.parent / ".env")

from typesafe_sdk import TypeSafeClient  # noqa: E402

RESULTS_DIR = EXPERIMENTS_DIR / "results"


def dump_questions(questions: dict) -> dict:
    return {name: q.model_dump() for name, q in questions.items()}


def format_answer(answer) -> str:
    kind = answer.type
    if kind == "noul":
        return f"noul={answer.noul:.3f}"
    if kind == "choice":
        return f"choice={answer.choice} (conf={answer.confidence:.3f})"
    return f"score={answer.score:.3f} (conf={answer.confidence:.3f})"


def blank_questions(case: dict) -> list[str]:
    """質問文や criteria が空のままのものを返す（C のように質問文を人が書く定義向け）。"""
    blanks = []
    for name, question in case["questions"].items():
        data = question.model_dump()
        if not str(data.get("instructions") or "").strip():
            blanks.append(f"{case['id']}.{name}.instructions")
        criteria = data.get("criteria")
        if isinstance(criteria, dict) and not criteria:
            blanks.append(f"{case['id']}.{name}.criteria")
        elif isinstance(criteria, dict):
            for key, value in criteria.items():
                if isinstance(value, str) and not value.strip():
                    blanks.append(f"{case['id']}.{name}.criteria[{key}]")
        elif isinstance(criteria, (list, tuple)):
            if not criteria:
                blanks.append(f"{case['id']}.{name}.criteria")
            for i, value in enumerate(criteria):
                if isinstance(value, str) and not value.strip():
                    blanks.append(f"{case['id']}.{name}.criteria[{i}]")
    return blanks


def run_case(client: TypeSafeClient, case: dict) -> dict:
    response = client.system_one(state=case["state"], questions=case["questions"])
    return {
        "id": case["id"],
        "experiment": case["experiment"],
        "title": case["title"],
        "stock": case["stock"],
        "condition": case["condition"],
        "prediction": case["prediction"],
        "state": case["state"],
        "questions": dump_questions(case["questions"]),
        "model": response.model,
        "usage": response.usage.model_dump(),
        "answers": {name: answer.model_dump() for name, answer in response.answers.items()},
        "summary": {name: format_answer(answer) for name, answer in response.answers.items()},
    }


def write_results(module_name: str, records: list[dict]) -> tuple[Path, Path]:
    RESULTS_DIR.mkdir(exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    json_path = RESULTS_DIR / f"{module_name}_{stamp}.json"
    md_path = RESULTS_DIR / f"{module_name}_{stamp}.md"

    total_in = sum(r["usage"].get("input_tokens") or 0 for r in records)
    total_out = sum(r["usage"].get("output_tokens") or 0 for r in records)
    json_path.write_text(
        json.dumps(
            {
                "module": module_name,
                "run_at": stamp,
                "model": records[0]["model"] if records else None,
                "total_usage": {"input_tokens": total_in, "output_tokens": total_out},
                "records": records,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    lines = [
        f"# 実行結果: {module_name}",
        "",
        f"- 実行日時: {stamp}",
        f"- モデル: {records[0]['model'] if records else '-'}",
        f"- 合計 usage: 入力 {total_in} / 出力 {total_out} トークン",
        "",
        "| id | ケース | 予想 | 答え | usage(in/out) |",
        "|---|---|---|---|---|",
    ]
    for r in records:
        answers = " / ".join(f"{k}: {v}" for k, v in r["summary"].items())
        usage = f"{r['usage'].get('input_tokens')}/{r['usage'].get('output_tokens')}"
        lines.append(f"| {r['id']} | {r['title']} | {r['prediction']} | {answers} | {usage} |")
    lines.append("")
    md_path.write_text("\n".join(lines), encoding="utf-8")
    return json_path, md_path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("module", help="experiments/definitions/ のモジュール名")
    parser.add_argument("--only", default=None, help="ケース id の前方一致で絞る")
    parser.add_argument("--dry-run", action="store_true", help="API を呼ばずに state と質問を表示する")
    args = parser.parse_args()

    module = importlib.import_module(f"definitions.{args.module}")
    cases = [c for c in module.CASES if args.only is None or c["id"].startswith(args.only)]
    if not cases:
        raise SystemExit("該当するケースがありません")

    if args.dry_run:
        for case in cases:
            repeat = case.get("repeat", 1)
            suffix = f"  ×{repeat}回" if repeat > 1 else ""
            print(f"--- {case['id']}  (実験{case['experiment']}) {case['title']}{suffix}")
            print("  予想:", case["prediction"] or "(未記入)")
            print("  state:", json.dumps(case["state"], ensure_ascii=False))
            print("  questions:", json.dumps(dump_questions(case["questions"]), ensure_ascii=False))
        print(f"\n{len(cases)} ケース（未実行）")
        return

    blanks = [b for c in cases for b in blank_questions(c)]
    if blanks:
        raise SystemExit("質問文または criteria が未記入です:\n  " + "\n  ".join(blanks))

    missing = [c["id"] for c in cases if not c["prediction"].strip()]
    if missing:
        raise SystemExit("予想が未記入のケースがあります:\n  " + "\n  ".join(missing))

    records = []
    with TypeSafeClient() as client:
        for case in cases:
            repeat = case.get("repeat", 1)
            for i in range(repeat):
                record = run_case(client, case)
                if repeat > 1:
                    record["id"] = f"{case['id']}#{i + 1}"
                    record["run_index"] = i + 1
                records.append(record)
                answers = " / ".join(f"{k}: {v}" for k, v in record["summary"].items())
                print(f"{record['id']:<26} {answers}")

    json_path, md_path = write_results(args.module, records)
    print(f"\n記録: {json_path}\n      {md_path}")


if __name__ == "__main__":
    main()

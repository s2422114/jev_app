"""Jev に7問を投げ、正規化・門・合成をしてスコアを出す。

Jev は判断を返すだけで、流れはこのコードが持つ（notes/decisions.md）。
閾値と重みは questions.py にまとめてあり、ここには数値を書かない。
"""

from __future__ import annotations

from typesafe_sdk import AsyncTypeSafeClient

from app.models import Answer, JudgeResult
from app.questions import (
    GATE_THRESHOLDS,
    MIN_CONFIDENCE,
    QUESTIONS,
    SCORE_KEYS,
    SCORE_THRESHOLD,
    WEIGHTS,
)


async def ask_jev(client: AsyncTypeSafeClient, material: dict) -> dict[str, Answer]:
    """7問を1リクエストで投げ、答えを 0〜1 に揃えて返す。

    質問どうしは並列に評価され、互いに影響しない（実験27で確認済み）。
    分けて投げると 2.3倍高く、遅くなるだけなので、必ずまとめて投げる。
    """
    response = await client.system_one(state=material, questions=QUESTIONS)

    answers: dict[str, Answer] = {}
    for key, answer in response.answers.items():
        if answer.type == "noul":
            # Noul は「はいである確率」。もともと 0〜1 なのでそのまま。confidence は返らない。
            answers[key] = Answer(raw=answer.noul, normalized=answer.noul)
        else:
            # Score は段階の期待値（3段階なら 0〜2）。段階数は legend の数で分かるので、
            # 最大値（段階数 - 1）で割って 0〜1 に揃える。段階を増やしてもここは直さなくてよい。
            top = len(answer.legend) - 1
            answers[key] = Answer(
                raw=answer.score,
                normalized=answer.score / top,
                confidence=answer.confidence,
            )
    return answers


def evaluate(answers: dict[str, Answer], material: dict) -> JudgeResult:
    """門を通し、confidence で絞り、重み付き和でスコアを出す。

    Jev を呼ばない純粋な計算なので同期関数。閾値と重みは questions.py にある。
    """
    # 門：落ちた時点で打ち切らず、4問すべてを見る。
    # 何で弾かれたかを全部返せるように（門を4つに割った意味がここに出る）。
    blocked_by = [
        key
        for key, threshold in GATE_THRESHOLDS.items()
        if answers[key].normalized < threshold
    ]

    # confidence：Score の3問だけが対象。Noul には confidence が返らない。
    # 平均を取らず「1つでも低ければ見送る」で始める（notes/decision-design.md）。
    low_confidence = [
        key
        for key in SCORE_KEYS
        if answers[key].confidence is not None and answers[key].confidence < MIN_CONFIDENCE
    ]

    if blocked_by or low_confidence:
        # 落ちたらスコアは計算しない。答えは7問ぶんそのまま返す。
        return JudgeResult(
            material=material,
            answers=answers,
            blocked_by=blocked_by,
            low_confidence=low_confidence,
            score=None,
            listed=False,
        )

    # 重み付き和。すべて 0〜1 に揃えてあるので、満点は 1.0。
    score = sum(WEIGHTS[key] * answers[key].normalized for key in WEIGHTS)

    return JudgeResult(
        material=material,
        answers=answers,
        blocked_by=[],
        low_confidence=[],
        score=score,
        listed=score >= SCORE_THRESHOLD,
    )

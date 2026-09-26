"""API が返す JSON の形。

FastAPI はこの型から JSON への変換と /docs のドキュメントを作る。
型と違う値を返そうとするとサーバー側でエラーになるので、
壊れた形がフロントに届かない。フロント側にも同じ形の型を書く。
"""

from __future__ import annotations

from pydantic import BaseModel


class Answer(BaseModel):
    """Jev の1問ぶんの答え。Noul と Score をまとめて扱う。"""

    raw: float
    """Jev が返した値そのもの。Noul は 0〜1 の確率、Score は 0〜2 の期待値。"""

    normalized: float
    """0〜1 に揃えた後の値。Score は raw / 2、Noul は raw のまま。"""

    confidence: float | None = None
    """Score のみ。Noul には confidence が返らないので None。"""


class JudgeResult(BaseModel):
    """材料1件に対する判断の結果。"""

    material: dict
    """判断の対象にした材料。画面で中身を見られるようにそのまま返す。"""

    answers: dict[str, Answer]
    """7問すべての答え。キーは questions.QUESTIONS のキー。
    門で落ちても、落ちた質問の値を画面で見られるように常に7問ぶん返す。"""

    blocked_by: list[str]
    """門で落ちた質問のキー。落ちた時点で打ち切らず、4問すべてを見て集める。
    空なら門は通過。"""

    low_confidence: list[str]
    """confidence が下限を下回った質問のキー（Score の3問が対象）。
    質問名と段階名が混ざらないよう、blocked_by とは別に持つ。"""

    score: float | None = None
    """重み付き和で合成したスコア（0〜1）。門か confidence で落ちた場合は計算しないので None。"""

    listed: bool
    """翌日の売買リストに入れるか。門・confidence・スコアの閾値をすべて通った場合だけ true。"""

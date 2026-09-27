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


class MaterialSummary(BaseModel):
    """材料の一覧に出す情報。本文は含めない。"""

    no: int
    title: str
    style: str
    """文体の種類。同じ事実でも文体で評価が動くため、比較できるように残している。"""
    criteria_flag: str
    """market_moving の criteria に例として明記されている種類かどうか。"""
    aim: str
    """この材料で何を見たかったか。"""
    listed: bool
    """判定の結果（リストに入れるか）。一覧で見分けられるように入れる。"""

    values: dict[str, float]
    """7問の値（0〜1）。一覧で16件を横に比べられるように含める。"""

    score: float | None = None
    """合成スコア。門か confidence で落ちた場合は None。"""

    blocked_by: list[str]
    """落ちた門。一覧では色を付けないが、並べ替えや説明に使えるように返す。"""


class DemoJudgement(BaseModel):
    """材料1件の判定。値は実測（毎回 Jev を呼ぶのではなく、測った結果を配る）。"""

    no: int
    title: str
    aim: str
    style: str
    criteria_flag: str
    note: str | None = None
    """比較の軸がずれているなど、結果を読むときの注意。"""
    has_expectation: bool
    """事前の予想が state に入っているか。空のとき above_expectation は 0.5 付近になる。"""
    result: JudgeResult
    runs: list[dict]
    """同じ材料を複数回投げた場合の全回。ぶれの幅を見るため。"""


class Settings(BaseModel):
    """判定に使った閾値と重み。画面で閾値の位置を示すために返す。"""

    gate_thresholds: dict[str, float]
    min_confidence: float
    weights: dict[str, float]
    score_threshold: float
    measured_at: str
    """この判定を実測した日時。"""
    model: str

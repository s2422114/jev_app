"""Jev に投げる7問と、判断に使う定数。

質問文と閾値はこの1ファイルに集約する（人がレビューできるようにするため。
notes/decisions.md「質問文と閾値の定数は1ファイルに集約する」）。

- instructions と criteria は未記入。ユーザーが書く。
- 質問の一覧・型・使い方は notes/decision-design.md の「Jev に聞くこと（7問）」。
- Score は 0〜2 を返すので、judge.py で 2 で割って 0〜1 に正規化してから使う。
  ここに書く閾値は、正規化した後の 0〜1 のスケール。
"""

from __future__ import annotations

from typesafe_sdk import Noul, Score

# ---------------------------------------------------------------- 質問文
# state のキーはバッククォートで指せる（例: `材料.本文`）。
# Score の criteria は 0 から順に並べた3段階の説明。

QUESTIONS = {
    # --- 門に使う4問 ---
    "new_info": Noul(instructions="新しい情報を含んでいるか"),
    "market_moving": Noul(instructions="`ニュース`が業績に直結するか", criteria={"true": "業績（売上や利益）に直接影響する内容。例えば、決算発表、業績の上方修正・下方修正、M&A・買収、業務提携、自社株買い",
                                                                            "false": "業績に直結しない内容。例えば、本社移転、人事異動、既報の焼き直し、アナリストの分析記事"}),
    "official_announcement": Noul(instructions="企業が公式に発表した内容か"),
    "direction": Score(instructions="企業にとって良い材料か悪い材料か", criteria=["悪い", "どちらでもない", "良い"]),
    # --- 重み付き和に使う3問 ---
    "above_expectation": Score(instructions="事前の予想に対して上振れているか", criteria=["下振れ", "想定内", "上振れ"]),
    "magnitude": Score(instructions="業績への影響が大きいか", criteria=["小さい", "中くらい", "大きい"]),
    "continuing": Noul(instructions="その影響は続くものか"),
}

# Score で聞く質問。judge.py で 2 で割る対象であり、confidence を見る対象でもある
# （Noul に confidence は返らない）。
SCORE_KEYS = ("direction", "above_expectation", "magnitude")


# ---------------------------------------------------------------- 閾値（すべて仮の値）
# 質問ごとに別の変数として持つ。全部同じ定数にしない
# （実験6は 0.5 付近、実験7は 0.3〜0.4 と、分かれ目が質問ごとに違った）。
# フェーズ4で正解データと突き合わせて調整する。

GATE_THRESHOLDS = {
    "new_info": 0.60,
    "market_moving": 0.60,
    "official_announcement": 0.60,
    "direction": 0.60,
}

# Score 3問の confidence。1つでも下回れば見送る（notes/decision-design.md）。
MIN_CONFIDENCE = 0.70

# 重み付き和。合計 1.00。すべて 0〜1 に正規化した後の値に掛ける。
WEIGHTS = {
    "above_expectation": 0.40,
    "magnitude": 0.35,
    "continuing": 0.25,
}

# 合成したスコアがこの値以上なら、翌日の売買リストに入れる。
SCORE_THRESHOLD = 0.60

"""G. 安定性（実験25〜27）の定義。

- 実験25 は同じリクエストを繰り返す（case の repeat で回数を指定する）。
- 実験26 は同じ内容を違う書き方にした3つの文で聞く。
- 実験27 は同じ state に対して、3問まとめて聞く場合と1問ずつ聞く場合を比べる。

実行前の確認: uv run python experiments/run.py g_stability --dry-run
"""

from __future__ import annotations

import indicators as ind
from typesafe_sdk import Noul, Score

MATERIALS = ind.load_materials()

REPEAT = 5  # 実験25で同じリクエストを投げる回数


# ---------------------------------------------------------------- 予想（ユーザーが書く）
#
#   Noul  → noul=0〜1。confidence は返らない。
#   Score → score=0〜2（期待値）と confidence=0〜1。

PREDICTIONS: dict[str, str] = {
    # ================================================================
    # 実験25：同じリクエストを何度か投げる（各5回）
    #
    #   これまでに1回だけ投げたリクエストのうち、答えの性格が違う3つを選んで繰り返す。
    #   予想は「どれくらいばらつくか（幅）」を書く。
    #
    #     saturated … 蒼井フーズの好決算コメント ＋ 上昇トレンドに Score（前向きさ）。
    #                 B・D で何度か投げていて、いずれも 2.00（conf 1.00）だった。
    #     uncertain … 千鳥化学（売上は過去最高だが営業赤字）に Score（前向きさ）。
    #                 F では 0.78（conf 0.67）。confidence がいちばん低かったケース。
    #     midrange  … 大湖精機（好決算 ＋ 発表前に急上昇）に Noul（織り込み済みか）。
    #                 B では 0.46。0.5 に近く、どちらにも倒れうるケース。
    # ----------------------------------------------------------------
    "exp25_saturated": "2。変わらないのは明白",
    "exp25_uncertain": "0.78前後。confが低いと結果も変わりそう",
    "exp25_midrange": "0.5前後。ばらつくのは実施済み",
    # ================================================================
    # 実験26：言い換え
    #
    #   榎木商事の同じ内容（売上 +6.2%、営業利益 -4.8%、通期予想は据え置き）を、
    #   3通りの書き方で渡す。数字と事実は同じで、語順と言い回しだけが違う。
    #
    #   聞くこと（3ケースとも同じ2問）：
    #     positivity     … Score「どれくらい前向きか」
    #     operating_down … Noul「営業利益は前年同期を下回った」
    #
    #     a … 「…6.2%増となりましたが、…転嫁しきれず、営業利益は同4.8%減となりました」
    #     b … 「売上高は前年同期を6.2%上回った一方、営業利益は4.8%の減少となりました」
    #     c … 「増収となったものの減益でした。…6.2%のプラス、…4.8%のマイナスです」
    #
    #   ＊ a は D の exp17_short、E の exp19_ja と同じ文。
    #      それぞれ positivity 0.96 / 0.95、operating_down 0.97 / 0.98 だった。
    # ----------------------------------------------------------------
    "exp26_wording_a": "0.96。0.97。どちらも大幅な変化なし",
    "exp26_wording_b": "0.96。0.97。aの表現を変えてるだけなので",
    "exp26_wording_c": "0.96。0.97。bと同じ",
    # ================================================================
    # 実験27：まとめて聞く vs 1問ずつ聞く
    #
    #   state は大湖精機（好決算のコメント ＋ 上昇トレンド ＋ 発表前に急上昇）。
    #   同じ3問を、1リクエストにまとめた場合と、1問ずつ3リクエストに分けた場合で比べる。
    #   公式は「独立した質問は並列に評価され、互いに影響しない」としている。その確認。
    #
    #     combined        … 3問を1リクエストで
    #     single_positive … Score（前向きさ）だけ
    #     single_temporary… Noul（一時的な要因か）だけ
    #     single_priced_in… Noul（織り込み済みか）だけ
    # ----------------------------------------------------------------
    "exp27_combined": "変化しない",
    "exp27_single_positive": "変化しない",
    "exp27_single_temporary": "変化しない",
    "exp27_single_priced_in": "変化しない",
}


# ---------------------------------------------------------------- 質問文

Q_POSITIVE = Score(
    instructions="`決算コメント` の内容がどれくらい前向きか。",
    criteria=[
        "業績の悪化や先行きへの懸念が中心で、後ろ向きな内容。",
        "良い材料と悪い材料が混ざっているか、どちらとも言えない内容。",
        "業績の改善や計画の超過が中心で、前向きな内容。",
    ],
)

Q_OPERATING_DOWN = Noul(
    instructions="`決算コメント` によれば、営業利益は前年同期を下回った。"
)

Q_PRICED_IN = Noul(
    instructions="`決算コメント` の内容は、`株価.発表前の動き` にすでに織り込まれている。"
)

Q_TEMPORARY = Noul(
    instructions="`決算コメント` が説明している増益は、一時的な要因によるものである。"
)


# ---------------------------------------------------------------- state の組み立て


def _stock(stock_id: str) -> dict:
    return ind.get_stock(stock_id, MATERIALS)


def _case(
    case_id: str,
    experiment: int,
    title: str,
    stock_id: str,
    condition: str,
    state: dict,
    questions: dict,
    repeat: int = 1,
) -> dict:
    return {
        "id": case_id,
        "experiment": experiment,
        "title": title,
        "stock": stock_id,
        "condition": condition,
        "prediction": PREDICTIONS.get(case_id, ""),
        "state": state,
        "questions": questions,
        "repeat": repeat,
    }


def _comment_state(stock_id: str, text_id: str, with_trend: bool = False, with_pre_move: bool = False) -> dict:
    stock = _stock(stock_id)
    text = ind.get_text(stock, text_id)
    state = {
        "銘柄": {"名前": stock["name"]["ja"], "日付": text["date"]},
        "決算コメント": text["ja"],
    }
    if with_trend or with_pre_move:
        index = ind.index_of_date(stock, text["date"])
        price: dict[str, str] = {}
        if with_trend:
            price["トレンド"] = ind.trend_label(stock, index)
        if with_pre_move:
            price["発表前の動き"] = ind.pre_event_move_label(stock, index)
        state["株価"] = price
    return state


def _build() -> list[dict]:
    aoi_state = _comment_state("aoi_foods", "aoi_earnings_q2", with_trend=True)
    chidori_state = _comment_state("chidori_chemical", "chidori_earnings_mixed")
    daiko_priced_state = _comment_state("daiko_precision", "daiko_earnings_q2", with_pre_move=True)

    cases = [
        _case("exp25_saturated", 25, "好決算 ＋ 上昇トレンドに Score", "aoi_foods", "saturated", aoi_state, {"positivity": Q_POSITIVE}, repeat=REPEAT),
        _case("exp25_uncertain", 25, "売上最高だが営業赤字に Score", "chidori_chemical", "uncertain", chidori_state, {"positivity": Q_POSITIVE}, repeat=REPEAT),
        _case("exp25_midrange", 25, "発表前に急上昇 ＋ 織り込み済みかの Noul", "daiko_precision", "midrange", daiko_priced_state, {"priced_in": Q_PRICED_IN}, repeat=REPEAT),
    ]

    questions_26 = {"positivity": Q_POSITIVE, "operating_down": Q_OPERATING_DOWN}
    for suffix, text_id in (("a", "enoki_tanshin_short"), ("b", "enoki_paraphrase_b"), ("c", "enoki_paraphrase_c")):
        cases.append(
            _case(
                f"exp26_wording_{suffix}",
                26,
                f"榎木商事：同じ内容の書き方 {suffix}",
                "enoki_trading",
                f"wording_{suffix}",
                _comment_state("enoki_trading", text_id),
                questions_26,
            )
        )

    daiko_full_state = _comment_state("daiko_precision", "daiko_earnings_q2", with_trend=True, with_pre_move=True)
    all_questions = {"positivity": Q_POSITIVE, "temporary": Q_TEMPORARY, "priced_in": Q_PRICED_IN}
    cases.append(
        _case("exp27_combined", 27, "3問を1リクエストでまとめて聞く", "daiko_precision", "combined", daiko_full_state, all_questions)
    )
    for suffix, name in (("positive", "positivity"), ("temporary", "temporary"), ("priced_in", "priced_in")):
        cases.append(
            _case(
                f"exp27_single_{suffix}",
                27,
                f"同じ state に {name} だけを聞く",
                "daiko_precision",
                "single",
                daiko_full_state,
                {name: all_questions[name]},
            )
        )

    return cases


CASES: list[dict] = _build()

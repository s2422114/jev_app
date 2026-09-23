"""B. 文章と文脈の組み合わせ（実験5〜8）の定義。

- A と同じく日本語で統一する。
- 文章は materials/stocks.json のもの。株価のラベルは indicators.py で計算する。
- 予想は PREDICTIONS に書く。実行前に埋める（空のままだと run.py が止まる）。

実行前の確認: uv run python experiments/run.py b_text_and_context --dry-run
"""

from __future__ import annotations

import indicators as ind
from typesafe_sdk import Noul, Score

MATERIALS = ind.load_materials()


# ---------------------------------------------------------------- 予想（ユーザーが書く）
#
# 書き方は A と同じ。返る値の見込みと、そう思う理由を一言。
#   Noul  → noul=0〜1（「はい」である確率）。confidence は返らない。
#   Score → score=0〜2（期待値）と confidence=0〜1。
#
# B は A と違い、材料が「文章」になる。株価のラベルは文脈として添えるだけで、
# 判断の対象はあくまで文章。

PREDICTIONS: dict[str, str] = {
    # ================================================================
    # 実験5：文脈を足しても答えがぶれないか
    #
    #   聞くこと（3ケースとも同じ Score）：
    #     「`決算コメント` の内容がどれくらい前向きか。」
    #      0=後ろ向き / 1=どちらとも言えない / 2=前向き
    #
    #   決算コメントは3ケースとも同じ文（好決算：計画を上回って着地、通期据え置き）。
    #   変えるのは、株価のトレンドを添えるかどうかと、その向き。
    #
    #     comment_only   … コメントだけ。株価の情報なし
    #     with_uptrend   … コメント ＋ トレンド「上昇トレンド」（蒼井フーズ）
    #     with_downtrend … コメント ＋ トレンド「下降トレンド」（紅屋電機）
    #
    #   見たいのは、コメントの前向きさの評価が、株価の文脈に引きずられるかどうか。
    #   引きずられないなら3つとも同じ score になるはず。
    # ----------------------------------------------------------------
    "exp5_comment_only": "1.5。コメントは割と前向きだが通気据え置きが弱く捉えられる可能性はある",
    "exp5_with_uptrend": "1.5。コメントだけを参照してほしい。exp5_comment_onlyと同じ。",
    "exp5_with_downtrend": "1.5。コメントだけを参照してほしい。exp5_comment_onlyと同じ。",
    # ================================================================
    # 実験6：整合性（本アプリの肝になりそうな判断）
    #
    #   聞くこと（2ケースとも同じ Noul）：
    #     「`決算コメント` の内容は、`株価.トレンド` が示す株価の動きと整合している。」
    #
    #   決算コメントは実験5と同じ好決算の文。2銘柄で株価だけが違う。
    #     aoi    … 好決算 ＋ 上昇トレンド（整合するケース。正解は「はい」）
    #     beniya … 好決算 ＋ 下降トレンド（矛盾するケース。正解は「いいえ」）
    #
    #   見たいのは、2つの noul がはっきり分かれるか。分かれないなら、
    #   この判断は Jev に任せられないことになる。
    # ----------------------------------------------------------------
    "exp6_aoi_consistent": "0.97。やはり通気据え置きに引っ張られそう。",
    "exp6_beniya_conflict": "0.03。今までの実験から言うと0に近くなると思う。",
    # ================================================================
    # 実験7：織り込み済みか
    #
    #   聞くこと（2ケースとも同じ Noul）：
    #     「`決算コメント` の内容は、`株価.発表前の動き` にすでに織り込まれている。」
    #
    #   決算コメントは2ケースとも同じ文（営業利益 前年同期比 +32%、受注残も高水準）。
    #   変えるのは発表前20営業日の値動きのラベルだけ。
    #     daiko   … 「発表前に急上昇していた」（実際は +44.47%）
    #     chidori … 「発表前はほぼ横ばいだった」（実際は -0.55%）
    #
    #   見たいのは、同じ好決算でも、発表前の動きで答えが変わるか。
    # ----------------------------------------------------------------
    "exp7_daiko_surged": "0.1。織り込まれていないから決算内容がバレて上がったと考えるのが普通。",
    "exp7_chidori_flat": "0.9。織り込まれていると考えるのが普通だから。",
    # ================================================================
    # 実験8：一時的か恒常的か
    #
    #   聞くこと（2ケースとも同じ Noul）：
    #     「`決算コメント` が説明している増益は、一時的な要因によるものである。」
    #
    #   株価は渡さない。文章だけで判断できるかを見る。同じ銘柄の2つの文で、
    #   増益の幅は同じ、理由だけが違う。
    #     extraordinary … 本社不動産の売却益を特別利益として計上（正解は「はい」）
    #     core_business … 主力製品の出荷数量が伸び、原価率も改善（正解は「いいえ」）
    # ----------------------------------------------------------------
    "exp8_extraordinary": "0.9。普通に考えると二度同じことが起こる保証はないので一時的。",
    "exp8_core_business": "0.6。恒久的かと思えるが、一時的かもしれない含みも残すので真ん中近く。",
}


# ---------------------------------------------------------------- 質問文
# 条件（state）を変えても質問文は変えない。

Q_POSITIVE = Score(
    instructions="`決算コメント` の内容がどれくらい前向きか。",
    criteria=[
        "業績の悪化や先行きへの懸念が中心で、後ろ向きな内容。",
        "良い材料と悪い材料が混ざっているか、どちらとも言えない内容。",
        "業績の改善や計画の超過が中心で、前向きな内容。",
    ],
)

Q_CONSISTENT = Noul(
    instructions="`決算コメント` の内容は、`株価.トレンド` が示す株価の動きと整合している。"
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


def _case(case_id: str, experiment: int, title: str, stock_id: str, condition: str, state: dict, questions: dict) -> dict:
    return {
        "id": case_id,
        "experiment": experiment,
        "title": title,
        "stock": stock_id,
        "condition": condition,
        "prediction": PREDICTIONS.get(case_id, ""),
        "state": state,
        "questions": questions,
    }


def _base(stock: dict, text: dict) -> dict:
    return {
        "銘柄": {"名前": stock["name"]["ja"], "日付": text["date"]},
        "決算コメント": text["ja"],
    }


def _positivity_cases() -> list[dict]:
    aoi = _stock("aoi_foods")
    beniya = _stock("beniya_electric")
    comment = ind.get_text(aoi, "aoi_earnings_q2")
    aoi_index = ind.index_of_date(aoi, comment["date"])
    beniya_index = ind.index_of_date(beniya, ind.get_text(beniya, "beniya_earnings_q2")["date"])
    aoi_trend = ind.trend_label(aoi, aoi_index)
    beniya_trend = ind.trend_label(beniya, beniya_index)
    return [
        _case(
            "exp5_comment_only",
            5,
            "好決算のコメントだけを渡す（株価の情報なし）",
            "aoi_foods",
            "comment_only",
            _base(aoi, comment),
            {"positivity": Q_POSITIVE},
        ),
        _case(
            "exp5_with_uptrend",
            5,
            f"同じコメント ＋ トレンド（{aoi_trend}）",
            "aoi_foods",
            "with_trend",
            {**_base(aoi, comment), "株価": {"トレンド": aoi_trend}},
            {"positivity": Q_POSITIVE},
        ),
        _case(
            "exp5_with_downtrend",
            5,
            f"同じコメント ＋ トレンド（{beniya_trend}）",
            "beniya_electric",
            "with_trend",
            {**_base(beniya, ind.get_text(beniya, "beniya_earnings_q2")), "株価": {"トレンド": beniya_trend}},
            {"positivity": Q_POSITIVE},
        ),
    ]


def _consistency_cases() -> list[dict]:
    cases = []
    for case_id, stock_id, text_id in (
        ("exp6_aoi_consistent", "aoi_foods", "aoi_earnings_q2"),
        ("exp6_beniya_conflict", "beniya_electric", "beniya_earnings_q2"),
    ):
        s = _stock(stock_id)
        text = ind.get_text(s, text_id)
        trend = ind.trend_label(s, ind.index_of_date(s, text["date"]))
        cases.append(
            _case(
                case_id,
                6,
                f"{s['name']['ja']}：好決算のコメント ＋ {trend}",
                stock_id,
                "consistent" if case_id.endswith("consistent") else "conflict",
                {**_base(s, text), "株価": {"トレンド": trend}},
                {"consistent": Q_CONSISTENT},
            )
        )
    return cases


def _priced_in_cases() -> list[dict]:
    cases = []
    for case_id, stock_id, text_id in (
        ("exp7_daiko_surged", "daiko_precision", "daiko_earnings_q2"),
        ("exp7_chidori_flat", "chidori_chemical", "chidori_earnings_q2"),
    ):
        s = _stock(stock_id)
        text = ind.get_text(s, text_id)
        index = ind.index_of_date(s, text["date"])
        pre_move = ind.pre_event_move_label(s, index)
        cases.append(
            _case(
                case_id,
                7,
                f"{s['name']['ja']}：好決算のコメント ＋ {pre_move}",
                stock_id,
                "surged" if case_id.endswith("surged") else "flat",
                {**_base(s, text), "株価": {"発表前の動き": pre_move}},
                {"priced_in": Q_PRICED_IN},
            )
        )
    return cases


def _profit_source_cases() -> list[dict]:
    s = _stock("hakuba_pharma")
    cases = []
    for case_id, text_id, condition in (
        ("exp8_extraordinary", "hakuba_profit_extraordinary", "extraordinary"),
        ("exp8_core_business", "hakuba_profit_core_business", "core_business"),
    ):
        text = ind.get_text(s, text_id)
        cases.append(
            _case(
                case_id,
                8,
                f"{s['name']['ja']}：{'特別利益による増益' if condition == 'extraordinary' else '本業の伸びによる増益'}",
                "hakuba_pharma",
                condition,
                _base(s, text),
                {"temporary": Q_TEMPORARY},
            )
        )
    return cases


CASES: list[dict] = _positivity_cases() + _consistency_cases() + _priced_in_cases() + _profit_source_cases()

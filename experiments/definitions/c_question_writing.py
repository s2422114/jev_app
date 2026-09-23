"""C. 質問の書き方（実験9〜15）の定義。

- 質問文と criteria はユーザーが書く。下の QUESTIONS を埋める。
- state とケースの組み合わせ（何と何を比べるか）はこちらで用意した。
- 空の質問文が1つでもあると run.py は実行しない。

実行前の確認: uv run python experiments/run.py c_question_writing --dry-run
"""

from __future__ import annotations

import indicators as ind
from typesafe_sdk import Choice, Noul, Score

MATERIALS = ind.load_materials()


# ================================================================
# 質問文（ユーザーが書く）
#
# state のキーはバッククォートで指せる（例: `決算コメント`、`株価.トレンド`）。
# 各ケースの state がどうなっているかは、この下のコメントに書いてある。
# Noul   … instructions は質問文でも断定文でもよい。criteria は任意。
# Choice … criteria は {ラベル: 説明 or None} の辞書。
# Score  … criteria は下から順に並べた説明のリスト（0, 1, 2, ...）。
# ================================================================

QUESTIONS = {
    # ----------------------------------------------------------------
    # 実験9：広い問い vs 分解
    #   state（2ケースとも同じ）:
    #     銘柄 {名前: 大湖精機, 日付}
    #     決算コメント「第2四半期の営業利益は前年同期比で32%の増益となりました。
    #                   新工場の稼働が寄与しており、受注残も高い水準を保っています。」
    #     株価 {トレンド: 上昇トレンド, 発表前の動き: 発表前に急上昇していた}
    #
    #   exp9_broad      … q9_broad の1問だけを投げる
    #   exp9_decomposed … 下の3問を1リクエストにまとめて投げ、合成はコードで行う
    #                     （合成の重みは実験の外。まずは3つの確率を見る）
    "q9_broad": Noul(instructions="この銘柄はこの先上がりそうですか？"),
    "q9_positive": Noul(instructions="`決算コメント`はポジティブですか？"),
    "q9_temporary": Noul(instructions="`決算コメント`の増益は一時的なものですか？"),
    "q9_priced_in": Noul(instructions="`決算コメント`の内容は、`株価.発表前の動き`にすでに反映されていますか？"),
    # ----------------------------------------------------------------
    # 実験10：criteria の有無
    #   state（2ケースとも同じ）:
    #     銘柄 {名前: 千鳥化学, 日付}
    #     決算コメント「通期の売上高は過去最高を更新しました。一方で、原材料価格の
    #                   高騰と販促費の増加により、営業損益は赤字に転落しています。」
    #
    #   同じ instructions を使い、criteria を付けるか付けないかだけを変える。
    #   q10_without_criteria と q10_with_criteria の instructions は同じ文にすること。
    "q10_without_criteria": Noul(instructions="`決算コメント`はポジティブですか？"),
    "q10_with_criteria": Noul(
        instructions="`決算コメント`はポジティブですか？",
        criteria={"true": "本業の利益が伸びている場合", "false": "営業損益が赤字、または減益の場合。売上高が過去最高でも、赤字ならこちら"},
    ),
    # ----------------------------------------------------------------
    # 実験11：曖昧な語 vs 具体的な語
    #   state（2ケースとも同じ）:
    #     銘柄 {名前: 榎木商事, 日付}
    #     決算コメント「当第2四半期の売上高は前年同期比6.2%増となりましたが、
    #                   仕入価格の上昇を販売価格に転嫁しきれず、営業利益は同4.8%減と
    #                   なりました。通期予想は据え置きます。」
    #
    #   vague    … 「好調か」のような、基準が人によって変わる語
    #   specific … 「増収か」のような、コメントから直接読み取れる語
    "q11_vague": Noul(instructions="`決算コメント`から読み取れる企業の調子は良いか"),
    "q11_specific": Noul(instructions="`決算コメント`によると、売上は増収か"),
    # ----------------------------------------------------------------
    # 実験12：否定形（1ケースに2問をまとめて投げる）
    #   state:
    #     銘柄 {名前: 蒼井フーズ, 日付}
    #     決算コメント「第2四半期は、売上高・営業利益ともに期初計画を上回って着地
    #                   しました。主力の冷凍食品カテゴリーの販売が伸び、通期の見通しは
    #                   据え置きます。」
    #
    #   肯定形と否定形を同時に聞いて、2つの noul を足して1になるかを見る。
    "q12_positive": Noul(instructions="`決算コメント`はポジティブか"),
    "q12_negative": Noul(instructions="`決算コメント`はネガティブか"),
    # ----------------------------------------------------------------
    # 実験13：Noul vs Choice
    #   state（2ケースとも実験12と同じ蒼井フーズのコメント）
    #   同じことを Noul と、はい／いいえの Choice で聞く。
    #   Choice の criteria のラベル名も自分で決める。
    "q13_noul": Noul(instructions="`決算コメント`は前向きか"),
    "q13_choice": Choice(instructions="`決算コメント`は前向きか", criteria={"はい": None, "いいえ": None}),
    # ----------------------------------------------------------------
    # 実験14：Choice vs Score
    #   state（2ケースとも同じ）:
    #     銘柄 {名前: 紅屋電機, 日付}
    #     決算コメント「当四半期は、想定どおりの厳しい結果となりました。構造改革の
    #                   効果が数字に表れるまでには、もう少しお時間をいただくことに
    #                   なります。」
    #
    #   悲観的／中立／楽観的のような3段階を、Choice と Score の両方で聞く。
    #   Choice は順序のない選択、Score は順序のある段階として扱われる点が違う。
    "q14_choice": Choice(instructions="`決算コメント`はどの立場にあるか", criteria={"悲観的": None, "中立": None, "楽観的": None}),
    "q14_score": Score(instructions="`決算コメント`はどの立場にあるか", criteria=["悲観的", "中立", "楽観的"]),
    # ----------------------------------------------------------------
    # 実験15：「該当なし」の有無
    #   state（4ケースとも形は同じ。ニュースの文だけが違う）:
    #     銘柄 {名前: 行田システム, 日付}
    #     ニュース「…」
    #
    #   対象のニュースは2本。
    #     ma          … 「同社は、産業用センサーを手がける企業を完全子会社化すると
    #                     発表した。」（材料側の分類は M&A）
    #     office_move … 「同社は、本社オフィスの移転先が決まったと発表した。新住所での
    #                     営業は来月から始まる。」（材料側の分類は 該当なし）
    #
    #   without_none … 「どれにも当てはまらない」を入れない criteria
    #   with_none    … 同じ criteria に「どれにも当てはまらない」を足したもの
    #   instructions は2つとも同じ文にすること。
    "q15_without_none": Choice(instructions="`ニュース`はなんの話か", criteria={"業績": None, "M&A": None, "不祥事": None, "人事": None}),
    "q15_with_none": Choice(instructions="`ニュース`はなんの話か", criteria={"業績": None, "M&A": None, "不祥事": None, "人事": None, "該当なし": None}),
}


# ================================================================
# 予想（ユーザーが書く）
#
#   Noul  → noul=0〜1。confidence は返らない。
#   Score → score と confidence。
#   Choice→ 選ばれたラベルと confidence、各ラベルの確率。
# ================================================================

PREDICTIONS: dict[str, str] = {
    # 実験9：広い問い1つ vs 分解した3問
    "exp9_broad": "1.0。下がる要素がないから",
    "exp9_decomposed": "0.9,0.3,0.8。bの実験とそれぞれは同じのため。",
    # 実験10：criteria なし / あり
    "exp10_without_criteria": "0.5。どちらを重視するのかわからないので真ん中",
    "exp10_with_criteria": "0.1。criteriaでfalseになるようになってるから",
    # 実験11：曖昧な語 / 具体的な語
    "exp11_vague": "0.4。営業利益を重視しそうだから",
    "exp11_specific": "1.0。stateに書いてあるから",
    # 実験12：肯定形と否定形（1リクエストで2問）
    "exp12_negation": "0.7。割と前向きなニュースだから",
    # 実験13：Noul / Choice
    "exp13_noul": "0.9。前向き以外読み取れないので",
    "exp13_choice": "0.9。choiceにしたところで変わらない気がする",
    # 実験14：Choice / Score
    "exp14_choice": "0.5。ほとんど悲観的だが具体的な対策を言わない点で少し楽観も入ってると思う",
    "exp14_score": "0。楽観要素はあるが一般的には悲観",
    # 実験15：該当なしの有無 × ニュース2本
    "exp15_ma_without_none": "1。これは明白",
    "exp15_ma_with_none": "1。流石に変わらない",
    "exp15_office_without_none": "0。業績とは関係ないが結びつけてくるかもしれない",
    "exp15_office_with_none": "4。選択肢にないので該当なし",
}


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


def _comment_state(stock_id: str, text_id: str, key: str = "決算コメント") -> dict:
    stock = _stock(stock_id)
    text = ind.get_text(stock, text_id)
    return {
        "銘柄": {"名前": stock["name"]["ja"], "日付": text["date"]},
        key: text["ja"],
    }


def _build() -> list[dict]:
    cases: list[dict] = []

    # 実験9 ---------------------------------------------------------
    daiko = _stock("daiko_precision")
    daiko_text = ind.get_text(daiko, "daiko_earnings_q2")
    daiko_index = ind.index_of_date(daiko, daiko_text["date"])
    daiko_state = {
        **_comment_state("daiko_precision", "daiko_earnings_q2"),
        "株価": {
            "トレンド": ind.trend_label(daiko, daiko_index),
            "発表前の動き": ind.pre_event_move_label(daiko, daiko_index),
        },
    }
    cases.append(
        _case("exp9_broad", 9, "広い問いを1つだけ投げる", "daiko_precision", "broad", daiko_state, {"broad": QUESTIONS["q9_broad"]})
    )
    cases.append(
        _case(
            "exp9_decomposed",
            9,
            "分解した3問を1リクエストで投げる",
            "daiko_precision",
            "decomposed",
            daiko_state,
            {
                "positive": QUESTIONS["q9_positive"],
                "temporary": QUESTIONS["q9_temporary"],
                "priced_in": QUESTIONS["q9_priced_in"],
            },
        )
    )

    # 実験10 --------------------------------------------------------
    chidori_state = _comment_state("chidori_chemical", "chidori_earnings_mixed")
    cases.append(
        _case("exp10_without_criteria", 10, "criteria なしで聞く", "chidori_chemical", "without_criteria", chidori_state, {"judgement": QUESTIONS["q10_without_criteria"]})
    )
    cases.append(
        _case("exp10_with_criteria", 10, "同じ質問に criteria を付けて聞く", "chidori_chemical", "with_criteria", chidori_state, {"judgement": QUESTIONS["q10_with_criteria"]})
    )

    # 実験11 --------------------------------------------------------
    enoki_state = _comment_state("enoki_trading", "enoki_tanshin_short")
    cases.append(
        _case("exp11_vague", 11, "曖昧な語で聞く", "enoki_trading", "vague", enoki_state, {"judgement": QUESTIONS["q11_vague"]})
    )
    cases.append(
        _case("exp11_specific", 11, "具体的な語で聞く", "enoki_trading", "specific", enoki_state, {"judgement": QUESTIONS["q11_specific"]})
    )

    # 実験12・13 ----------------------------------------------------
    aoi_state = _comment_state("aoi_foods", "aoi_earnings_q2")
    cases.append(
        _case(
            "exp12_negation",
            12,
            "肯定形と否定形を同時に聞く",
            "aoi_foods",
            "both",
            aoi_state,
            {"positive": QUESTIONS["q12_positive"], "negative": QUESTIONS["q12_negative"]},
        )
    )
    cases.append(
        _case("exp13_noul", 13, "Noul で聞く", "aoi_foods", "noul", aoi_state, {"judgement": QUESTIONS["q13_noul"]})
    )
    cases.append(
        _case("exp13_choice", 13, "同じことを Choice で聞く", "aoi_foods", "choice", aoi_state, {"judgement": QUESTIONS["q13_choice"]})
    )

    # 実験14 --------------------------------------------------------
    beniya_state = _comment_state("beniya_electric", "beniya_earnings_understated")
    cases.append(
        _case("exp14_choice", 14, "3段階を Choice で聞く", "beniya_electric", "choice", beniya_state, {"judgement": QUESTIONS["q14_choice"]})
    )
    cases.append(
        _case("exp14_score", 14, "同じ3段階を Score で聞く", "beniya_electric", "score", beniya_state, {"judgement": QUESTIONS["q14_score"]})
    )

    # 実験15 --------------------------------------------------------
    for news_key, text_id, news_label in (
        ("ma", "gyoda_news_ma", "M&A のニュース"),
        ("office", "gyoda_news_office_move", "どの分類にも当てはまらないニュース"),
    ):
        news_state = _comment_state("gyoda_systems", text_id, key="ニュース")
        for condition, question_key in (("without_none", "q15_without_none"), ("with_none", "q15_with_none")):
            cases.append(
                _case(
                    f"exp15_{news_key}_{condition}",
                    15,
                    f"{news_label}：{'該当なしを入れない' if condition == 'without_none' else '該当なしを入れる'}",
                    "gyoda_systems",
                    condition,
                    news_state,
                    {"category": QUESTIONS[question_key]},
                )
            )

    return cases


CASES: list[dict] = _build()

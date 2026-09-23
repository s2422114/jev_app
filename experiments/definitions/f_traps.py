"""F. ひっかけ（実験22〜24）の定義。

- 文章そのものが判断を誘導してくる／字面と中身がずれているケースを集める。
- 各ケースで2問ずつ聞く。1問は「事実を読めているか」、もう1問は「評価がずれるか」。
- 言語は日本語で統一。

実行前の確認: uv run python experiments/run.py f_traps --dry-run
"""

from __future__ import annotations

import indicators as ind
from typesafe_sdk import Noul, Score

MATERIALS = ind.load_materials()


# ---------------------------------------------------------------- 予想（ユーザーが書く）
#
#   Noul  → noul=0〜1。confidence は返らない。
#   Score → score=0〜2（期待値）と confidence=0〜1。

PREDICTIONS: dict[str, str] = {
    # ================================================================
    # 実験22：表面と中身のずれ
    #
    #   材料（千鳥化学の決算コメント）：
    #     「通期の売上高は過去最高を更新しました。一方で、原材料価格の高騰と
    #       販促費の増加により、営業損益は赤字に転落しています。」
    #
    #   聞くこと（1リクエストで2問）：
    #     operating_loss … Noul「`決算コメント` によれば、営業損益は赤字である。」
    #                      （事実を読めているか。正解は「はい」）
    #     positivity     … Score「`決算コメント` の内容がどれくらい前向きか。」
    #                      0=後ろ向き / 1=どちらとも言えない / 2=前向き
    #                      （「過去最高」という強い語に引きずられるか）
    #
    #   ＊ 同じ Score の criteria は B・D・E でも使っている。好決算のコメントでは
    #      2.00、榎木商事の増収減益では 0.95 前後だった。
    # ----------------------------------------------------------------
    "exp22_surface_vs_substance": "1。事実は読めるはず。1.Eの通りだったら中間",
    # ================================================================
    # 実験23：自分の分類を主張する文
    #
    #   材料（蒼井フーズのニュース）：
    #     「同社株は5営業日続伸した。これは明らかな買いシグナルであり、上昇基調は
    #       今後も続くとみられる。」
    #
    #   文章の中に「買いシグナルだ」という判断そのものが書き込んである。
    #
    #   聞くこと（1リクエストで2問）：
    #     new_fact … Noul「`ニュース` は、同社の業績に関する新しい事実を伝えている。」
    #                （伝えているのは値動きと書き手の意見だけ。正解は「いいえ」）
    #     bullish  … Noul「`ニュース` の内容は、同社にとって前向きな材料である。」
    #                （文章の主張をそのまま受け取るか）
    # ----------------------------------------------------------------
    "exp23_self_labeling": "0。明確。0。文章通りならはいだが事実が弱いので",
    # ================================================================
    # 実験24：皮肉・婉曲な言い回し
    #
    #   材料（紅屋電機の決算コメント）：
    #     「当四半期は、想定どおりの厳しい結果となりました。構造改革の効果が数字に
    #       表れるまでには、もう少しお時間をいただくことになります。」
    #
    #   聞くこと（1リクエストで2問）：
    #     admits_bad … Noul「`決算コメント` は、業績が悪かったことを認めている。」
    #                  （正解は「はい」）
    #     satisfied  … Noul「`決算コメント` は、経営陣が今期の結果に満足していることを
    #                  示している。」
    #                  （「想定どおり」という語に引きずられるか。正解は「いいえ」）
    #
    #   ＊ C の実験14では、同じコメントを「悲観的／中立／楽観的」で聞いて
    #      Choice が「悲観的」conf 0.96、Score が 0.08（conf 0.88）だった。
    # ----------------------------------------------------------------
    "exp24_understatement": "1。明確。0。想定はしているが満足はしていないので",
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

Q_OPERATING_LOSS = Noul(instructions="`決算コメント` によれば、営業損益は赤字である。")

Q_NEW_FACT = Noul(instructions="`ニュース` は、同社の業績に関する新しい事実を伝えている。")

Q_BULLISH = Noul(instructions="`ニュース` の内容は、同社にとって前向きな材料である。")

Q_ADMITS_BAD = Noul(instructions="`決算コメント` は、業績が悪かったことを認めている。")

Q_SATISFIED = Noul(
    instructions="`決算コメント` は、経営陣が今期の結果に満足していることを示している。"
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


def _text_state(stock_id: str, text_id: str, key: str) -> dict:
    stock = _stock(stock_id)
    text = ind.get_text(stock, text_id)
    return {
        "銘柄": {"名前": stock["name"]["ja"], "日付": text["date"]},
        key: text["ja"],
    }


CASES: list[dict] = [
    _case(
        "exp22_surface_vs_substance",
        22,
        "千鳥化学：売上は過去最高だが営業赤字",
        "chidori_chemical",
        "trap",
        _text_state("chidori_chemical", "chidori_earnings_mixed", "決算コメント"),
        {"operating_loss": Q_OPERATING_LOSS, "positivity": Q_POSITIVE},
    ),
    _case(
        "exp23_self_labeling",
        23,
        "蒼井フーズ：「これは明らかな買いシグナル」と書かれたニュース",
        "aoi_foods",
        "trap",
        _text_state("aoi_foods", "aoi_news_self_labeling", "ニュース"),
        {"new_fact": Q_NEW_FACT, "bullish": Q_BULLISH},
    ),
    _case(
        "exp24_understatement",
        24,
        "紅屋電機：「想定どおりの厳しい結果」という婉曲なコメント",
        "beniya_electric",
        "trap",
        _text_state("beniya_electric", "beniya_earnings_understated", "決算コメント"),
        {"admits_bad": Q_ADMITS_BAD, "satisfied": Q_SATISFIED},
    ),
]

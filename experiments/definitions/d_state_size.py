"""D. state の量（実験16〜18）の定義。

- 質問文は条件を通して同じ。変えるのは state に入れる情報の量だけ。
- 判断の対象は常に「対象銘柄」。余分な情報を足したときに答えがぶれるかを見る。

実行前の確認: uv run python experiments/run.py d_state_size --dry-run
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
    # 実験16：他の銘柄を混ぜる
    #
    #   聞くこと（2ケースとも同じ Score）：
    #     「`対象銘柄.決算コメント` の内容がどれくらい前向きか。」
    #      0=後ろ向き / 1=どちらとも言えない / 2=前向き
    #
    #   対象銘柄は蒼井フーズ（好決算のコメント ＋ 上昇トレンド）。
    #     single      … 対象銘柄だけ
    #     with_others … 同じ state に「他の銘柄」3社分（紅屋電機・千鳥化学・白馬製薬の
    #                   コメントとトレンド）を足す。対象銘柄の中身は変えない。
    #
    #   見たいのは、関係のある形式の情報が増えたときに、対象銘柄への評価がぶれるか。
    # ----------------------------------------------------------------
    "exp16_single": "2。前向きであることは明白",
    "exp16_with_others": "2。情報が増えても対象だけにフォーカスできると思う。",
    # ================================================================
    # 実験17：短文 vs 長文
    #
    #   聞くこと（2ケースとも同じ2問。1リクエストにまとめる）：
    #     positivity      … Score「`対象銘柄.決算コメント` の内容がどれくらい前向きか。」
    #     operating_down  … Noul「`対象銘柄.決算コメント` によれば、営業利益は
    #                             前年同期を下回った。」
    #
    #   榎木商事の同じ内容を、長さだけ変えて渡す（材料側で対にしてある）。
    #     short … 2文（増収だが仕入価格を転嫁できず営業減益、通期予想は据え置き）
    #     long  … 決算短信のような長文。同じ数字（売上 +6.2%、営業利益 -4.8%）が
    #             経済情勢やセグメント別の記述に埋もれている
    #
    #   見たいのは、長文でも同じ事実を拾えるか、前向きさの評価が変わらないか。
    # ----------------------------------------------------------------
    "exp17_short": "0。後ろ向きであるから。1。利益が前年を下回ったのは事実なので",
    "exp17_long": "0.5。後ろ向きと判断はできるが確信度は下がりそう。0.97。埋もれている分他の情報に惑わされ少し上がる",
    # ================================================================
    # 実験18：無関係な情報を混ぜる
    #
    #   聞くこと（2ケースとも実験16と同じ Score）。
    #   対象銘柄も実験16と同じ蒼井フーズ。
    #     clean      … 対象銘柄だけ（exp16_single と同じ state・同じ質問）
    #     with_noise … 同じ state に、市況全般の記事2本と、他社（行田システム）の
    #                  不祥事のニュースを足す。対象銘柄とは無関係な情報。
    #
    #   見たいのは、無関係な情報、とくに他社のネガティブなニュースに引きずられるか。
    #   ＊ exp16_single と exp18_clean は中身が同じリクエスト。同じものを2回投げた
    #      ことになるので、実験25（同じリクエストを何度か）の材料にもなる。
    # ----------------------------------------------------------------
    "exp18_clean": "2。exp16_singleと同じ",
    "exp18_with_noise": "2。無関係な情報である以上引っ張られない気がする",
}


# ---------------------------------------------------------------- 質問文

Q_POSITIVE = Score(
    instructions="`対象銘柄.決算コメント` の内容がどれくらい前向きか。",
    criteria=[
        "業績の悪化や先行きへの懸念が中心で、後ろ向きな内容。",
        "良い材料と悪い材料が混ざっているか、どちらとも言えない内容。",
        "業績の改善や計画の超過が中心で、前向きな内容。",
    ],
)

Q_OPERATING_DOWN = Noul(
    instructions="`対象銘柄.決算コメント` によれば、営業利益は前年同期を下回った。"
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


def _target(stock_id: str, text_id: str, with_trend: bool = True) -> dict:
    stock = _stock(stock_id)
    text = ind.get_text(stock, text_id)
    entry = {"名前": stock["name"]["ja"], "日付": text["date"], "決算コメント": text["ja"]}
    if with_trend:
        entry["トレンド"] = ind.trend_label(stock, ind.index_of_date(stock, text["date"]))
    return {"対象銘柄": entry}


def _other(stock_id: str, text_id: str) -> dict:
    stock = _stock(stock_id)
    text = ind.get_text(stock, text_id)
    return {
        "名前": stock["name"]["ja"],
        "日付": text["date"],
        "決算コメント": text["ja"],
        "トレンド": ind.trend_label(stock, ind.index_of_date(stock, text["date"])),
    }


def _build() -> list[dict]:
    cases: list[dict] = []

    aoi_state = _target("aoi_foods", "aoi_earnings_q2")

    # 実験16 --------------------------------------------------------
    others = [
        _other("beniya_electric", "beniya_earnings_q2"),
        _other("chidori_chemical", "chidori_earnings_mixed"),
        _other("hakuba_pharma", "hakuba_profit_extraordinary"),
    ]
    cases.append(
        _case("exp16_single", 16, "対象銘柄だけを渡す", "aoi_foods", "single", aoi_state, {"positivity": Q_POSITIVE})
    )
    cases.append(
        _case(
            "exp16_with_others",
            16,
            "同じ state に他の銘柄3社を足す",
            "aoi_foods",
            "with_others",
            {**aoi_state, "他の銘柄": others},
            {"positivity": Q_POSITIVE},
        )
    )

    # 実験17 --------------------------------------------------------
    questions_17 = {"positivity": Q_POSITIVE, "operating_down": Q_OPERATING_DOWN}
    cases.append(
        _case(
            "exp17_short",
            17,
            "同じ内容を短文で渡す",
            "enoki_trading",
            "short",
            _target("enoki_trading", "enoki_tanshin_short", with_trend=False),
            questions_17,
        )
    )
    cases.append(
        _case(
            "exp17_long",
            17,
            "同じ内容を決算短信のような長文で渡す",
            "enoki_trading",
            "long",
            _target("enoki_trading", "enoki_tanshin_long", with_trend=False),
            questions_17,
        )
    )

    # 実験18 --------------------------------------------------------
    gyoda = _stock("gyoda_systems")
    misconduct = ind.get_text(gyoda, "gyoda_news_misconduct")
    noise = {
        "市況": [{"日付": t["date"], "記事": t["ja"]} for t in MATERIALS["market_texts"]],
        "他社のニュース": [
            {"名前": gyoda["name"]["ja"], "日付": misconduct["date"], "記事": misconduct["ja"]}
        ],
    }
    cases.append(
        _case("exp18_clean", 18, "対象銘柄だけを渡す（exp16_single と同じ）", "aoi_foods", "clean", aoi_state, {"positivity": Q_POSITIVE})
    )
    cases.append(
        _case(
            "exp18_with_noise",
            18,
            "同じ state に市況2本と他社の不祥事ニュースを足す",
            "aoi_foods",
            "with_noise",
            {**aoi_state, **noise},
            {"positivity": Q_POSITIVE},
        )
    )

    return cases


CASES: list[dict] = _build()

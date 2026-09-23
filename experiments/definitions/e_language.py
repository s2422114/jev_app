"""E. 言語（実験19〜21）の定義。

- 実験19 は、同じ内容を日本語と英語の両方で投げて比べる。state のキー・値・質問文・
  criteria をすべてその言語にそろえる。
- 実験20 は、state だけ日本語、質問文と criteria を英語にする（混在）。
- 実験21 は、日本語の金融用語を正しく読めるかを見る。

実行前の確認: uv run python experiments/run.py e_language --dry-run
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
    # 実験19：英語 vs 日本語（未決の論点4に直結）
    #
    #   聞くこと（2ケースとも同じ2問。1リクエストにまとめる）：
    #     positivity     … Score「決算コメントの内容がどれくらい前向きか」
    #                      0=後ろ向き / 1=どちらとも言えない / 2=前向き
    #     operating_down … Noul「決算コメントによれば、営業利益は前年同期を下回った」
    #
    #   材料は榎木商事の短いコメント（売上 +6.2%、営業利益 -4.8%、通期予想は据え置き）。
    #   良い材料と悪い材料が混ざっているので、真ん中あたりの答えになるはずの文。
    #   飽和した設問（誰が見ても 2.0）だと言語差が見えないため、これを選んでいる。
    #
    #     ja … state のキーも値も質問文も日本語
    #     en … 同じ内容をすべて英語に置き換える（材料の en 版を使う）
    #
    #   ＊ ja は D の exp17_short と同じリクエスト。あちらの結果は
    #      positivity 0.96（conf 0.93）/ operating_down 0.97 だった。
    # ----------------------------------------------------------------
    "exp19_ja": "positivity 0.96（conf 0.93）/ operating_down 0.97。Dと同じ",
    "exp19_en": "positivity 0.96（conf 0.93）多少言語の違いで前後するが大幅には変化しない/ operating_down 0.97。言語が変わっても数字は変わらないので",
    # ================================================================
    # 実験20：混在（state は日本語、質問は英語）
    #
    #   聞くことは実験19と同じ2問だが、質問文と criteria だけ英語にする。
    #   state は日本語のままなので、質問文の中で指す場所も日本語のキーになる
    #   （例：`対象銘柄.決算コメント`）。
    #
    #   見たいのは、ja と en の間のどこに落ちるか。
    # ----------------------------------------------------------------
    "exp20_ja_state_en_question": "0.9。0.9。質問文中に日本語のキーが入ることで下がりそうな気がする",
    # ================================================================
    # 実験21：日本語の金融用語
    #
    #   聞くこと（4ケースとも同じ Noul）：
    #     「`ニュース` の内容は、同社の利益にとってプラスの材料である。」
    #
    #   富士見運輸のニュース4本。用語を正しく読めているかだけを見る。
    #     upward_revision    … 通期の営業利益予想を上方修正（正解は「はい」）
    #     downward_revision  … 通期の売上高予想を下方修正（正解は「いいえ」）
    #     impairment         … 海外子会社の固定資産に減損損失を計上（正解は「いいえ」）
    #     extraordinary_loss … 配送センター閉鎖に伴う費用を特別損失として計上
    #                          （正解は「いいえ」）
    # ----------------------------------------------------------------
    "exp21_upward_revision": "1。明確",
    "exp21_downward_revision": "0。明確",
    "exp21_impairment": "0。明確",
    "exp21_extraordinary_loss": "0。明確",
}


# ---------------------------------------------------------------- 質問文

Q_POSITIVE_JA = Score(
    instructions="`対象銘柄.決算コメント` の内容がどれくらい前向きか。",
    criteria=[
        "業績の悪化や先行きへの懸念が中心で、後ろ向きな内容。",
        "良い材料と悪い材料が混ざっているか、どちらとも言えない内容。",
        "業績の改善や計画の超過が中心で、前向きな内容。",
    ],
)

Q_OPERATING_DOWN_JA = Noul(
    instructions="`対象銘柄.決算コメント` によれば、営業利益は前年同期を下回った。"
)

Q_POSITIVE_EN = Score(
    instructions="How positive is the content of `target.earnings_comment`?",
    criteria=[
        "Mostly about deteriorating results or concerns about the outlook; a negative message.",
        "A mix of good and bad points, or nothing clearly either way.",
        "Mostly about improving results or beating the plan; a positive message.",
    ],
)

Q_OPERATING_DOWN_EN = Noul(
    instructions="According to `target.earnings_comment`, operating profit was lower than in the same period a year earlier."
)

# 実験20：質問だけ英語。state は日本語なので、指す場所は日本語のキーのまま。
Q_POSITIVE_MIXED = Score(
    instructions="How positive is the content of `対象銘柄.決算コメント`?",
    criteria=[
        "Mostly about deteriorating results or concerns about the outlook; a negative message.",
        "A mix of good and bad points, or nothing clearly either way.",
        "Mostly about improving results or beating the plan; a positive message.",
    ],
)

Q_OPERATING_DOWN_MIXED = Noul(
    instructions="According to `対象銘柄.決算コメント`, operating profit was lower than in the same period a year earlier."
)

Q_GOOD_FOR_PROFIT = Noul(
    instructions="`ニュース` の内容は、同社の利益にとってプラスの材料である。"
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


def _build() -> list[dict]:
    enoki = _stock("enoki_trading")
    short = ind.get_text(enoki, "enoki_tanshin_short")

    state_ja = {
        "対象銘柄": {
            "名前": enoki["name"]["ja"],
            "日付": short["date"],
            "決算コメント": short["ja"],
        }
    }
    state_en = {
        "target": {
            "name": enoki["name"]["en"],
            "date": short["date"],
            "earnings_comment": short["en"],
        }
    }

    cases = [
        _case(
            "exp19_ja",
            19,
            "state も質問もすべて日本語",
            "enoki_trading",
            "ja",
            state_ja,
            {"positivity": Q_POSITIVE_JA, "operating_down": Q_OPERATING_DOWN_JA},
        ),
        _case(
            "exp19_en",
            19,
            "同じ内容をすべて英語で",
            "enoki_trading",
            "en",
            state_en,
            {"positivity": Q_POSITIVE_EN, "operating_down": Q_OPERATING_DOWN_EN},
        ),
        _case(
            "exp20_ja_state_en_question",
            20,
            "state は日本語、質問は英語",
            "enoki_trading",
            "mixed",
            state_ja,
            {"positivity": Q_POSITIVE_MIXED, "operating_down": Q_OPERATING_DOWN_MIXED},
        ),
    ]

    fujimi = _stock("fujimi_logistics")
    for case_id, text_id in (
        ("exp21_upward_revision", "fujimi_news_upward_revision"),
        ("exp21_downward_revision", "fujimi_news_downward_revision"),
        ("exp21_impairment", "fujimi_news_impairment"),
        ("exp21_extraordinary_loss", "fujimi_news_extraordinary_loss"),
    ):
        text = ind.get_text(fujimi, text_id)
        cases.append(
            _case(
                case_id,
                21,
                f"{text['note'].split('：')[-1]}：{text['ja']}",
                "fujimi_logistics",
                "ja",
                {
                    "銘柄": {"名前": fujimi["name"]["ja"], "日付": text["date"]},
                    "ニュース": text["ja"],
                },
                {"good_for_profit": Q_GOOD_FOR_PROFIT},
            )
        )

    return cases


CASES: list[dict] = _build()

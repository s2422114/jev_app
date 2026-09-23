"""A. 数値とラベル（実験1〜4）の定義。

- 言語は日本語で統一する（state のキーも値も質問文も）。英語との差は実験19で別に測る。
- state は materials/stocks.json から作り、指標は indicators.py で計算する。
- 予想は PREDICTIONS に書く。実行前に埋める（空のままだと run.py が止まる）。

実行前の確認: uv run python experiments/run.py a_numbers_and_labels --dry-run
"""

from __future__ import annotations

import indicators as ind
from typesafe_sdk import Noul, Score

MATERIALS = ind.load_materials()


# ---------------------------------------------------------------- 予想（ユーザーが書く）
#
# 書き方：返る値の見込みと、そう思う理由を一言。理由がないと、あとで
# 「予想と違った」の中身を追えない。
#   Noul  → noul=0〜1（「はい」である確率）。confidence は返らない。
#   Score → score=0〜2（各段階の確率で重みづけした期待値）と confidence=0〜1。
# 例："noul=0.95。差が50以上あるので数値の比較でも間違えないと思う"
#
# 下に書いた数値は、seed 固定の材料から計算した実際の値。
# generate.py を作り直さないかぎり変わらない。

PREDICTIONS: dict[str, str] = {
    # ================================================================
    # 実験1：比較が要る数値
    #   聞くこと（6ケースとも同じ Noul）：
    #     「この銘柄の25日移動平均は、75日移動平均より大きい。」
    #   変えるのは state だけ。raw は数値そのもの、label は計算済みのラベル。
    #   見たいのは、raw と label で noul がどれだけ変わるか。
    # ----------------------------------------------------------------
    # 蒼井フーズ：25日線 1471.15 > 75日線 1418.59（差 +52.56、正解は「はい」）
    #   raw   … state に 25日移動平均・75日移動平均の数値を入れる。数値を比べられるか。
    "exp1_aoi_raw": "0.97。結果は明白だから割と簡単に判断できると思う。",
    #   label … state はトレンド「上昇トレンド」だけ。数値は渡さない。
    #           ラベルから同じ結論に辿り着けるか、raw と比べて確率は上がるか下がるか。
    "exp1_aoi_label": "0.8。上昇トレンドの時、25日線は75日線を上回るがそうでない時も考慮されるためrawよりは下がると思う。",
    # 紅屋電機：25日線 2765.16 < 75日線 2873.87（差 -108.71、正解は「いいえ」）
    #   raw   … 数値2つ。「いいえ」なので noul は 0 に近いはず。
    "exp1_beniya_raw": "0.1。先ほどよりも差が大きく判定は簡単になるため値は0に限りなく近いはず",
    #   label … トレンド「下降トレンド」だけ。
    "exp1_beniya_label": "0.2。exp1_aoi_labelと同じでrawよりは高くなりそう",
    # 千鳥化学：25日線 880.51 > 75日線 879.97（差 +0.54 の僅差。正解は「はい」）
    #   raw   … 僅差でも数値を正しく比べられるか。ここが実験1の山。
    "exp1_chidori_raw": "0.97。ただの数値の計算なのでexp1_aoi_rawと変わらなそう。",
    #   label … トレンド「横ばい」だけ。ラベルにした時点で大小の情報は消えている。
    #           判断材料がないときに Jev が 0.5 付近を返すのか、どちらかに寄せるのか。
    "exp1_chidori_label": "0.5。これは真ん中であってほしい。もしかしたらネットの横ばいという情報が偏りがあって少しズレるかもしれないが大きなずれはないはず。",
    # ================================================================
    # 実験2：境目の近く / 実験4：数値とラベルで confidence が変わるか
    #   聞くこと（4ケースとも同じ。state が同じなので1リクエストにまとめて2問）：
    #     big_drop  … Noul 「この銘柄は、この日に大幅な下落をした。」
    #     move_size … Score 「この銘柄の、この日の値動きの大きさ。」
    #                 0=ほとんど動いていない / 1=下落したが小幅 / 2=大幅に下落した
    #   コード側のしきい値は -3.0%（indicators.BIG_MOVE_PCT）。
    #   実験2 = raw の2銘柄（-2.9% と -3.1%）を比べ、Jev の「大幅」の感覚が
    #           自分の境目とずれるかを見る。
    #   実験4 = 同じ銘柄の raw と label で move_size の confidence を比べる。
    # ----------------------------------------------------------------
    # 榎木商事：前日終値 1572.65 → 終値 1527.04、前日比 -2.9%
    #          （コード側では境目の手前なので「下落」扱い）
    #   raw   … state に前日終値・終値・前日比の数値。big_drop と move_size の両方を予想する。
    "exp2_enoki_raw": "big_drop=0.3。大幅ではないのではないが下落ではあるので。move_size=1.2。下落ではあるが大幅ではないので。",
    #   label … state は値動き「下落」だけ。数値は渡さない。
    #           ラベルを渡すと confidence が上がるのか（実験4の本題）。
    "exp2_enoki_label": "big_drop=0.5。下落だが大幅ではない、だが下落の中にも大幅な下落が含まれるため二択になるはず。move_size=1.5。big_dropと同じ理由。",
    # 富士見運輸：前日終値 724.98 → 終値 702.51、前日比 -3.1%
    #            （コード側では境目を超えるので「大幅下落」扱い）
    #   raw   … 榎木商事との差は 0.2 ポイントだけ。Jev の答えが分かれるかどうか。
    "exp2_fujimi_raw": "big_drop=0.2。コードでは大幅下落になっているが一般的にはただの下落なため。move_size=1.5。exp2_enoki_rawと同じ理由だが、下落幅が大きくなった分少しだけ増えそう。",
    #   label … state は値動き「大幅下落」だけ。
    "exp2_fujimi_label": "big_drop=0.9。stateを文字通り受け取ると高くなる気がする。move_size=1.9。big_dropと同じ理由。exp2_enoki_labelと違い小幅の下落の可能性が消えたため2.0に近くなるとおもう。",
    # ================================================================
    # 実験3：同じ事実を3通りの表し方で渡す
    #   聞くこと（6ケースとも同じ Noul）：
    #     「この銘柄のこの日の出来高は、普段と比べて目立って多い。」
    #   同じ事実でも、どの表し方が安定するかを見る。
    #   株数だけでは「普段」が分からないので、判断材料が足りない条件でもある。
    # ----------------------------------------------------------------
    # 行田システム：出来高 1,837,597株。直近25日平均の3.1倍（本当に多い）
    #   shares … state は「1,837,597株」だけ。平均が分からない状態で何を答えるか。
    "exp3_gyoda_shares": "0.5。基準がわからない上に実在しない企業なので比べ用がないため真ん中。confidenceは限りなく低いはず",
    #   ratio  … state は「直近25日平均の3.1倍」。比較の基準が文章で入っている。
    "exp3_gyoda_ratio": "0.9。基準がある分高くなるはず。confidenceも高くなる（0.8あたり）",
    #   label  … state は「急増」。答えがほぼ言葉に入っている。
    "exp3_gyoda_label": "0.9。exp3_gyoda_ratioとそんなに変わらない。ただ文字のため少し低くなるかも。",
    # 白馬製薬：出来高 923,824株。直近25日平均の1.01倍（普段どおり）
    #   shares … state は「923,824株」だけ。行田システムの株数条件と答えが変わるか。
    #            変わるなら、Jev は株数の絶対値で「多い」を判断していることになる。
    "exp3_hakuba_shares": "0.5。exp3_gyoda_sharesと同じ。",
    #   ratio  … state は「直近25日平均の1.01倍」。
    "exp3_hakuba_ratio": "0.5。多くもないし少なくもないので。confidenceは高そう。",
    #   label  … state は「平均並み」。
    "exp3_hakuba_label": "0.5。これもexp3_hakuba_ratioとそんなに変わらないか少し小さい。理由はexp3_gyoda_labelと同じ。",
}


# ---------------------------------------------------------------- 質問文
# 条件（state）を変えても質問文は変えない。変えるのは渡し方だけ。

Q_TREND = Noul(instructions="この銘柄の25日移動平均は、75日移動平均より大きい。")

Q_BIG_DROP = Noul(instructions="この銘柄は、この日に大幅な下落をした。")

Q_MOVE_SIZE = Score(
    instructions="この銘柄の、この日の値動きの大きさ。",
    criteria=[
        "ほとんど動いていない。",
        "下落したが、小幅な下落にとどまる。",
        "大幅に下落した。",
    ],
)

Q_VOLUME = Noul(instructions="この銘柄のこの日の出来高は、普段と比べて目立って多い。")


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


def _trend_cases() -> list[dict]:
    cases = []
    for stock_id in ("aoi_foods", "beniya_electric", "chidori_chemical"):
        s = _stock(stock_id)
        snap = ind.snapshot(s)
        name = s["name"]["ja"]
        short = stock_id.split("_")[0]
        base = {"名前": name, "日付": snap["date"]}
        cases.append(
            _case(
                f"exp1_{short}_raw",
                1,
                f"{name}：25日線と75日線を生の数値で渡す",
                stock_id,
                "raw",
                {"銘柄": {**base, "25日移動平均": snap["raw"]["sma25"], "75日移動平均": snap["raw"]["sma75"]}},
                {"trend_compare": Q_TREND},
            )
        )
        cases.append(
            _case(
                f"exp1_{short}_label",
                1,
                f"{name}：トレンドのラベルだけを渡す（{snap['labels']['trend']}）",
                stock_id,
                "label",
                {"銘柄": {**base, "トレンド": snap["labels"]["trend"]}},
                {"trend_compare": Q_TREND},
            )
        )
    return cases


def _drop_cases() -> list[dict]:
    cases = []
    for stock_id in ("enoki_trading", "fujimi_logistics"):
        s = _stock(stock_id)
        snap = ind.snapshot(s)
        closes = ind.closes(s)
        name = s["name"]["ja"]
        short = stock_id.split("_")[0]
        base = {"名前": name, "日付": snap["date"]}
        questions = {"big_drop": Q_BIG_DROP, "move_size": Q_MOVE_SIZE}
        cases.append(
            _case(
                f"exp2_{short}_raw",
                2,
                f"{name}：前日比 {snap['raw']['pct_change']}% を生の数値で渡す",
                stock_id,
                "raw",
                {
                    "銘柄": {
                        **base,
                        "前日終値": closes[-2],
                        "終値": snap["raw"]["close"],
                        "前日比（%）": snap["raw"]["pct_change"],
                    }
                },
                questions,
            )
        )
        cases.append(
            _case(
                f"exp2_{short}_label",
                4,
                f"{name}：値動きのラベルだけを渡す（{snap['labels']['move']}）",
                stock_id,
                "label",
                {"銘柄": {**base, "値動き": snap["labels"]["move"]}},
                questions,
            )
        )
    return cases


def _volume_cases() -> list[dict]:
    cases = []
    for stock_id in ("gyoda_systems", "hakuba_pharma"):
        s = _stock(stock_id)
        snap = ind.snapshot(s)
        name = s["name"]["ja"]
        short = stock_id.split("_")[0]
        base = {"名前": name, "日付": snap["date"]}
        shares = snap["raw"]["volume"]
        ratio = snap["raw"]["volume_ratio"]
        label = snap["labels"]["volume"]
        for condition, value, title in (
            ("shares", f"{shares:,}株", f"{name}：出来高を株数で渡す"),
            ("ratio", f"直近25日平均の{ratio}倍", f"{name}：出来高を平均との比で渡す"),
            ("label", label, f"{name}：出来高をラベルで渡す（{label}）"),
        ):
            cases.append(
                _case(
                    f"exp3_{short}_{condition}",
                    3,
                    title,
                    stock_id,
                    condition,
                    {"銘柄": {**base, "出来高": value}},
                    {"volume_high": Q_VOLUME},
                )
            )
    return cases


CASES: list[dict] = _trend_cases() + _drop_cases() + _volume_cases()

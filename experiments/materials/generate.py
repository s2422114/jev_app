"""フェーズ1の材料（stocks.json）を生成する。

- 銘柄はすべて架空。実在企業の名前・数値は使わない。
- 株価と出来高は、狙った形（上昇・下落・横ばい・発表前の急上昇など）になるよう
  seed 固定で生成する。実行しても同じ材料になる。
- 指標・ラベル・予想はここでは持たせない。指標とラベルは experiments/indicators.py で計算する。

実行: uv run python experiments/materials/generate.py
"""

from __future__ import annotations

import json
import random
from datetime import date, timedelta
from pathlib import Path

SEED = 20260921
DAYS = 150  # 75日線の計算に76日必要。形を作り分ける余裕をみて長めに取る
ANNOUNCE_INDEX = 140  # 決算コメントの発表日にあたる位置
RISE_START_INDEX = 120  # 「発表前の急上昇」が始まる位置
OUT_PATH = Path(__file__).with_name("stocks.json")
START_DATE = date(2026, 1, 5)


# ---------------------------------------------------------------- 系列の生成


def business_days(start: date, count: int) -> list[date]:
    days: list[date] = []
    day = start
    while len(days) < count:
        if day.weekday() < 5:
            days.append(day)
        day += timedelta(days=1)
    return days


def build_prices(rng: random.Random, n: int, start_price: float, level_at, noise: float = 0.006) -> list[float]:
    """level_at(i) が決める水準に、小さなノイズを乗せる。

    ランダムウォークにすると、ノイズが積み上がって横ばいのはずの銘柄が
    トレンドを持ってしまうため、水準を決めてからノイズを乗せる形にしている。
    """
    return [round(start_price * level_at(i) * (1 + rng.gauss(0, noise)), 2) for i in range(n)]


def make_volumes(rng: random.Random, n: int, base: int, spike_ratio: float | None = None) -> list[int]:
    vols = [max(1000, int(base * (1 + rng.gauss(0, 0.15)))) for _ in range(n)]
    if spike_ratio is not None:
        # indicators.volume_ratio と同じ定義（当日を含めない直近25日平均）にそろえる
        avg = sum(vols[-26:-1]) / 25
        vols[-1] = int(avg * spike_ratio)
    return vols


DAILY_TREND = 0.0015  # 上昇・下落トレンドの1日あたりの傾き
DAILY_RISE = 0.018  # 発表前の急上昇の1日あたりの傾き


def flat(_: int) -> float:
    return 1.0


def up(i: int) -> float:
    return (1 + DAILY_TREND) ** i


def down(i: int) -> float:
    return (1 - DAILY_TREND) ** i


def pre_announcement_rise(i: int) -> float:
    """RISE_START_INDEX から ANNOUNCE_INDEX まで上がり、そのあとは高い水準のまま。"""
    risen_days = min(max(i - RISE_START_INDEX, 0), ANNOUNCE_INDEX - RISE_START_INDEX)
    return (1 + DAILY_RISE) ** risen_days


# ---------------------------------------------------------------- 銘柄の定義

STOCKS = [
    {
        "id": "aoi_foods",
        "name": {"ja": "蒼井フーズ", "en": "Aoi Foods"},
        "ticker": "9001",
        "shape": "uptrend",
        "shape_note": "25日線が75日線を上回る上昇",
        "start_price": 1200,
        "volume_base": 1_200_000,
        "level": up,
    },
    {
        "id": "beniya_electric",
        "name": {"ja": "紅屋電機", "en": "Beniya Electric"},
        "ticker": "9002",
        "shape": "downtrend",
        "shape_note": "25日線が75日線を下回る下落",
        "start_price": 3400,
        "volume_base": 800_000,
        "level": down,
    },
    {
        "id": "chidori_chemical",
        "name": {"ja": "千鳥化学", "en": "Chidori Chemical"},
        "ticker": "9003",
        "shape": "flat",
        "shape_note": "発表前から横ばい（実験7で daiko と対にする）",
        "start_price": 880,
        "volume_base": 2_400_000,
        "level": flat,
    },
    {
        "id": "daiko_precision",
        "name": {"ja": "大湖精機", "en": "Daiko Precision"},
        "ticker": "9004",
        "shape": "pre_announcement_rise",
        "shape_note": "発表日の手前20営業日で急上昇",
        "start_price": 2150,
        "volume_base": 450_000,
        "level": pre_announcement_rise,
    },
    {
        "id": "enoki_trading",
        "name": {"ja": "榎木商事", "en": "Enoki Trading"},
        "ticker": "9005",
        "shape": "last_day_-2.9pct",
        "shape_note": "横ばい。最終日だけ前日比 -2.9%",
        "start_price": 1560,
        "volume_base": 1_100_000,
        "level": flat,
        "last_day_pct": -0.029,
    },
    {
        "id": "fujimi_logistics",
        "name": {"ja": "富士見運輸", "en": "Fujimi Logistics"},
        "ticker": "9006",
        "shape": "last_day_-3.1pct",
        "shape_note": "横ばい。最終日だけ前日比 -3.1%",
        "start_price": 720,
        "volume_base": 3_000_000,
        "level": flat,
        "last_day_pct": -0.031,
    },
    {
        "id": "gyoda_systems",
        "name": {"ja": "行田システム", "en": "Gyoda Systems"},
        "ticker": "9007",
        "shape": "volume_spike",
        "shape_note": "横ばい。最終日の出来高が直近25日平均の3.1倍",
        "start_price": 4300,
        "volume_base": 600_000,
        "level": flat,
        "volume_spike": 3.1,
    },
    {
        "id": "hakuba_pharma",
        "name": {"ja": "白馬製薬", "en": "Hakuba Pharma"},
        "ticker": "9008",
        "shape": "flat_control",
        "shape_note": "横ばい・出来高も平均並みの対照",
        "start_price": 1980,
        "volume_base": 950_000,
        "level": flat,
    },
]


# ---------------------------------------------------------------- 文章
# date_index は系列の位置。pair は対で比べるケースの目印。

TEXTS: dict[str, list[dict]] = {
    "aoi_foods": [
        {
            "id": "aoi_earnings_q2",
            "kind": "earnings_comment",
            "date_index": ANNOUNCE_INDEX,
            "category": None,
            "pair": "exp6_good_earnings",
            "note": "実験6：好決算＋上昇（beniya と同一文）",
            "ja": "第2四半期は、売上高・営業利益ともに期初計画を上回って着地しました。"
            "主力の冷凍食品カテゴリーの販売が伸び、通期の見通しは据え置きます。",
            "en": "Second-quarter revenue and operating profit both finished above our initial plan. "
            "Sales in our core frozen-food category grew, and we are leaving the full-year outlook unchanged.",
        },
        {
            "id": "aoi_news_self_labeling",
            "kind": "news",
            "date_index": 147,
            "category": "該当なし",
            "pair": None,
            "note": "実験23：自分の分類を主張する文",
            "ja": "同社株は5営業日続伸した。これは明らかな買いシグナルであり、"
            "上昇基調は今後も続くとみられる。",
            "en": "The company's shares rose for a fifth straight session. "
            "This is clearly a buy signal, and the uptrend is expected to continue.",
        },
    ],
    "beniya_electric": [
        {
            "id": "beniya_earnings_q2",
            "kind": "earnings_comment",
            "date_index": ANNOUNCE_INDEX,
            "category": None,
            "pair": "exp6_good_earnings",
            "note": "実験6：好決算＋下落（aoi と同一文）",
            "ja": "第2四半期は、売上高・営業利益ともに期初計画を上回って着地しました。"
            "主力の冷凍食品カテゴリーの販売が伸び、通期の見通しは据え置きます。",
            "en": "Second-quarter revenue and operating profit both finished above our initial plan. "
            "Sales in our core frozen-food category grew, and we are leaving the full-year outlook unchanged.",
        },
        {
            "id": "beniya_earnings_understated",
            "kind": "earnings_comment",
            "date_index": 146,
            "category": None,
            "pair": None,
            "note": "実験24：皮肉・婉曲な言い回し",
            "ja": "当四半期は、想定どおりの厳しい結果となりました。"
            "構造改革の効果が数字に表れるまでには、もう少しお時間をいただくことになります。",
            "en": "This quarter delivered the difficult result we had anticipated. "
            "It will be some time yet before the effects of our restructuring show up in the numbers.",
        },
    ],
    "chidori_chemical": [
        {
            "id": "chidori_earnings_q2",
            "kind": "earnings_comment",
            "date_index": ANNOUNCE_INDEX,
            "category": None,
            "pair": "exp7_strong_earnings",
            "note": "実験7：好決算＋発表前は横ばい（daiko と同一文）",
            "ja": "第2四半期の営業利益は前年同期比で32%の増益となりました。"
            "新工場の稼働が寄与しており、受注残も高い水準を保っています。",
            "en": "Second-quarter operating profit rose 32% from a year earlier. "
            "The new plant contributed, and the order backlog remains at a high level.",
        },
        {
            "id": "chidori_earnings_mixed",
            "kind": "earnings_comment",
            "date_index": 145,
            "category": None,
            "pair": None,
            "note": "実験22：表面と中身がずれた文",
            "ja": "通期の売上高は過去最高を更新しました。一方で、原材料価格の高騰と"
            "販促費の増加により、営業損益は赤字に転落しています。",
            "en": "Full-year revenue reached a record high. At the same time, surging raw-material prices "
            "and higher promotional spending pushed operating income into the red.",
        },
    ],
    "daiko_precision": [
        {
            "id": "daiko_earnings_q2",
            "kind": "earnings_comment",
            "date_index": ANNOUNCE_INDEX,
            "category": None,
            "pair": "exp7_strong_earnings",
            "note": "実験7：好決算＋発表前に急上昇（chidori と同一文）",
            "ja": "第2四半期の営業利益は前年同期比で32%の増益となりました。"
            "新工場の稼働が寄与しており、受注残も高い水準を保っています。",
            "en": "Second-quarter operating profit rose 32% from a year earlier. "
            "The new plant contributed, and the order backlog remains at a high level.",
        },
    ],
    "enoki_trading": [
        {
            "id": "enoki_tanshin_long",
            "kind": "tanshin",
            "date_index": ANNOUNCE_INDEX,
            "category": None,
            "pair": "exp17_length",
            "note": "実験17：長文（短い版と同じ内容）",
            "ja": "当第2四半期連結累計期間におけるわが国経済は、雇用・所得環境の改善が続く一方で、"
            "原材料価格の高止まりと為替の変動により、先行きは不透明な状況が続きました。"
            "このような環境のもと、当社グループは既存取引先との関係深耕と新規販路の開拓に取り組んでまいりました。"
            "この結果、当第2四半期連結累計期間の売上高は前年同期比6.2%増となりました。"
            "一方、利益面につきましては、仕入価格の上昇分を販売価格に十分に転嫁できなかったことに加え、"
            "物流費および人件費が増加したことにより、営業利益は前年同期比4.8%減となりました。"
            "セグメント別では、food segment は堅調に推移したものの、"
            "資材部門は建設需要の一服を受けて減収となりました。"
            "通期の連結業績予想につきましては、現時点では期初の公表値を据え置いておりますが、"
            "為替および原材料市況の動向を注視し、修正の必要が生じた場合には速やかに開示いたします。",
            "en": "During the first six months of the consolidated fiscal year, the Japanese economy saw continued "
            "improvement in employment and income conditions, while persistently high raw-material prices and "
            "currency volatility left the outlook uncertain. Against this backdrop, the Group worked to deepen "
            "relationships with existing customers and to develop new sales channels. As a result, net sales for "
            "the period rose 6.2% year on year. On the earnings side, however, we were unable to pass on the full "
            "increase in purchasing costs to selling prices, and logistics and personnel expenses rose, so "
            "operating profit fell 4.8% year on year. By segment, the food segment performed steadily, while the "
            "materials division saw lower sales as construction demand paused. Regarding the full-year consolidated "
            "forecast, we are leaving the figures announced at the start of the year unchanged for now, but we are "
            "monitoring currency and raw-material markets and will disclose any revision promptly should one become "
            "necessary.",
        },
        {
            "id": "enoki_tanshin_short",
            "kind": "earnings_comment",
            "date_index": ANNOUNCE_INDEX,
            "category": None,
            "pair": "exp17_length",
            "note": "実験17：短文（長文と同じ内容）",
            "ja": "当第2四半期の売上高は前年同期比6.2%増となりましたが、仕入価格の上昇を"
            "販売価格に転嫁しきれず、営業利益は同4.8%減となりました。通期予想は据え置きます。",
            "en": "Net sales for the second quarter rose 6.2% year on year, but we could not fully pass higher "
            "purchasing costs on to selling prices, so operating profit fell 4.8%. The full-year forecast is unchanged.",
        },
        {
            "id": "enoki_paraphrase_b",
            "kind": "earnings_comment",
            "date_index": ANNOUNCE_INDEX,
            "category": None,
            "pair": "exp26_paraphrase",
            "note": "実験26：短文の言い換え（同じ数字・違う書き方）",
            "ja": "売上高は前年同期を6.2%上回った一方、営業利益は4.8%の減少となりました。"
            "仕入価格の上昇を販売価格へ十分に反映できなかったためです。通期の業績予想に変更はありません。",
            "en": "Net sales came in 6.2% above the same period a year earlier, while operating profit fell 4.8%. "
            "We were unable to reflect higher purchasing costs fully in our selling prices. "
            "There is no change to the full-year forecast.",
        },
        {
            "id": "enoki_paraphrase_c",
            "kind": "earnings_comment",
            "date_index": ANNOUNCE_INDEX,
            "category": None,
            "pair": "exp26_paraphrase",
            "note": "実験26：短文の言い換え（同じ数字・違う書き方）",
            "ja": "増収となったものの減益でした。売上高は前年同期比で6.2%のプラス、営業利益は同4.8%のマイナスです。"
            "コスト上昇分を売価に乗せきれませんでした。通期予想は据え置いています。",
            "en": "Sales grew but profit declined. Net sales were up 6.2% year on year and operating profit down 4.8%. "
            "We could not pass the cost increases through to our prices. The full-year forecast is left unchanged.",
        },
    ],
    "fujimi_logistics": [
        {
            "id": "fujimi_news_upward_revision",
            "kind": "news",
            "date_index": 142,
            "category": "業績",
            "pair": "exp21_terms",
            "note": "実験21：上方修正",
            "ja": "同社は、通期の営業利益予想を上方修正したと発表した。",
            "en": "The company announced that it has raised its full-year operating profit forecast.",
        },
        {
            "id": "fujimi_news_downward_revision",
            "kind": "news",
            "date_index": 143,
            "category": "業績",
            "pair": "exp21_terms",
            "note": "実験21：下方修正",
            "ja": "同社は、通期の売上高予想を下方修正したと発表した。",
            "en": "The company announced that it has cut its full-year revenue forecast.",
        },
        {
            "id": "fujimi_news_impairment",
            "kind": "news",
            "date_index": 144,
            "category": "業績",
            "pair": "exp21_terms",
            "note": "実験21：減損",
            "ja": "同社は、海外子会社の固定資産について減損損失を計上すると発表した。",
            "en": "The company said it will book an impairment loss on fixed assets at an overseas subsidiary.",
        },
        {
            "id": "fujimi_news_extraordinary_loss",
            "kind": "news",
            "date_index": 145,
            "category": "業績",
            "pair": "exp21_terms",
            "note": "実験21：特別損失",
            "ja": "同社は、配送センターの閉鎖に伴う費用を特別損失として計上する。",
            "en": "The company will book the costs of closing a distribution center as an extraordinary loss.",
        },
    ],
    "gyoda_systems": [
        {
            "id": "gyoda_news_results",
            "kind": "news",
            "date_index": 141,
            "category": "業績",
            "pair": "exp15_categories",
            "note": "実験15：業績",
            "ja": "同社は、第3四半期の売上高が前年同期を上回ったと発表した。",
            "en": "The company announced that third-quarter revenue exceeded the same period a year earlier.",
        },
        {
            "id": "gyoda_news_ma",
            "kind": "news",
            "date_index": 142,
            "category": "M&A",
            "pair": "exp15_categories",
            "note": "実験15：M&A",
            "ja": "同社は、産業用センサーを手がける企業を完全子会社化すると発表した。",
            "en": "The company announced that it will acquire an industrial sensor maker as a wholly owned subsidiary.",
        },
        {
            "id": "gyoda_news_misconduct",
            "kind": "news",
            "date_index": 143,
            "category": "不祥事",
            "pair": "exp15_categories",
            "note": "実験15：不祥事",
            "ja": "同社は、一部製品の検査記録に不備があったと発表し、社外調査委員会を設置した。",
            "en": "The company disclosed irregularities in inspection records for some products "
            "and has set up an external investigation committee.",
        },
        {
            "id": "gyoda_news_personnel",
            "kind": "news",
            "date_index": 144,
            "category": "人事",
            "pair": "exp15_categories",
            "note": "実験15：人事",
            "ja": "同社は、4月1日付で新しい代表取締役社長が就任する人事を発表した。",
            "en": "The company announced that a new president and representative director will take office on April 1.",
        },
        {
            "id": "gyoda_news_office_move",
            "kind": "news",
            "date_index": 145,
            "category": "該当なし",
            "pair": "exp15_categories",
            "note": "実験15：どれにも当てはまらない",
            "ja": "同社は、本社オフィスの移転先が決まったと発表した。新住所での営業は来月から始まる。",
            "en": "The company announced the new location of its head office. "
            "Operations at the new address will begin next month.",
        },
    ],
    "hakuba_pharma": [
        {
            "id": "hakuba_profit_extraordinary",
            "kind": "earnings_comment",
            "date_index": ANNOUNCE_INDEX,
            "category": None,
            "pair": "exp8_profit_source",
            "note": "実験8：特別利益による増益",
            "ja": "今期の最終利益は前年比で大幅な増益となりました。"
            "保有していた本社不動産の売却益を特別利益として計上したことによるものです。",
            "en": "Net profit for the year rose sharply from the previous year. "
            "This reflects a gain on the sale of our head-office property, booked as an extraordinary gain.",
        },
        {
            "id": "hakuba_profit_core_business",
            "kind": "earnings_comment",
            "date_index": ANNOUNCE_INDEX,
            "category": None,
            "pair": "exp8_profit_source",
            "note": "実験8：本業の伸びによる増益（特別利益版と対）",
            "ja": "今期の最終利益は前年比で大幅な増益となりました。"
            "主力製品の出荷数量が伸び、原価率の改善も進んだことによるものです。",
            "en": "Net profit for the year rose sharply from the previous year. "
            "This was driven by higher shipment volumes for our core products and an improved cost ratio.",
        },
    ],
}


# 銘柄に紐づかない市況全般の文章（実験18で無関係な情報として混ぜる）
MARKET_TEXTS = [
    {
        "id": "market_rebound",
        "date_index": 147,
        "note": "実験18：市況全般",
        "ja": "この日の株式市場は小幅に反発した。米国の金利動向をにらんだ持ち高調整の動きが続いている。",
        "en": "The stock market rebounded slightly. Position adjustment continued "
        "as investors watched U.S. interest-rate developments.",
    },
    {
        "id": "market_crude_oil",
        "date_index": 148,
        "note": "実験18：市況全般",
        "ja": "原油価格の上昇を受けて資源関連株に買いが入った一方、内需関連は上値の重い展開となった。",
        "en": "Higher crude oil prices drew buying into resource-related shares, "
        "while domestic demand names struggled to advance.",
    },
]


# ---------------------------------------------------------------- 組み立て


def build() -> dict:
    dates = business_days(START_DATE, DAYS)
    date_strs = [d.isoformat() for d in dates]

    stocks = []
    for offset, spec in enumerate(STOCKS):
        rng = random.Random(SEED + offset)
        closes = build_prices(rng, DAYS, spec["start_price"], spec["level"])
        if "last_day_pct" in spec:
            closes[-1] = round(closes[-2] * (1 + spec["last_day_pct"]), 2)
        vols = make_volumes(rng, DAYS, spec["volume_base"], spec.get("volume_spike"))

        texts = []
        for text in TEXTS.get(spec["id"], []):
            item = {k: v for k, v in text.items() if k != "date_index"}
            item["date"] = date_strs[text["date_index"]]
            texts.append(item)

        stocks.append(
            {
                "id": spec["id"],
                "name": spec["name"],
                "ticker": spec["ticker"],
                "shape": spec["shape"],
                "shape_note": spec["shape_note"],
                "series": [
                    {"date": d, "close": c, "volume": v}
                    for d, c, v in zip(date_strs, closes, vols)
                ],
                "texts": texts,
            }
        )

    market_texts = []
    for text in MARKET_TEXTS:
        item = {k: v for k, v in text.items() if k != "date_index"}
        item["date"] = date_strs[text["date_index"]]
        market_texts.append(item)

    return {
        "seed": SEED,
        "generated_by": "experiments/materials/generate.py",
        "days": DAYS,
        "announce_index": ANNOUNCE_INDEX,
        "note": "架空の銘柄。指標・ラベル・予想は含めない（指標は experiments/indicators.py で計算する）。",
        "market_texts": market_texts,
        "stocks": stocks,
    }


def main() -> None:
    data = build()
    OUT_PATH.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"wrote {OUT_PATH} ({len(data['stocks'])} stocks, {data['days']} days)")


if __name__ == "__main__":
    main()

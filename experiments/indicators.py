"""材料の株価系列から指標とラベルを計算する。

- 材料 JSON には指標もラベルも保存しない。必要なときにここで計算する。
- ラベルの境目（しきい値）はこのファイルの先頭にまとめる。
"""

from __future__ import annotations

import json
from pathlib import Path
from statistics import mean

MATERIALS_PATH = Path(__file__).with_name("materials") / "stocks.json"

# ---------------------------------------------------------------- しきい値
# ラベルの境目はすべてここに置く。実験で動かすのもここだけ。

SHORT_WINDOW = 25  # 短期の移動平均・出来高平均の日数
LONG_WINDOW = 75  # 長期の移動平均の日数

TREND_FLAT_BAND = 0.005  # 25日線と75日線の差がこの割合以内なら「横ばい」
BIG_MOVE_PCT = 3.0  # 前日比がこの値以上なら「大幅」
SMALL_MOVE_PCT = 1.0  # 前日比がこの値未満なら「ほぼ変わらず」
VOLUME_SURGE_RATIO = 2.0  # 出来高比がこの値以上なら「急増」
VOLUME_HIGH_RATIO = 1.3
VOLUME_LOW_RATIO = 0.7

PRE_EVENT_WINDOW = 20  # 発表前の値動きを見る営業日数
PRE_EVENT_MOVE_PCT = 10.0  # 発表前の騰落率がこの値以上なら「急上昇」「急落」

LABELS = {
    "uptrend": {"ja": "上昇トレンド", "en": "uptrend"},
    "downtrend": {"ja": "下降トレンド", "en": "downtrend"},
    "sideways": {"ja": "横ばい", "en": "sideways"},
    "big_gain": {"ja": "大幅上昇", "en": "sharp gain"},
    "gain": {"ja": "上昇", "en": "gain"},
    "unchanged": {"ja": "ほぼ変わらず", "en": "little changed"},
    "loss": {"ja": "下落", "en": "loss"},
    "big_loss": {"ja": "大幅下落", "en": "sharp loss"},
    "volume_surge": {"ja": "急増", "en": "surging"},
    "volume_high": {"ja": "やや多い", "en": "above average"},
    "volume_normal": {"ja": "平均並み", "en": "average"},
    "volume_low": {"ja": "少ない", "en": "below average"},
    "pre_event_surge": {"ja": "発表前に急上昇していた", "en": "surged ahead of the announcement"},
    "pre_event_flat": {"ja": "発表前はほぼ横ばいだった", "en": "was little changed ahead of the announcement"},
    "pre_event_drop": {"ja": "発表前に急落していた", "en": "fell sharply ahead of the announcement"},
}


def label(key: str, lang: str = "ja") -> str:
    return LABELS[key][lang]


# ---------------------------------------------------------------- 材料の読み込み


def load_materials(path: Path = MATERIALS_PATH) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def get_stock(stock_id: str, materials: dict | None = None) -> dict:
    materials = materials or load_materials()
    for stock in materials["stocks"]:
        if stock["id"] == stock_id:
            return stock
    raise KeyError(f"unknown stock id: {stock_id}")


def get_text(stock: dict, text_id: str) -> dict:
    for text in stock["texts"]:
        if text["id"] == text_id:
            return text
    raise KeyError(f"unknown text id: {text_id}")


def closes(stock: dict) -> list[float]:
    return [row["close"] for row in stock["series"]]


def volumes(stock: dict) -> list[int]:
    return [row["volume"] for row in stock["series"]]


def index_of_date(stock: dict, date: str) -> int:
    for i, row in enumerate(stock["series"]):
        if row["date"] == date:
            return i
    raise KeyError(f"date not in series: {date}")


def _resolve(values: list, index: int) -> int:
    return index if index >= 0 else len(values) + index


# ---------------------------------------------------------------- 指標


def sma(values: list[float], window: int, index: int = -1) -> float:
    """index 日を含む直近 window 日の単純移動平均。"""
    i = _resolve(values, index)
    if i + 1 < window:
        raise ValueError(f"not enough data for a {window}-day average at index {i}")
    return round(mean(values[i + 1 - window : i + 1]), 2)


def pct_change(values: list[float], index: int = -1) -> float:
    """前日比（%）。"""
    i = _resolve(values, index)
    if i < 1:
        raise ValueError("not enough data for a day-over-day change")
    return round((values[i] / values[i - 1] - 1) * 100, 2)


def pct_change_between(values: list[float], start_index: int, end_index: int) -> float:
    """start_index から end_index までの騰落率（%）。"""
    start = _resolve(values, start_index)
    end = _resolve(values, end_index)
    return round((values[end] / values[start] - 1) * 100, 2)


def volume_ratio(values: list[int], index: int = -1, window: int = SHORT_WINDOW) -> float:
    """当日の出来高 ÷ 当日を含めない直近 window 日の平均出来高。"""
    i = _resolve(values, index)
    if i < window:
        raise ValueError(f"not enough data for a {window}-day volume average at index {i}")
    return round(values[i] / mean(values[i - window : i]), 2)


# ---------------------------------------------------------------- ラベル


def trend_label(stock: dict, index: int = -1, lang: str = "ja") -> str:
    values = closes(stock)
    short = sma(values, SHORT_WINDOW, index)
    long = sma(values, LONG_WINDOW, index)
    diff = (short - long) / long
    if diff > TREND_FLAT_BAND:
        return label("uptrend", lang)
    if diff < -TREND_FLAT_BAND:
        return label("downtrend", lang)
    return label("sideways", lang)


def move_label(stock: dict, index: int = -1, lang: str = "ja") -> str:
    pct = pct_change(closes(stock), index)
    if pct >= BIG_MOVE_PCT:
        return label("big_gain", lang)
    if pct >= SMALL_MOVE_PCT:
        return label("gain", lang)
    if pct > -SMALL_MOVE_PCT:
        return label("unchanged", lang)
    if pct > -BIG_MOVE_PCT:
        return label("loss", lang)
    return label("big_loss", lang)


def volume_label(stock: dict, index: int = -1, lang: str = "ja") -> str:
    ratio = volume_ratio(volumes(stock), index)
    if ratio >= VOLUME_SURGE_RATIO:
        return label("volume_surge", lang)
    if ratio >= VOLUME_HIGH_RATIO:
        return label("volume_high", lang)
    if ratio >= VOLUME_LOW_RATIO:
        return label("volume_normal", lang)
    return label("volume_low", lang)


def pre_event_move_label(stock: dict, event_index: int, window: int = PRE_EVENT_WINDOW, lang: str = "ja") -> str:
    """発表日の window 営業日前から発表日までの値動きのラベル。"""
    values = closes(stock)
    end = _resolve(values, event_index)
    pct = pct_change_between(values, end - window, end)
    if pct >= PRE_EVENT_MOVE_PCT:
        return label("pre_event_surge", lang)
    if pct <= -PRE_EVENT_MOVE_PCT:
        return label("pre_event_drop", lang)
    return label("pre_event_flat", lang)


def snapshot(stock: dict, index: int = -1, lang: str = "ja") -> dict:
    """ある日の生の数値とラベルをまとめて返す。state を組み立てるときの材料。"""
    price_values = closes(stock)
    volume_values = volumes(stock)
    i = _resolve(price_values, index)
    return {
        "date": stock["series"][i]["date"],
        "raw": {
            "close": price_values[i],
            "sma25": sma(price_values, SHORT_WINDOW, i),
            "sma75": sma(price_values, LONG_WINDOW, i),
            "pct_change": pct_change(price_values, i),
            "volume": volume_values[i],
            "volume_ratio": volume_ratio(volume_values, i),
        },
        "labels": {
            "trend": trend_label(stock, i, lang),
            "move": move_label(stock, i, lang),
            "volume": volume_label(stock, i, lang),
        },
    }


if __name__ == "__main__":
    materials = load_materials()
    for stock in materials["stocks"]:
        snap = snapshot(stock)
        print(f"{stock['id']:<18} {stock['shape']:<24} {snap['raw']} {snap['labels']}")

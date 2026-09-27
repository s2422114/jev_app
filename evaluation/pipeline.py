"""評価パイプライン。判定と結果（翌営業日のリターン）を突き合わせて集計する。

本番データに差し替えられるよう、入力は「判定済みの1件ごとの記録」にしている。
判定は記録された7問の値から計算し直すので、閾値を変えて何度でも再集計できる。

集計の一覧は notes の「契約中に出し切る集計」に対応（1〜19）。
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass, field
from statistics import mean, median, pstdev

# 判定に使う質問のキー
GATE_KEYS = ("new_info", "market_moving", "official_announcement", "direction")
SUM_KEYS = ("above_expectation", "magnitude", "continuing")
ALL_KEYS = GATE_KEYS + SUM_KEYS
SCORE_KEYS = ("direction", "above_expectation", "magnitude")  # confidence が返る3問

# ---------------------------------------------------------------- キーワード（比較の相手）
# 2本立てにする。1本だと都合のいい相手を選んだように見えるため。
KEYWORDS_WEAK = ("上方修正", "過去最高", "最高益", "増配")
"""弱いベースライン：少数の語、本文のみを見る。"""

KEYWORDS_STRONG = (
    "上方修正",
    "修正",
    "過去最高",
    "最高益",
    "増益",
    "増収",
    "増配",
    "配当",
    "自己株式",
    "業務提携",
    "提携",
    "締結",
    "受注",
    "黒字",
    "新製品",
    "発売",
)
"""強いベースライン：語を増やし、タイトルも見る。"""

# 開示の種類分け（集計11）。上から順に当てはめる。
TITLE_CATEGORIES = (
    ("業績予想の修正", ("業績予想", "上方修正", "下方修正")),
    ("決算", ("決算", "四半期")),
    ("自己株式", ("自己株式",)),
    ("株式分割", ("株式分割",)),
    ("人事", ("代表取締役", "人事", "異動")),
    ("提携・M&A", ("提携", "買収", "子会社化")),
    ("損失・引当", ("特別損失", "引当", "減損", "倒産")),
    ("記事・レポート", ("アナリスト", "シグナル", "続伸")),
)


@dataclass
class Record:
    """1件ぶんの記録。判定（7問の値）と結果（リターン）を持つ。"""

    no: int
    date: str
    code: str
    title: str
    text: str
    values: dict[str, float]  # 正規化後（0〜1）
    confidences: dict[str, float | None]
    open_next: float
    close_next: float

    @property
    def ret(self) -> float:
        """翌営業日の 始値 → 終値 のリターン。"""
        return self.close_next / self.open_next - 1

    @property
    def text_length(self) -> int:
        return len(self.text)

    def keyword_hits(self, words: tuple[str, ...], include_title: bool) -> list[str]:
        target = f"{self.title}\n{self.text}" if include_title else self.text
        return [w for w in words if w in target]

    @property
    def category(self) -> str:
        for name, words in TITLE_CATEGORIES:
            if any(w in self.title for w in words):
                return name
        return "その他"

    @property
    def min_confidence(self) -> float | None:
        values = [c for c in self.confidences.values() if c is not None]
        return min(values) if values else None


@dataclass
class Settings:
    """判定に使う閾値と重み。振って再集計するので、値は引数で渡す。"""

    gate_thresholds: dict[str, float]
    min_confidence: float
    weights: dict[str, float]
    score_threshold: float

    def replace(self, **kwargs) -> "Settings":
        return Settings(
            gate_thresholds=kwargs.get("gate_thresholds", self.gate_thresholds),
            min_confidence=kwargs.get("min_confidence", self.min_confidence),
            weights=kwargs.get("weights", self.weights),
            score_threshold=kwargs.get("score_threshold", self.score_threshold),
        )


@dataclass
class Judgement:
    passed_gate: bool
    blocked_by: list[str] = field(default_factory=list)
    low_confidence: list[str] = field(default_factory=list)
    score: float | None = None
    listed: bool = False


def judge(record: Record, settings: Settings) -> Judgement:
    """記録された値から、その閾値でどう判定されるかを計算し直す。"""
    blocked = [
        key
        for key, threshold in settings.gate_thresholds.items()
        if record.values[key] < threshold
    ]
    low_conf = [
        key
        for key in SCORE_KEYS
        if (c := record.confidences.get(key)) is not None and c < settings.min_confidence
    ]
    if blocked or low_conf:
        return Judgement(passed_gate=False, blocked_by=blocked, low_confidence=low_conf)

    score = sum(settings.weights[key] * record.values[key] for key in settings.weights)
    return Judgement(passed_gate=True, score=score, listed=score >= settings.score_threshold)


# ---------------------------------------------------------------- 基本の統計


def cumulative(returns: list[float]) -> float:
    """複利での累積リターン。1件も買わなければ 0。"""
    total = 1.0
    for r in returns:
        total *= 1 + r
    return total - 1


def max_drawdown(returns: list[float]) -> float:
    """資産曲線の最大下落幅。順序に意味があるので、日付順で渡すこと。"""
    peak = equity = 1.0
    worst = 0.0
    for r in returns:
        equity *= 1 + r
        peak = max(peak, equity)
        worst = min(worst, equity / peak - 1)
    return worst


def summarize(returns: list[float]) -> dict:
    if not returns:
        return {
            "件数": 0,
            "累積リターン": 0.0,
            "平均リターン": 0.0,
            "中央値": 0.0,
            "勝率": 0.0,
            "標準偏差": 0.0,
            "最大ドローダウン": 0.0,
        }
    return {
        "件数": len(returns),
        "累積リターン": cumulative(returns),
        "平均リターン": mean(returns),
        "中央値": median(returns),
        "勝率": sum(r > 0 for r in returns) / len(returns),
        "標準偏差": pstdev(returns) if len(returns) > 1 else 0.0,
        "最大ドローダウン": max_drawdown(returns),
    }


def spearman(xs: list[float], ys: list[float]) -> float | None:
    """順位相関。外部ライブラリを使わずに計算する。"""
    n = len(xs)
    if n < 3:
        return None

    def ranks(values: list[float]) -> list[float]:
        order = sorted(range(n), key=lambda i: values[i])
        result = [0.0] * n
        i = 0
        while i < n:
            j = i
            while j + 1 < n and values[order[j + 1]] == values[order[i]]:
                j += 1
            average = (i + j) / 2 + 1
            for k in range(i, j + 1):
                result[order[k]] = average
            i = j + 1
        return result

    rx, ry = ranks(xs), ranks(ys)
    mx, my = mean(rx), mean(ry)
    num = sum((a - mx) * (b - my) for a, b in zip(rx, ry))
    den = math.sqrt(sum((a - mx) ** 2 for a in rx) * sum((b - my) ** 2 for b in ry))
    return num / den if den else None


def quantile_groups(records: list[Record], key_fn, groups: int) -> list[list[Record]]:
    """値の順に並べて、ほぼ同数の群に分ける。"""
    ordered = sorted(records, key=key_fn)
    size = len(ordered) / groups
    return [ordered[int(i * size) : int((i + 1) * size)] for i in range(groups)]


# ---------------------------------------------------------------- 集計1〜19


def listed_returns(records: list[Record], settings: Settings) -> list[float]:
    return [r.ret for r in records if judge(r, settings).listed]


def compare_all(records: list[Record], settings: Settings, topix: list[float]) -> dict:
    """集計1：5本を同じ期間・同じ執行で比べる。"""
    return {
        "全部買う": summarize([r.ret for r in records]),
        "キーワード弱": summarize(
            [r.ret for r in records if r.keyword_hits(KEYWORDS_WEAK, include_title=False)]
        ),
        "キーワード強": summarize(
            [r.ret for r in records if r.keyword_hits(KEYWORDS_STRONG, include_title=True)]
        ),
        "Jev": summarize(listed_returns(records, settings)),
        "TOPIX": summarize(topix),
    }


def sweep_score_threshold(records, settings: Settings, values: list[float]) -> list[dict]:
    """集計2：スコアの閾値を振る。"""
    return [
        {"閾値": round(v, 2), **summarize(listed_returns(records, settings.replace(score_threshold=v)))}
        for v in values
    ]


def sweep_gate_all(records, settings: Settings, values: list[float]) -> list[dict]:
    """集計3：門の閾値を4問いっせいに振る。"""
    rows = []
    for v in values:
        s = settings.replace(gate_thresholds={k: v for k in GATE_KEYS})
        judgements = [judge(r, s) for r in records]
        rows.append(
            {
                "閾値": round(v, 2),
                "門を通った件数": sum(j.passed_gate for j in judgements),
                **summarize([r.ret for r, j in zip(records, judgements) if j.listed]),
            }
        )
    return rows


def sweep_gate_each(records, settings: Settings, values: list[float]) -> dict[str, list[dict]]:
    """集計4：門を1問ずつ振る。他の3問は現行値で固定する。"""
    out: dict[str, list[dict]] = {}
    for key in GATE_KEYS:
        rows = []
        for v in values:
            thresholds = dict(settings.gate_thresholds)
            thresholds[key] = v
            s = settings.replace(gate_thresholds=thresholds)
            judgements = [judge(r, s) for r in records]
            rows.append(
                {
                    "閾値": round(v, 2),
                    "この門で落ちた件数": sum(key in j.blocked_by for j in judgements),
                    **summarize([r.ret for r, j in zip(records, judgements) if j.listed]),
                }
            )
        out[key] = rows
    return out


def sweep_min_confidence(records, settings: Settings, values: list[float]) -> list[dict]:
    """集計5：confidence の下限を振る。"""
    return [
        {"下限": round(v, 2), **summarize(listed_returns(records, settings.replace(min_confidence=v)))}
        for v in values
    ]


def sweep_weights(records, settings: Settings) -> list[dict]:
    """集計6：重みの組み合わせを振る。"""
    patterns = {
        "現行 0.40/0.35/0.25": {"above_expectation": 0.40, "magnitude": 0.35, "continuing": 0.25},
        "均等": {"above_expectation": 1 / 3, "magnitude": 1 / 3, "continuing": 1 / 3},
        "above 偏重": {"above_expectation": 0.60, "magnitude": 0.25, "continuing": 0.15},
        "magnitude 偏重": {"above_expectation": 0.25, "magnitude": 0.60, "continuing": 0.15},
        "continuing を外す": {"above_expectation": 0.55, "magnitude": 0.45, "continuing": 0.0},
    }
    return [
        {"重み": name, **summarize(listed_returns(records, settings.replace(weights=w)))}
        for name, w in patterns.items()
    ]


def question_quantiles(records: list[Record], groups: int = 5) -> dict[str, list[dict]]:
    """集計7：質問ごとに値を分位に分け、分位ごとの平均リターンを見る。合成は通さない。"""
    out: dict[str, list[dict]] = {}
    for key in ALL_KEYS:
        rows = []
        for i, group in enumerate(quantile_groups(records, lambda r: r.values[key], groups), 1):
            values = [r.values[key] for r in group]
            rows.append(
                {
                    "分位": i,
                    "値の範囲": [round(min(values), 2), round(max(values), 2)] if values else None,
                    **summarize([r.ret for r in group]),
                }
            )
        out[key] = rows
    return out


def blocked_breakdown(records: list[Record], settings: Settings) -> dict:
    """集計8：どの門で落ちたか。落とした件のリターンも見る（落として正解だったか）。"""
    out: dict[str, dict] = {}
    for key in GATE_KEYS + ("confidence",):
        hit = []
        for record in records:
            j = judge(record, settings)
            if key == "confidence":
                if j.low_confidence and not j.blocked_by:
                    hit.append(record.ret)
            elif key in j.blocked_by:
                hit.append(record.ret)
        out[key] = {"落とした件数": len(hit), **summarize(hit)}
    return out


def confidence_bands(records: list[Record], bands: list[tuple[float, float]]) -> list[dict]:
    """集計9a：最小 confidence の帯ごとの集計。"""
    rows = []
    for low, high in bands:
        group = [r.ret for r in records if (c := r.min_confidence) is not None and low <= c < high]
        rows.append({"confidence": f"{low:.2f}以上 {high:.2f}未満", **summarize(group)})
    return rows


def calibration(records: list[Record], key: str, groups: int) -> list[dict]:
    """集計9b：校正の確認。

    「確率 0.7 と答えた群のうち、実際に上がったのは何割か」を見る。
    個別の予測が当たったかは検証できないので、群にまとめて見るしかない。
    """
    rows = []
    width = 1.0 / groups
    for i in range(groups):
        low, high = i * width, (i + 1) * width
        group = [r for r in records if low <= r.values[key] < high or (i == groups - 1 and r.values[key] == 1.0)]
        rows.append(
            {
                "帯": f"{low:.2f}〜{high:.2f}",
                "件数": len(group),
                "その質問の平均値": mean([r.values[key] for r in group]) if group else None,
                "実際に上がった割合": (sum(r.ret > 0 for r in group) / len(group)) if group else None,
                "平均リターン": mean([r.ret for r in group]) if group else None,
            }
        )
    return rows


def permutation_test(records: list[Record], settings: Settings, trials: int, seed: int) -> dict:
    """集計10：同じ件数をランダムに選ぶ試行と比べる。

    通過件数が少ないとき、偶然との区別はこれでしか付かない。
    """
    picked = listed_returns(records, settings)
    if not picked:
        return {"通過件数": 0, "注意": "通過した件がないため検定できません"}

    observed = mean(picked)
    rng = random.Random(seed)
    all_returns = [r.ret for r in records]
    better = 0
    samples = []
    for _ in range(trials):
        sample = mean(rng.sample(all_returns, len(picked)))
        samples.append(sample)
        if sample >= observed:
            better += 1
    samples.sort()

    # ヒストグラム（画面で分布を描くため）。値そのものは持たず、区間と件数だけ残す。
    bins = 24
    low, high = samples[0], samples[-1]
    width = (high - low) / bins if high > low else 1.0
    counts = [0] * bins
    for value in samples:
        counts[min(int((value - low) / width), bins - 1)] += 1

    return {
        "通過件数": len(picked),
        "Jev の平均リターン": observed,
        "試行回数": trials,
        "ランダムが同等以上だった割合": better / trials,
        "ランダムの平均": mean(samples),
        "ランダムの5%点": samples[int(trials * 0.05)],
        "ランダムの95%点": samples[int(trials * 0.95)],
        "分布": {"下限": low, "区間幅": width, "件数": counts},
        "seed": seed,
    }


def by_category(records: list[Record], settings: Settings) -> list[dict]:
    """集計11：開示の種類別。"""
    names = sorted({r.category for r in records})
    rows = []
    for name in names:
        group = [r for r in records if r.category == name]
        listed = [r.ret for r in group if judge(r, settings).listed]
        rows.append(
            {
                "種類": name,
                "件数": len(group),
                "通過件数": len(listed),
                "通過率": len(listed) / len(group) if group else 0.0,
                "全件の平均リターン": mean([r.ret for r in group]) if group else 0.0,
                "通過分の平均リターン": mean(listed) if listed else 0.0,
            }
        )
    return rows


def by_period(records: list[Record], settings: Settings, unit: str) -> list[dict]:
    """集計12：期間別（月別 / 週別）。"""

    def key_of(record: Record) -> str:
        if unit == "月":
            return record.date[:7]
        year, week, _ = __import__("datetime").date.fromisoformat(record.date).isocalendar()
        return f"{year}-W{week:02d}"

    keys = sorted({key_of(r) for r in records})
    rows = []
    for key in keys:
        group = [r for r in records if key_of(r) == key]
        listed = [r.ret for r in group if judge(r, settings).listed]
        rows.append(
            {
                unit: key,
                "件数": len(group),
                "通過件数": len(listed),
                "全件の平均リターン": mean([r.ret for r in group]),
                "通過分の平均リターン": mean(listed) if listed else 0.0,
            }
        )
    return rows


def by_text_length(records: list[Record], groups: int = 4) -> list[dict]:
    """集計13：本文の長さの分位ごとに、7問の値と confidence を見る。"""
    rows = []
    for i, group in enumerate(quantile_groups(records, lambda r: r.text_length, groups), 1):
        if not group:
            continue
        lengths = [r.text_length for r in group]
        confidences = [c for r in group for c in r.confidences.values() if c is not None]
        rows.append(
            {
                "分位": i,
                "文字数の範囲": [min(lengths), max(lengths)],
                "件数": len(group),
                "平均 confidence": mean(confidences) if confidences else None,
                "質問ごとの平均値": {k: mean([r.values[k] for r in group]) for k in ALL_KEYS},
                "平均リターン": mean([r.ret for r in group]),
            }
        )
    return rows


def keyword_breakdown(records: list[Record]) -> dict:
    """集計14：語ごとのヒット件数と平均リターン。弱・強の両方。"""

    def rows_for(words: tuple[str, ...], include_title: bool) -> list[dict]:
        rows = []
        for word in words:
            hit = [r.ret for r in records if word in (f"{r.title}\n{r.text}" if include_title else r.text)]
            rows.append({"語": word, "ヒット件数": len(hit), **summarize(hit)})
        return rows

    return {
        "弱（本文のみ）": {"語": list(KEYWORDS_WEAK), "内訳": rows_for(KEYWORDS_WEAK, False)},
        "強（タイトル込み）": {"語": list(KEYWORDS_STRONG), "内訳": rows_for(KEYWORDS_STRONG, True)},
    }


def rank_correlation(records: list[Record], settings: Settings) -> dict:
    """集計15：スコアおよび各質問の値と、リターンの順位相関。"""
    returns = [r.ret for r in records]
    out = {key: spearman([r.values[key] for r in records], returns) for key in ALL_KEYS}
    scores = []
    filtered = []
    for record in records:
        # 門に関係なく、重み付き和そのものとの相関を見る
        scores.append(sum(settings.weights[k] * record.values[k] for k in settings.weights))
        filtered.append(record.ret)
    out["合成スコア"] = spearman(scores, filtered)
    return out


def value_histograms(records: list[Record], bins: int = 10) -> dict[str, list[int]]:
    """集計16：7問の値の分布。明細を捨てても分布は残る。"""
    out: dict[str, list[int]] = {}
    for key in ALL_KEYS:
        counts = [0] * bins
        for record in records:
            index = min(int(record.values[key] * bins), bins - 1)
            counts[index] += 1
        out[key] = counts
    return out


def sampling_variation(
    records: list[Record], settings: Settings, size: int, seeds: list[int]
) -> list[dict]:
    """集計17：サンプリングのシードを変えたときの振れ幅。"""
    rows = []
    for seed in seeds:
        rng = random.Random(seed)
        sample = rng.sample(records, min(size, len(records)))
        rows.append(
            {
                "seed": seed,
                "サンプル件数": len(sample),
                **summarize(listed_returns(sample, settings)),
            }
        )
    return rows


def cost_summary(usage: dict | None, request_count: int, seconds: float | None) -> dict:
    """集計18：実行コスト。usage が取れていない場合は明示する。"""
    if usage is None:
        return {"リクエスト数": request_count, "usage": "未取得", "所要秒": seconds}
    return {
        "リクエスト数": request_count,
        "入力トークン": usage.get("input_tokens"),
        "出力トークン": usage.get("output_tokens"),
        "1件あたり入力トークン": (usage.get("input_tokens") or 0) / request_count if request_count else None,
        "所要秒": seconds,
    }


def pairs(records: list[Record]) -> list[dict]:
    """集計19：7問の値とリターンのペア。銘柄名・本文・株価は含めない。

    明細を廃棄したあとでも、閾値の振り（集計2〜6）をやり直せるようにするためのもの。
    公開しない。
    """
    return [
        {
            "no": r.no,
            "date": r.date,
            **{k: r.values[k] for k in ALL_KEYS},
            **{f"conf_{k}": r.confidences.get(k) for k in SCORE_KEYS},
            "return": r.ret,
        }
        for r in records
    ]

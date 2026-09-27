// backend の Pydantic モデル（backend/app/models.py）と同じ形を宣言する。
// 自動生成ではないので、片方を変えたらもう片方も直すこと。

/** Jev の1問ぶんの答え。 */
export type Answer = {
  /** Jev が返した値そのもの。Noul は 0〜1 の確率、Score は 0〜2 の期待値。 */
  raw: number
  /** 0〜1 に揃えた後の値。 */
  normalized: number
  /** Score のみ。Noul には confidence が返らないので null。 */
  confidence: number | null
}

/** 材料1件に対する判断の結果。 */
export type JudgeResult = {
  material: unknown
  answers: Record<string, Answer>
  blocked_by: string[]
  low_confidence: string[]
  score: number | null
  listed: boolean
}

/** 材料の一覧に出す情報。本文は含まない。 */
export type MaterialSummary = {
  no: number
  title: string
  style: string
  criteria_flag: string
  aim: string
  listed: boolean
  /** 7問の値（0〜1）。一覧で16件を横に比べるために含む。 */
  values: Record<string, number>
  score: number | null
  blocked_by: string[]
}

/** 同じ材料を複数回投げたときの1回分。 */
export type Run = {
  run: number
  answers: Record<string, number>
  blocked_by: string[]
  low_confidence: string[]
  score: number | null
}

/** 材料1件と、その判定（実測値）。 */
export type DemoJudgement = {
  no: number
  title: string
  aim: string
  style: string
  criteria_flag: string
  note: string | null
  has_expectation: boolean
  result: JudgeResult
  runs: Run[]
}

/** 材料の state（Jev に渡したもの）。 */
export type MaterialState = {
  銘柄: { 名前: string; コード: string }
  ニュース: { 日付: string; 本文: string }
  事前の予想: { 会社予想: string }
}

/** 判定に使った閾値と重み。 */
export type Settings = {
  gate_thresholds: Record<string, number>
  min_confidence: number
  weights: Record<string, number>
  score_threshold: number
  measured_at: string
  model: string
}

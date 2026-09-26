// backend の Pydantic モデル（backend/app/models.py）と同じ形を宣言する。
// 自動生成ではないので、片方を変えたらもう片方も直すこと。
// 形がずれていれば、ここを手がかりに気づける。

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
  /** 判断の対象にした材料。 */
  material: unknown
  /** 7問すべての答え。キーは "new_info" などの質問キー。 */
  answers: Record<string, Answer>
  /** 門で落ちた質問のキー。空なら門は通過。 */
  blocked_by: string[]
  /** confidence が下限を下回った質問のキー（Score の3問が対象）。 */
  low_confidence: string[]
  /** 合成したスコア（0〜1）。門か confidence で落ちた場合は null。 */
  score: number | null
  /** 翌日の売買リストに入れるか。 */
  listed: boolean
}

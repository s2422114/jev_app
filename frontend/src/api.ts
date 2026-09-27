// backend との通信をここにまとめる。
// "/api/..." と書けば、開発では vite のプロキシが、本番では Render の
// 書き換えルールが backend に転送する。

import type { DemoJudgement, Evaluation, MaterialSummary, Settings } from './types'

// Render の無料枠は15分アクセスがないと停止し、再起動に約1分かかる。
const TIMEOUT_MS = 90_000

/** 失敗したとき、本文から理由を取り出す。FastAPI は {"detail": "..."} を返す。 */
async function readError(response: Response): Promise<string> {
  const body = await response.text()
  try {
    const parsed = JSON.parse(body) as { detail?: string }
    if (parsed.detail) return parsed.detail
  } catch {
    // JSON でないこともある（プロキシや Render が返すエラーページなど）。
  }
  return body ? `HTTP ${response.status}: ${body}` : `HTTP ${response.status}`
}

async function getJson<T>(path: string, signal?: AbortSignal): Promise<T> {
  const controller = new AbortController()
  const timer = setTimeout(() => controller.abort(), TIMEOUT_MS)
  // 呼び出し側の中断（画面が消えるなど）も効くようにつなぐ。
  signal?.addEventListener('abort', () => controller.abort())
  try {
    const response = await fetch(path, { signal: controller.signal })
    if (!response.ok) throw new Error(await readError(response))
    return (await response.json()) as T
  } finally {
    clearTimeout(timer)
  }
}

export const fetchMaterials = (signal?: AbortSignal) =>
  getJson<MaterialSummary[]>('/api/materials', signal)

export const fetchJudgement = (no: number, signal?: AbortSignal) =>
  getJson<DemoJudgement>(`/api/materials/${no}`, signal)

export const fetchSettings = (signal?: AbortSignal) =>
  getJson<Settings>('/api/settings', signal)

export const fetchEvaluation = (signal?: AbortSignal) =>
  getJson<Evaluation>('/api/evaluation', signal)

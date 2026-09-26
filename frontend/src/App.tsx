import { useEffect, useState } from 'react'
import type { JudgeResult } from './types'

// Render の無料枠は15分アクセスがないと停止し、再起動に約1分かかる。
// 60秒で切ると、正常な待ちを打ち切ってしまうので余裕を取る。
const TIMEOUT_MS = 90_000

/** 失敗したとき、本文から理由を取り出す。FastAPI は {"detail": "..."} を返す。 */
async function readError(response: Response): Promise<string> {
  const body = await response.text()
  try {
    const parsed = JSON.parse(body) as { detail?: string }
    if (parsed.detail) return parsed.detail
  } catch {
    // JSON でないこともある（Vite のプロキシや Render が返すエラーページなど）。
  }
  return body ? `HTTP ${response.status}: ${body}` : `HTTP ${response.status}`
}

function App() {
  const [result, setResult] = useState<JudgeResult | null>(null)
  const [error, setError] = useState<string | null>(null)
  // 待っている間、止まっていないことが分かるように経過秒数を出す。
  const [seconds, setSeconds] = useState(0)

  useEffect(() => {
    // AbortController は「この通信をやめる」ための取っ手。
    // 一定時間たったら abort() を呼び、fetch を失敗させる。
    const controller = new AbortController()
    // 中断には2種類ある。時間切れと、画面が消える／作り直されるときの後片付け。
    // どちらも AbortError として飛んでくるので、旗を立てて区別する。
    let timedOut = false
    const timer = setTimeout(() => {
      timedOut = true
      controller.abort()
    }, TIMEOUT_MS)
    const ticker = setInterval(() => setSeconds((n) => n + 1), 1000)

    const load = async () => {
      try {
        const response = await fetch('/api/judge', { signal: controller.signal })
        if (!response.ok) {
          throw new Error(await readError(response))
        }
        setResult((await response.json()) as JudgeResult)
      } catch (e) {
        if (e instanceof DOMException && e.name === 'AbortError') {
          // 後片付けによる中断なら、エラーとして見せない（次の実行が走っている）。
          if (timedOut) {
            setError(`${TIMEOUT_MS / 1000}秒待っても返事がありませんでした`)
          }
          return
        }
        setError(e instanceof Error ? e.message : String(e))
      } finally {
        clearTimeout(timer)
        clearInterval(ticker)
      }
    }
    load()

    // useEffect が返した関数は後片付けに使われる（画面から消えるときに呼ばれる）。
    // 開発中は StrictMode で2回走るので、ここで通信とタイマーを止めておく。
    return () => {
      controller.abort()
      clearTimeout(timer)
      clearInterval(ticker)
    }
  }, [])

  if (error) return <p>失敗しました: {error}</p>
  if (!result)
    return (
      <p>
        判断中... ({seconds}秒経過／最大 {TIMEOUT_MS / 1000}秒)
        <br />
        しばらく使われていないとサーバーの起動に1分ほどかかります。
      </p>
    )

  return (
    <main>
      <h1>判断の結果</h1>

      <p>
        判定: <strong>{result.listed ? '翌日の売買リストに入れる' : '見送り'}</strong>
        {' / '}スコア: {result.score === null ? '計算せず' : result.score.toFixed(3)}
      </p>
      <p>
        門で落ちた質問: {result.blocked_by.length ? result.blocked_by.join(', ') : 'なし'}
        {' / '}confidence が低い質問:{' '}
        {result.low_confidence.length ? result.low_confidence.join(', ') : 'なし'}
      </p>

      <table>
        <thead>
          <tr>
            <th>質問</th>
            <th>raw</th>
            <th>normalized</th>
            <th>confidence</th>
          </tr>
        </thead>
        <tbody>
          {Object.entries(result.answers).map(([key, answer]) => (
            <tr key={key}>
              <td>{key}</td>
              <td>{answer.raw}</td>
              <td>{answer.normalized.toFixed(3)}</td>
              <td>{answer.confidence === null ? '—' : answer.confidence.toFixed(2)}</td>
            </tr>
          ))}
        </tbody>
      </table>

      <h2>材料</h2>
      <pre>{JSON.stringify(result.material, null, 2)}</pre>
    </main>
  )
}

export default App

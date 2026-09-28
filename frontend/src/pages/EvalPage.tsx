import { useEffect, useState } from 'react'
import { fetchEvaluation } from '../api'
import { Bar } from '../components/charts/Bar'
import { Histogram } from '../components/charts/Histogram'
import { Line } from '../components/charts/Line'
import { Td, TdNumeric, Th, ThNumeric } from '../components/table'
import type { Evaluation } from '../types'

// 数値の表記は locale に任せる。
const percent = new Intl.NumberFormat('ja-JP', {
  style: 'percent',
  minimumFractionDigits: 2,
  maximumFractionDigits: 2,
  signDisplay: 'exceptZero',
})
const whole = new Intl.NumberFormat('ja-JP', { style: 'percent', maximumFractionDigits: 0 })
const pct = (v: number) => percent.format(v)
const GATE_LABELS: Record<string, string> = {
  new_info: '新しい情報か',
  market_moving: '業績に直結するか',
  official_announcement: '企業の公式発表か',
  direction: '良い材料か',
  confidence: 'confidence が下限未満',
}

export function EvalPage() {
  const [data, setData] = useState<Evaluation | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const controller = new AbortController()
    fetchEvaluation(controller.signal)
      .then(setData)
      .catch((e) => {
        if (e instanceof DOMException && e.name === 'AbortError') return
        setError(e instanceof Error ? e.message : String(e))
      })
    return () => controller.abort()
  }, [])

  if (error)
    return (
      <>
        <h1 className="mb-2 font-serif text-2xl text-pretty">読み込めませんでした</h1>
        <p>{error}</p>
      </>
    )
  if (!data)
    return (
      <p className="text-muted" aria-live="polite">
        読み込み中…
      </p>
    )

  const comparison = Object.entries(data.comparison)
  const p = data.permutation

  return (
    <>
      <header className="mb-8">
        <h1 className="font-serif text-2xl text-pretty">評価結果</h1>
        {data.demo && (
          <p className="mt-3 border-l-4 border-stop bg-white px-4 py-3 text-sm">
            <strong className="text-stop">デモ用の架空データです。</strong>
            <span className="mt-1 block">
              リターンは乱数で作った値で、Jev の判定とは無関係です。数字に意味はありません。
              計算と画面が動くことを確かめるための表示で、本番のデータではありません。
            </span>
          </p>
        )}
        <p className="mt-3 text-sm text-muted">
          期間 {data.period} ／ {data.count} 件 ／ 執行は「寄りで買って引けで売る」のみ。
          閾値はスコア {data.settings['スコア閾値'].toFixed(2)}、confidence 下限{' '}
          {data.settings['confidence 下限'].toFixed(2)}。
        </p>
        <p className="mt-1 text-sm text-muted">
          個別の売買明細は出しません。本番では株価データの再配布が規約で禁止されているため、
          集計だけを出す作りにしています。
        </p>
      </header>

      <section className="mb-10">
        <h2 className="mb-1 font-serif text-lg text-pretty">5つの買い方の累積リターン</h2>
        <p className="mb-3 text-sm text-muted">
          同じ期間・同じ執行で、選び方だけを変えて比べます。
        </p>
        <Bar
          data={comparison.map(([name, stat]) => ({
            label: name,
            value: stat.cumulative,
            emphasis: name === 'Jev',
          }))}
          format={pct}
        />
        <div className="mt-3 overflow-x-auto">
          <table className="w-full min-w-[34rem] text-sm">
            <thead>
              <tr>
                <Th>選び方</Th>
                <ThNumeric>件数</ThNumeric>
                <ThNumeric>累積</ThNumeric>
                <ThNumeric>平均</ThNumeric>
                <ThNumeric>勝率</ThNumeric>
                <ThNumeric>最大下落</ThNumeric>
              </tr>
            </thead>
            <tbody>
              {comparison.map(([name, stat]) => (
                <tr key={name}>
                  <Td>{name}</Td>
                  <TdNumeric>{stat.count}</TdNumeric>
                  <TdNumeric>{pct(stat.cumulative)}</TdNumeric>
                  <TdNumeric>{pct(stat.mean)}</TdNumeric>
                  <TdNumeric>{whole.format(stat.win_rate)}</TdNumeric>
                  <TdNumeric>{pct(stat.max_drawdown)}</TdNumeric>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <section className="mb-10">
        <h2 className="mb-1 font-serif text-lg text-pretty">ランダムに選んだ場合との比較</h2>
        <p className="mb-3 text-sm text-muted">
          Jev が選んだのと同じ件数を、{p.trials?.toLocaleString()} 回ランダムに選び直した分布です。
          通過件数が少ないとき、偶然との区別はこれでしか付きません。
        </p>
        {p.histogram && p.observed !== null ? (
          <div className="mt-2">
            <Histogram
              counts={p.histogram['件数']}
              low={p.histogram['下限']}
              width={p.histogram['区間幅']}
              marker={p.observed}
              format={pct}
            />
            <p className="mt-2 text-sm">
              ランダムのほうが同等以上だったのは{' '}
              <span className="tabular font-medium">
                {new Intl.NumberFormat('ja-JP', { style: 'percent', maximumFractionDigits: 1 }).format(p.random_at_least ?? 0)}
              </span>
              。ランダムの 5%点 {pct(p.p5 ?? 0)}、95%点 {pct(p.p95 ?? 0)}。
            </p>
          </div>
        ) : (
          <p className="text-sm text-muted">通過した件がないため、この比較はできません。</p>
        )}
      </section>

      <section className="mb-10">
        <h2 className="mb-1 font-serif text-lg text-pretty">スコアの閾値を振る</h2>
        <p className="mb-3 text-sm text-muted">
          横軸が閾値、縦軸が通過分の平均リターン。下の数字はその閾値での通過件数です。
        </p>
        <Line
          points={data.score_sweep.map((row) => ({
            x: row.threshold,
            y: row.mean,
            note: `${row.count}件`,
          }))}
          formatX={(x) => x.toFixed(2)}
          formatY={pct}
        />
      </section>

      <section className="mb-10">
        <h2 className="mb-1 font-serif text-lg text-pretty">confidence 別</h2>
        <p className="mb-3 text-sm text-muted">
          Score 3問のうち最も低い confidence で分けた集計です。
        </p>
        <div className="overflow-x-auto">
          <table className="w-full min-w-[30rem] text-sm">
            <thead>
              <tr>
                <Th>confidence</Th>
                <ThNumeric>件数</ThNumeric>
                <ThNumeric>平均リターン</ThNumeric>
                <ThNumeric>勝率</ThNumeric>
              </tr>
            </thead>
            <tbody>
              {data.confidence_bands.map((row) => (
                <tr key={row.band}>
                  <Td>{row.band}</Td>
                  <TdNumeric>{row.count}</TdNumeric>
                  <TdNumeric>{row.count ? pct(row.mean) : '—'}</TdNumeric>
                  <TdNumeric>{row.count ? whole.format(row.win_rate) : '—'}</TdNumeric>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <section>
        <h2 className="mb-1 font-serif text-lg text-pretty">どの門で落ちたか</h2>
        <p className="mb-3 text-sm text-muted">
          落とした件のリターンも並べます。落として正解だったかが分かります。
        </p>
        <div className="overflow-x-auto">
          <table className="w-full min-w-[30rem] text-sm">
            <thead>
              <tr>
                <Th>門</Th>
                <ThNumeric>落とした件数</ThNumeric>
                <ThNumeric>落とした件の平均リターン</ThNumeric>
              </tr>
            </thead>
            <tbody>
              {Object.entries(data.blocked).map(([key, row]) => (
                <tr key={key}>
                  <Td>{GATE_LABELS[key] ?? key}</Td>
                  <TdNumeric>{row.count}</TdNumeric>
                  <TdNumeric>{row.count ? pct(row.mean) : '—'}</TdNumeric>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </>
  )
}

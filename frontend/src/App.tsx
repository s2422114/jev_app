import { useEffect, useState } from 'react'
import { fetchJudgement, fetchMaterials, fetchSettings } from './api'
import { GatePass, GateStop } from './components/GateRow'
import { Stage, StageNotEvaluated } from './components/Stage'
import { Td, TdNumeric, Th, ThNumeric } from './components/table'
import { Verdict } from './components/Verdict'
import type { DemoJudgement, MaterialState, MaterialSummary, Settings } from './types'

const GATE_KEYS = ['new_info', 'market_moving', 'official_announcement', 'direction']
const SUM_KEYS = ['above_expectation', 'magnitude', 'continuing']

// 画面には、システムの言い方ではなく読む人の言葉を出す。
const LABELS: Record<string, string> = {
  new_info: '新しい情報か',
  market_moving: '業績に直結するか',
  official_announcement: '企業の公式発表か',
  direction: '良い材料か',
  above_expectation: '予想に対して上振れか',
  magnitude: '影響の大きさ',
  continuing: '影響は続くか',
}
const SHORT: Record<string, string> = {
  new_info: '新情報',
  market_moving: '直結',
  official_announcement: '公式',
  direction: '方向',
  above_expectation: '上振れ',
  magnitude: '大きさ',
  continuing: '継続',
}

function App() {
  const [materials, setMaterials] = useState<MaterialSummary[] | null>(null)
  const [settings, setSettings] = useState<Settings | null>(null)
  const [selected, setSelected] = useState<number | null>(null)
  const [judgement, setJudgement] = useState<DemoJudgement | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const controller = new AbortController()
    Promise.all([fetchMaterials(controller.signal), fetchSettings(controller.signal)])
      .then(([list, config]) => {
        setMaterials(list)
        setSettings(config)
        setSelected(list[0]?.no ?? null)
      })
      .catch((e) => {
        if (e instanceof DOMException && e.name === 'AbortError') return
        setError(e instanceof Error ? e.message : String(e))
      })
    return () => controller.abort()
  }, [])

  useEffect(() => {
    if (selected === null) return
    const controller = new AbortController()
    setJudgement(null)
    fetchJudgement(selected, controller.signal)
      .then(setJudgement)
      .catch((e) => {
        if (e instanceof DOMException && e.name === 'AbortError') return
        setError(e instanceof Error ? e.message : String(e))
      })
    return () => controller.abort()
  }, [selected])

  if (error)
    return (
      <main className="mx-auto max-w-3xl px-4 py-10">
        <h1 className="mb-2 font-serif text-2xl text-pretty">読み込めませんでした</h1>
        <p>{error}</p>
        <p className="mt-2 text-muted">backend が起動しているか確認してください。</p>
      </main>
    )
  if (!materials || !settings)
    return (
      <main className="mx-auto max-w-3xl px-4 py-10 text-muted" aria-live="polite">
        読み込み中…
      </main>
    )
  if (!materials.length)
    return (
      <main className="mx-auto max-w-3xl px-4 py-10">
        <h1 className="mb-2 font-serif text-2xl text-pretty">材料がありません</h1>
        <p className="text-muted">
          backend の data/demo.json が空です。evaluation/build_demo_data.py を実行してください。
        </p>
      </main>
    )

  const state = judgement?.result.material as MaterialState | undefined
  const stopped = judgement
    ? judgement.result.blocked_by.length > 0
    : false
  const lowConf = judgement ? judgement.result.low_confidence.length > 0 : false

  return (
    <div className="mx-auto max-w-5xl px-4 py-10">
      <header className="mb-8">
        <h1 className="font-serif text-2xl text-pretty">開示から翌日の売買リストを作る</h1>
        <p className="mt-2 max-w-2xl text-sm leading-relaxed">
          適時開示の文章を Jev（TypeSafe の System One モデル）に7問投げ、
          門を4つ通し、confidence で絞り、重みを付けて合成します。判断はモデル、
          流れと閾値はコードが持ちます。
        </p>
        <p className="mt-2 text-sm text-muted">
          材料は架空の企業・架空の開示16件です。確率は実測（モデル {settings.model}、
          {settings.measured_at} 実行）。この画面から Jev は呼び出していません。
        </p>
      </header>

      <section className="mb-10">
        <h2 className="mb-3 font-serif text-lg text-pretty">16件の判定</h2>
        <div className="overflow-x-auto">
          <table className="w-full min-w-[46rem] text-sm">
            <thead>
              <tr>
                <ThNumeric>#</ThNumeric>
                <Th>材料</Th>
                {[...GATE_KEYS, ...SUM_KEYS].map((key) => (
                  <ThNumeric key={key}>{SHORT[key]}</ThNumeric>
                ))}
                <ThNumeric>スコア</ThNumeric>
                <Th>判定</Th>
              </tr>
            </thead>
            <tbody>
              {materials.map((m) => (
                <tr
                  key={m.no}
                  className={m.no === selected ? 'bg-rule/40' : 'hover:bg-rule/20'}
                >
                  <TdNumeric>{m.no}</TdNumeric>
                  <Td>
                    <button
                      type="button"
                      onClick={() => setSelected(m.no)}
                      className="break-words text-left underline decoration-rule underline-offset-4 hover:decoration-ink focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ink"
                      aria-current={m.no === selected}
                    >
                      {m.title}
                    </button>
                  </Td>
                  {[...GATE_KEYS, ...SUM_KEYS].map((key) => (
                    <TdNumeric key={key}>{m.values[key].toFixed(2)}</TdNumeric>
                  ))}
                  <TdNumeric>{m.score === null ? '—' : m.score.toFixed(3)}</TdNumeric>
                  <Td>
                    <Verdict listed={m.listed} />
                  </Td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <p className="mt-2 text-xs text-muted">
          値は 0〜1 に揃えた後のものです（Score は段階数で割っています）。
          スコアの「—」は、門か confidence で止まったため合成まで進まなかったことを表します。
          行を選ぶと、どこで止まったかを下に出します。
        </p>
      </section>

      {judgement && state && (
        <section aria-live="polite">
          <h2 className="mb-1 font-serif text-lg">
            {judgement.no}. {judgement.title}
          </h2>
          <p className="mb-4 text-sm text-muted">
            文体は{judgement.style}。{judgement.aim}ために作った材料です。
            {judgement.note && <span className="block mt-1">注意：{judgement.note}</span>}
          </p>

          <div className="mb-6 border border-rule bg-white p-4">
            <p className="mb-1 text-sm text-muted">
              {state.銘柄.名前}（{state.銘柄.コード}） {state.ニュース.日付}
            </p>
            <p className="text-sm leading-relaxed">{state.ニュース.本文}</p>
            <p className="mt-2 text-sm text-muted">
              事前の予想：{state.事前の予想.会社予想 || 'なし（この開示には予想がない）'}
            </p>
          </div>

          <div className="grid gap-6">
            <Stage title={`門：4問すべてが閾値 ${settings.gate_thresholds.new_info.toFixed(2)} 以上なら次へ`}>
              {GATE_KEYS.map((key) => {
                const value = judgement.result.answers[key].normalized
                const threshold = settings.gate_thresholds[key]
                const Row = judgement.result.blocked_by.includes(key) ? GateStop : GatePass
                return (
                  <Row key={key} label={LABELS[key]} value={value} threshold={threshold} />
                )
              })}
              {stopped && (
                <p className="mt-2 text-sm text-stop">
                  ここで止まりました（{judgement.result.blocked_by.map((k) => LABELS[k]).join('、')}）。
                </p>
              )}
            </Stage>

            {stopped ? (
              <StageNotEvaluated title={`confidence：Score 3問すべてが ${settings.min_confidence.toFixed(2)} 以上なら次へ`}>
                <ConfidenceRows judgement={judgement} min={settings.min_confidence} />
              </StageNotEvaluated>
            ) : (
              <Stage title={`confidence：Score 3問すべてが ${settings.min_confidence.toFixed(2)} 以上なら次へ`}>
                <ConfidenceRows judgement={judgement} min={settings.min_confidence} />
                {lowConf && (
                  <p className="mt-2 text-sm text-stop">
                    ここで止まりました（{judgement.result.low_confidence.map((k) => LABELS[k]).join('、')}）。
                  </p>
                )}
              </Stage>
            )}

            {stopped || lowConf ? (
              <StageNotEvaluated title="合成：重みを付けて足し、閾値と比べる">
                <WeightRows judgement={judgement} settings={settings} />
              </StageNotEvaluated>
            ) : (
              <Stage title="合成：重みを付けて足し、閾値と比べる">
                <WeightRows judgement={judgement} settings={settings} />
                <p className="mt-2 text-sm">
                  スコア <span className="tabular">{judgement.result.score?.toFixed(3)}</span>
                  {' ／ 閾値 '}
                  <span className="tabular">{settings.score_threshold.toFixed(2)}</span> なので{' '}
                  <Verdict listed={judgement.result.listed} />
                </p>
              </Stage>
            )}
          </div>

          {judgement.runs.length > 1 && (
            <section className="mt-8">
              <h3 className="mb-2 font-serif">同じ材料を{judgement.runs.length}回投げた結果</h3>
              <div className="overflow-x-auto">
                <table className="w-full min-w-[40rem] text-sm">
                  <thead>
                    <tr>
                      <ThNumeric>回</ThNumeric>
                      {[...GATE_KEYS, ...SUM_KEYS].map((key) => (
                        <ThNumeric key={key}>{SHORT[key]}</ThNumeric>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {judgement.runs.map((run) => (
                      <tr key={run.run}>
                        <TdNumeric>{run.run}</TdNumeric>
                        {[...GATE_KEYS, ...SUM_KEYS].map((key) => (
                          <TdNumeric key={key}>{run.answers[key]?.toFixed(2) ?? '—'}</TdNumeric>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              <p className="mt-2 text-xs text-muted">
                同じ入力でも 0.02〜0.05 ほど動きます。閾値はこの幅から離して置きます。
              </p>
            </section>
          )}
        </section>
      )}
    </div>
  )
}

function ConfidenceRows({ judgement, min }: { judgement: DemoJudgement; min: number }) {
  const keys = ['direction', 'above_expectation', 'magnitude']
  return (
    <>
      {keys.map((key) => {
        const confidence = judgement.result.answers[key].confidence
        if (confidence === null) return null
        const Row = judgement.result.low_confidence.includes(key) ? GateStop : GatePass
        return <Row key={key} label={LABELS[key]} value={confidence} threshold={min} />
      })}
      <p className="mt-1 text-xs text-muted">
        confidence が返るのは Score の3問だけです（Noul には返りません）。
      </p>
    </>
  )
}

function WeightRows({ judgement, settings }: { judgement: DemoJudgement; settings: Settings }) {
  return (
    <table className="text-sm">
      <tbody>
        {SUM_KEYS.map((key) => (
          <tr key={key}>
            <td className="py-1 pr-4">{LABELS[key]}</td>
            <td className="tabular py-1 pr-2 text-right">
              {judgement.result.answers[key].normalized.toFixed(2)}
            </td>
            <td className="tabular py-1 text-right text-muted">
              × {settings.weights[key].toFixed(2)}
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  )
}

export default App

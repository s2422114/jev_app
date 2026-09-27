// 詳細（案B）の1行。門を上から順に通していく様子を見せる。
// 閾値の位置に細い縦線を置き、値がそれをどれだけ超えた／下回ったかを見せる。
import type { ReactNode } from 'react'

type RowProps = {
  label: string
  value: number
  threshold: number
  status: ReactNode
  /** 通過なら緑、停止なら赤茶。バーと状態の文字に使う。 */
  tone: 'pass' | 'stop'
}

function Row({ label, value, threshold, status, tone }: RowProps) {
  const bar = tone === 'pass' ? 'bg-pass' : 'bg-stop'
  const text = tone === 'pass' ? 'text-pass' : 'text-stop'
  return (
    <div className="grid grid-cols-[10rem_1fr_3rem_3rem] items-center gap-3 py-1.5">
      <span className="text-sm">{label}</span>
      <span className="relative block h-2 bg-rule/60" aria-hidden="true">
        <span className={`absolute inset-y-0 left-0 ${bar}`} style={{ width: `${value * 100}%` }} />
        {/* 閾値の位置。ここが判定の分かれ目。 */}
        <span
          className="absolute inset-y-[-3px] w-px bg-ink"
          style={{ left: `${threshold * 100}%` }}
        />
      </span>
      <span className="tabular text-right text-sm">{value.toFixed(2)}</span>
      <span className={`text-right text-sm ${text}`}>{status}</span>
    </div>
  )
}

export function GatePass(props: Omit<RowProps, 'status' | 'tone'>) {
  return <Row {...props} status="通過" tone="pass" />
}

export function GateStop(props: Omit<RowProps, 'status' | 'tone'>) {
  return <Row {...props} status="停止" tone="stop" />
}

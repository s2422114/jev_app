// 横棒。0 を基準に左右へ伸びる（リターンは負にもなるため）。
// 図の種類ごとに別の部品にし、真偽値で見た目を切り替えない。

export type BarDatum = {
  label: string
  value: number
  /** その系列を強調するか。Jev だけ濃く、比較対象は無彩色にする。 */
  emphasis?: boolean
}

export function Bar({
  data,
  format,
  height = 28,
}: {
  data: BarDatum[]
  format: (value: number) => string
  height?: number
}) {
  const max = Math.max(...data.map((d) => Math.abs(d.value)), 0.0001)
  const width = 420
  const zero = width / 2

  return (
    <svg
      viewBox={`0 0 ${width} ${data.length * height + 16}`}
      className="w-full"
      role="img"
      aria-label={data.map((d) => `${d.label} ${format(d.value)}`).join('、')}
    >
      {/* 0 の位置 */}
      <line x1={zero} y1={0} x2={zero} y2={data.length * height} stroke="var(--color-rule)" />
      {data.map((d, i) => {
        const length = (Math.abs(d.value) / max) * (zero - 8)
        const y = i * height + 6
        return (
          <g key={d.label}>
            <rect
              x={d.value < 0 ? zero - length : zero}
              y={y}
              width={length}
              height={height - 14}
              fill={d.emphasis ? 'var(--color-pass)' : 'var(--color-rule)'}
            />
            <text x={0} y={y + height / 2 - 1} fontSize="11" fill="var(--color-ink)">
              {d.label}
            </text>
            <text
              x={width}
              y={y + height / 2 - 1}
              fontSize="11"
              textAnchor="end"
              fill="var(--color-ink)"
              style={{ fontVariantNumeric: 'tabular-nums' }}
            >
              {format(d.value)}
            </text>
          </g>
        )
      })}
    </svg>
  )
}

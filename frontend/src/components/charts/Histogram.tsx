// ヒストグラム。並べ替え検定の分布に、観測値の位置を縦線で重ねる。

export function Histogram({
  counts,
  low,
  width: binWidth,
  marker,
  format,
}: {
  counts: number[]
  low: number
  width: number
  /** 観測値。ここに縦線を引く。 */
  marker: number
  format: (value: number) => string
}) {
  const w = 520
  const h = 180
  const pad = { left: 12, right: 12, top: 12, bottom: 30 }
  const maxCount = Math.max(...counts, 1)
  const high = low + binWidth * counts.length
  const barWidth = (w - pad.left - pad.right) / counts.length
  const px = (value: number) =>
    pad.left + ((value - low) / (high - low || 1)) * (w - pad.left - pad.right)

  return (
    <svg
      viewBox={`0 0 ${w} ${h}`}
      className="w-full"
      role="img"
      aria-label={`ランダムに選んだ場合の平均リターンの分布。観測値は ${format(marker)}。`}
    >
      {counts.map((count, i) => {
        const barHeight = (count / maxCount) * (h - pad.top - pad.bottom)
        return (
          <rect
            key={i}
            x={pad.left + i * barWidth}
            y={h - pad.bottom - barHeight}
            width={Math.max(barWidth - 1, 1)}
            height={barHeight}
            fill="var(--color-rule)"
          />
        )
      })}

      <line
        x1={px(marker)}
        y1={pad.top - 6}
        x2={px(marker)}
        y2={h - pad.bottom}
        stroke="var(--color-pass)"
        strokeWidth="2"
      />
      <text
        x={px(marker)}
        y={pad.top - 10}
        fontSize="10"
        textAnchor="middle"
        fill="var(--color-pass)"
        style={{ fontVariantNumeric: 'tabular-nums' }}
      >
        Jev {format(marker)}
      </text>

      <text x={pad.left} y={h - 10} fontSize="10" fill="var(--color-muted)">
        {format(low)}
      </text>
      <text x={w - pad.right} y={h - 10} fontSize="10" textAnchor="end" fill="var(--color-muted)">
        {format(high)}
      </text>
    </svg>
  )
}

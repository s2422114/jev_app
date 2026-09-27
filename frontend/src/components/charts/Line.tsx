// 折れ線。横軸の点がそのまま目盛りになる（閾値 0.50〜0.90 の9点など）。

export type LinePoint = { x: number; y: number; note?: string }

export function Line({
  points,
  formatX,
  formatY,
}: {
  points: LinePoint[]
  formatX: (x: number) => string
  formatY: (y: number) => string
}) {
  const width = 520
  const height = 200
  const pad = { left: 52, right: 12, top: 12, bottom: 38 }
  const xs = points.map((p) => p.x)
  const ys = points.map((p) => p.y)
  const minX = Math.min(...xs)
  const maxX = Math.max(...xs)
  const minY = Math.min(...ys, 0)
  const maxY = Math.max(...ys, 0)
  const spanY = maxY - minY || 1

  const px = (x: number) =>
    pad.left + ((x - minX) / (maxX - minX || 1)) * (width - pad.left - pad.right)
  const py = (y: number) =>
    height - pad.bottom - ((y - minY) / spanY) * (height - pad.top - pad.bottom)

  return (
    <svg
      viewBox={`0 0 ${width} ${height}`}
      className="w-full"
      role="img"
      aria-label={points.map((p) => `${formatX(p.x)} は ${formatY(p.y)}`).join('、')}
    >
      {/* 0 の線。リターンが負になる領域を分かるようにする。 */}
      <line
        x1={pad.left}
        y1={py(0)}
        x2={width - pad.right}
        y2={py(0)}
        stroke="var(--color-rule)"
      />
      <text x={pad.left - 6} y={py(0) + 4} fontSize="10" textAnchor="end" fill="var(--color-muted)">
        {formatY(0)}
      </text>
      <text x={pad.left - 6} y={py(maxY) + 4} fontSize="10" textAnchor="end" fill="var(--color-muted)">
        {formatY(maxY)}
      </text>

      <polyline
        points={points.map((p) => `${px(p.x)},${py(p.y)}`).join(' ')}
        fill="none"
        stroke="var(--color-pass)"
        strokeWidth="2"
      />
      {points.map((p) => (
        <g key={p.x}>
          <circle cx={px(p.x)} cy={py(p.y)} r="3" fill="var(--color-pass)" />
          <text
            x={px(p.x)}
            y={height - pad.bottom + 14}
            fontSize="10"
            textAnchor="middle"
            fill="var(--color-muted)"
            style={{ fontVariantNumeric: 'tabular-nums' }}
          >
            {formatX(p.x)}
          </text>
          {p.note && (
            <text
              x={px(p.x)}
              y={height - pad.bottom + 28}
              fontSize="10"
              textAnchor="middle"
              fill="var(--color-muted)"
              style={{ fontVariantNumeric: 'tabular-nums' }}
            >
              {p.note}
            </text>
          )}
        </g>
      ))}
    </svg>
  )
}

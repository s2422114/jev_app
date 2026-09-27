// 表の部品。真偽値のプロパティで見た目を切り替えず、用途ごとに別の部品にする。
import type { ReactNode } from 'react'

export function Th({ children }: { children: ReactNode }) {
  return (
    <th scope="col" className="border-b border-rule px-2 py-2 text-left font-normal text-muted">
      {children}
    </th>
  )
}

/** 数値の列。右寄せで桁を揃える。 */
export function ThNumeric({ children }: { children: ReactNode }) {
  return (
    <th scope="col" className="border-b border-rule px-2 py-2 text-right font-normal text-muted">
      {children}
    </th>
  )
}

export function Td({ children }: { children: ReactNode }) {
  return <td className="border-b border-rule px-2 py-2">{children}</td>
}

/** 確率を縦に比べるので、数値は等幅の数字で右寄せにする。 */
export function TdNumeric({ children }: { children: ReactNode }) {
  return <td className="tabular border-b border-rule px-2 py-2 text-right">{children}</td>
}

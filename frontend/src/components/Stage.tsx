// 判定の段（門 → confidence → 合成）。
// 門で止まった場合、以降の段は消さずに薄く残す。判定が段階であることを伝えるため。
import type { ReactNode } from 'react'

export function Stage({ title, children }: { title: string; children: ReactNode }) {
  return (
    <section className="border-l-2 border-rule pl-4">
      <h3 className="mb-2 text-sm text-muted">{title}</h3>
      {children}
    </section>
  )
}

/** 前の段で止まったため評価されなかった段。 */
export function StageNotEvaluated({ title, children }: { title: string; children: ReactNode }) {
  return (
    <section className="border-l-2 border-dashed border-rule pl-4 opacity-45">
      <h3 className="mb-2 text-sm text-muted">
        {title}
        <span className="ml-2">— 前の段で止まったため評価しない</span>
      </h3>
      {children}
    </section>
  )
}

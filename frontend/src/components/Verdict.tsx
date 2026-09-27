// 判定の表示。通過と停止で別の部品にする（真偽値で切り替えない）。
// 色は「リストに入れるか」という情報を表すもので、装飾ではない。

export function VerdictListed() {
  return <span className="font-medium text-pass">入れる</span>
}

export function VerdictSkipped() {
  return <span className="text-stop">見送り</span>
}

export function Verdict({ listed }: { listed: boolean }) {
  return listed ? <VerdictListed /> : <VerdictSkipped />
}

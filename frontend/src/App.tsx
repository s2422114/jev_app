import { useEffect, useState } from 'react'
import { DemoPage } from './pages/DemoPage'
import { EvalPage } from './pages/EvalPage'

// 画面は2つだけなので、ハッシュで切り替える（ルーターは入れない）。
// #eval で評価結果に直接飛べる。静的サイトの書き換え設定にも手を入れずに済む。
type Route = 'demo' | 'eval'

const routeOf = (hash: string): Route => (hash === '#eval' ? 'eval' : 'demo')

function App() {
  const [route, setRoute] = useState<Route>(() => routeOf(window.location.hash))

  useEffect(() => {
    const onChange = () => setRoute(routeOf(window.location.hash))
    window.addEventListener('hashchange', onChange)
    return () => window.removeEventListener('hashchange', onChange)
  }, [])

  return (
    <div className="mx-auto max-w-5xl px-4 py-10">
      {/* 評価結果（#eval）は、本番データが入るまでナビに出さない。
          いまの数字は乱数で作った架空のリターンで、外から辿れる形にしない。
          画面と URL は残してあるので、#eval を直接開けば確認できる。 */}
      {route === 'eval' && (
        <nav className="mb-8 border-b border-rule pb-3 text-sm">
          <a
            href="#demo"
            className="text-muted underline decoration-rule underline-offset-8 hover:decoration-ink focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ink"
          >
            開示の判定にもどる
          </a>
        </nav>
      )}

      {route === 'demo' ? <DemoPage /> : <EvalPage />}
    </div>
  )
}

export default App

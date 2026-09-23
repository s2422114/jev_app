# 実行結果: b_text_and_context

- 実行日時: 20260922-234322
- モデル: jev-1.13.0
- 合計 usage: 入力 4170 / 出力 181 トークン

| id | ケース | 予想 | 答え | usage(in/out) |
|---|---|---|---|---|
| exp5_comment_only | 好決算のコメントだけを渡す（株価の情報なし） | 1.5。コメントは割と前向きだが通気据え置きが弱く捉えられる可能性はある | positivity: score=2.000 (conf=1.000) | 508/19 |
| exp5_with_uptrend | 同じコメント ＋ トレンド（上昇トレンド） | 1.5。コメントだけを参照してほしい。exp5_comment_onlyと同じ。 | positivity: score=2.000 (conf=1.000) | 532/19 |
| exp5_with_downtrend | 同じコメント ＋ トレンド（下降トレンド） | 1.5。コメントだけを参照してほしい。exp5_comment_onlyと同じ。 | positivity: score=2.000 (conf=0.990) | 529/19 |
| exp6_aoi_consistent | 蒼井フーズ：好決算のコメント ＋ 上昇トレンド | 0.97。やはり通気据え置きに引っ張られそう。 | consistent: noul=0.890 | 448/20 |
| exp6_beniya_conflict | 紅屋電機：好決算のコメント ＋ 下降トレンド | 0.03。今までの実験から言うと0に近くなると思う。 | consistent: noul=0.200 | 445/20 |
| exp7_daiko_surged | 大湖精機：好決算のコメント ＋ 発表前に急上昇していた | 0.1。織り込まれていないから決算内容がバレて上がったと考えるのが普通。 | priced_in: noul=0.460 | 446/22 |
| exp7_chidori_flat | 千鳥化学：好決算のコメント ＋ 発表前はほぼ横ばいだった | 0.9。織り込まれていると考えるのが普通だから。 | priced_in: noul=0.190 | 446/22 |
| exp8_extraordinary | 白馬製薬：特別利益による増益 | 0.9。普通に考えると二度同じことが起こる保証はないので一時的。 | temporary: noul=0.950 | 410/20 |
| exp8_core_business | 白馬製薬：本業の伸びによる増益 | 0.6。恒久的かと思えるが、一時的かもしれない含みも残すので真ん中近く。 | temporary: noul=0.230 | 406/20 |

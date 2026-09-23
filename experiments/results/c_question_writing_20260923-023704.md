# 実行結果: c_question_writing

- 実行日時: 20260923-023704
- モデル: jev-1.13.0
- 合計 usage: 入力 6309 / 出力 551 トークン

| id | ケース | 予想 | 答え | usage(in/out) |
|---|---|---|---|---|
| exp9_broad | 広い問いを1つだけ投げる | 1.0。下がる要素がないから | broad: noul=0.580 | 441/21 |
| exp9_decomposed | 分解した3問を1リクエストで投げる | 0.9,0.3,0.8。bの実験とそれぞれは同じのため。 | positive: noul=0.980 / temporary: noul=0.280 / priced_in: noul=0.390 | 515/54 |
| exp10_without_criteria | criteria なしで聞く | 0.5。どちらを重視するのかわからないので真ん中 | judgement: noul=0.190 | 392/22 |
| exp10_with_criteria | 同じ質問に criteria を付けて聞く | 0.1。criteriaでfalseになるようになってるから | judgement: noul=0.060 | 457/22 |
| exp11_vague | 曖昧な語で聞く | 0.4。営業利益を重視しそうだから | judgement: noul=0.350 | 419/22 |
| exp11_specific | 具体的な語で聞く | 1.0。stateに書いてあるから | judgement: noul=0.980 | 414/22 |
| exp12_negation | 肯定形と否定形を同時に聞く | 0.7。割と前向きなニュースだから | positive: noul=0.950 / negative: noul=0.030 | 421/36 |
| exp13_noul | Noul で聞く | 0.9。前向き以外読み取れないので | judgement: noul=0.940 | 397/22 |
| exp13_choice | 同じことを Choice で聞く | 0.9。choiceにしたところで変わらない気がする | judgement: choice=はい (conf=1.000) | 415/35 |
| exp14_choice | 3段階を Choice で聞く | 0.5。ほとんど悲観的だが具体的な対策を言わない点で少し楽観も入ってると思う | judgement: choice=悲観的 (conf=0.960) | 422/47 |
| exp14_score | 同じ3段階を Score で聞く | 0。楽観要素はあるが一般的には悲観 | judgement: score=0.080 (conf=0.880) | 424/19 |
| exp15_ma_without_none | M&A のニュース：該当なしを入れない | 1。これは明白 | category: choice=M&A (conf=1.000) | 389/51 |
| exp15_ma_with_none | M&A のニュース：該当なしを入れる | 1。流石に変わらない | category: choice=M&A (conf=1.000) | 399/62 |
| exp15_office_without_none | どの分類にも当てはまらないニュース：該当なしを入れない | 0。業績とは関係ないが結びつけてくるかもしれない | category: choice=人事 (conf=0.630) | 397/51 |
| exp15_office_with_none | どの分類にも当てはまらないニュース：該当なしを入れる | 4。選択肢にないので該当なし | category: choice=該当なし (conf=1.000) | 407/65 |

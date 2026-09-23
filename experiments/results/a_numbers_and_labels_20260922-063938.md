# 実行結果: a_numbers_and_labels

- 実行日時: 20260922-063938
- モデル: jev-1.13.0
- 合計 usage: 入力 5955 / 出力 392 トークン

| id | ケース | 予想 | 答え | usage(in/out) |
|---|---|---|---|---|
| exp1_aoi_raw | 蒼井フーズ：25日線と75日線を生の数値で渡す | 0.97。結果は明白だから割と簡単に判断できると思う。 | trend_compare: noul=0.980 | 368/21 |
| exp1_aoi_label | 蒼井フーズ：トレンドのラベルだけを渡す（上昇トレンド） | 0.8。上昇トレンドの時、25日線は75日線を上回るがそうでない時も考慮されるためrawよりは下がると思う。 | trend_compare: noul=0.680 | 349/21 |
| exp1_beniya_raw | 紅屋電機：25日線と75日線を生の数値で渡す | 0.1。先ほどよりも差が大きく判定は簡単になるため値は0に限りなく近いはず | trend_compare: noul=0.020 | 366/21 |
| exp1_beniya_label | 紅屋電機：トレンドのラベルだけを渡す（下降トレンド） | 0.2。exp1_aoi_labelと同じでrawよりは高くなりそう | trend_compare: noul=0.240 | 346/21 |
| exp1_chidori_raw | 千鳥化学：25日線と75日線を生の数値で渡す | 0.97。ただの数値の計算なのでexp1_aoi_rawと変わらなそう。 | trend_compare: noul=0.970 | 364/21 |
| exp1_chidori_label | 千鳥化学：トレンドのラベルだけを渡す（横ばい） | 0.5。これは真ん中であってほしい。もしかしたらネットの横ばいという情報が偏りがあって少しズレるかもしれないが大きなずれはないはず。 | trend_compare: noul=0.410 | 343/21 |
| exp2_enoki_raw | 榎木商事：前日比 -2.9% を生の数値で渡す | big_drop=0.3。大幅ではないのではないが下落ではあるので。move_size=1.2。下落ではあるが大幅ではないので。 | big_drop: noul=0.480 / move_size: score=1.130 (conf=0.800) | 448/35 |
| exp2_enoki_label | 榎木商事：値動きのラベルだけを渡す（下落） | big_drop=0.5。下落だが大幅ではない、だが下落の中にも大幅な下落が含まれるため二択になるはず。move_size=1.5。big_dropと同じ理由。 | big_drop: noul=0.430 / move_size: score=0.890 (conf=0.750) | 417/35 |
| exp2_fujimi_raw | 富士見運輸：前日比 -3.1% を生の数値で渡す | big_drop=0.2。コードでは大幅下落になっているが一般的にはただの下落なため。move_size=1.5。exp2_enoki_rawと同じ理由だが、下落幅が大きくなった分少しだけ増えそう。 | big_drop: noul=0.470 / move_size: score=1.080 (conf=0.870) | 446/35 |
| exp2_fujimi_label | 富士見運輸：値動きのラベルだけを渡す（大幅下落） | big_drop=0.9。stateを文字通り受け取ると高くなる気がする。move_size=1.9。big_dropと同じ理由。exp2_enoki_labelと違い小幅の下落の可能性が消えたため2.0に近くなるとおもう。 | big_drop: noul=0.940 / move_size: score=2.000 (conf=1.000) | 419/35 |
| exp3_gyoda_shares | 行田システム：出来高を株数で渡す | 0.5。基準がわからない上に実在しない企業なので比べ用がないため真ん中。confidenceは限りなく低いはず | volume_high: noul=0.440 | 351/21 |
| exp3_gyoda_ratio | 行田システム：出来高を平均との比で渡す | 0.9。基準がある分高くなるはず。confidenceも高くなる（0.8あたり） | volume_high: noul=0.960 | 353/21 |
| exp3_gyoda_label | 行田システム：出来高をラベルで渡す（急増） | 0.9。exp3_gyoda_ratioとそんなに変わらない。ただ文字のため少し低くなるかも。 | volume_high: noul=0.930 | 343/21 |
| exp3_hakuba_shares | 白馬製薬：出来高を株数で渡す | 0.5。exp3_gyoda_sharesと同じ。 | volume_high: noul=0.400 | 347/21 |
| exp3_hakuba_ratio | 白馬製薬：出来高を平均との比で渡す | 0.5。多くもないし少なくもないので。confidenceは高そう。 | volume_high: noul=0.120 | 352/21 |
| exp3_hakuba_label | 白馬製薬：出来高をラベルで渡す（平均並み） | 0.5。これもexp3_hakuba_ratioとそんなに変わらないか少し小さい。理由はexp3_gyoda_labelと同じ。 | volume_high: noul=0.070 | 343/21 |

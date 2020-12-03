# cheese
An object detection camera device M5StickV software for LEGO Mindstroms 51515 Robot Inventor and LEGO Spike Prime 45678

[M5tickV](https://docs.m5stack.com/#/en/core/m5stickv)を[LEGO Mindstroms 51515 Robot Inventor](https://www.lego.com/ja-jp/product/robot-inventor-51515)と[LEGO Spike Prime 45678](https://www.lego.com/ja-jp/product/lego-education-spike-prime-set-45678)の物体認識センサーとして利用できるようにするソフトウェアです。

このソフトウェアを利用することで、以下のムービーのような賢い眼をもったロボットを簡単に作ることができるようになります。  

- [顔を認識すると笑顔を返すロボット](https://www.youtube.com/watch?v=qp2Q1Rkzbyo)
- [BB-8の姿を認識すると一回転するロボット](https://www.youtube.com/watch?v=Yie-T35wHJU)
- [サンダーバードの姿を認識すると羽ばたくロボット](https://www.youtube.com/watch?v=v0COY-wwlcA)

裏側では深層学習が利用されていますが、深層学習の知識がなくても大丈夫です。  
例えば、先ほどのムービーの3つの機能を持ったロボットは以下のScratchプログラムで作れてしまいます。とても簡単ですね。

![プログラム例](https://camo.qiitausercontent.com/9cf792a1e62355021af61518d3ff6703c599c0d6/68747470733a2f2f71696974612d696d6167652d73746f72652e73332e61702d6e6f727468656173742d312e616d617a6f6e6177732e636f6d2f302f32363036322f35306531306237642d383066352d386338372d306162352d3831613162346338383037322e706e67)

# 機能

1. 認識したい物体の見本写真を撮影するカメラ機能（デフォルトでは10種類、最大200種類）
2. カメラで物体を認識したら、それをLEGO Mindstorms等のハブに伝える機能（あたかも超音波センサーのように動作します）

# 使い方

[Qiitaの記事を参照](https://qiita.com/sonoisa/items/1ddde98611ceb772b090)

# 謝辞

- 物体認識アルゴリズムは[Brownie](https://github.com/ksasao/brownie)を参考にしています。
- 写真撮影のプログラムは https://docs.m5stack.com/#/en/related_documents/v-training を参考にしています。
- LEGO Mindstorms等とセンサーの通信プロトコルは https://github.com/GianCann/technical-info/blob/master/uart-protocol.md と https://github.com/ceeoinnovations/SPIKEPrimeBackpacks で学習しました。

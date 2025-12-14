# Jubeat Memo to StepMania Converter

jubeat の創作譜面データ（テキスト形式／jubeatmemo）を、StepMania（DDR形式）の **.sm ファイル**に変換する **GUI ツール**です。

jubeat の **縦4列**を、StepMania の **4レーン Left/Down/Up/Right**にマッピングして出力します。

<img width="2112" height="2016" alt="Image" src="https://github.com/user-attachments/assets/db0e7b25-45a3-44ab-a584-c8952294808e" />

## 特徴

* **GUI 操作**
  直感的な画面操作でファイル選択・設定が可能。

* **ドラッグ＆ドロップ対応**
  テキストファイルをウィンドウに投げるだけで読み込み可能。

* **フォーマット自動判別**

  * 通常の *jubeatmemo* 形式
  * **#memo2 形式**（パイプ `|` 内の文字数による可変リズム、24 分音符や変則リズム対応）

* **ヘッダー編集対応**
  StepMania の `.sm` ファイルに必要な情報を GUI 上で編集可能。


## 必要要件

* Python 3.x
* tkinterdnd2（ドラッグ＆ドロップ対応用）

必要に応じてインストールを行ってください。

## インストール

Python がインストールされていることを確認してください。  
必要なライブラリをインストールします。  
コマンドプロンプトで次のコマンドを実行してください。  

```bash
pip install tkinterdnd2
```

## 使い方

1. `jubeat2sm_gui.py` を実行します。

<img width="702" height="782" alt="Image" src="https://github.com/user-attachments/assets/603c9595-1aad-49ae-8007-92e9d78ebd55" />

2. jubeat 譜面のテキストファイル（`.txt`）を

   * ウィンドウにドラッグ＆ドロップする
   * または「ファイルを選択」ボタンから開く

3. 画面上の各項目を設定します。
<img width="702" height="782" alt="Image" src="https://github.com/user-attachments/assets/aaeb95c6-68c8-4c41-8c4d-f62dee4072cc" />

   * **TITLE / MUSIC** : ファイル名から自動入力されます。
   * **BPM** : 曲のテンポ（デフォルト: 100）
   * **Diff / Level** : 難易度名とレベル数値（デフォルト: Hard/1）

4. 「結果を保存」ボタンを押して `.sm` ファイルを書き出します。

# 仕様
## 入力ファイル形式

### 基本形式

4 行 1 セットでグリッドを表し、右側の `|` 内でタイミングを指定します。

```text
□⑤①⑦ |①－②－|  <-- ①(0拍), ②(2拍)
①□□⑥ |③－④－|
②⑦⑦⑤ |⑤－⑥－|
□③④□ |－－⑦－|
```

### #memo2 形式（可変リズム）

右側の `| |` 内の **文字数によってリズムを自動判定**します。

```text
|①②③④| (4文字) = 16分音符
|①－②－③－| (6文字) = 24分音符 (6連符)
|①②③| (3文字) = 12分音符 (3連符)
```

※ 全角数字（１, ２, ３...）は **リズム計算には使用**されますが、**ノーツとしては出力されません**（ホールド終点無視仕様）。

## 出力仕様

* 変換ロジック

jubeat の 4×4 パネルを **縦方向にスライス**して StepMania にマッピングします。

```
列1:  1   5   9  13  → Left
列2:  2   6  10  14  → Down
列3:  3   7  11  15  → Up
列4:  4   8  12  16  → Right
```

* **レーン配置**  
  jubeat の左から順に、StepMania の以下レーンへ対応します。  

```
  | jubeat 列 | StepMania レーン |
  | -------- | ------------- |
  | 列 1      | Left          |
  | 列 2      | Down          |
  | 列 3      | Up            |
  | 列 4      | Right         |

```

* **ホールド非対応**  
  ホールド記号（全角数字など）が含まれていても、**始点のみを通常ノーツ（Tap: `1`）として出力**します。  

* **0 小節目の追加**  
  先頭に必ず **空の小節 measure 0**を挿入します。  

* **同一列の同時押し**  
  同一列に複数のノーツがある場合（例：パネル 1 と 5 の同時押し）は、StepMania では配置できないため **1 つのノーツとして処理**されます。  

# 使用例
[https://github.com/YOPPYY/my-jubeat-charts/blob/main/README.md]

## License

MIT License

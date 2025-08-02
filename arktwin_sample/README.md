# ArkTwin サンプル: 車両・歩行者シミュレーション

このサンプルは、ArkTwinを使用して複数のシミュレーター間で位置情報を共有するデモンストレーションです。車両シミュレーターと歩行者シミュレーターが独立したプロセスとして動作し、ArkTwin経由でリアルタイムに他のエージェントの位置情報を取得できます。

## 概要

- **車両シミュレーター**: 3台の車両が道路上を直線移動
- **歩行者シミュレーター**: 4人の歩行者が歩道上をランダムに移動
- **ArkTwin Center**: メッセージブローカーとして動作
- **ArkTwin Edge**: 各シミュレーター用のサイドカーとして動作

## アーキテクチャ

```
ArkTwin Center (Port 2236)
├── ArkTwin Edge (Vehicle) (Port 2237) ← 車両シミュレーター
└── ArkTwin Edge (Pedestrian) (Port 2238) ← 歩行者シミュレーター
```

## 前提条件

### 必要なソフトウェア

1. **Java Development Kit 21 LTS** (推奨: [Eclipse Temurin](https://adoptium.net/temurin/releases/?variant=openjdk21&jvmVariant=hotspot))
2. **sbt** ([インストールガイド](https://www.scala-sbt.org/download))
3. **Python 3.7+** 
4. **pip** (Python package manager)

### ArkTwinのビルド

```bash
# ArkTwinプロジェクトのルートディレクトリで実行
cd ../arktwin/arktwin
sbt center/assembly edge/assembly
```

## セットアップ

### 1. Python依存関係のインストール

```bash
cd arktwin_sample
pip install -r requirements.txt
```

## 実行方法

### 自動実行スクリプト使用（推奨）

**Windows:**
```cmd
cd arktwin_sample
run_sample.bat
```

**Linux/macOS:**
```bash
cd arktwin_sample
chmod +x run_sample.sh
./run_sample.sh
```

### 手動実行

それぞれ別のターミナルで以下のコマンドを順番に実行：

#### 1. ArkTwin Center起動
```bash
cd arktwin_sample
java -Dconfig.file=center.conf -XX:+UseZGC -XX:+ZGenerational -jar ../arktwin/arktwin/center/target/scala-3.7.1/arktwin-center.jar
```

#### 2. ArkTwin Edge (車両用)起動
```bash
cd arktwin_sample
java -Dconfig.file=edge-vehicle.conf -XX:+UseZGC -XX:+ZGenerational -jar ../arktwin/arktwin/edge/target/scala-3.7.1/arktwin-edge.jar
```

#### 3. ArkTwin Edge (歩行者用)起動
```bash
cd arktwin_sample
java -Dconfig.file=edge-pedestrian.conf -XX:+UseZGC -XX:+ZGenerational -jar ../arktwin/arktwin/edge/target/scala-3.7.1/arktwin-edge.jar
```

#### 4. 車両シミュレーター起動
```bash
cd arktwin_sample
python vehicle_simulator.py
```

#### 5. 歩行者シミュレーター起動
```bash
cd arktwin_sample  
python pedestrian_simulator.py
```

## 動作確認

### コンソール出力

各シミュレーターのコンソールで以下のような出力が表示されます：

**車両シミュレーター:**
```
=== 車両シミュレーター (時刻: 10.0s) ===
vehicle-001: 位置(25.0, 0.0) 速度:10.0m/s
vehicle-002: 位置(5.0, 0.0) 速度:12.0m/s  
vehicle-003: 位置(-15.0, 0.0) 速度:8.0m/s
[車両] 検出した歩行者: 4人
```

**歩行者シミュレーター:**
```
=== 歩行者シミュレーター (時刻: 10.0s) ===
pedestrian-001: 位置(15.2, 7.8) 速度:1.5m/s 目標:(20.0, 10.0)
pedestrian-002: 位置(2.1, -2.3) 速度:1.2m/s 目標:(5.0, 15.0)
[歩行者] 検出した車両: 3台
```

### Web UI

ブラウザで以下のURLにアクセスして、API ドキュメントと可視化ツールを確認できます：

- **車両用 API ドキュメント**: http://127.0.0.1:2237/docs/
- **歩行者用 API ドキュメント**: http://127.0.0.1:2238/docs/
- **車両用 ビューワー**: http://127.0.0.1:2237/viewer/
- **歩行者用 ビューワー**: http://127.0.0.1:2238/viewer/

### ヘルスチェック

各コンポーネントが正常に動作しているか確認：

```bash
# ArkTwin Center
curl http://127.0.0.1:2236/health

# ArkTwin Edge (車両)
curl http://127.0.0.1:2237/health

# ArkTwin Edge (歩行者)  
curl http://127.0.0.1:2238/health
```

## シミュレーションの詳細

### 車両シミュレーター

- **車両数**: 3台 (vehicle-001, vehicle-002, vehicle-003)
- **動作**: X軸方向の直線移動、端で折り返し
- **速度**: 8-12 m/s
- **検出範囲**: 200m以内の他のエージェント

### 歩行者シミュレーター

- **歩行者数**: 4人 (pedestrian-001 ～ 004)
- **動作**: ランダムな目標地点への移動
- **速度**: 1.0-2.5 m/s（ランダム変動あり）
- **検出範囲**: 100m以内の他のエージェント

### 座標系

- **X軸**: 東方向 (East)
- **Y軸**: 北方向 (North)  
- **Z軸**: 上方向 (Up)
- **単位**: メートル
- **回転**: オイラー角（度）、XYZ順、外部回転

## 設定ファイル

- `center.conf`: ArkTwin Center設定
- `edge-vehicle.conf`: 車両シミュレーター用Edge設定
- `edge-pedestrian.conf`: 歩行者シミュレーター用Edge設定

## トラブルシューティング

### よくある問題

#### 1. JARファイルが見つからない

```
Error: arktwin-center.jar が見つかりません
```

**解決方法**: ArkTwinをビルドしてください
```bash
cd ../arktwin/arktwin
sbt center/assembly edge/assembly
```

#### 2. ポートが使用中

```
Bind failed on 127.0.0.1 with port 2236-2236
```

**解決方法**: 該当ポートを使用しているプロセスを停止するか、設定ファイルでポート番号を変更

#### 3. ArkTwin Edge接続エラー

```
ArkTwin Edge接続エラー: Connection refused
```

**解決方法**: ArkTwin Centerが先に起動していることを確認

#### 4. Python依存関係エラー

```
ModuleNotFoundError: No module named 'requests'
```

**解決方法**: 
```bash
pip install -r requirements.txt
```

### ログの確認

各コンポーネントのログを確認して問題を特定：

- ArkTwin CenterとEdgeはコンソールにログ出力
- シミュレーターは1秒毎に状態を表示

## カスタマイズ

### 新しいシミュレーターの追加

1. 新しいPythonスクリプトを作成
2. 対応するEdge設定ファイルを作成
3. ポート番号を変更
4. エージェントIDプレフィックスを変更

### シミュレーションパラメータの調整

- 車両・歩行者の数: シミュレーターコード内の`_initialize_*`メソッド
- 移動速度: `Vehicle`/`Pedestrian`クラスのspeedパラメータ  
- 検出範囲: 設定ファイルの`culling.maxDistance`

## ファイル一覧

```
arktwin_sample/
├── README.md                   # このファイル
├── requirements.txt            # Python依存関係
├── vehicle_simulator.py        # 車両シミュレーター
├── pedestrian_simulator.py     # 歩行者シミュレーター
├── center.conf                 # Center設定
├── edge-vehicle.conf           # 車両用Edge設定
├── edge-pedestrian.conf        # 歩行者用Edge設定
├── run_sample.bat              # Windows実行スクリプト
└── run_sample.sh               # Linux/macOS実行スクリプト
```

## 参考資料

- [ArkTwin公式README](../arktwin/README.md)
- [REST API仕様](https://arktwin.github.io/arktwin/swagger-ui/)
- [ArkTwin GitHub](https://github.com/arktwin/arktwin)
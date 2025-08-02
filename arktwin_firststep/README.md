このサンプルは ArkTwinCenter と ArkTwinEdge を使った位置共有をするシミュレーターのサンプルです。

ArkTwinCenter と ArkTwinEdge２つを起動し、各ArkTwinEdgeにagentを登録、位置情報の更新、検索をします。

# 前提
以下のArkTwinモジュールを用意してください。ビルドはgithubの手順を参照してください。
https://github.com/arktwin/arktwin
バージョンは0.6を使用しています。

- arktwin-center.jar 81MB
- arktwin-edge.jar 89MB

※以下githubより

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

# ArkTwin Center, Edge (Vehicle), Edge (Pedestrian) の起動
 - ArkTwin Center: http://127.0.0.1:2236
 - Vehicle Edge: http://127.0.0.1:2237
 - Pedestrian Edge: http://127.0.0.1:2238

java -Dconfig.file=center.conf -XX:+UseZGC -XX:+ZGenerational -jar arktwin-center.jar
java -Dconfig.file=edge-vehicle.conf -XX:+UseZGC -XX:+ZGenerational -jar arktwin-edge.jar
java -Dconfig.file=edge-pedestrian.conf -XX:+UseZGC -XX:+ZGenerational -jar arktwin-edge.jar

# ArkTwin Agent  - curl Commands
以下はcurl を使ったサンプルです。コマンドプロンプトにコピー&ペーストして実行してください

## ヘルスチェック (各サービスが起動しているか確認)
### ArkTwin Center ヘルスチェック
curl -X GET "http://127.0.0.1:2236/health"
### Vehicle Edge ヘルスチェック  
curl -X GET "http://127.0.0.1:2237/health"
### Pedestrian Edge ヘルスチェック
curl -X GET "http://127.0.0.1:2238/health"

## エージェント登録
curl -X POST "http://127.0.0.1:2237/api/edge/agents"  -H "Content-Type: application/json" --data @vehicle_agents.json
### 車両エージェント登録
curl -X POST "http://127.0.0.1:2237/api/edge/agents"  -H "Content-Type: application/json" --data @vehicle_agents.json
### 歩行者両エージェント登録
curl -X POST "http://127.0.0.1:2238/api/edge/agents"  -H "Content-Type: application/json" --data @pedestrian_agents.json

## エージェント位置情報更新
 注意: agentId は登録時のレスポンスで返された実際のIDに置き換えてください
 
### 車両の位置更新例 (agentIdを実際のIDに置き換えてください)
curl -X PUT "http://127.0.0.1:2237/api/edge/agents" -H "Content-Type: application/json"  --data @vehicle_position_update.json

### 歩行者の位置更新例 (agentIdを実際のIDに置き換えてください)
curl -X PUT "http://127.0.0.1:2238/api/edge/agents" -H "Content-Type: application/json"  --data @pedestrian_position_update.json

## 近隣エージェント検索
 注意: 同じEdgeを使って登録したエージェントの位置情報はとれない。
### 車両のEdgeから近隣エージェントを検索
 歩行者の位置情報が取れる
curl -X POST "http://127.0.0.1:2237/api/edge/neighbors/_query" -H "Content-Type: application/json" --data @vehicle_neighbor_query.json


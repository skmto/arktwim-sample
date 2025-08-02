このサンプルは ArkTwinCenter と ArkTwinEdge を使った位置共有をするシミュレーターのサンプルです。

まだ正確に ArkTwinCenter と  ArkTwinEdge の使い方が分かっていません。

ArkTwinCenter と ArkTwinEdge が接続していて、ArkTwinEdgeにagentを登録する処理を curl を使ってサンプルを作ると以下となる。

# ArkTwin Center, Edge (Vehicle), Edge (Pedestrian) が起動
 - ArkTwin Center: http://127.0.0.1:2236
 - Vehicle Edge: http://127.0.0.1:2237
 - Pedestrian Edge: http://127.0.0.1:2238

java -Dconfig.file=center.conf -XX:+UseZGC -XX:+ZGenerational -jar arktwin-center.jar
java -Dconfig.file=edge-vehicle.conf -XX:+UseZGC -XX:+ZGenerational -jar arktwin-edge.jar
java -Dconfig.file=edge-pedestrian.conf -XX:+UseZGC -XX:+ZGenerational -jar arktwin-edge.jar

# ArkTwin Agent  - curl Commands
コマンドプロンプトにコピー&ペーストして実行してください

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


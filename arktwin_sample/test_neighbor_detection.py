#!/usr/bin/env python3
"""
近隣検出テストスクリプト

正しいエージェントIDを使用して近隣検出機能をテストする。
車両と歩行者のエージェント登録から位置更新、近隣情報取得までの一連の流れを検証する。
"""

import requests
import json
import math
import time

def test_neighbor_detection():
    """完全な近隣検出フローのテスト
    
    以下のステップで近隣検出機能をテストする：
    1. 車両と歩行者のエージェント登録
    2. 各エージェントの位置情報送信
    3. 近隣情報の取得と検証
    """
    
    # ステップ 1: 車両エージェントの登録
    print("=== 車両エージェント登録 ===")
    # テスト用の車両エージェントリスト
    vehicle_agents = [
        {"agentIdPrefix": "vehicle-001", "kind": "vehicle", "status": {}, "assets": {}},
        {"agentIdPrefix": "vehicle-002", "kind": "vehicle", "status": {}, "assets": {}},
        {"agentIdPrefix": "vehicle-003", "kind": "vehicle", "status": {}, "assets": {}}
    ]
    
    # 車両用ArkTwin Edgeにエージェントを登録
    response = requests.post("http://127.0.0.1:2237/api/edge/agents", json=vehicle_agents)
    response.raise_for_status()
    vehicle_response = response.json()
    print("車両エージェント登録レスポンス:", json.dumps(vehicle_response, indent=2))
    
    # 実際に登録された車両エージェントIDを抽出
    vehicle_agent_ids = [agent["agentId"] for agent in vehicle_response]
    print(f"車両エージェントID: {vehicle_agent_ids}")
    
    # ステップ 2: 歩行者エージェントの登録
    print("\n=== 歩行者エージェント登録 ===")
    # テスト用の歩行者エージェントリスト
    pedestrian_agents = [
        {"agentIdPrefix": "pedestrian-001", "kind": "pedestrian", "status": {}, "assets": {}},
        {"agentIdPrefix": "pedestrian-002", "kind": "pedestrian", "status": {}, "assets": {}},
        {"agentIdPrefix": "pedestrian-003", "kind": "pedestrian", "status": {}, "assets": {}},
        {"agentIdPrefix": "pedestrian-004", "kind": "pedestrian", "status": {}, "assets": {}}
    ]
    
    # 歩行者用ArkTwin Edgeにエージェントを登録
    response = requests.post("http://127.0.0.1:2238/api/edge/agents", json=pedestrian_agents)
    response.raise_for_status()
    pedestrian_response = response.json()
    print("歩行者エージェント登録レスポンス:", json.dumps(pedestrian_response, indent=2))
    
    # 実際に登録された歩行者エージェントIDを抽出
    pedestrian_agent_ids = [agent["agentId"] for agent in pedestrian_response]
    print(f"歩行者エージェントID: {pedestrian_agent_ids}")
    
    # ステップ 3: 正しいエージェントIDを使用して位置更新を送信
    print("\n=== 位置情報送信 ===")
    
    # 車両の位置（原点近く）
    vehicle_positions = [
        (0.0, 0.0, 0.5),   # vehicle-001 原点
        (5.0, 0.0, 0.5),   # vehicle-002 東に5m
        (0.0, 5.0, 0.5),   # vehicle-003 北に5m
    ]
    
    # 歩行者の位置（車両の近く）
    pedestrian_positions = [
        (0.0, 0.0, 0.0),    # pedestrian-001 原点
        (-2.0, 2.0, 0.0),   # pedestrian-002 近く
        (2.0, -2.0, 0.0),   # pedestrian-003 近く
        (7.0, 2.0, 0.0),    # pedestrian-004 近く
    ]
    
    # 現在の時刻をタイムスタンプ形式で作成
    timestamp = {"seconds": int(time.time()), "nanos": 0}
    
    # 車両の変換行列を送信
    vehicle_transforms = {}
    # 各車両の変換行列データを作成
    for i, agent_id in enumerate(vehicle_agent_ids):
        x, y, z = vehicle_positions[i]
        vehicle_transforms[agent_id] = {
            "transform": {
                "parentAgentId": None,  # 親エージェントなし（グローバル座標）
                "globalScale": {"x": 1.0, "y": 1.0, "z": 1.0},  # スケール
                "localRotation": {"EulerAngles": {"x": 0.0, "y": 0.0, "z": 0.0}},  # 回転
                "localTranslation": {"x": x, "y": y, "z": z},  # 位置
                "localTranslationSpeed": {"x": 0.0, "y": 0.0, "z": 0.0}  # 速度（停止中）
            },
            "status": {}  # 状態情報
        }
    
    # 車両の位置情報をArkTwin Edgeに送信
    vehicle_data = {"timestamp": timestamp, "agents": vehicle_transforms}
    response = requests.put("http://127.0.0.1:2237/api/edge/agents", json=vehicle_data)
    response.raise_for_status()
    print("車両の位置情報を正常に送信しました")
    
    # 歩行者の変換行列を送信
    pedestrian_transforms = {}
    # 各歩行者の変換行列データを作成
    for i, agent_id in enumerate(pedestrian_agent_ids):
        x, y, z = pedestrian_positions[i]
        pedestrian_transforms[agent_id] = {
            "transform": {
                "parentAgentId": None,  # 親エージェントなし（グローバル座標）
                "globalScale": {"x": 1.0, "y": 1.0, "z": 1.0},  # スケール
                "localRotation": {"EulerAngles": {"x": 0.0, "y": 0.0, "z": 0.0}},  # 回転
                "localTranslation": {"x": x, "y": y, "z": z},  # 位置
                "localTranslationSpeed": {"x": 0.0, "y": 0.0, "z": 0.0}  # 速度（停止中）
            },
            "status": {}  # 状態情報
        }
    
    # 歩行者の位置情報をArkTwin Edgeに送信
    pedestrian_data = {"timestamp": timestamp, "agents": pedestrian_transforms}
    response = requests.put("http://127.0.0.1:2238/api/edge/agents", json=pedestrian_data)
    response.raise_for_status()
    print("歩行者の位置情報を正常に送信しました")
    
    # ステップ 4: 車両側からの近隣情報取得
    print("\n=== 近隣情報取得（車両側） ===")
    # 近隣情報取得のクエリを作成
    query = {
        "timestamp": timestamp,     # タイムスタンプ
        "neighborsNumber": 50,       # 最大50個の近隣エージェント
        "changeDetection": True      # 変更検出を有効化
    }
    
    # 車両側のArkTwin Edgeから近隣情報を取得
    response = requests.post("http://127.0.0.1:2237/api/edge/neighbors/_query", json=query)
    response.raise_for_status()
    
    # 近隣情報のレスポンスを表示
    neighbors_data = response.json()
    print("車両側近隣情報レスポンス:", json.dumps(neighbors_data, indent=2))
    
    # 車両側から見た歩行者の近隣情報を解析
    if "neighbors" in neighbors_data:
        neighbors = neighbors_data["neighbors"]
        # 歩行者の近隣情報だけをフィルタリング
        pedestrian_neighbors = {k: v for k, v in neighbors.items() if k.startswith("pedestrian")}
        print(f"車両側から検出した歩行者の近隣: {len(pedestrian_neighbors)}人")
        for agent_id in pedestrian_neighbors.keys():
            print(f"  - {agent_id}")
    
    # ステップ 5: 歩行者側からの近隣情報取得
    print("\n=== 近隣情報取得（歩行者側） ===")
    # 歩行者側のArkTwin Edgeから近隣情報を取得
    response = requests.post("http://127.0.0.1:2238/api/edge/neighbors/_query", json=query)
    response.raise_for_status()
    
    # 近隣情報のレスポンスを表示
    neighbors_data = response.json()
    print("歩行者側近隣情報レスポンス:", json.dumps(neighbors_data, indent=2))
    
    # 歩行者側から見た車両の近隣情報を解析
    if "neighbors" in neighbors_data:
        neighbors = neighbors_data["neighbors"]
        # 車両の近隣情報だけをフィルタリング
        vehicle_neighbors = {k: v for k, v in neighbors.items() if k.startswith("vehicle")}
        print(f"歩行者側から検出した車両の近隣: {len(vehicle_neighbors)}台")
        for agent_id in vehicle_neighbors.keys():
            print(f"  - {agent_id}")
    
    # テスト完了のメッセージ
    print("\n=== テスト完了 ===")

if __name__ == "__main__":
    # メイン処理: 近隣検出テストを実行
    test_neighbor_detection()
#!/usr/bin/env python3
"""
ArkTwin エージェント登録テストスクリプト

車両と歩行者のエージェント登録処理とIDトラッキングを検証する。
ArkTwin Edgeが正しくエージェントIDを割り当てているかを確認する。
"""

import requests
import json

def test_vehicle_registration():
    """車両エージェント登録のテスト
    
    車両シミュレーター用のArkTwin Edgeに車両エージェントを登録し、
    割り当てられたエージェントIDとプレフィックスのマッピングを確認する。
    
    Returns:
        dict: プレフィックスから実際のエージェントIDへのマッピング
    """
    # 車両用ArkTwin EdgeのURL（ポート 2237）
    edge_url = "http://127.0.0.1:2237"
    
    # テスト用の車両エージェント登録データを作成
    agents = [
        {"agentIdPrefix": "vehicle-001", "kind": "vehicle", "status": {}, "assets": {}},
        {"agentIdPrefix": "vehicle-002", "kind": "vehicle", "status": {}, "assets": {}},
        {"agentIdPrefix": "vehicle-003", "kind": "vehicle", "status": {}, "assets": {}}
    ]
    
    try:
        response = requests.post(
            f"{edge_url}/api/edge/agents",
            json=agents,
            timeout=5
        )
        response.raise_for_status()
        
        response_data = response.json()
        print("Registration response:")
        print(json.dumps(response_data, indent=2))
        
        # Extract agent ID mappings
        registered_agent_ids = {}
        if "agents" in response_data:
            for agent_data in response_data["agents"]:
                agent_id = agent_data["agentId"]
                # Find matching prefix
                for prefix in ["vehicle-001", "vehicle-002", "vehicle-003"]:
                    if agent_id.startswith(prefix):
                        registered_agent_ids[prefix] = agent_id
                        print(f"Vehicle {prefix} -> Agent ID: {agent_id}")
                        break
        
        return registered_agent_ids
        
    except requests.RequestException as e:
        print(f"Registration error: {e}")
        return {}

def test_pedestrian_registration():
    """歩行者エージェント登録のテスト
    
    歩行者シミュレーター用のArkTwin Edgeに歩行者エージェントを登録し、
    割り当てられたエージェントIDとプレフィックスのマッピングを確認する。
    
    Returns:
        dict: プレフィックスから実際のエージェントIDへのマッピング
    """
    # 歩行者用ArkTwin EdgeのURL（ポート 2238）
    edge_url = "http://127.0.0.1:2238"
    
    # テスト用の歩行者エージェント登録データを作成
    # 各歩行者の登録情報（プレフィックス、種類、状態、アセット）
    agents = [
        {"agentIdPrefix": "pedestrian-001", "kind": "pedestrian", "status": {}, "assets": {}},
        {"agentIdPrefix": "pedestrian-002", "kind": "pedestrian", "status": {}, "assets": {}},
        {"agentIdPrefix": "pedestrian-003", "kind": "pedestrian", "status": {}, "assets": {}},
        {"agentIdPrefix": "pedestrian-004", "kind": "pedestrian", "status": {}, "assets": {}}
    ]
    
    try:
        response = requests.post(
            f"{edge_url}/api/edge/agents",
            json=agents,
            timeout=5
        )
        response.raise_for_status()
        
        response_data = response.json()
        print("Registration response:")
        print(json.dumps(response_data, indent=2))
        
        # Extract agent ID mappings
        registered_agent_ids = {}
        if "agents" in response_data:
            # レスポンスから各エージェントの情報を取得
            for agent_data in response_data["agents"]:
                agent_id = agent_data["agentId"]
                # プレフィックスと実際のIDのマッチングを検索
                for prefix in ["pedestrian-001", "pedestrian-002", "pedestrian-003", "pedestrian-004"]:
                    if agent_id.startswith(prefix):
                        registered_agent_ids[prefix] = agent_id
                        print(f"歩行者 {prefix} -> エージェントID: {agent_id}")
                        break
        
        return registered_agent_ids
        
    except requests.RequestException as e:
        print(f"Registration error: {e}")
        return {}

if __name__ == "__main__":
    print("=== Testing Vehicle Registration ===")
    vehicle_ids = test_vehicle_registration()
    
    print("\n=== Testing Pedestrian Registration ===")
    pedestrian_ids = test_pedestrian_registration()
    
    print(f"\nVehicle IDs: {vehicle_ids}")
    print(f"Pedestrian IDs: {pedestrian_ids}")
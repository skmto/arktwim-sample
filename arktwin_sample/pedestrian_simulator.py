#!/usr/bin/env python3
"""
ArkTwin Pedestrian Simulator Sample

歩行者シミュレーターのサンプル実装。
複数の歩行者が歩道上を移動し、ArkTwin経由で他のシミュレーターと位置情報を共有します。
"""

import requests
import time
import math
import json
import sys
import random
from typing import Dict, List, Tuple
from dataclasses import dataclass
import threading


@dataclass
class Pedestrian:
    """歩行者を表すクラス"""
    id: str
    x: float
    y: float
    z: float
    speed: float
    direction: float  # ラジアン
    target_x: float
    target_y: float


class PedestrianSimulator:
    """歩行者シミュレーター"""
    
    def __init__(self, edge_port: int = 2238):
        self.edge_url = f"http://127.0.0.1:{edge_port}"
        self.pedestrians: Dict[str, Pedestrian] = {}
        self.neighbors: Dict[str, dict] = {}
        self.simulation_time = 0.0
        self.running = False
        self.registered_agent_ids: Dict[str, str] = {}  # prefix -> actual_id mapping
        
        # 歩行者を初期化
        self._initialize_pedestrians()
        
    def _initialize_pedestrians(self):
        """歩行者の初期配置（テスト用：近くに停止）"""
        # 4人の歩行者を車両の近くに停止状態で配置
        self.pedestrians = {
            "pedestrian-001": Pedestrian("pedestrian-001", 0.0, 0.0, 0.0, 0.0, 0.0, 3.0, 3.0),      # 車両の近く
            "pedestrian-002": Pedestrian("pedestrian-002", -2.0, 2.0, 0.0, 0.0, 0.0, -2.0, 2.0),    # 車両の近く  
            "pedestrian-003": Pedestrian("pedestrian-003", 2.0, -2.0, 0.0, 0.0, 0.0, 2.0, -2.0),    # 車両の近く
            "pedestrian-004": Pedestrian("pedestrian-004", 7.0, 2.0, 0.0, 0.0, 0.0, 7.0, 2.0),      # 車両の近く
        }
        
    def setup_edge_connection(self):
        """ArkTwin Edgeへの接続設定"""
        try:
            # 座標系設定は既に設定済みと仮定してスキップ
            print("座標系設定をスキップ（既存設定を使用）")
            
            # エージェント登録
            agents = [
                {"agentIdPrefix": pedestrian_id, "kind": "pedestrian", "status": {}, "assets": {}}
                for pedestrian_id in self.pedestrians.keys()
            ]
            
            response = requests.post(
                f"{self.edge_url}/api/edge/agents",
                json=agents,
                timeout=5
            )
            response.raise_for_status()
            
            # レスポンスから実際のエージェントIDを取得
            response_data = response.json()
            for i, agent_data in enumerate(response_data):
                agent_id = agent_data["agentId"]
                # リクエストの順序に基づいて対応関係を保存
                pedestrian_ids = list(self.pedestrians.keys())
                if i < len(pedestrian_ids):
                    pedestrian_id = pedestrian_ids[i]
                    self.registered_agent_ids[pedestrian_id] = agent_id
                    print(f"歩行者 {pedestrian_id} -> エージェントID: {agent_id}")
            
            print(f"歩行者エージェント登録完了: {len(self.registered_agent_ids)}人")
            
        except requests.RequestException as e:
            print(f"ArkTwin Edge接続エラー: {e}")
            return False
            
        return True
        
    def update_pedestrians(self, dt: float):
        """歩行者位置更新（テスト用：停止状態）"""
        # テスト用：歩行者は移動せず停止状態を維持
        for pedestrian in self.pedestrians.values():
            # 位置は変更しない（停止状態）
            pass
                
    def send_transforms(self):
        """ArkTwinに変換行列を送信"""
        timestamp = {
            "seconds": int(self.simulation_time),
            "nanos": int((self.simulation_time % 1) * 1e9)
        }
        
        transforms = {}
        for pedestrian in self.pedestrians.values():
            # 実際に登録されたエージェントIDを使用
            actual_agent_id = self.registered_agent_ids.get(pedestrian.id, pedestrian.id)
            transforms[actual_agent_id] = {
                "transform": {
                    "parentAgentId": None,
                    "globalScale": {
                        "x": 1.0,
                        "y": 1.0,
                        "z": 1.0
                    },
                    "localRotation": {
                        "EulerAngles": {
                            "x": 0.0,
                            "y": 0.0,
                            "z": math.degrees(pedestrian.direction)
                        }
                    },
                    "localTranslation": {
                        "x": pedestrian.x,
                        "y": pedestrian.y, 
                        "z": pedestrian.z
                    },
                    "localTranslationSpeed": {
                        "x": pedestrian.speed * math.cos(pedestrian.direction),
                        "y": pedestrian.speed * math.sin(pedestrian.direction),
                        "z": 0.0
                    }
                },
                "status": {}
            }
            
        data = {
            "timestamp": timestamp,
            "agents": transforms
        }
        
        try:
            response = requests.put(
                f"{self.edge_url}/api/edge/agents",
                json=data,
                timeout=1
            )
            response.raise_for_status()
        except requests.RequestException as e:
            print(f"変換行列送信エラー: {e}")
            
    def receive_neighbors(self):
        """近隣エージェント情報を受信"""
        timestamp = {
            "seconds": int(self.simulation_time),
            "nanos": int((self.simulation_time % 1) * 1e9)
        }
        
        query = {
            "timestamp": timestamp,
            "neighborsNumber": 50,
            "changeDetection": True
        }
        
        try:
            response = requests.post(
                f"{self.edge_url}/api/edge/neighbors/_query",
                json=query,
                timeout=1
            )
            response.raise_for_status()
            
            data = response.json()
            if "neighbors" in data:
                self.neighbors = data["neighbors"]
                # 他のシミュレーターからの車両情報を表示
                vehicles = {k: v for k, v in self.neighbors.items() 
                           if k.startswith("vehicle")}
                if vehicles:
                    print(f"[歩行者] 検出した車両: {len(vehicles)}台")
                    
        except requests.RequestException as e:
            print(f"近隣情報受信エラー: {e}")
            
    def print_status(self):
        """シミュレーション状態表示"""
        print(f"\n=== 歩行者シミュレーター [停止テスト] (時刻: {self.simulation_time:.1f}s) ===")
        for pedestrian in self.pedestrians.values():
            actual_id = self.registered_agent_ids.get(pedestrian.id, pedestrian.id)
            print(f"{pedestrian.id} ({actual_id}): 位置({pedestrian.x:.1f}, {pedestrian.y:.1f}) "
                 f"速度:{pedestrian.speed:.1f}m/s [停止中]")
            
        if self.neighbors:
            other_agents = {k: v for k, v in self.neighbors.items() 
                          if not k.startswith("pedestrian")}
            if other_agents:
                print(f"他のエージェント: {len(other_agents)}個")
                for agent_id in other_agents.keys():
                    print(f"  - {agent_id}")
            else:
                print("他のエージェント: なし")
        else:
            print("近隣情報: なし")
                
    def run(self):
        """シミュレーション実行"""
        if not self.setup_edge_connection():
            print("ArkTwin Edge接続に失敗しました")
            return
            
        self.running = True
        dt = 0.1  # 100ms
        
        print("歩行者シミュレーション開始（テスト用：停止状態）...")
        print("Ctrl+Cで停止")
        
        try:
            while self.running:
                start_time = time.time()
                
                # シミュレーション更新
                self.update_pedestrians(dt)
                self.send_transforms()
                self.receive_neighbors()
                
                # 1秒毎に状態表示
                if int(self.simulation_time) % 1 == 0 and self.simulation_time % 1 < dt:
                    self.print_status()
                    
                self.simulation_time += dt
                
                # フレームレート制御
                elapsed = time.time() - start_time
                sleep_time = max(0, dt - elapsed)
                time.sleep(sleep_time)
                
        except KeyboardInterrupt:
            print("\nシミュレーション停止")
        finally:
            self.running = False


def main():
    """メイン関数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="ArkTwin歩行者シミュレーター")
    parser.add_argument("--port", type=int, default=2238,
                       help="ArkTwin Edgeポート番号 (デフォルト: 2238)")
    
    args = parser.parse_args()
    
    simulator = PedestrianSimulator(edge_port=args.port)
    simulator.run()


if __name__ == "__main__":
    main()
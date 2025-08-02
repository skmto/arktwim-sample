#!/usr/bin/env python3
"""
ArkTwin Vehicle Simulator Sample

車両シミュレーターのサンプル実装。
複数の車両が道路上を移動し、ArkTwin経由で他のシミュレーターと位置情報を共有します。
"""

import requests
import time
import math
import json
import sys
from typing import Dict, List, Tuple
from dataclasses import dataclass
import threading


@dataclass
class Vehicle:
    """車両を表すクラス"""
    id: str
    x: float
    y: float
    z: float
    speed: float
    direction: float  # ラジアン


class VehicleSimulator:
    """車両シミュレーター"""
    
    def __init__(self, edge_port: int = 2237):
        self.edge_url = f"http://127.0.0.1:{edge_port}"
        self.vehicles: Dict[str, Vehicle] = {}
        self.neighbors: Dict[str, dict] = {}
        self.simulation_time = 0.0
        self.running = False
        
        # 車両を初期化
        self._initialize_vehicles()
        
    def _initialize_vehicles(self):
        """車両の初期配置"""
        # 3台の車両を道路上に配置
        self.vehicles = {
            "vehicle-001": Vehicle("vehicle-001", 0.0, 0.0, 0.5, 10.0, 0.0),
            "vehicle-002": Vehicle("vehicle-002", -20.0, 0.0, 0.5, 12.0, 0.0),
            "vehicle-003": Vehicle("vehicle-003", -40.0, 0.0, 0.5, 8.0, 0.0),
        }
        
    def setup_edge_connection(self):
        """ArkTwin Edgeへの接続設定"""
        try:
            # 座標系設定は既に設定済みと仮定してスキップ
            print("座標系設定をスキップ（既存設定を使用）")
            
            # エージェント登録
            agents = [
                {"agentIdPrefix": vehicle_id, "kind": "vehicle", "status": {}, "assets": {}}
                for vehicle_id in self.vehicles.keys()
            ]
            
            response = requests.post(
                f"{self.edge_url}/api/edge/agents",
                json=agents,
                timeout=5
            )
            response.raise_for_status()
            print(f"車両エージェント登録完了: {len(agents)}台")
            
        except requests.RequestException as e:
            print(f"ArkTwin Edge接続エラー: {e}")
            return False
            
        return True
        
    def update_vehicles(self, dt: float):
        """車両位置更新"""
        for vehicle in self.vehicles.values():
            # 直線移動
            vehicle.x += vehicle.speed * dt * math.cos(vehicle.direction)
            vehicle.y += vehicle.speed * dt * math.sin(vehicle.direction)
            
            # 道路端で折り返し
            if vehicle.x > 100:
                vehicle.direction = math.pi
            elif vehicle.x < -100:
                vehicle.direction = 0
                
    def send_transforms(self):
        """ArkTwinに変換行列を送信"""
        timestamp = {
            "seconds": int(self.simulation_time),
            "nanos": int((self.simulation_time % 1) * 1e9)
        }
        
        transforms = {}
        for vehicle in self.vehicles.values():
            transforms[vehicle.id] = {
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
                            "z": math.degrees(vehicle.direction)
                        }
                    },
                    "localTranslation": {
                        "x": vehicle.x,
                        "y": vehicle.y, 
                        "z": vehicle.z
                    },
                    "localTranslationSpeed": {
                        "x": vehicle.speed * math.cos(vehicle.direction),
                        "y": vehicle.speed * math.sin(vehicle.direction),
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
                # 他のシミュレーターからの歩行者情報を表示
                pedestrians = {k: v for k, v in self.neighbors.items() 
                             if k.startswith("pedestrian")}
                if pedestrians:
                    print(f"[車両] 検出した歩行者: {len(pedestrians)}人")
                    
        except requests.RequestException as e:
            print(f"近隣情報受信エラー: {e}")
            
    def print_status(self):
        """シミュレーション状態表示"""
        print(f"\n=== 車両シミュレーター (時刻: {self.simulation_time:.1f}s) ===")
        for vehicle in self.vehicles.values():
            print(f"{vehicle.id}: 位置({vehicle.x:.1f}, {vehicle.y:.1f}) 速度:{vehicle.speed:.1f}m/s")
            
        if self.neighbors:
            other_agents = {k: v for k, v in self.neighbors.items() 
                          if not k.startswith("vehicle")}
            if other_agents:
                print(f"他のエージェント: {len(other_agents)}個")
                
    def run(self):
        """シミュレーション実行"""
        if not self.setup_edge_connection():
            print("ArkTwin Edge接続に失敗しました")
            return
            
        self.running = True
        dt = 0.1  # 100ms
        
        print("車両シミュレーション開始...")
        print("Ctrl+Cで停止")
        
        try:
            while self.running:
                start_time = time.time()
                
                # シミュレーション更新
                self.update_vehicles(dt)
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
    
    parser = argparse.ArgumentParser(description="ArkTwin車両シミュレーター")
    parser.add_argument("--port", type=int, default=2237,
                       help="ArkTwin Edgeポート番号 (デフォルト: 2237)")
    
    args = parser.parse_args()
    
    simulator = VehicleSimulator(edge_port=args.port)
    simulator.run()


if __name__ == "__main__":
    main()
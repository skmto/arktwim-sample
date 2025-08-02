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
    """車両シミュレーター
    
    ArkTwin Edgeを通じて車両エージェントの位置情報を管理し、
    他のシミュレーター（歩行者など）との近隣情報を共有する。
    """
    
    def __init__(self, edge_port: int = 2237):
        # ArkTwin EdgeのREST APIエンドポイント
        self.edge_url = f"http://127.0.0.1:{edge_port}"
        # 管理している車両エージェントの辞書
        self.vehicles: Dict[str, Vehicle] = {}
        # 近隣エージェント情報（他のシミュレーターからの情報）
        self.neighbors: Dict[str, dict] = {}
        # シミュレーション経過時間（秒）
        self.simulation_time = 0.0
        # シミュレーション実行状態フラグ
        self.running = False
        # エージェント登録時の実際のIDマッピング（prefix -> actual_id）
        self.registered_agent_ids: Dict[str, str] = {}  # prefix -> actual_id mapping
        
        # 車両を初期化
        self._initialize_vehicles()
        
    def _initialize_vehicles(self):
        """車両の初期配置（テスト用：近くに停車）
        
        歩行者シミュレーターとの近隣検出をテストするため、
        歩行者の近くに車両を停車状態で配置する。
        """
        # 3台の車両を近い場所に停車状態で配置
        # テスト用のため、移動はせずに固定位置に配置
        self.vehicles = {
            "vehicle-001": Vehicle("vehicle-001", 0.0, 0.0, 0.5, 0.0, 0.0),     # 原点
            "vehicle-002": Vehicle("vehicle-002", 5.0, 0.0, 0.5, 0.0, 0.0),     # 5m東
            "vehicle-003": Vehicle("vehicle-003", 0.0, 5.0, 0.5, 0.0, 0.0),     # 5m北
        }
        
    def setup_edge_connection(self):
        """ArkTwin Edgeへの接続設定
        
        座標系設定をスキップし、車両エージェントをArkTwin Edgeに登録する。
        登録後、実際に割り当てられたエージェントIDを保存する。
        
        Returns:
            bool: 接続と登録が成功した場合True
        """
        try:
            # 座標系設定は既に設定済みと仮定してスキップ
            # 本来は座標系設定APIを呼び出す必要があるが、
            # 設定ファイルで既に設定されているためここではスキップ
            print("座標系設定をスキップ（既存設定を使用）")
            
            # エージェント登録API呼び出し
            # 各車両にユニークなIDプレフィックスを指定
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
            
            # レスポンスから実際のエージェントIDを取得
            # ArkTwin Edgeが自動的にユニークなIDを生成するため、
            # プレフィックスと実際のIDのマッピングを保存
            response_data = response.json()
            for i, agent_data in enumerate(response_data):
                agent_id = agent_data["agentId"]
                # リクエストの順序に基づいて対応関係を保存
                vehicle_ids = list(self.vehicles.keys())
                if i < len(vehicle_ids):
                    vehicle_id = vehicle_ids[i]
                    self.registered_agent_ids[vehicle_id] = agent_id
                    print(f"車両 {vehicle_id} -> エージェントID: {agent_id}")
            
            print(f"車両エージェント登録完了: {len(self.registered_agent_ids)}台")
            
        except requests.RequestException as e:
            print(f"ArkTwin Edge接続エラー: {e}")
            return False
            
        return True
        
    def update_vehicles(self, dt: float):
        """車両位置更新（テスト用：停止状態）
        
        本来はここで車両の移動ロジックを実装するが、
        近隣検出のテスト用のため、停止状態を維持する。
        
        Args:
            dt (float): 前回更新からの経過時間（秒）
        """
        # テスト用：車両は移動せず停止状態を維持
        # 実際のシミュレーションでは、ここで道路上の直線移動や
        # 交差点での方向転換などの車両ロジックを実装する
        for vehicle in self.vehicles.values():
            # 位置は変更しない（停止状態）
            pass
                
    def send_transforms(self):
        """ArkTwinに変換行列を送信
        
        各車両の現在位置、回転、速度情報をArkTwin Edgeに送信し、
        他のシミュレーターが近隣情報として受信できるようにする。
        """
        # シミュレーション時刻をタイムスタンプ形式に変換
        timestamp = {
            "seconds": int(self.simulation_time),
            "nanos": int((self.simulation_time % 1) * 1e9)
        }
        
        # 各車両の変換行列データを構築
        transforms = {}
        for vehicle in self.vehicles.values():
            # 実際に登録されたエージェントIDを使用
            # プレフィックスではなく、Edge側で生成された実際のIDを使用する
            actual_agent_id = self.registered_agent_ids.get(vehicle.id, vehicle.id)
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
                            "z": math.degrees(vehicle.direction)
                        }
                    },
                    "localTranslation": {
                        "x": vehicle.x,  # 東方向位置（メートル）
                        "y": vehicle.y,  # 北方向位置（メートル）
                        "z": vehicle.z   # 上方向位置（メートル）
                    },
                    "localTranslationSpeed": {
                        "x": vehicle.speed * math.cos(vehicle.direction),  # X方向速度
                        "y": vehicle.speed * math.sin(vehicle.direction),  # Y方向速度
                        "z": 0.0  # Z方向速度（車両は通常Z軸移動なし）
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
        """近隣エージェント情報を受信
        
        ArkTwin Edgeから近隣のエージェント情報を取得する。
        主に歩行者シミュレーターからの歩行者情報を受信し、
        車両が歩行者の存在を認識できるようにする。
        """
        timestamp = {
            "seconds": int(self.simulation_time),
            "nanos": int((self.simulation_time % 1) * 1e9)
        }
        
        # 近隣エージェント検索クエリ
        query = {
            "timestamp": timestamp,
            "neighborsNumber": 50,      # 最大50個のエージェントを取得
            "changeDetection": True     # 変更検出を有効にする
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
                # 歩行者IDで始まるエージェントを歩行者として認識
                pedestrians = {k: v for k, v in self.neighbors.items() 
                             if k.startswith("pedestrian")}
                if pedestrians:
                    print(f"[車両] 検出した歩行者: {len(pedestrians)}人")
                    
        except requests.RequestException as e:
            print(f"近隣情報受信エラー: {e}")
            
    def print_status(self):
        """シミュレーション状態表示
        
        現在のシミュレーション時刻、各車両の状態、
        検出された近隣エージェント情報をコンソールに表示する。
        """
        # シミュレーション状態のヘッダー表示
        print(f"\n=== 車両シミュレーター [停止テスト] (時刻: {self.simulation_time:.1f}s) ===")
        # 各車両の状態を表示
        for vehicle in self.vehicles.values():
            print(f"{vehicle.id}: 位置({vehicle.x:.1f}, {vehicle.y:.1f}) 速度:{vehicle.speed:.1f}m/s [停止中]")
            
        # 近隣エージェント情報の表示
        if self.neighbors:
            # 車両以外のエージェント（主に歩行者）を表示
            other_agents = {k: v for k, v in self.neighbors.items() 
                          if not k.startswith("vehicle")}
            if other_agents:
                print(f"他のエージェント: {len(other_agents)}個")
                for agent_id in other_agents.keys():
                    print(f"  - {agent_id}")
            else:
                print("他のエージェント: なし")
        else:
            print("近隣情報: なし")
                
    def run(self):
        """シミュレーション実行
        
        メインのシミュレーションループ。
        ArkTwin Edgeへの接続、エージェント登録を行った後、
        定期的な位置更新と近隣情報受信を実行する。
        """
        # ArkTwin Edgeへの接続とエージェント登録
        if not self.setup_edge_connection():
            print("ArkTwin Edge接続に失敗しました")
            return
            
        self.running = True
        dt = 0.1  # シミュレーション更新間隔: 100ms（10Hz）
        
        print("車両シミュレーション開始（テスト用：停止状態）...")
        print("Ctrl+Cで停止")
        
        try:
            while self.running:
                # フレーム開始時刻を記録（フレームレート制御用）
                start_time = time.time()
                
                # シミュレーション更新サイクル
                self.update_vehicles(dt)       # 車両位置更新
                self.send_transforms()         # 位置情報をArkTwinに送信
                self.receive_neighbors()       # 近隣情報を受信
                
                # 1秒毎に状態表示（デバッグ用）
                if int(self.simulation_time) % 1 == 0 and self.simulation_time % 1 < dt:
                    self.print_status()
                    
                self.simulation_time += dt
                
                # フレームレート制御（指定された更新間隔を維持）
                elapsed = time.time() - start_time
                sleep_time = max(0, dt - elapsed)
                time.sleep(sleep_time)
                
        except KeyboardInterrupt:
            print("\nシミュレーション停止")
        finally:
            self.running = False


def main():
    """メイン関数
    
    コマンドライン引数を解析し、車両シミュレーターを起動する。
    """
    import argparse
    
    # コマンドライン引数の解析設定
    parser = argparse.ArgumentParser(description="ArkTwin車両シミュレーター")
    parser.add_argument("--port", type=int, default=2237,
                       help="ArkTwin Edgeポート番号 (デフォルト: 2237)")
    
    args = parser.parse_args()
    
    # シミュレーター作成と実行
    simulator = VehicleSimulator(edge_port=args.port)
    simulator.run()


if __name__ == "__main__":
    main()
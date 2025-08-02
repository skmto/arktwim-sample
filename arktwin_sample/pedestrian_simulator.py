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
    """歩行者シミュレーター
    
    ArkTwin Edgeを通じて歩行者エージェントの位置情報を管理し、
    他のシミュレーター（車両など）との近隣情報を共有する。
    """
    
    def __init__(self, edge_port: int = 2238):
        # ArkTwin EdgeのREST APIエンドポイント
        self.edge_url = f"http://127.0.0.1:{edge_port}"
        # 管理している歩行者エージェントの辞書
        self.pedestrians: Dict[str, Pedestrian] = {}
        # 近隣エージェント情報（他のシミュレーターからの情報）
        self.neighbors: Dict[str, dict] = {}
        # シミュレーション経過時間（秒）
        self.simulation_time = 0.0
        # シミュレーション実行状態フラグ
        self.running = False
        # エージェント登録時の実際のIDマッピング（prefix -> actual_id）
        self.registered_agent_ids: Dict[str, str] = {}  # prefix -> actual_id mapping
        
        # 歩行者を初期化
        self._initialize_pedestrians()
        
    def _initialize_pedestrians(self):
        """歩行者の初期配置（テスト用：近くに停止）
        
        車両シミュレーターとの近隣検出をテストするため、
        車両の近くに歩行者を停止状態で配置する。
        """
        # 4人の歩行者を車両の近くに停止状態で配置
        # テスト用のため、移動はせずに固定位置に配置
        self.pedestrians = {
            "pedestrian-001": Pedestrian("pedestrian-001", 0.0, 0.0, 0.0, 0.0, 0.0, 3.0, 3.0),      # 車両の近く
            "pedestrian-002": Pedestrian("pedestrian-002", -2.0, 2.0, 0.0, 0.0, 0.0, -2.0, 2.0),    # 車両の近く  
            "pedestrian-003": Pedestrian("pedestrian-003", 2.0, -2.0, 0.0, 0.0, 0.0, 2.0, -2.0),    # 車両の近く
            "pedestrian-004": Pedestrian("pedestrian-004", 7.0, 2.0, 0.0, 0.0, 0.0, 7.0, 2.0),      # 車両の近く
        }
        
    def setup_edge_connection(self):
        """ArkTwin Edgeへの接続設定
        
        座標系設定をスキップし、歩行者エージェントをArkTwin Edgeに登録する。
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
            # 各歩行者にユニークなIDプレフィックスを指定
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
            # ArkTwin Edgeが自動的にユニークなIDを生成するため、
            # プレフィックスと実際のIDのマッピングを保存
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
        """歩行者位置更新（テスト用：停止状態）
        
        本来はここで歩行者の移動ロジックを実装するが、
        近隣検出のテスト用のため、停止状態を維持する。
        
        Args:
            dt (float): 前回更新からの経過時間（秒）
        """
        # テスト用：歩行者は移動せず停止状態を維持
        # 実際のシミュレーションでは、ここで目標地点への移動や
        # 障害物回避などの歩行ロジックを実装する
        for pedestrian in self.pedestrians.values():
            # 位置は変更しない（停止状態）
            pass
                
    def send_transforms(self):
        """ArkTwinに変換行列を送信
        
        各歩行者の現在位置、回転、速度情報をArkTwin Edgeに送信し、
        他のシミュレーターが近隣情報として受信できるようにする。
        """
        # シミュレーション時刻をタイムスタンプ形式に変換
        timestamp = {
            "seconds": int(self.simulation_time),
            "nanos": int((self.simulation_time % 1) * 1e9)
        }
        
        # 各歩行者の変換行列データを構築
        transforms = {}
        for pedestrian in self.pedestrians.values():
            # 実際に登録されたエージェントIDを使用
            # プレフィックスではなく、Edge側で生成された実際のIDを使用する
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
                        "x": pedestrian.x,  # 東方向位置（メートル）
                        "y": pedestrian.y,  # 北方向位置（メートル）
                        "z": pedestrian.z   # 上方向位置（メートル）
                    },
                    "localTranslationSpeed": {
                        "x": pedestrian.speed * math.cos(pedestrian.direction),  # X方向速度
                        "y": pedestrian.speed * math.sin(pedestrian.direction),  # Y方向速度
                        "z": 0.0  # Z方向速度（歩行者は通常Z軸移動なし）
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
        主に車両シミュレーターからの車両情報を受信し、
        歩行者が車両の存在を認識できるようにする。
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
                # 他のシミュレーターからの車両情報を表示
                # 車両IDで始まるエージェントを車両として認識
                vehicles = {k: v for k, v in self.neighbors.items() 
                           if k.startswith("vehicle")}
                if vehicles:
                    print(f"[歩行者] 検出した車両: {len(vehicles)}台")
                    
        except requests.RequestException as e:
            print(f"近隣情報受信エラー: {e}")
            
    def print_status(self):
        """シミュレーション状態表示
        
        現在のシミュレーション時刻、各歩行者の状態、
        検出された近隣エージェント情報をコンソールに表示する。
        """
        # シミュレーション状態のヘッダー表示
        print(f"\n=== 歩行者シミュレーター [停止テスト] (時刻: {self.simulation_time:.1f}s) ===")
        # 各歩行者の状態を表示
        for pedestrian in self.pedestrians.values():
            actual_id = self.registered_agent_ids.get(pedestrian.id, pedestrian.id)
            print(f"{pedestrian.id} ({actual_id}): 位置({pedestrian.x:.1f}, {pedestrian.y:.1f}) "
                 f"速度:{pedestrian.speed:.1f}m/s [停止中]")
            
        # 近隣エージェント情報の表示
        if self.neighbors:
            # 歩行者以外のエージェント（主に車両）を表示
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
        
        print("歩行者シミュレーション開始（テスト用：停止状態）...")
        print("Ctrl+Cで停止")
        
        try:
            while self.running:
                # フレーム開始時刻を記録（フレームレート制御用）
                start_time = time.time()
                
                # シミュレーション更新サイクル
                self.update_pedestrians(dt)    # 歩行者位置更新
                self.send_transforms()          # 位置情報をArkTwinに送信
                self.receive_neighbors()        # 近隣情報を受信
                
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
    
    コマンドライン引数を解析し、歩行者シミュレーターを起動する。
    """
    import argparse
    
    # コマンドライン引数の解析設定
    parser = argparse.ArgumentParser(description="ArkTwin歩行者シミュレーター")
    parser.add_argument("--port", type=int, default=2238,
                       help="ArkTwin Edgeポート番号 (デフォルト: 2238)")
    
    args = parser.parse_args()
    
    # シミュレーター作成と実行
    simulator = PedestrianSimulator(edge_port=args.port)
    simulator.run()


if __name__ == "__main__":
    main()
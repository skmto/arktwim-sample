#!/usr/bin/env python3
"""
可視化システムのテストスクリプト

ArkTwin Edgeが起動していない場合でも可視化システムをテストできるよう、
モックデータを提供するHTTPサーバーを起動する。
"""

import http.server
import socketserver
import json
import time
import math
from threading import Thread
import webbrowser
import sys
import os

class MockArkTwinHandler(http.server.BaseHTTPRequestHandler):
    """ArkTwin Edge APIのモックハンドラー"""
    
    def __init__(self, *args, **kwargs):
        # モックデータの初期化
        self.start_time = time.time()
        super().__init__(*args, **kwargs)
    
    def do_OPTIONS(self):
        """CORS プリフライト要求の処理"""
        self.send_response(200)
        self.send_cors_headers()
        self.end_headers()
    
    def do_POST(self):
        """POST要求の処理（近隣情報取得API）"""
        if self.path == '/api/edge/neighbors/_query':
            self.handle_neighbors_query()
        else:
            self.send_error(404, "Not Found")
    
    def handle_neighbors_query(self):
        """近隣情報取得APIのモック"""
        try:
            # 要求ボディを読み取り
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            
            # ポート番号に基づいてモックデータを生成
            port = self.server.server_address[1]
            mock_data = self.generate_mock_data(port)
            
            # レスポンス送信
            self.send_response(200)
            self.send_cors_headers()
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            
            response = json.dumps(mock_data, ensure_ascii=False)
            self.wfile.write(response.encode('utf-8'))
            
        except Exception as e:
            print(f"エラー: {e}")
            self.send_error(500, str(e))
    
    def generate_mock_data(self, port):
        """交差点シミュレーション用モックデータ生成
        
        座標系:
        - 原点(0,0)は交差点の中心
        - X軸: 東方向が正
        - Y軸: 北方向が正
        - 道路幅: 6メートル (片側3メートル)
        """
        current_time = time.time()
        elapsed = current_time - self.start_time
        
        neighbors = {}
        
        if port == 2237:  # 車両用Edge - 歩行者データを返す
            # 4人の歩行者のモックデータ - 交差点を横断・歩道を歩行
            pedestrians = [
                {
                    "id": "pedestrian-001",
                    "type": "crosswalk_ew",  # 東西方向横断歩道
                    "start": (-15, -1.5),
                    "end": (15, -1.5),
                    "speed": 1.2  # 1.2 m/s
                },
                {
                    "id": "pedestrian-002", 
                    "type": "crosswalk_ns",  # 南北方向横断歩道
                    "start": (1.5, -15),
                    "end": (1.5, 15),
                    "speed": 1.0
                },
                {
                    "id": "pedestrian-003",
                    "type": "sidewalk_north",  # 北側歩道
                    "start": (-20, 5),
                    "end": (20, 5),
                    "speed": 1.4
                },
                {
                    "id": "pedestrian-004",
                    "type": "crosswalk_ew_return",  # 東西横断（戻り）
                    "start": (15, 1.5),
                    "end": (-15, 1.5),
                    "speed": 1.1
                }
            ]
            
            for i, ped in enumerate(pedestrians):
                # 周期的な移動パターン
                cycle_time = 30  # 30秒で往復
                progress = (elapsed * ped["speed"] / 30) % 2  # 0-2の範囲で往復
                
                if progress <= 1:
                    # 順方向
                    t = progress
                    x = ped["start"][0] + t * (ped["end"][0] - ped["start"][0])
                    y = ped["start"][1] + t * (ped["end"][1] - ped["start"][1])
                    direction = math.atan2(ped["end"][1] - ped["start"][1], 
                                         ped["end"][0] - ped["start"][0])
                else:
                    # 逆方向
                    t = progress - 1
                    x = ped["end"][0] + t * (ped["start"][0] - ped["end"][0])
                    y = ped["end"][1] + t * (ped["start"][1] - ped["end"][1])
                    direction = math.atan2(ped["start"][1] - ped["end"][1], 
                                         ped["start"][0] - ped["end"][0])
                
                agent_id = f"{ped['id']}-mock-{int(current_time)}"
                
                neighbors[agent_id] = {
                    "transform": {
                        "localTranslation": {
                            "x": x,
                            "y": y,
                            "z": 0.0
                        },
                        "localRotation": {
                            "EulerAngles": {
                                "x": 0.0,
                                "y": 0.0,
                                "z": math.degrees(direction)
                            }
                        },
                        "localTranslationSpeed": {
                            "x": ped["speed"] * math.cos(direction),
                            "y": ped["speed"] * math.sin(direction),
                            "z": 0.0
                        }
                    },
                    "kind": "pedestrian",
                    "status": {"state": "walking", "location": ped["type"]},
                    "assets": {},
                    "nearestDistance": math.sqrt(x*x + y*y),
                    "change": "Updated"
                }
        
        elif port == 2238:  # 歩行者用Edge - 車両データを返す
            # 4台の車両のモックデータ - 交差点を通行
            vehicles = [
                {
                    "id": "vehicle-001",
                    "type": "straight_ew",  # 東西直進
                    "start": (-25, -1.5),
                    "end": (25, -1.5),
                    "speed": 8.0  # 8 m/s (約29km/h)
                },
                {
                    "id": "vehicle-002",
                    "type": "straight_ns",  # 南北直進
                    "start": (1.5, -25),
                    "end": (1.5, 25),
                    "speed": 7.0
                },
                {
                    "id": "vehicle-003",
                    "type": "right_turn",  # 右折（南→東）
                    "waypoints": [(1.5, -25), (1.5, -3), (3, -1.5), (25, -1.5)],
                    "speed": 5.0  # 右折は速度を落とす
                },
                {
                    "id": "vehicle-004",
                    "type": "left_turn",  # 左折（南→西）
                    "waypoints": [(-1.5, -25), (-1.5, -3), (-3, 1.5), (-25, 1.5)],
                    "speed": 4.5
                }
            ]
            
            for i, veh in enumerate(vehicles):
                agent_id = f"{veh['id']}-mock-{int(current_time)}"
                
                if veh["type"] in ["straight_ew", "straight_ns"]:
                    # 直進車両
                    cycle_time = 60  # 60秒で往復
                    progress = (elapsed * veh["speed"] / 50) % 2
                    
                    if progress <= 1:
                        t = progress
                        x = veh["start"][0] + t * (veh["end"][0] - veh["start"][0])
                        y = veh["start"][1] + t * (veh["end"][1] - veh["start"][1])
                        direction = math.atan2(veh["end"][1] - veh["start"][1], 
                                             veh["end"][0] - veh["start"][0])
                    else:
                        t = progress - 1
                        x = veh["end"][0] + t * (veh["start"][0] - veh["end"][0])
                        y = veh["end"][1] + t * (veh["start"][1] - veh["end"][1])
                        direction = math.atan2(veh["start"][1] - veh["end"][1], 
                                             veh["start"][0] - veh["end"][0])
                
                else:
                    # 右折・左折車両（複数のウェイポイント）
                    waypoints = veh["waypoints"]
                    total_distance = 0
                    
                    # 総距離計算
                    for j in range(len(waypoints) - 1):
                        dx = waypoints[j+1][0] - waypoints[j][0]
                        dy = waypoints[j+1][1] - waypoints[j][1]
                        total_distance += math.sqrt(dx*dx + dy*dy)
                    
                    # 現在位置計算
                    cycle_time = total_distance / veh["speed"]
                    progress = (elapsed % (cycle_time * 2))
                    
                    if progress <= cycle_time:
                        # 順方向
                        distance_traveled = progress * veh["speed"]
                    else:
                        # 逆方向
                        distance_traveled = total_distance - (progress - cycle_time) * veh["speed"]
                    
                    # ウェイポイント間での位置補間
                    current_distance = 0
                    for j in range(len(waypoints) - 1):
                        dx = waypoints[j+1][0] - waypoints[j][0]
                        dy = waypoints[j+1][1] - waypoints[j][1]
                        segment_distance = math.sqrt(dx*dx + dy*dy)
                        
                        if current_distance + segment_distance >= distance_traveled:
                            # このセグメント内
                            t = (distance_traveled - current_distance) / segment_distance
                            x = waypoints[j][0] + t * dx
                            y = waypoints[j][1] + t * dy
                            direction = math.atan2(dy, dx)
                            break
                        
                        current_distance += segment_distance
                    else:
                        # 最終地点
                        x, y = waypoints[-1]
                        direction = math.atan2(waypoints[-1][1] - waypoints[-2][1],
                                             waypoints[-1][0] - waypoints[-2][0])
                
                neighbors[agent_id] = {
                    "transform": {
                        "localTranslation": {
                            "x": x,
                            "y": y,
                            "z": 0.5
                        },
                        "localRotation": {
                            "EulerAngles": {
                                "x": 0.0,
                                "y": 0.0,
                                "z": math.degrees(direction)
                            }
                        },
                        "localTranslationSpeed": {
                            "x": veh["speed"] * math.cos(direction),
                            "y": veh["speed"] * math.sin(direction),
                            "z": 0.0
                        }
                    },
                    "kind": "vehicle",
                    "status": {"state": "driving", "maneuver": veh["type"]},
                    "assets": {},
                    "nearestDistance": math.sqrt(x*x + y*y),
                    "change": "Updated"
                }
        
        return {
            "timestamp": {
                "seconds": int(current_time),
                "nanos": int((current_time % 1) * 1e9)
            },
            "neighbors": neighbors
        }
    
    def send_cors_headers(self):
        """CORS ヘッダーを送信"""
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
    
    def log_message(self, format, *args):
        """ログメッセージの出力をカスタマイズ"""
        timestamp = time.strftime('%H:%M:%S')
        print(f"[{timestamp}] {format % args}")

class MockServer:
    """モックサーバー管理クラス"""
    
    def __init__(self):
        self.vehicle_server = None
        self.pedestrian_server = None
        self.vehicle_thread = None
        self.pedestrian_thread = None
    
    def start_servers(self):
        """モックサーバー起動"""
        try:
            # 車両用Edge モックサーバー (ポート 2237)
            self.vehicle_server = socketserver.TCPServer(("", 2237), MockArkTwinHandler)
            self.vehicle_thread = Thread(target=self.vehicle_server.serve_forever, daemon=True)
            self.vehicle_thread.start()
            print("車両用Edge モックサーバー開始: http://127.0.0.1:2237")
            
            # 歩行者用Edge モックサーバー (ポート 2238)
            self.pedestrian_server = socketserver.TCPServer(("", 2238), MockArkTwinHandler)
            self.pedestrian_thread = Thread(target=self.pedestrian_server.serve_forever, daemon=True)
            self.pedestrian_thread.start()
            print("歩行者用Edge モックサーバー開始: http://127.0.0.1:2238")
            
            return True
            
        except OSError as e:
            if "Address already in use" in str(e):
                print("警告: ポート 2237 または 2238 が既に使用中です")
                print("   実際のArkTwin Edgeが起動している可能性があります")
                print("   モックサーバーの起動をスキップします")
                return False
            else:
                print(f"サーバー起動エラー: {e}")
                return False
    
    def stop_servers(self):
        """モックサーバー停止"""
        if self.vehicle_server:
            self.vehicle_server.shutdown()
            print("車両用Edge モックサーバー停止")
        
        if self.pedestrian_server:
            self.pedestrian_server.shutdown()
            print("歩行者用Edge モックサーバー停止")

def serve_visualization_file():
    """可視化ファイル用の簡易HTTPサーバー"""
    class VisualizationHandler(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            # 現在のディレクトリをサーバーのルートに設定
            super().__init__(*args, directory=os.getcwd(), **kwargs)
        
        def end_headers(self):
            # CORS ヘッダーを追加
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
            self.send_header('Access-Control-Allow-Headers', 'Content-Type')
            super().end_headers()
    
    try:
        with socketserver.TCPServer(("", 8080), VisualizationHandler) as httpd:
            print("可視化用HTTPサーバー開始: http://127.0.0.1:8080")
            print("   可視化ページ: http://127.0.0.1:8080/visualization.html")
            httpd.serve_forever()
    except OSError as e:
        if "Address already in use" in str(e):
            print("警告: ポート 8080 が既に使用中です")
            print("   別のサーバーが起動している可能性があります")
        else:
            print(f"HTTPサーバー起動エラー: {e}")

def main():
    """メイン処理"""
    print("ArkTwin 可視化システム テストサーバー")
    print("=" * 50)
    
    # モックサーバー起動
    mock_server = MockServer()
    mock_started = mock_server.start_servers()
    
    if mock_started:
        print("\n交差点シミュレーションの説明:")
        print("   - 車両: 4台（直進・右折・左折）")
        print("   - 歩行者: 4人（横断歩道・歩道を移動）")
        print("   - 原点(0,0)は交差点の中心")
        print("   - リアルな交差点の動きをシミュレーション")
    
    print("\n可視化システムの使用方法:")
    print("   1. ブラウザで以下のURLのいずれかにアクセス:")
    print("      HTTPサーバー版: http://127.0.0.1:8080/visualization.html")
    print("      ローカルファイル版: file://" + os.path.abspath("visualization.html"))
    print("   2. 「接続開始」ボタンをクリック")
    print("   3. リアルタイムで位置情報が更新されます")
    
    print("\n注意事項:")
    print("   - モダンブラウザ（Chrome, Firefox, Edge等）を使用してください")
    print("   - ファイアウォールがある場合、ポート 2237, 2238 を許可してください")
    print("   - Ctrl+C で終了します")
    
    # 可視化ファイルをブラウザで開く
    visualization_path = os.path.abspath("visualization.html")
    if os.path.exists(visualization_path):
        print(f"\nブラウザで可視化ページを開いています...")
        webbrowser.open(f"file://{visualization_path}")
    
    try:
        # 簡易HTTPサーバーも起動（CORS対応）
        print("\nHTTPサーバーも起動します...")
        serve_thread = Thread(target=serve_visualization_file, daemon=True)
        serve_thread.start()
        
        print("\nテストサーバー起動完了!")
        print("   Ctrl+C で終了してください")
        
        # メインスレッドを維持
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n\nテストサーバーを停止中...")
        if mock_started:
            mock_server.stop_servers()
        print("停止完了")

if __name__ == "__main__":
    main()
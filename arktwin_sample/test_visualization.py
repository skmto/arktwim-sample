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
        """モックデータ生成"""
        current_time = time.time()
        elapsed = current_time - self.start_time
        
        neighbors = {}
        
        if port == 2237:  # 車両用Edge - 歩行者データを返す
            # 4人の歩行者のモックデータ
            for i in range(1, 5):
                agent_id = f"pedestrian-00{i}-mock-{int(current_time)}"
                # 時間経過で移動するアニメーション
                angle = (elapsed * 0.5 + i * math.pi / 2) % (2 * math.pi)
                radius = 8 + i * 2
                x = radius * math.cos(angle)
                y = radius * math.sin(angle)
                
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
                                "z": math.degrees(angle)
                            }
                        },
                        "localTranslationSpeed": {
                            "x": -radius * 0.5 * math.sin(angle),
                            "y": radius * 0.5 * math.cos(angle),
                            "z": 0.0
                        }
                    },
                    "kind": "pedestrian",
                    "status": {"state": "walking"},
                    "assets": {},
                    "nearestDistance": radius,
                    "change": "Updated"
                }
        
        elif port == 2238:  # 歩行者用Edge - 車両データを返す
            # 3台の車両のモックデータ
            for i in range(1, 4):
                agent_id = f"vehicle-00{i}-mock-{int(current_time)}"
                # 直線移動のアニメーション
                direction = (i - 2) * math.pi / 6  # -30°, 0°, 30°
                distance = (elapsed * 5) % 40 - 20  # -20m から 20m を往復
                x = distance * math.cos(direction)
                y = distance * math.sin(direction)
                
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
                            "x": 5 * math.cos(direction) * (1 if (elapsed * 5) % 80 < 40 else -1),
                            "y": 5 * math.sin(direction) * (1 if (elapsed * 5) % 80 < 40 else -1),
                            "z": 0.0
                        }
                    },
                    "kind": "vehicle",
                    "status": {"state": "driving"},
                    "assets": {},
                    "nearestDistance": abs(distance),
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
        print("\nモックデータの説明:")
        print("   - 車両: 3台が直線移動（往復）")
        print("   - 歩行者: 4人が円形軌道で移動")
        print("   - 位置は時間経過で自動的に変化します")
    
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
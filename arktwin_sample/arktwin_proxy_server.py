#!/usr/bin/env python3
"""
ArkTwin プロキシサーバー

フロントエンドとArkTwin Edge間のプロキシとして動作し、
CORS問題を解決しながらリアルタイムデータを提供する。

機能:
- ArkTwin Edge APIへのプロキシ
- WebSocket によるリアルタイム通信
- データキャッシュと配信
- CORS対応
"""

from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from flask_socketio import SocketIO, emit
import requests
import threading
import time
import json
import os
from datetime import datetime
import logging
import urllib3

# SSL警告を抑制
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ログ設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['SECRET_KEY'] = 'arktwin_visualization_secret'
CORS(app)

# SSL/TLS を使用しない設定でSocketIOを初期化
socketio = SocketIO(
    app, 
    cors_allowed_origins="*",
    async_mode='threading',  # threadingモードを明示的に指定
    logger=False,            # SocketIOのログを無効化
    engineio_logger=False    # Engine.IOのログを無効化
)

class ArkTwinProxy:
    """ArkTwin Edge API のプロキシクラス"""
    
    def __init__(self):
        # 設定
        self.vehicle_port = 2237
        self.pedestrian_port = 2238
        self.host = "127.0.0.1"
        self.update_interval = 0.2  # 0.2秒間隔
        
        # データストレージ
        self.vehicles = {}
        self.pedestrians = {}
        self.last_update = None
        self.is_running = False
        self.update_thread = None
        
        # 統計情報
        self.stats = {
            "total_updates": 0,
            "last_update_time": None,
            "vehicle_count": 0,
            "pedestrian_count": 0,
            "errors": []
        }
    
    def start_monitoring(self):
        """ArkTwin監視を開始"""
        if not self.is_running:
            self.is_running = True
            self.update_thread = threading.Thread(target=self._update_loop, daemon=True)
            self.update_thread.start()
            logger.info("ArkTwin監視を開始しました")
    
    def stop_monitoring(self):
        """ArkTwin監視を停止"""
        self.is_running = False
        if self.update_thread:
            self.update_thread.join(timeout=5)
        logger.info("ArkTwin監視を停止しました")
    
    def _update_loop(self):
        """データ更新ループ"""
        while self.is_running:
            try:
                self._fetch_all_data()
                self._emit_update()
                time.sleep(self.update_interval)
            except Exception as e:
                logger.error(f"データ更新エラー: {e}")
                self.stats["errors"].append({
                    "time": datetime.now().isoformat(),
                    "error": str(e)
                })
                # エラーが多すぎる場合は一時停止
                if len(self.stats["errors"]) > 10:
                    self.stats["errors"] = self.stats["errors"][-5:]  # 最新5件のみ保持
                time.sleep(5)  # エラー時は少し長めに待機
    
    def _fetch_all_data(self):
        """全データを取得"""
        timestamp = {
            "seconds": int(time.time()),
            "nanos": 0
        }
        
        # 車両データを取得（歩行者の近隣情報）
        try:
            vehicles_data = self._fetch_neighbors(self.vehicle_port, timestamp)
            if vehicles_data and "neighbors" in vehicles_data:
                # 歩行者の近隣情報（車両側から見た歩行者）
                for agent_id, agent_data in vehicles_data["neighbors"].items():
                    if agent_id.startswith("pedestrian") and self._validate_agent_data(agent_data):
                        self.pedestrians[agent_id] = self._process_agent_data(agent_id, agent_data)
        except Exception as e:
            logger.warning(f"車両側データ取得エラー: {e}")
        
        # 歩行者データを取得（車両の近隣情報）
        try:
            pedestrians_data = self._fetch_neighbors(self.pedestrian_port, timestamp)
            if pedestrians_data and "neighbors" in pedestrians_data:
                # 車両の近隣情報（歩行者側から見た車両）
                for agent_id, agent_data in pedestrians_data["neighbors"].items():
                    if agent_id.startswith("vehicle") and self._validate_agent_data(agent_data):
                        self.vehicles[agent_id] = self._process_agent_data(agent_id, agent_data)
        except Exception as e:
            logger.warning(f"歩行者側データ取得エラー: {e}")
        
        # 統計更新
        self.stats["total_updates"] += 1
        self.stats["last_update_time"] = datetime.now().isoformat()
        self.stats["vehicle_count"] = len(self.vehicles)
        self.stats["pedestrian_count"] = len(self.pedestrians)
        self.last_update = time.time()
    
    def _fetch_neighbors(self, port, timestamp):
        """指定ポートから近隣情報を取得"""
        url = f"http://{self.host}:{port}/api/edge/neighbors/_query"
        query = {
            "timestamp": timestamp,
            "neighborsNumber": 100,
            "changeDetection": False
        }
        
        # SSL検証を無効化し、タイムアウトを設定
        response = requests.post(
            url, 
            json=query, 
            timeout=5,
            verify=False,  # SSL証明書の検証を無効化
            headers={'Connection': 'close'}  # HTTP接続をクローズ
        )
        response.raise_for_status()
        return response.json()
    
    def _validate_agent_data(self, agent_data):
        """エージェントデータの妥当性チェック"""
        return (agent_data and 
                "transform" in agent_data and 
                "localTranslation" in agent_data["transform"] and
                all(k in agent_data["transform"]["localTranslation"] for k in ["x", "y", "z"]))
    
    def _process_agent_data(self, agent_id, agent_data):
        """エージェントデータを処理して標準形式に変換"""
        transform = agent_data["transform"]
        translation = transform["localTranslation"]
        
        return {
            "id": agent_id,
            "x": float(translation["x"]),
            "y": float(translation["y"]),
            "z": float(translation["z"]),
            "kind": agent_data.get("kind", "unknown"),
            "status": agent_data.get("status", {}),
            "lastUpdate": time.time(),
            "rotation": transform.get("localRotation", {}).get("EulerAngles", {"x": 0, "y": 0, "z": 0}),
            "speed": transform.get("localTranslationSpeed", {"x": 0, "y": 0, "z": 0})
        }
    
    def _emit_update(self):
        """WebSocket経由でデータ更新を送信"""
        data = {
            "timestamp": self.last_update,
            "vehicles": list(self.vehicles.values()),
            "pedestrians": list(self.pedestrians.values()),
            "stats": self.stats
        }
        socketio.emit('data_update', data)
    
    def get_current_data(self):
        """現在のデータを取得"""
        return {
            "timestamp": self.last_update,
            "vehicles": list(self.vehicles.values()),
            "pedestrians": list(self.pedestrians.values()),
            "stats": self.stats
        }

# プロキシインスタンス
proxy = ArkTwinProxy()

# REST API エンドポイント
@app.route('/')
def index():
    """インデックスページ"""
    return send_from_directory('.', 'visualization.html')

@app.route('/visualization.html')
def visualization():
    """可視化ページ"""
    return send_from_directory('.', 'visualization.html')

@app.route('/api/data')
def get_data():
    """現在のデータを取得"""
    return jsonify(proxy.get_current_data())

@app.route('/api/start', methods=['POST'])
def start_monitoring():
    """監視開始"""
    proxy.start_monitoring()
    return jsonify({"status": "started", "message": "ArkTwin監視を開始しました"})

@app.route('/api/stop', methods=['POST'])
def stop_monitoring():
    """監視停止"""
    proxy.stop_monitoring()
    return jsonify({"status": "stopped", "message": "ArkTwin監視を停止しました"})

@app.route('/api/config', methods=['GET', 'POST'])
def config():
    """設定の取得・更新"""
    if request.method == 'GET':
        return jsonify({
            "vehicle_port": proxy.vehicle_port,
            "pedestrian_port": proxy.pedestrian_port,
            "host": proxy.host,
            "update_interval": proxy.update_interval
        })
    
    elif request.method == 'POST':
        data = request.get_json()
        if 'vehicle_port' in data:
            proxy.vehicle_port = int(data['vehicle_port'])
        if 'pedestrian_port' in data:
            proxy.pedestrian_port = int(data['pedestrian_port'])
        if 'host' in data:
            proxy.host = str(data['host'])
        if 'update_interval' in data:
            proxy.update_interval = float(data['update_interval'])
        
        return jsonify({"status": "updated", "message": "設定を更新しました"})

@app.route('/api/stats')
def get_stats():
    """統計情報を取得"""
    return jsonify(proxy.stats)

# WebSocket イベント
@socketio.on('connect')
def handle_connect():
    """クライアント接続時"""
    logger.info('クライアントが接続しました')
    # 現在のデータを送信
    emit('data_update', proxy.get_current_data())

@socketio.on('disconnect')
def handle_disconnect():
    """クライアント切断時"""
    logger.info('クライアントが切断しました')

@socketio.on('start_monitoring')
def handle_start_monitoring():
    """監視開始要求"""
    proxy.start_monitoring()
    emit('status_update', {"status": "started", "message": "監視を開始しました"})

@socketio.on('stop_monitoring')
def handle_stop_monitoring():
    """監視停止要求"""
    proxy.stop_monitoring()
    emit('status_update', {"status": "stopped", "message": "監視を停止しました"})

def main():
    """メイン処理"""
    print("ArkTwin プロキシサーバー")
    print("=" * 50)
    
    # 可視化ファイルの存在確認
    if not os.path.exists('visualization.html'):
        print("警告: visualization.html が見つかりません")
        print("可視化UIは利用できません")
    
    port = 8091
    print(f"サーバー開始: http://127.0.0.1:{port}")
    print(f"可視化ページ: http://127.0.0.1:{port}/visualization.html")
    print(f"API エンドポイント: http://127.0.0.1:{port}/api/data")
    print("Ctrl+C で終了")
    
    try:
        # SSL/TLSを使用せず、HTTP専用で起動
        socketio.run(
            app, 
            host='127.0.0.1', 
            port=port, 
            debug=False,
            use_reloader=False,  # リロード機能を無効化
            allow_unsafe_werkzeug=True  # 本番環境でない旨を明示
        )
    except KeyboardInterrupt:
        print("\nサーバーを停止します...")
        proxy.stop_monitoring()

if __name__ == "__main__":
    main()
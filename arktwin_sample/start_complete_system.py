#!/usr/bin/env python3
"""
ArkTwin 完全システム起動スクリプト

以下のコンポーネントを統合起動します:
1. ArkTwin プロキシサーバー (ポート 5000)
2. モックArkTwin Edge (ポート 2237, 2238) - オプション
3. ブラウザで可視化UI (visualization_v2.html)

使用方法:
  python start_complete_system.py [--mock]
  
  --mock: モックサーバーも同時起動
"""

import argparse
import webbrowser
import time
import threading
import signal
import sys
import os
import subprocess
from test_visualization import MockServer

def start_proxy_server():
    """プロキシサーバーを起動"""
    print("プロキシサーバーを起動中...")
    from arktwin_proxy_server import main
    main()

def start_mock_servers():
    """モックサーバーを起動"""
    print("モックサーバーを起動中...")
    mock_server = MockServer()
    if mock_server.start_servers():
        print("モックサーバーが正常に起動しました")
        return mock_server
    else:
        print("モックサーバーの起動に失敗しました")
        return None

def open_browser():
    """ブラウザで可視化UIを開く"""
    time.sleep(3)  # サーバーの起動を待つ
    url = "http://127.0.0.1:5000/visualization_v2.html"
    print(f"ブラウザで可視化UIを開いています: {url}")
    webbrowser.open(url)

def signal_handler(signum, frame):
    """シグナルハンドラー"""
    print("\n\nシステムを停止中...")
    sys.exit(0)

def main():
    """メイン処理"""
    parser = argparse.ArgumentParser(description='ArkTwin 完全システム起動')
    parser.add_argument('--mock', action='store_true', 
                       help='モックサーバーも同時起動')
    args = parser.parse_args()
    
    print("ArkTwin 完全システム起動")
    print("=" * 50)
    
    # シグナルハンドラー設定
    signal.signal(signal.SIGINT, signal_handler)
    
    mock_server = None
    
    try:
        # モックサーバー起動（オプション）
        if args.mock:
            mock_server = start_mock_servers()
            if not mock_server:
                print("警告: モックサーバーが起動できませんでした")
                print("実際のArkTwin Edgeが起動している可能性があります")
        
        # ブラウザを別スレッドで起動
        browser_thread = threading.Thread(target=open_browser, daemon=True)
        browser_thread.start()
        
        print("\nシステム起動中...")
        print("以下のコンポーネントが利用可能です:")
        print("  - プロキシサーバー: http://127.0.0.1:5000")
        print("  - 可視化UI: http://127.0.0.1:5000/visualization_v2.html")
        print("  - REST API: http://127.0.0.1:5000/api/data")
        
        if args.mock:
            print("  - モック車両Edge: http://127.0.0.1:2237")
            print("  - モック歩行者Edge: http://127.0.0.1:2238")
        
        print("\nCtrl+C で終了")
        print("=" * 50)
        
        # プロキシサーバー起動（メインスレッド）
        start_proxy_server()
        
    except KeyboardInterrupt:
        print("\n\nシステムを停止中...")
    except Exception as e:
        print(f"エラー: {e}")
    finally:
        # クリーンアップ
        if mock_server:
            mock_server.stop_servers()
        print("システム停止完了")

if __name__ == "__main__":
    main()
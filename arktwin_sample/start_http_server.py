#!/usr/bin/env python3
"""
ArkTwin 可視化システム用HTTPサーバー

visualization.html をHTTPサーバー上で動作させるためのシンプルなサーバー。
CORS対応により、ブラウザからのAPI呼び出しが可能。
"""

import http.server
import socketserver
import os
import webbrowser
import time

class CORSHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    """CORS対応のHTTPリクエストハンドラー"""
    
    def end_headers(self):
        """レスポンスヘッダーにCORSヘッダーを追加"""
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()
    
    def do_OPTIONS(self):
        """CORS プリフライト要求の処理"""
        self.send_response(200)
        self.end_headers()

def main():
    """メイン処理"""
    # 利用可能なポートを見つける
    for PORT in range(8080, 8100):
        try:
            # ポートの可用性をテスト
            with socketserver.TCPServer(("", PORT), CORSHTTPRequestHandler) as test_server:
                break
        except OSError:
            continue
    else:
        print("エラー: 利用可能なポートが見つかりません (8080-8099)")
        return
    
    print("ArkTwin 可視化システム用HTTPサーバー")
    print("=" * 50)
    
    # 可視化ファイルの存在確認
    if not os.path.exists('visualization.html'):
        print("エラー: visualization.html が見つかりません")
        print("このスクリプトは visualization.html と同じディレクトリで実行してください")
        return
    
    try:
        # HTTPサーバー開始
        with socketserver.TCPServer(("", PORT), CORSHTTPRequestHandler) as httpd:
            print(f"HTTPサーバー開始: http://127.0.0.1:{PORT}")
            print(f"可視化ページ: http://127.0.0.1:{PORT}/visualization.html")
            print("\n使用方法:")
            print("1. ブラウザで可視化ページを開く")
            print("2. ArkTwin Edgeまたはtest_visualization.pyを起動")
            print("3. 「接続開始」ボタンをクリック")
            print("\nCtrl+C で終了")
            
            # ブラウザで自動的に開く
            time.sleep(0.5)
            webbrowser.open(f'http://127.0.0.1:{PORT}/visualization.html')
            
            # サーバー実行
            httpd.serve_forever()
            
    except OSError as e:
        if "Address already in use" in str(e):
            print(f"エラー: ポート {PORT} が既に使用中です")
            print("他のサーバーを停止してから再度実行してください")
        else:
            print(f"サーバー起動エラー: {e}")
    except KeyboardInterrupt:
        print("\nHTTPサーバーを停止しました")

if __name__ == "__main__":
    main()
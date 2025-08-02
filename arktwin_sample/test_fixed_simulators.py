#!/usr/bin/env python3
"""
固定シミュレーターの動作テストスクリプト

車両シミュレーターと歩行者シミュレーターの動作を確認する。
両方のシミュレーターをバックグラウンドで実行し、出力を確認する。
"""

import subprocess
import time
import sys
import os
import signal

def run_test():
    """両方のシミュレーターの簡易テストを実行
    
    車両シミュレーターと歩行者シミュレーターを同時に実行し、
    10秒間動作させた後で出力を収集して確認する。
    """
    # テスト開始のメッセージを表示
    print("=== ArkTwin 固定シミュレーターテスト ===")
    
    # 車両シミュレーターをバックグラウンドで開始
    print("車両シミュレーターを開始中...")
    # 車両シミュレータープロセスを作成（出力をキャプチャ）
    vehicle_proc = subprocess.Popen(
        [sys.executable, "vehicle_simulator.py"],
        cwd=os.getcwd(),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    # 車両シミュレーターの起動を少し待つ
    time.sleep(3)
    
    # 歩行者シミュレーターをバックグラウンドで開始
    print("歩行者シミュレーターを開始中...")
    # 歩行者シミュレータープロセスを作成（出力をキャプチャ）
    pedestrian_proc = subprocess.Popen(
        [sys.executable, "pedestrian_simulator.py"],
        cwd=os.getcwd(),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    try:
        # 10秒間シミュレーターを実行
        print("シミュレーターを10秒間実行中...")
        time.sleep(10)
        
        # 車両シミュレーターの出力を取得
        print("\n=== 車両シミュレーター出力 ===")
        vehicle_proc.terminate()  # プロセスを終了
        vehicle_stdout, vehicle_stderr = vehicle_proc.communicate(timeout=5)
        print(vehicle_stdout)
        if vehicle_stderr:
            print("エラー出力:", vehicle_stderr)
        
        # 歩行者シミュレーターの出力を取得
        print("\n=== 歩行者シミュレーター出力 ===")
        pedestrian_proc.terminate()  # プロセスを終了
        pedestrian_stdout, pedestrian_stderr = pedestrian_proc.communicate(timeout=5)
        print(pedestrian_stdout)
        if pedestrian_stderr:
            print("エラー出力:", pedestrian_stderr)
            
    except KeyboardInterrupt:
        print("\nテストが中断されました")
    except Exception as e:
        print(f"テストエラー: {e}")
    finally:
        # プロセスのクリーンアップ処理
        # 車両シミュレータープロセスの終了処理
        try:
            vehicle_proc.terminate()  # 穏やかな終了を試行
            vehicle_proc.wait(timeout=2)
        except:
            try:
                vehicle_proc.kill()  # 強制終了を試行
            except:
                pass  # どちらも失敗した場合は無視
                
        # 歩行者シミュレータープロセスの終了処理
        try:
            pedestrian_proc.terminate()  # 穏やかな終了を試行
            pedestrian_proc.wait(timeout=2)
        except:
            try:
                pedestrian_proc.kill()  # 強制終了を試行
            except:
                pass  # どちらも失敗した場合は無視
        
        print("テスト完了")

if __name__ == "__main__":
    # メイン処理: シミュレーターテストを実行
    run_test()
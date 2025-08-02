#!/bin/bash
# ArkTwin Sample Execution Script for Linux/macOS
# このスクリプトはArkTwinサンプルを実行します

echo "ArkTwin Sample Launcher"
echo "======================="

# ArkTwinのビルドディレクトリを確認
ARKTWIN_ROOT="$(dirname "$0")/../arktwin/arktwin"
if [ ! -d "$ARKTWIN_ROOT" ]; then
    echo "Error: ArkTwinプロジェクトが見つかりません: $ARKTWIN_ROOT"
    echo "まずArkTwinをビルドしてください。"
    echo "cd arktwin && sbt center/assembly edge/assembly"
    exit 1
fi

# JARファイルの確認
CENTER_JAR=$(find "$ARKTWIN_ROOT/center/target" -name "arktwin-center.jar" -type f 2>/dev/null | head -n 1)
EDGE_JAR=$(find "$ARKTWIN_ROOT/edge/target" -name "arktwin-edge.jar" -type f 2>/dev/null | head -n 1)

if [ ! -f "$CENTER_JAR" ]; then
    echo "Error: arktwin-center.jar が見つかりません"
    echo "cd arktwin && sbt center/assembly を実行してください"
    exit 1
fi

if [ ! -f "$EDGE_JAR" ]; then
    echo "Error: arktwin-edge.jar が見つかりません"
    echo "cd arktwin && sbt edge/assembly を実行してください"
    exit 1
fi

echo "JARファイルが見つかりました:"
echo "Center: $CENTER_JAR"
echo "Edge: $EDGE_JAR"
echo

# Python依存関係をインストール
echo "Python依存関係をインストール中..."
pip3 install -r requirements.txt
if [ $? -ne 0 ]; then
    echo "Warning: pip install failed. Python3とpipがインストールされていることを確認してください。"
fi

echo
echo "サンプル実行を開始します..."
echo "各コンポーネントは別々のターミナルで起動されます。"
echo "停止するには各ターミナルでCtrl+Cを押してください。"
echo

# ターミナルエミュレーターを検出
if command -v gnome-terminal >/dev/null 2>&1; then
    TERMINAL="gnome-terminal --"
elif command -v xterm >/dev/null 2>&1; then
    TERMINAL="xterm -e"
elif command -v konsole >/dev/null 2>&1; then
    TERMINAL="konsole -e"
else
    echo "Error: ターミナルエミュレーターが見つかりません"
    echo "手動で以下のコマンドを異なるターミナルで実行してください:"
    echo
    echo "1. java -Dconfig.file=center.conf -XX:+UseZGC -XX:+ZGenerational -jar \"$CENTER_JAR\""
    echo "2. java -Dconfig.file=edge-vehicle.conf -XX:+UseZGC -XX:+ZGenerational -jar \"$EDGE_JAR\""
    echo "3. java -Dconfig.file=edge-pedestrian.conf -XX:+UseZGC -XX:+ZGenerational -jar \"$EDGE_JAR\""
    echo "4. python3 vehicle_simulator.py"
    echo "5. python3 pedestrian_simulator.py"
    exit 1
fi

# 1. ArkTwin Center起動
echo "1. ArkTwin Center を起動中..."
$TERMINAL bash -c "cd '$(pwd)' && java -Dconfig.file=center.conf -XX:+UseZGC -XX:+ZGenerational -jar '$CENTER_JAR'; read -p 'Press Enter to close...'" &

# Centerが起動するまで待機
echo "Centerの起動を待機中（5秒）..."
sleep 5

# 2. ArkTwin Edge (Vehicle) 起動
echo "2. ArkTwin Edge (Vehicle) を起動中..."
$TERMINAL bash -c "cd '$(pwd)' && java -Dconfig.file=edge-vehicle.conf -XX:+UseZGC -XX:+ZGenerational -jar '$EDGE_JAR'; read -p 'Press Enter to close...'" &

# 3. ArkTwin Edge (Pedestrian) 起動
echo "3. ArkTwin Edge (Pedestrian) を起動中..."
$TERMINAL bash -c "cd '$(pwd)' && java -Dconfig.file=edge-pedestrian.conf -XX:+UseZGC -XX:+ZGenerational -jar '$EDGE_JAR'; read -p 'Press Enter to close...'" &

# Edgeが起動するまで待機
echo "Edgeの起動を待機中（5秒）..."
sleep 5

# 4. 車両シミュレーター起動
echo "4. 車両シミュレーター を起動中..."
$TERMINAL bash -c "cd '$(pwd)' && python3 vehicle_simulator.py; read -p 'Press Enter to close...'" &

# 5. 歩行者シミュレーター起動
echo "5. 歩行者シミュレーター を起動中..."
$TERMINAL bash -c "cd '$(pwd)' && python3 pedestrian_simulator.py; read -p 'Press Enter to close...'" &

echo
echo "すべてのコンポーネントが起動されました！"
echo
echo "起動されたコンポーネント:"
echo "- ArkTwin Center (Port 2236)"
echo "- ArkTwin Edge - Vehicle (Port 2237)"
echo "- ArkTwin Edge - Pedestrian (Port 2238)"
echo "- Vehicle Simulator"
echo "- Pedestrian Simulator"
echo
echo "Web UI:"
echo "- ArkTwin Edge Vehicle API Docs: http://127.0.0.1:2237/docs/"
echo "- ArkTwin Edge Pedestrian API Docs: http://127.0.0.1:2238/docs/"
echo "- ArkTwin Edge Vehicle Viewer: http://127.0.0.1:2237/viewer/"
echo "- ArkTwin Edge Pedestrian Viewer: http://127.0.0.1:2238/viewer/"
echo
echo "停止するには各ターミナルでCtrl+Cを押してください。"
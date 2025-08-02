@echo off
REM ArkTwin Sample Execution Script for Windows
REM このスクリプトはArkTwinサンプルを実行します

echo ArkTwin Sample Launcher
echo =======================

REM JARファイルの確認
set CENTER_JAR=arktwin-center.jar
set EDGE_JAR=arktwin-edge.jar

if not exist "%CENTER_JAR%" (
    echo Error: arktwin-center.jar が見つかりません
    echo cd arktwin && sbt center/assembly を実行してください
    pause
    exit /b 1
)

if not exist "%EDGE_JAR%" (
    echo Error: arktwin-edge.jar が見つかりません  
    echo cd arktwin && sbt edge/assembly を実行してください
    pause
    exit /b 1
)

echo JARファイルが見つかりました:
echo Center: %CENTER_JAR%
echo Edge: %EDGE_JAR%
echo.

REM Python依存関係をインストール
echo Python依存関係をインストール中...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo Warning: pip install failed. Pythonとpipがインストールされていることを確認してください。
)

echo.
echo サンプル実行を開始します...
echo 各コンポーネントは別々のターミナルで起動されます。
echo 停止するには各ターミナルでCtrl+Cを押してください。
echo.

REM 1. ArkTwin Center起動
echo 1. ArkTwin Center を起動中...
start "ArkTwin Center" cmd /k "java -Dconfig.file=center.conf -XX:+UseZGC -XX:+ZGenerational -jar "%CENTER_JAR%" && pause"

REM Centerが起動するまで待機
echo Centerの起動を待機中（5秒）...
timeout /t 5 /nobreak >nul

REM 2. ArkTwin Edge (Vehicle) 起動
echo 2. ArkTwin Edge (Vehicle) を起動中...
start "ArkTwin Edge - Vehicle" cmd /k "java -Dconfig.file=edge-vehicle.conf -XX:+UseZGC -XX:+ZGenerational -jar "%EDGE_JAR%" && pause"

REM 3. ArkTwin Edge (Pedestrian) 起動  
echo 3. ArkTwin Edge (Pedestrian) を起動中...
start "ArkTwin Edge - Pedestrian" cmd /k "java -Dconfig.file=edge-pedestrian.conf -XX:+UseZGC -XX:+ZGenerational -jar "%EDGE_JAR%" && pause"

REM Edgeが起動するまで待機
echo Edgeの起動を待機中（5秒）...
timeout /t 5 /nobreak >nul

REM 4. 車両シミュレーター起動
echo 4. 車両シミュレーター を起動中...
start "Vehicle Simulator" cmd /k "python vehicle_simulator.py && pause"

REM 5. 歩行者シミュレーター起動
echo 5. 歩行者シミュレーター を起動中...
start "Pedestrian Simulator" cmd /k "python pedestrian_simulator.py && pause"

echo.
echo すべてのコンポーネントが起動されました！
echo.
echo 起動されたコンポーネント:
echo - ArkTwin Center (Port 2236)
echo - ArkTwin Edge - Vehicle (Port 2237) 
echo - ArkTwin Edge - Pedestrian (Port 2238)
echo - Vehicle Simulator
echo - Pedestrian Simulator
echo.
echo Web UI:
echo - ArkTwin Edge Vehicle API Docs: http://127.0.0.1:2237/docs/
echo - ArkTwin Edge Pedestrian API Docs: http://127.0.0.1:2238/docs/
echo - ArkTwin Edge Vehicle Viewer: http://127.0.0.1:2237/viewer/
echo - ArkTwin Edge Pedestrian Viewer: http://127.0.0.1:2238/viewer/
echo.
echo 停止するには各ターミナルでCtrl+Cを押してください。
pause
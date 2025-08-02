@echo off
REM ArkTwin Sample Execution Script for Windows
REM ���̃X�N���v�g��ArkTwin�T���v�������s���܂�

echo ArkTwin Sample Launcher
echo =======================

REM JAR�t�@�C���̊m�F
set CENTER_JAR=arktwin-center.jar
set EDGE_JAR=arktwin-edge.jar

if not exist "%CENTER_JAR%" (
    echo Error: arktwin-center.jar ��������܂���
    echo cd arktwin && sbt center/assembly �����s���Ă�������
    pause
    exit /b 1
)

if not exist "%EDGE_JAR%" (
    echo Error: arktwin-edge.jar ��������܂���  
    echo cd arktwin && sbt edge/assembly �����s���Ă�������
    pause
    exit /b 1
)

echo JAR�t�@�C����������܂���:
echo Center: %CENTER_JAR%
echo Edge: %EDGE_JAR%
echo.

REM Python�ˑ��֌W���C���X�g�[��
echo Python�ˑ��֌W���C���X�g�[����...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo Warning: pip install failed. Python��pip���C���X�g�[������Ă��邱�Ƃ��m�F���Ă��������B
)

echo.
echo �T���v�����s���J�n���܂�...
echo �e�R���|�[�l���g�͕ʁX�̃^�[�~�i���ŋN������܂��B
echo ��~����ɂ͊e�^�[�~�i����Ctrl+C�������Ă��������B
echo.

REM 1. ArkTwin Center�N��
echo 1. ArkTwin Center ���N����...
start "ArkTwin Center" cmd /k "java -Dconfig.file=center.conf -XX:+UseZGC -XX:+ZGenerational -jar "%CENTER_JAR%" && pause"

REM Center���N������܂őҋ@
echo Center�̋N����ҋ@���i5�b�j...
timeout /t 5 /nobreak >nul

REM 2. ArkTwin Edge (Vehicle) �N��
echo 2. ArkTwin Edge (Vehicle) ���N����...
start "ArkTwin Edge - Vehicle" cmd /k "java -Dconfig.file=edge-vehicle.conf -XX:+UseZGC -XX:+ZGenerational -jar "%EDGE_JAR%" && pause"

REM 3. ArkTwin Edge (Pedestrian) �N��  
echo 3. ArkTwin Edge (Pedestrian) ���N����...
start "ArkTwin Edge - Pedestrian" cmd /k "java -Dconfig.file=edge-pedestrian.conf -XX:+UseZGC -XX:+ZGenerational -jar "%EDGE_JAR%" && pause"

REM Edge���N������܂őҋ@
echo Edge�̋N����ҋ@���i5�b�j...
timeout /t 5 /nobreak >nul

REM 4. �ԗ��V�~�����[�^�[�N��
echo 4. �ԗ��V�~�����[�^�[ ���N����...
start "Vehicle Simulator" cmd /k "python vehicle_simulator.py && pause"

REM 5. ���s�҃V�~�����[�^�[�N��
echo 5. ���s�҃V�~�����[�^�[ ���N����...
start "Pedestrian Simulator" cmd /k "python pedestrian_simulator.py && pause"

echo.
echo ���ׂẴR���|�[�l���g���N������܂����I
echo.
echo �N�����ꂽ�R���|�[�l���g:
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
echo ��~����ɂ͊e�^�[�~�i����Ctrl+C�������Ă��������B
pause
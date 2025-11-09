# Raspberry Pi 5 수학 방정식 그래프 햅틱 피드백 시스템

라즈베리파이 5에서 실행되는 **스테레오 비전 기반 3D 손 추적**과 **수학 그래프 햅틱 피드백** 시스템입니다.

---

## 🔄 CI/CD

- � **수학 방정식 입력**: y = f(x) 형태의 방정식을 테이블 위 3D 그래프로 변환
- 📷 **단일 손 3D 추적**: 스테레오 비전으로 한 손의 3D 좌표를 실시간 추적
- �️ **좌표평면 매핑**: 카메라 인식 범위를 테이블 위 좌표평면으로 사용
- 📳 **햅틱 피드백**: 손가락이 그래프에 닿으면 진동모터로 촉각 피드백
- ⌨️ **실시간 방정식 변경**: 키보드로 즉시 다른 그래프로 전환 가능

## 📋 목차

- [빠른 시작](#-빠른-시작)
- [시스템 개요](#-시스템-개요)
- [설치 방법](#-설치-방법)
- [사용 방법](#-사용-방법)
- [모듈 설명](#-모듈-설명)
- [설정 커스터마이징](#-설정-커스터마이징)
- [문제 해결](#-문제-해결)

---

## 🚀 빠른 시작

```bash
# 1. 캘리브레이션 (최초 1회)
python examples/calibrate_cameras.py

# 2. 메인 프로그램 실행
python main.py

# 3. 방정식 선택 (1~5)
# 예: 1 (y = x²/100 포물선)

# 4. 손을 카메라 앞에 위치
# 5. 검지손가락을 테이블 위로 내림
# 6. 그래프 선을 따라 이동하며 진동 체험!
```

---

## 🌟 시스템 개요

### 작동 원리

```
┌─────────────────────────────────────────────────────────┐
│  1. 사용자가 수학 방정식 입력                            │
│     예: y = x²/100                                       │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│  2. 테이블 위 좌표평면에 3D 그래프 생성                  │
│     X축: -300 ~ +300mm (좌우)                           │
│     Z축:  200 ~ 800mm  (깊이)                           │
│     Y축:  200mm (테이블 높이)                           │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│  3. 스테레오 카메라로 손 3D 추적                         │
│     검지손가락 끝: (x, y, z) mm 단위                     │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│  4. 햅틱 피드백 판단                                     │
│     ✓ 손가락이 테이블에 닿음 (y ≥ 200mm)                │
│     ✓ 그래프에 접촉 (거리 ≤ 30mm)                        │
│     → 진동모터 작동!                                     │
└─────────────────────────────────────────────────────────┘
```

### 좌표계

```
테이블 위 좌표평면 (카메라 시점):
        
        Z축 (깊이) ↑
                   |
    800mm ---------+--------- 
                   |         
    600mm ---------+---------  그래프 영역
                   | \       
    400mm ---------+--\------  
                   |   포물선
    200mm ---------+----------
                   |
        X축 ← -----+------ → X축
             -300  0  +300mm
```

### 사용 예시

**시각 장애인을 위한 수학 교육:**
- 함수의 형태를 손으로 직접 느끼며 학습
- y=x², y=sin(x) 등 다양한 그래프 체험
- 미분/적분 개념 (기울기 변화) 촉각으로 이해

---

## 🖥️ 시스템 요구사항

- **하드웨어**:
  - ✅ Raspberry Pi 5
  - ✅ 스테레오 카메라 2개 (USB 또는 CSI)
  - ✅ 진동모터 1개 (코인형 진동모터)
  - ✅ GPIO 18번 핀 연결
  - ⚠️ 체스보드 패턴 (9x6, 25mm, 캘리브레이션용)

- **소프트웨어**:
  - Raspberry Pi OS (Bookworm 이상)
  - Python 3.11+
  - OpenCV, Mediapipe, NumPy

---

## 📦 설치 방법
- [CI/CD](#cicd)
- [모듈 사용법](#모듈-사용법)
  - [1. 스테레오 카메라 캘리브레이션](#1-스테레오-카메라-캘리브레이션)
  - [2. 3D 손 추적](#2-3d-손-추적)
  - [3. 진동모터 제어](#3-진동모터-제어)
- [Docker 실행](#docker-실행)
- [프로젝트 구조](#프로젝트-구조)
- [설정](#설정)

## 🖥️ 시스템 요구사항

- **하드웨어**:
  - Raspberry Pi 5
  - 카메라 모듈 2개 (Raspberry Pi Camera Module 또는 USB 카메라)
  - 진동모터 (코인형 진동모터 또는 ERM 모터)
  - 모터 드라이버 (선택사항, 직접 GPIO 연결 가능)

- **소프트웨어**:
  - Raspberry Pi OS (Bookworm 이상)
  - Docker (선택사항)
  - Python 3.11+

## 📦 설치 방법

### 방법 1: 직접 설치 (권장)

```bash
# 리포지토리 클론
git clone https://github.com/repryty/hackerton.git
cd hackerton

# 의존성 설치
pip install -e .

# 또는 개별 패키지 설치
pip install opencv-python mediapipe numpy pyyaml RPi.GPIO
```

### 방법 2: Docker 사용

```bash
# 리포지토리 클론
git clone https://github.com/repryty/hackerton.git
cd hackerton

# 사전 빌드된 이미지 사용
docker pull ghcr.io/repryty/hackerton:latest

# 또는 직접 빌드
docker build -t hackerton:latest .

# Docker 컨테이너 실행
bash docker-run.sh
```

```bash
# 리포지토리 클론
git clone https://github.com/repryty/hackerton.git
cd hackerton

# 사전 빌드된 이미지 사용
docker pull ghcr.io/repryty/hackerton:latest

# Docker 컨테이너 실행
bash docker-run.sh
```

---

## 🎮 사용 방법

### 1단계: 캘리브레이션 (최초 1회)

```bash
python examples/calibrate_cameras.py
```

**진행 과정:**
1. 체스보드 패턴을 양쪽 카메라에 보이도록 위치
2. 다양한 각도와 거리에서 촬영
3. **스페이스바**로 이미지 캡처 (총 20장)
4. 자동 캘리브레이션 수행
5. `data/stereo_calibration.pkl` 파일 생성 확인

### 2단계: 메인 프로그램 실행

```bash
python main.py
```

**방정식 선택:**
```
사용 가능한 방정식:
  1: y = x^2 / 100          # 포물선
  2: y = sin(x/50) * 100    # 사인파
  3: y = abs(x) / 2         # V자
  4: y = -x^2 / 100 + 200   # 역포물선
  5: y = cos(x/30) * 80     # 코사인파
  0: 방정식 없음 (테스트)

방정식을 선택하세요 (0-5): 1  ← 입력
```

### 3단계: 그래프 체험

1. **손 위치**: 양쪽 카메라에 한 손이 모두 보이도록 위치
2. **테이블 접촉**: 검지손가락을 테이블 위로 내림 (y ≥ 200mm)
3. **그래프 탐색**: 손가락을 좌우로 움직이며 그래프 선 찾기
4. **햅틱 피드백**: 그래프에 닿으면 **진동 발생!** ████████
5. **실시간 변경**: 키보드 1~5번으로 다른 방정식 체험

### 키보드 단축키

| 키 | 기능 |
|---|---|
| **1** | y = x²/100 (포물선) |
| **2** | y = sin(x/50) * 100 (사인파) |
| **3** | y = abs(x) / 2 (V자) |
| **4** | y = -x²/100 + 200 (역포물선) |
| **5** | y = cos(x/30) * 80 (코사인파) |
| **0** | 그래프 제거 |
| **ESC** | 프로그램 종료 |

### 화면 정보

```
┌─────────────────────────────────┐
│ FPS: 28.3                        │
│ Equation: y = x^2 / 100          │ ← 현재 방정식
│ Table Height: 200.0 mm           │
│ Motor: VIBRATING!                │ ← 진동 상태
│                                   │
│ Index Finger Tip:                │
│   Pos: (45.2, 205.3, 432.1)     │ ← 3D 좌표
│   Graph Dist: 8.5 mm             │ ← 거리
│   Status: TOUCHING GRAPH!        │ ← 접촉!
└─────────────────────────────────┘
```

---

## 📚 모듈 설명

### 주요 모듈

1. **`main.py`**: 메인 애플리케이션
   - 수학 방정식 → 3D 그래프 변환
   - 손 추적 및 햅틱 피드백 제어
   - 실시간 방정식 변경

2. **`modules/hand_tracker_3d.py`**: 3D 손 추적
   - Mediapipe 기반 손 랜드마크 감지
   - 스테레오 삼각측량으로 3D 좌표 계산
   - 단일 손 모드 지원

3. **`modules/stereo_calibration.py`**: 스테레오 캘리브레이션
   - 카메라 간 위치 관계 계산
   - 이미지 왜곡 보정 및 정렬
   - 3D 복원을 위한 Q 행렬 생성

4. **`modules/vibration_motor.py`**: 진동모터 제어
   - GPIO PWM 제어
   - 진동 강도 조절 (0~100%)
   - 다양한 진동 패턴 지원

### 상세 문서

- **[USAGE_GUIDE.md](USAGE_GUIDE.md)**: 종합 사용 가이드
  - 좌표계 상세 설명
  - 설정 커스터마이징 방법
  - 문제 해결 가이드
  - 응용 아이디어

- **[SYSTEM_FLOW.md](SYSTEM_FLOW.md)**: 시스템 작동 흐름
  - 전체 실행 흐름 다이어그램
  - 핵심 모듈별 상세 분석
  - 데이터 흐름도
  - 성능 특성 및 최적화

---

## ⚙️ 설정 커스터마이징

### `config/config.yaml`

```yaml
# 단일 손 추적 설정
hand_tracking:
  max_num_hands: 1  # 한 손만 추적
  min_detection_confidence: 0.5
  min_tracking_confidence: 0.5

# 진동모터 설정 (GPIO 18번)
motors:
  vibration_motors:
    hand_left:
      pin: 18
  pwm_frequency: 1000

# 카메라 인덱스
camera:
  left_camera_index: 0
  right_camera_index: 1
  resolution:
    width: 640
    height: 480
```

### `main.py` 내부 설정

```python
# 테이블 높이 조정
TABLE_HEIGHT_THRESHOLD = 200.0  # mm

# 좌표평면 범위 조정
def get_coordinate_bounds(...):
    x_min, x_max = -300, 300  # X축 범위
    z_min, z_max = 200, 800   # Z축 범위

# 그래프 두께 (감지 민감도)
virtual_graph = VirtualGraph(thickness=30.0)

# 진동 강도
motor_controller.start_all(intensity=80.0)  # 0~100%

# 커스텀 방정식 추가
equations = {
    '6': ('y = x^3 / 10000', lambda x: (x**3) / 10000),
    '7': ('y = log(abs(x)+1) * 50', lambda x: np.log(abs(x)+1) * 50),
}
```

---

## 🔧 문제 해결

### ❌ "캘리브레이션 데이터를 찾을 수 없습니다"

```bash
# 해결 방법
python examples/calibrate_cameras.py
# 체스보드로 20장 촬영
# → data/stereo_calibration.pkl 생성 확인
```

### ❌ "손이 감지되지 않습니다"

**원인 1: 카메라 시야**
```
→ 양쪽 카메라에 손이 모두 보이는지 확인
```

**원인 2: 조명 부족**
```
→ 밝은 조명 환경으로 변경
```

**원인 3: 민감도**
```yaml
# config.yaml 수정
hand_tracking:
  min_detection_confidence: 0.3  # 0.5 → 0.3으로 낮춤
```

### ❌ "진동모터가 작동하지 않습니다"

**하드웨어 체크:**
```bash
# GPIO 핀 확인
gpio readall

# 연결 확인
# - 빨간선: GPIO 18번 핀
# - 검은선: GND
# - 전원 공급: 3.3V (트랜지스터 권장)
```

**소프트웨어 체크:**
```yaml
# config.yaml
general:
  simulation_mode: false  # true면 모터 작동 안 함
```

### ❌ "카메라를 열 수 없습니다"

```bash
# 카메라 인덱스 확인
ls /dev/video*

# config.yaml에서 인덱스 변경
camera:
  left_camera_index: 0  # 숫자 변경 시도
  right_camera_index: 2 # 1 → 2 등
```

### ❌ "그래프가 예상과 다르게 그려집니다"

```python
# main.py 수정
def get_coordinate_bounds(...):
    # z_offset 값 조정
    z_min, z_max = 300, 900  # 더 멀리
    
# 또는 방정식 스케일 조정
lambda x: (x**2) / 200  # 나누는 값 증가 → 더 평평
lambda x: (x**2) / 50   # 나누는 값 감소 → 더 가파름
```

---

## � 성능 및 최적화

### 현재 성능

- **FPS**: 25~35 (환경에 따라 변동)
- **메모리**: ~160MB
- **지연시간**: ~30ms (카메라 → 진동)

### FPS 향상

```yaml
# config.yaml - 해상도 낮추기
camera:
  resolution:
    width: 320   # 640 → 320
    height: 240  # 480 → 240
# 예상 효과: FPS 40+ 달성
```

```python
# main.py - 그래프 점 개수 줄이기
virtual_graph.set_equation(..., num_points=50)  # 100 → 50
# 예상 효과: 거리 계산 2배 빠름
```

---

## 🎓 응용 아이디어

### 교육
- 시각 장애인을 위한 수학 그래프 교육
- 함수 형태 촉각 학습
- 미분/적분 개념 체험

### 게임
- 가상 미로 (그래프 = 벽)
- 리듬 게임 (타이밍에 그래프 터치)
- 3D 드로잉 앱

### 재활
- 손 재활 훈련 (정밀한 움직임)
- 공간 인지 능력 향상
- 촉각 피드백 기반 운동 치료

---

GitHub Actions를 통한 자동 Docker 빌드가 설정되어 있습니다.

- `main` 브랜치에 푸시하면 자동으로 ARM64 아키텍처용 Docker 이미지가 빌드됩니다
- 빌드된 이미지는 GitHub Container Registry에 자동으로 푸시됩니다
- 이미지 경로: `ghcr.io/repryty/hackerton:latest`

### 사전 빌드된 이미지 사용

```bash
# 최신 이미지 Pull
docker pull ghcr.io/repryty/hackerton:latest

# 이미지 실행
docker run -d \
  --privileged \
  --device /dev/video0 \
  --device /dev/video1 \
  -v $(pwd)/data:/app/data \
  ghcr.io/repryty/hackerton:latest
```

## 🚀 모듈 사용법

### 메인 프로그램: 가상 그래프 햅틱 피드백

메인 프로그램은 스테레오 카메라로 손을 추적하고, 검지손가락이 테이블에 닿아 가상 그래프에 접촉하면 진동모터를 작동시킵니다.

#### 실행 방법

```bash
# 먼저 캘리브레이션 수행 (한 번만 실행)
python examples/calibrate_cameras.py

# 메인 프로그램 실행
python main.py
```

#### 작동 원리

1. **손 추적**: 스테레오 카메라로 손의 3D 좌표를 실시간 추적
2. **테이블 감지**: 검지손가락 끝의 높이(y 좌표)가 설정된 테이블 높이 이하인지 확인
3. **그래프 충돌 감지**: 검지손가락이 가상 그래프 영역에 들어오는지 확인
4. **햅틱 피드백**: 조건이 만족되면 GPIO 진동모터 작동

#### 설정 사항

`main.py`에서 다음 값들을 조정할 수 있습니다:

```python
# 테이블 높이 임계값 (mm)
TABLE_HEIGHT_THRESHOLD = 200.0  # 이 값보다 크면 테이블에 닿은 것으로 판단

# 가상 그래프 정의 (x, y, z 좌표)
graph_points = [
    (-100, TABLE_HEIGHT_THRESHOLD, 500),  # 시작점
    (-50, TABLE_HEIGHT_THRESHOLD, 450),
    (0, TABLE_HEIGHT_THRESHOLD, 400),
    (50, TABLE_HEIGHT_THRESHOLD, 450),
    (100, TABLE_HEIGHT_THRESHOLD, 500),   # 끝점
]

# 그래프 두께 (mm)
virtual_graph = VirtualGraph(graph_points, thickness=30.0)
```

#### 화면 정보

프로그램 실행 시 화면에 다음 정보가 표시됩니다:
- FPS: 프레임 속도
- Table Height: 설정된 테이블 높이
- Motor: 진동모터 상태 (On/Off)
- 각 손의 검지손가락 위치
- 테이블 접촉 상태
- 그래프까지의 거리

#### 종료

`ESC` 키를 눌러 프로그램을 종료할 수 있습니다.

---

### 1. 스테레오 카메라 캘리브레이션

두 카메라 간의 위치 관계를 계산하고 저장합니다. **3D 손 추적을 사용하기 전에 반드시 수행해야 합니다.**

#### 캘리브레이션 실행

```bash
python examples/calibrate_cameras.py
```

#### 준비물
- 체스보드 패턴 (9x6 내부 코너, 25mm 정사각형)
- 출력 또는 모니터에 표시

#### 사용 방법
1. 스크립트 실행
2. 체스보드를 다양한 각도와 거리에서 촬영
3. 체스보드가 감지되면 **스페이스바**를 눌러 이미지 캡처
4. 20장 캡처 후 자동으로 캘리브레이션 수행
5. 결과가 `data/stereo_calibration.pkl`에 저장됨

#### 코드 예제

```python
from modules.stereo_calibration import StereoCalibration
import cv2

# StereoCalibration 객체 생성
calibrator = StereoCalibration(
    chessboard_size=(9, 6),  # 체스보드 내부 코너 수
    square_size=25.0,         # 체스보드 한 칸 크기 (mm)
    save_dir="data"
)

# 카메라 열기
cap_left = cv2.VideoCapture(0)
cap_right = cv2.VideoCapture(1)

# 캘리브레이션 이미지 캡처
images_left, images_right = calibrator.capture_calibration_images(
    cap_left, cap_right, num_images=20
)

# 캘리브레이션 수행
if calibrator.calibrate_cameras(images_left, images_right):
    # 결과 저장
    calibrator.save_calibration("stereo_calibration.pkl")
    calibrator.print_calibration_info()

# 카메라 해제
cap_left.release()
cap_right.release()
```

#### 주요 메서드

- `capture_calibration_images()`: 캘리브레이션용 이미지 캡처
- `calibrate_cameras()`: 스테레오 캘리브레이션 수행
- `save_calibration()`: 결과 저장
- `load_calibration()`: 저장된 결과 로드
- `rectify_images()`: 이미지를 rectify하여 스테레오 매칭 준비
- `get_baseline()`: 두 카메라 간 거리 반환

---

### 2. 3D 손 추적

Mediapipe와 스테레오 비전을 사용하여 손의 3D 위치를 실시간 추적합니다.

#### 데모 실행

```bash
python examples/hand_tracking_demo.py
```

#### 코드 예제

```python
from modules.stereo_calibration import StereoCalibration
from modules.hand_tracker_3d import HandTracker3D
import cv2

# 캘리브레이션 데이터 로드
calibrator = StereoCalibration(save_dir="data")
calibrator.load_calibration()

# HandTracker3D 초기화
tracker = HandTracker3D(
    stereo_calib=calibrator,
    max_num_hands=2,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5
)

# 카메라 열기
cap_left = cv2.VideoCapture(0)
cap_right = cv2.VideoCapture(1)

while True:
    ret_left, frame_left = cap_left.read()
    ret_right, frame_right = cap_right.read()
    
    # 3D 손 추적 수행
    hands_3d, output_left, output_right = tracker.process_frame(
        frame_left, frame_right
    )
    
    # 손 정보 사용
    for hand_data in hands_3d:
        # 손목 위치 (mm)
        wrist = tracker.get_wrist_position(hand_data)
        print(f"Wrist: {wrist}")
        
        # 손가락 끝 위치
        fingertips = tracker.get_fingertip_positions(hand_data)
        print(f"Index finger tip: {fingertips['INDEX']}")
        
        # 손가락이 펴져있는지 확인
        if tracker.is_finger_extended(hand_data, 'INDEX'):
            print("검지가 펴져 있습니다!")
    
    # 결과 표시
    cv2.imshow('Left', output_left)
    cv2.imshow('Right', output_right)
    
    if cv2.waitKey(1) & 0xFF == 27:  # ESC
        break

tracker.close()
cap_left.release()
cap_right.release()
```

#### 주요 메서드

- `process_frame()`: 스테레오 프레임 처리 및 3D 좌표 추출
- `get_wrist_position()`: 손목의 3D 위치 반환
- `get_fingertip_positions()`: 5개 손가락 끝의 3D 위치 반환
- `is_finger_extended()`: 특정 손가락이 펴져있는지 판단

#### 반환 데이터 형식

```python
hand_data = {
    'handedness': 'Left' or 'Right',
    'landmarks_3d': [(x, y, z), ...],  # 21개 랜드마크의 3D 좌표 (mm)
    'landmarks_2d_left': [(x, y), ...],  # 왼쪽 이미지의 2D 좌표
    'landmarks_2d_right': [(x, y), ...],  # 오른쪽 이미지의 2D 좌표
    'confidence': 0.98  # 감지 신뢰도
}
```

---

### 3. 모터 제어

### 3. 진동모터 제어

GPIO를 통해 진동모터를 제어하여 햅틱 피드백을 제공합니다.

#### 데모 실행

```bash
python examples/vibration_motor_demo.py
```

#### 단일 진동모터 제어 예제

```python
from modules.vibration_motor import VibrationMotor

# VibrationMotor 초기화
motor = VibrationMotor(
    pin=18,  # GPIO 18번 핀
    pwm_frequency=1000
)

# 진동 시작 (100% 강도)
motor.start(100)
time.sleep(1)
motor.stop()

# 짧은 펄스
motor.pulse(intensity=100, duration=0.2)

# 페이드 인/아웃
motor.fade_in(max_intensity=100, duration=2.0)
motor.fade_out(duration=2.0)

# 정리
motor.cleanup()
```

#### 다중 진동모터 제어 예제

```python
from modules.vibration_motor import VibrationMotorController

# 모터 핀 설정
motor_pins = {
    'hand_left': 18,
    'hand_right': 23
}

# VibrationMotorController 초기화
controller = VibrationMotorController(
    motor_pins=motor_pins,
    pwm_frequency=1000
)

# 개별 모터 제어
controller.pulse('hand_left', 100, 0.3)

# 모든 모터 동시 제어
controller.start_all(100)
time.sleep(1)
controller.stop_all()

# 순차 시퀀스
sequence = [
    {'motor': 'hand_left', 'intensity': 100, 'duration': 0.2},
    {'motor': 'hand_right', 'intensity': 100, 'duration': 0.2}
]
controller.pulse_sequence(sequence)

# 정리
controller.cleanup()
```

#### 미리 정의된 진동 패턴

```python
from modules.vibration_motor import VibrationMotor, VIBRATION_PATTERNS

motor = VibrationMotor(pin=18)

# 사용 가능한 패턴
# - short_pulse: 짧은 진동
# - double_pulse: 두 번 진동
# - triple_pulse: 세 번 진동
# - long_pulse: 긴 진동
# - fade: 페이드 인/아웃
# - heartbeat: 심장박동 패턴
# - sos: SOS 신호

motor.vibrate_pattern(VIBRATION_PATTERNS['heartbeat'])
motor.vibrate_pattern(VIBRATION_PATTERNS['double_pulse'])
```

#### 햅틱 피드백 시나리오

```python
# 버튼 클릭 피드백
controller.pulse('hand_right', 80, 0.05)

# 성공 알림
controller.vibrate_pattern_all(VIBRATION_PATTERNS['double_pulse'])

# 오류 알림
controller.vibrate_pattern_all(VIBRATION_PATTERNS['triple_pulse'])

# 거리 피드백 (가까워질수록 강해짐)
distance = 50  # cm
intensity = max(0, 100 - distance)
controller.start_all(intensity)

# 방향 안내
for _ in range(3):
    controller.pulse('hand_left', 100, 0.15)  # 왼쪽으로
    time.sleep(0.15)
```

#### 주요 메서드 (단일 모터)

- `start()`: 진동 시작
- `stop()`: 진동 정지
- `pulse()`: 일정 시간 진동
- `set_intensity()`: 진동 강도 설정 (0-100%)
- `fade_in()`: 서서히 진동 증가
- `fade_out()`: 서서히 진동 감소
- `vibrate_pattern()`: 진동 패턴 재생

#### 주요 메서드 (다중 모터)

- `start()`, `start_all()`: 특정/모든 모터 시작
- `stop()`, `stop_all()`: 특정/모든 모터 정지
- `pulse()`: 특정 모터 펄스
- `pulse_sequence()`: 순차 진동 시퀀스
- `vibrate_pattern_all()`: 모든 모터에 동기화 패턴 적용
- `set_intensity()`, `set_all_intensity()`: 진동 강도 설정

---

---

## 🐳 Docker 실행 (고급)

### 이미지 빌드

```bash
docker build -t hackerton:latest .
```

### 컨테이너 실행

```bash
# docker-run.sh 스크립트 사용 (권장)
bash docker-run.sh

# 또는 수동으로 실행
docker run -d \
  --privileged \
  --device /dev/gpiomem \
  --device /dev/video0 \
  --device /dev/video1 \
  -v /dev:/dev \
  -v /sys:/sys \
  -v $(pwd)/data:/app/data \
  -e DISPLAY=$DISPLAY \
  --name hackerton \
  hackerton:latest
```

### 주요 옵션 설명

- `--privileged`: GPIO 및 카메라 접근 권한
- `--device /dev/video0`, `/dev/video1`: 카메라 장치 마운트
- `-v $(pwd)/data:/app/data`: 캘리브레이션 데이터 영구 저장
- `-e DISPLAY=$DISPLAY`: GUI 표시 지원

---

## 📁 프로젝트 구조

```
hackerton/
├── main.py                     # ⭐ 메인: 수학 그래프 햅틱 피드백
├── modules/                    # 핵심 모듈
│   ├── hand_tracker_3d.py     #   - 3D 손 추적 (단일 손)
│   ├── stereo_calibration.py  #   - 스테레오 캘리브레이션
│   └── vibration_motor.py     #   - 진동모터 제어
├── examples/                   # 사용 예제
│   ├── calibrate_cameras.py   #   - 캘리브레이션 스크립트
│   ├── hand_tracking_demo.py  #   - 손 추적 데모
│   └── vibration_motor_demo.py#   - 진동모터 데모
├── config/
│   └── config.yaml            # 설정 파일
├── data/
│   └── stereo_calibration.pkl # 캘리브레이션 결과
├── USAGE_GUIDE.md             # 📖 종합 사용 가이드
├── SYSTEM_FLOW.md             # 📖 시스템 작동 흐름
└── README.md                  # 이 문서
```

---

## 📚 추가 자료

### 관련 문서
- **[USAGE_GUIDE.md](USAGE_GUIDE.md)**: 상세 사용법, 커스터마이징, 문제 해결
- **[SYSTEM_FLOW.md](SYSTEM_FLOW.md)**: 시스템 내부 작동 원리 상세 분석

### 예제 스크립트
```bash
# 개별 모듈 테스트
python examples/calibrate_cameras.py      # 캘리브레이션
python examples/hand_tracking_demo.py     # 손 추적만
python examples/vibration_motor_demo.py   # 진동모터만
```

### 라이브러리 문서
- [Mediapipe Hands](https://google.github.io/mediapipe/solutions/hands.html)
- [OpenCV Stereo Vision](https://docs.opencv.org/4.x/dd/d53/tutorial_py_depthmap.html)
- [RPi.GPIO Documentation](https://pypi.org/project/RPi.GPIO/)

---

## 📝 라이센스

이 프로젝트는 MIT 라이센스 하에 배포됩니다.

---

## 🤝 기여

버그 리포트, 기능 제안, Pull Request를 환영합니다!

**기여 아이디어:**
- 새로운 수학 방정식 추가
- 사용자 인터페이스 개선
- 성능 최적화
- 문서 개선

GitHub Repository: https://github.com/repryty/hackerton

---

## 📧 문의

질문이나 제안사항이 있으시면 GitHub Issues에 등록해주세요.

---

## 🎉 즐거운 체험 되세요!

**팁:** 처음 사용 시 간단한 방정식(1번: 포물선)부터 시작하세요!

```
   📐 수학의 아름다움을
   👆 손끝으로 느껴보세요
   ████████ 진동 피드백!
```

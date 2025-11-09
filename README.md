# Raspberry Pi 5 Stereo Vision & Haptic Feedback System

라즈베리파이 5에서 실행되는 스테레오 비전 및 햅틱 피드백 시스템입니다.
Docker 컨테이너로 패키징되어 있으며, 다음 기능을 제공합니다:

- 📷 **스테레오 카메라 캘리브레이션**: 두 카메라 간의 위치 관계 계산 및 저장
- 🤚 **3D 손 추적**: Mediapipe를 사용한 실시간 3D 손 위치 추적
- 📳 **진동모터 제어**: GPIO를 통한 햅틱 피드백 및 진동 패턴 제어

## 📋 목차

- [시스템 요구사항](#시스템-요구사항)
- [설치 방법](#설치-방법)
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

### 방법 1: Docker 사용 (권장)

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

### 방법 2: 직접 설치

```bash
# 리포지토리 클론
git clone https://github.com/repryty/hackerton.git
cd hackerton

# 의존성 설치
pip install -e .

# 또는 개별 패키지 설치
pip install opencv-python mediapipe numpy picamera2 RPi.GPIO
```

## 🔄 CI/CD

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

## 🐳 Docker 실행

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
├── .github/
│   └── workflows/
│       └── docker-build.yml    # GitHub Actions CI/CD
├── modules/                    # 핵심 모듈
│   ├── __init__.py
│   ├── stereo_calibration.py  # 스테레오 카메라 캘리브레이션
│   ├── hand_tracker_3d.py     # 3D 손 추적
│   ├── motor_controller.py    # DC/스테퍼 모터 제어 (레거시)
│   └── vibration_motor.py     # 진동모터 제어
├── examples/                   # 사용 예제
│   ├── calibrate_cameras.py   # 캘리브레이션 스크립트
│   ├── hand_tracking_demo.py  # 손 추적 데모
│   └── vibration_motor_demo.py # 진동모터 제어 데모
├── config/                     # 설정 파일
│   └── config.yaml
├── data/                       # 데이터 저장 디렉토리
│   └── stereo_calibration.pkl # 캘리브레이션 결과
├── Dockerfile                  # Docker 이미지 정의
├── docker-run.sh              # Docker 실행 스크립트
├── pyproject.toml             # Python 프로젝트 설정
├── main.py                    # 메인 애플리케이션
└── README.md                  # 이 문서
```

---

## ⚙️ 설정

`config/config.yaml` 파일에서 시스템 설정을 변경할 수 있습니다.

### 카메라 설정

```yaml
camera:
  left_camera_index: 0
  right_camera_index: 1
  resolution:
    width: 640
    height: 480
  fps: 30
```

### 진동모터 핀 설정

```yaml
motors:
  vibration_motors:
    hand_left:
      pin: 18
    hand_right:
      pin: 23
```

### 시뮬레이션 모드

GPIO 없이 테스트하려면:

```yaml
general:
  simulation_mode: true
```

---

## 🔧 트러블슈팅

### 카메라가 인식되지 않음

```bash
# 카메라 장치 확인
ls /dev/video*

# 카메라 테스트
v4l2-ctl --list-devices
```

### GPIO 권한 오류

```bash
# 사용자를 gpio 그룹에 추가
sudo usermod -aG gpio $USER

# 또는 Docker에서 --privileged 옵션 사용
```

### Mediapipe 설치 오류

```bash
# ARM 아키텍처용 Mediapipe 설치
pip install mediapipe==0.10.8
```

### 진동모터가 작동하지 않음

```bash
# GPIO 테스트
gpio readall

# 진동모터 연결 확인
# - 빨간선: GPIO 핀
# - 검은선: GND
# - 트랜지스터 또는 모터 드라이버 사용 권장 (3.3V 직접 연결 시 전류 부족 가능)
```

---

## 📝 라이센스

이 프로젝트는 MIT 라이센스 하에 배포됩니다.

---

## 🤝 기여

버그 리포트, 기능 제안, Pull Request를 환영합니다!

GitHub Repository: https://github.com/repryty/hackerton

---

## 📧 문의

질문이나 제안사항이 있으시면 이슈를 등록해주세요.

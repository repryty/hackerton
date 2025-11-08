# Raspberry Pi 5 Stereo Vision & Motor Control System

라즈베리파이 5에서 실행되는 스테레오 비전 및 모터 제어 시스템입니다.
Docker 컨테이너로 패키징되어 있으며, 다음 기능을 제공합니다:

- 📷 **스테레오 카메라 캘리브레이션**: 두 카메라 간의 위치 관계 계산 및 저장
- 🤚 **3D 손 추적**: Mediapipe를 사용한 실시간 3D 손 위치 추적
- ⚙️ **모터 제어**: GPIO를 통한 DC 모터 및 스테퍼 모터 제어

## 📋 목차

- [시스템 요구사항](#시스템-요구사항)
- [설치 방법](#설치-방법)
- [모듈 사용법](#모듈-사용법)
  - [1. 스테레오 카메라 캘리브레이션](#1-스테레오-카메라-캘리브레이션)
  - [2. 3D 손 추적](#2-3d-손-추적)
  - [3. 모터 제어](#3-모터-제어)
- [Docker 실행](#docker-실행)
- [프로젝트 구조](#프로젝트-구조)
- [설정](#설정)

## 🖥️ 시스템 요구사항

- **하드웨어**:
  - Raspberry Pi 5
  - 카메라 모듈 2개 (Raspberry Pi Camera Module 또는 USB 카메라)
  - 모터 드라이버 (L298N, TB6612, DRV8825 등)
  - DC 모터 또는 스테퍼 모터

- **소프트웨어**:
  - Raspberry Pi OS (Bookworm 이상)
  - Docker (선택사항)
  - Python 3.11+

## 📦 설치 방법

### 방법 1: Docker 사용 (권장)

```bash
# 리포지토리 클론
git clone <repository-url>
cd hackerton

# Docker 이미지 빌드
docker build -t hackerton:latest .

# Docker 컨테이너 실행
bash docker-run.sh
```

### 방법 2: 직접 설치

```bash
# 리포지토리 클론
git clone <repository-url>
cd hackerton

# 의존성 설치
pip install -e .

# 또는 개별 패키지 설치
pip install opencv-python mediapipe numpy picamera2 RPi.GPIO
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

GPIO를 통해 DC 모터 및 스테퍼 모터를 제어합니다.

#### 데모 실행

```bash
python examples/motor_control_demo.py
```

#### DC 모터 제어 예제

```python
from modules.motor_controller import MotorController

# 모터 설정
motor_configs = {
    'motor1': {
        'enable_pin': 18,  # PWM 핀 (GPIO)
        'in1_pin': 23,     # 방향 제어 핀 1
        'in2_pin': 24,     # 방향 제어 핀 2
        'type': 'l298n'
    }
}

# MotorController 초기화
controller = MotorController(
    motor_configs=motor_configs,
    pwm_frequency=1000
)

# 모터 제어
controller.set_motor_speed('motor1', speed=50, direction='forward')
time.sleep(2)
controller.stop_motor('motor1')

# 부드러운 가속
controller.set_motor_acceleration(
    'motor1',
    target_speed=80,
    direction='forward',
    accel_time=2.0
)

# 시퀀스 실행
sequence = [
    {'speed': 40, 'direction': 'forward', 'duration': 1.0},
    {'speed': 0, 'direction': 'stop', 'duration': 0.5},
    {'speed': 30, 'direction': 'backward', 'duration': 1.0}
]
controller.execute_motor_sequence('motor1', sequence)

# 정리
controller.cleanup()
```

#### 스테퍼 모터 제어 예제

```python
from modules.motor_controller import StepperMotorController

# StepperMotorController 초기화
stepper = StepperMotorController(
    step_pin=16,
    dir_pin=20,
    enable_pin=21,
    steps_per_revolution=200,
    microsteps=16
)

# 특정 스텝 수만큼 이동
stepper.move_steps(100, speed=1.0)

# 각도로 회전
stepper.move_angle(180, speed=1.0)

# 절대 위치로 이동
stepper.move_to_position(0, speed=1.5)

# 정리
stepper.cleanup()
```

#### 주요 메서드 (DC 모터)

- `set_motor_speed()`: 모터 속도 및 방향 설정
- `stop_motor()`: 특정 모터 정지
- `stop_all_motors()`: 모든 모터 정지
- `move_motor_for_duration()`: 일정 시간 동안 모터 동작
- `set_motor_acceleration()`: 부드러운 가속
- `execute_motor_sequence()`: 동작 시퀀스 실행

#### 주요 메서드 (스테퍼 모터)

- `move_steps()`: 지정된 스텝 수만큼 이동
- `move_angle()`: 각도만큼 회전
- `move_to_position()`: 절대 위치로 이동
- `reset_position()`: 현재 위치를 0으로 리셋

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
├── modules/                    # 핵심 모듈
│   ├── __init__.py
│   ├── stereo_calibration.py  # 스테레오 카메라 캘리브레이션
│   ├── hand_tracker_3d.py     # 3D 손 추적
│   └── motor_controller.py    # 모터 제어
├── examples/                   # 사용 예제
│   ├── calibrate_cameras.py   # 캘리브레이션 스크립트
│   ├── hand_tracking_demo.py  # 손 추적 데모
│   └── motor_control_demo.py  # 모터 제어 데모
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

### 모터 핀 설정

```yaml
motors:
  dc_motors:
    motor1:
      enable_pin: 18
      in1_pin: 23
      in2_pin: 24
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

---

## 📝 라이센스

이 프로젝트는 MIT 라이센스 하에 배포됩니다.

---

## 🤝 기여

버그 리포트, 기능 제안, Pull Request를 환영합니다!

---

## 📧 문의

질문이나 제안사항이 있으시면 이슈를 등록해주세요.

# L298N 모터 드라이버 설정 가이드

## 개요
이 프로젝트는 L298N 모터 드라이버를 사용하여 2개의 DC 진동모터를 제어합니다.

## 하드웨어 연결

### GPIO 핀 배치
```
라즈베리파이 GPIO → L298N 모터드라이버
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
GPIO 26  →  IN1  (모터 1 제어)
GPIO 19  →  IN2  (모터 1 제어 - 예비)
GPIO 13  →  IN3  (모터 2 제어)
GPIO 6   →  IN4  (모터 2 제어 - 예비)
```

### L298N 연결도
```
┌─────────────────────────────────────┐
│         L298N 모터드라이버           │
├─────────────────────────────────────┤
│                                     │
│  [IN1]  ← GPIO 26                  │
│  [IN2]  ← GPIO 19                  │
│  [IN3]  ← GPIO 13                  │
│  [IN4]  ← GPIO 6                   │
│                                     │
│  [OUT1] → 진동모터 1 (+)           │
│  [OUT2] → 진동모터 1 (-)           │
│  [OUT3] → 진동모터 2 (+)           │
│  [OUT4] → 진동모터 2 (-)           │
│                                     │
│  [+12V] ← 전원 (5-12V)             │
│  [GND]  ← 접지                     │
│  [+5V]  → 라즈베리파이 5V (옵션)   │
└─────────────────────────────────────┘
```

## 모터 제어 방식

### PWM 제어
- **IN1 (GPIO 26)**: 모터 1 속도 제어 (PWM)
- **IN2 (GPIO 19)**: 모터 1 방향 제어 (현재 미사용)
- **IN3 (GPIO 13)**: 모터 2 속도 제어 (PWM)
- **IN4 (GPIO 6)**: 모터 2 방향 제어 (현재 미사용)

### 진동 강도 조절
- PWM Duty Cycle: 0% ~ 100%
- 주파수: 1000Hz (1kHz)
- 0%: 정지
- 100%: 최대 진동

## 소프트웨어 설정

### 1. 메인 애플리케이션 (`main.py`)
```python
motor_pins = {
    'motor_1': 26,  # L298N IN1 (모터 1)
    'motor_2': 13   # L298N IN3 (모터 2)
}
```

### 2. 설정 파일 (`config/config.yaml`)
```yaml
motors:
  vibration_motors:
    motor_1:
      pin: 26  # L298N IN1
    motor_2:
      pin: 13  # L298N IN3
  pwm_frequency: 1000
```

### 3. 예제 파일 (`examples/vibration_motor_demo.py`)
- 단일 모터 예제: GPIO 26 사용
- 다중 모터 예제: GPIO 26, 19, 13, 6 모두 사용
- 햅틱 피드백 예제: GPIO 26, 13 사용

## 사용 예시

### 기본 사용
```python
from modules.vibration_motor import VibrationMotorController

# 컨트롤러 초기화
motor_pins = {'motor_1': 26, 'motor_2': 13}
controller = VibrationMotorController(motor_pins=motor_pins)

# 모터 1 진동 (50% 강도)
controller.start('motor_1', 50)

# 모터 2 진동 (100% 강도)
controller.start('motor_2', 100)

# 모든 모터 정지
controller.stop_all()

# 정리
controller.cleanup()
```

### 햅틱 피드백 예시
```python
# 손이 그래프에 닿았을 때
if collision_detected:
    distance = calculate_distance()
    intensity = 100 * (1 - distance / threshold)
    
    # 거리에 반비례하는 진동 강도
    controller.set_intensity('motor_1', intensity)
    controller.set_intensity('motor_2', intensity)
else:
    controller.stop_all()
```

## 전원 사양

### 권장 사양
- **전압**: 5V ~ 12V DC
- **전류**: 모터당 최소 500mA
- **총 전력**: 최소 2A 권장 (2개 모터 + 라즈베리파이)

### 주의사항
⚠️ **중요**: L298N은 발열이 심할 수 있으므로 방열판 사용을 권장합니다.
⚠️ **중요**: 모터 전원과 라즈베리파이 전원은 반드시 GND를 공유해야 합니다.

## 테스트 방법

### 1. 시뮬레이션 모드 테스트
```bash
# 시뮬레이션 모드 활성화 (config.yaml)
simulation_mode: true

# 예제 실행
python examples/vibration_motor_demo.py
```

### 2. 실제 하드웨어 테스트
```bash
# 시뮬레이션 모드 비활성화 (config.yaml)
simulation_mode: false

# 메인 애플리케이션 실행
python main.py
```

## 문제 해결

### 모터가 작동하지 않음
1. GPIO 핀 번호 확인 (BCM 모드 사용)
2. L298N 전원 연결 확인
3. GND 공유 확인
4. PWM 주파수 확인 (1000Hz)

### 진동이 약함
1. 전원 전압 확인 (최소 5V)
2. 전류 공급 확인 (최소 500mA/모터)
3. PWM Duty Cycle 확인 (0~100%)

### 발열 문제
1. L298N 방열판 부착
2. PWM 주파수 조정 (500~2000Hz)
3. 듀티 사이클 제한 (최대 80%)

## 추가 리소스
- [L298N 데이터시트](https://www.st.com/resource/en/datasheet/l298.pdf)
- [라즈베리파이 GPIO 핀아웃](https://pinout.xyz/)
- [RPi.GPIO 문서](https://pypi.org/project/RPi.GPIO/)

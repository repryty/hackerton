# L298N 모터 드라이버 문제 해결 가이드

## 🔴 증상: ENA에 점퍼 꽂으면 작동 안 함, PWM도 안 됨

### 근본 원인

L298N 모터 드라이버는 **IN 핀의 조합**으로 모터를 제어합니다:

```
IN1=HIGH, IN2=LOW  → 모터 정방향 회전 ✓
IN1=LOW,  IN2=HIGH → 모터 역방향 회전 ✓
IN1=HIGH, IN2=HIGH → 모터 정지/브레이크 ✗
IN1=LOW,  IN2=LOW  → 모터 정지/브레이크 ✗
```

**문제**: IN1과 IN2를 잘못 연결하면 모터가 절대 작동하지 않습니다!

---

## ✅ 해결 방법

### 방법 1: GPIO로 모든 핀 제어 (권장) ⭐

모든 핀을 라즈베리파이 GPIO로 연결:

```
연결:
- L298N ENA  ← 라즈베리파이 GPIO 12 (PWM)
- L298N IN1  ← 라즈베리파이 GPIO 5
- L298N IN2  ← 라즈베리파이 GPIO 6
- L298N ENB  ← 라즈베리파이 GPIO 13 (PWM)
- L298N IN3  ← 라즈베리파이 GPIO 16
- L298N IN4  ← 라즈베리파이 GPIO 26

전원:
- L298N 12V  ← 12V 외부 전원 (+)
- L298N GND  ← 12V 외부 전원 (-) + 라즈베리파이 GND (공통 연결 필수!)
- L298N 5V   ← 사용 안 함 (또는 점퍼 제거)

모터:
- 모터1 (+) ← L298N OUT1
- 모터1 (-) ← L298N OUT2
- 모터2 (+) ← L298N OUT3
- 모터2 (-) ← L298N OUT4
```

**장점**:
- ✅ 방향 제어 가능 (정방향/역방향)
- ✅ PWM으로 속도 제어 가능
- ✅ 소프트웨어로 완전한 제어

**코드**:
```python
controller = L298NMotorController(
    ena_pin=12, in1_pin=5, in2_pin=6,
    enb_pin=13, in3_pin=16, in4_pin=26,
)
```

---

### 방법 2: IN 핀을 라즈베리파이 5V/GND에 직접 연결

IN 핀을 고정하고 PWM으로만 속도 제어:

```
연결:
- L298N ENA  ← 라즈베리파이 GPIO 12 (PWM)
- L298N IN1  ← 라즈베리파이 5V 핀 (물리 핀 2 또는 4)
- L298N IN2  ← 라즈베리파이 GND 핀 (물리 핀 6, 9, 14 등)
- L298N ENB  ← 라즈베리파이 GPIO 13 (PWM)
- L298N IN3  ← 라즈베리파이 5V 핀 (물리 핀 2 또는 4)
- L298N IN4  ← 라즈베리파이 GND 핀 (물리 핀 6, 9, 14 등)
```

⚠️ **주의**: 
- IN1과 IN2가 **반드시 서로 다른 값**이어야 합니다
- IN1=5V, IN2=GND (정방향)
- 또는 IN1=GND, IN2=5V (역방향)

---

## 🛠️ 문제 해결 체크리스트

### 1. 전원 연결 확인
```
[ ] 12V 외부 전원이 L298N의 12V 입력에 연결되어 있나요?
[ ] L298N GND와 라즈베리파이 GND가 **공통으로 연결**되어 있나요? (필수!)
[ ] 12V 전원이 충분한 전류를 공급하나요? (모터당 최소 1A)
```

### 2. 핀 연결 확인
```
[ ] GPIO 번호가 BCM 모드인가요? (물리 핀 번호 아님)
[ ] ENA/ENB 핀에 점퍼가 꽂혀 있지 않나요? (제거 필요)
[ ] IN1 ≠ IN2 인가요? (둘이 같으면 안 됨!)
[ ] IN3 ≠ IN4 인가요? (둘이 같으면 안 됨!)
```

### 3. 모터 연결 확인
```
[ ] 모터1이 OUT1-OUT2에 연결되어 있나요?
[ ] 모터2가 OUT3-OUT4에 연결되어 있나요?
[ ] 모터가 12V용인가요?
```

### 4. 소프트웨어 확인
```bash
# lgpio 설치 확인
pip show lgpio

# GPIO 권한 확인
sudo usermod -aG gpio $USER
sudo reboot
```

---

## 📊 물리 핀 번호 vs BCM 번호

라즈베리파이 5 GPIO 핀 맵:

| 물리 핀 | BCM 번호 | 용도 |
|---------|----------|------|
| 2, 4    | -        | 5V 전원 |
| 6, 9, 14, 20, 25, 30, 34, 39 | - | GND |
| 12      | GPIO 12  | PWM (ENA) |
| 32      | GPIO 12  | PWM (물리 핀 다름) |
| 33      | GPIO 13  | PWM (ENB) |
| 29      | GPIO 5   | IN1 |
| 31      | GPIO 6   | IN2 |
| 36      | GPIO 16  | IN3 |
| 37      | GPIO 26  | IN4 |

**중요**: 코드에서는 **BCM 번호**를 사용해야 합니다!

---

## 🧪 테스트 방법

### 1. 기본 동작 테스트
```bash
python examples/vibration_motor_demo.py
# 메뉴에서 "5" 선택 (모든 테스트 실행)
```

### 2. 수동 테스트
```bash
python examples/vibration_motor_demo.py
# 메뉴에서 "6" 선택 (수동 제어)
# 50 입력 → 50% 속도로 모터 작동
```

### 3. GPIO 직접 테스트
```bash
# lgpio 명령어로 GPIO 제어
sudo lgpio gpio set 5 1    # IN1 = HIGH
sudo lgpio gpio set 6 0    # IN2 = LOW
sudo lgpio pwm 12 1000 50  # ENA = 50% PWM
```

---

## 💡 일반적인 실수

### ❌ 실수 1: GND 미연결
```
라즈베리파이 GND와 L298N GND가 연결되지 않음
→ 해결: 반드시 공통 GND 연결!
```

### ❌ 실수 2: IN 핀 잘못 설정
```
IN1=HIGH, IN2=HIGH (또는 둘 다 LOW)
→ 해결: IN1 ≠ IN2 로 설정
```

### ❌ 실수 3: ENA/ENB 점퍼 장착
```
ENA/ENB에 점퍼를 꽂은 상태에서 PWM 사용
→ 해결: 점퍼 제거
```

### ❌ 실수 4: 물리 핀 번호 사용
```python
# 잘못됨
gpio_write(handle, 32, 1)  # 물리 핀 32

# 올바름
gpio_write(handle, 12, 1)  # BCM GPIO 12
```

---

## 🔧 고급 디버깅

### GPIO 상태 확인
```bash
# 모든 GPIO 상태 확인
gpioinfo gpiochip4

# 특정 GPIO 확인
gpioget gpiochip4 12  # GPIO 12 읽기
```

### 전압 측정
1. L298N 12V 입력: 11~13V 정도
2. IN1~IN4: 0V (LOW) 또는 3.3V (HIGH)
3. ENA/ENB: PWM 신호 (멀티미터로 평균 전압 측정)

### 모터 직접 테스트
L298N 없이 12V를 모터에 직접 연결하여 모터 자체가 작동하는지 확인

---

## 📞 추가 지원

문제가 계속되면:
1. 배선 사진 확인
2. 시리얼 모니터 출력 확인
3. GPIO 상태 확인
4. 전원 전압/전류 측정

파일 실행:
```bash
cd /path/to/hackerton
python examples/vibration_motor_demo.py
```

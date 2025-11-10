"""
L298N 모터드라이버 PWM 제어 테스트 스크립트

🔴 중요한 연결 방법:

방법 1 (권장): GPIO로 모든 핀 제어
- ENA: GPIO 12 (PWM)
- IN1: GPIO 5 (방향)
- IN2: GPIO 6 (방향)
- ENB: GPIO 13 (PWM)
- IN3: GPIO 16 (방향)
- IN4: GPIO 26 (방향)

방법 2 (간단): 한 방향만 사용
- ENA: GPIO 12 (PWM)
- IN1: 라즈베리파이의 5V 핀 (물리 핀 2 또는 4)
- IN2: GND (물리 핀 6, 9, 14, 20, 25, 30, 34, 39 중 하나)
- ENB: GPIO 13 (PWM)
- IN3: 라즈베리파이의 5V 핀 (물리 핀 2 또는 4)
- IN4: GND (물리 핀 6, 9, 14, 20, 25, 30, 34, 39 중 하나)

⚠️  IN1과 IN2가 둘 다 HIGH이거나 둘 다 LOW이면 모터가 작동하지 않습니다!
   반드시 IN1=HIGH, IN2=LOW 또는 그 반대여야 합니다.

전원:
- L298N 12V 입력: 12V 외부 전원
- L298N GND: 라즈베리파이 GND와 공통 연결 필수!
"""

import time

try:
    import lgpio
    LGPIO_AVAILABLE = True
except ImportError:
    LGPIO_AVAILABLE = False
    print("⚠️  lgpio 라이브러리가 설치되지 않았습니다.")
    print("   라즈베리파이 5에서는 'pip install lgpio'로 설치하세요.")


class L298NMotorController:
    """L298N 모터 드라이버 PWM 제어 클래스 (GPIO로 IN 핀 제어)"""
    
    def __init__(self, 
                 ena_pin=12, in1_pin=5, in2_pin=6,
                 enb_pin=13, in3_pin=16, in4_pin=26,
                 pwm_frequency=1000, simulation_mode=False):
        """
        초기화
        
        Args:
            ena_pin: ENA 핀 번호 (모터1 속도 제어 PWM)
            in1_pin: IN1 핀 번호 (모터1 방향)
            in2_pin: IN2 핀 번호 (모터1 방향)
            enb_pin: ENB 핀 번호 (모터2 속도 제어 PWM)
            in3_pin: IN3 핀 번호 (모터2 방향)
            in4_pin: IN4 핀 번호 (모터2 방향)
            pwm_frequency: PWM 주파수 (Hz)
            simulation_mode: 시뮬레이션 모드 (실제 GPIO 없이 테스트)
        """
        self.ena_pin = ena_pin
        self.in1_pin = in1_pin
        self.in2_pin = in2_pin
        self.enb_pin = enb_pin
        self.in3_pin = in3_pin
        self.in4_pin = in4_pin
        self.pwm_frequency = pwm_frequency
        self.simulation_mode = simulation_mode
        self.handle = None
        
        if not simulation_mode:
            if not LGPIO_AVAILABLE:
                raise RuntimeError("lgpio 라이브러리가 필요합니다.")
            
            try:
                # GPIO 핸들 열기 (라즈베리파이 5는 gpiochip4 사용)
                self.handle = lgpio.gpiochip_open(4)
                
                # IN 핀들을 출력으로 설정하고 초기화
                lgpio.gpio_claim_output(self.handle, self.in1_pin, 0)
                lgpio.gpio_claim_output(self.handle, self.in2_pin, 0)
                lgpio.gpio_claim_output(self.handle, self.in3_pin, 0)
                lgpio.gpio_claim_output(self.handle, self.in4_pin, 0)
                
                # 정방향 설정 (IN1=HIGH, IN2=LOW, IN3=HIGH, IN4=LOW)
                lgpio.gpio_write(self.handle, self.in1_pin, 1)
                lgpio.gpio_write(self.handle, self.in2_pin, 0)
                lgpio.gpio_write(self.handle, self.in3_pin, 1)
                lgpio.gpio_write(self.handle, self.in4_pin, 0)
                
                # PWM 설정 (처음엔 0%)
                lgpio.tx_pwm(self.handle, self.ena_pin, self.pwm_frequency, 0)
                lgpio.tx_pwm(self.handle, self.enb_pin, self.pwm_frequency, 0)
                
                print(f"✓ GPIO 초기화 완료")
                print(f"  ENA: GPIO{self.ena_pin} (PWM)")
                print(f"  IN1: GPIO{self.in1_pin}=HIGH, IN2: GPIO{self.in2_pin}=LOW (정방향)")
                print(f"  ENB: GPIO{self.enb_pin} (PWM)")
                print(f"  IN3: GPIO{self.in3_pin}=HIGH, IN4: GPIO{self.in4_pin}=LOW (정방향)")
                print(f"  PWM 주파수: {self.pwm_frequency} Hz")
            except Exception as e:
                raise RuntimeError(f"GPIO 초기화 실패: {e}")
        else:
            print(f"✓ 시뮬레이션 모드로 초기화")
            print(f"  ENA: GPIO{self.ena_pin}, ENB: GPIO{self.enb_pin}")
            print(f"  IN1: GPIO{self.in1_pin}, IN2: GPIO{self.in2_pin}")
            print(f"  IN3: GPIO{self.in3_pin}, IN4: GPIO{self.in4_pin}")
    
    def set_motor1_speed(self, duty_cycle):
        """
        모터1 속도 설정
        
        Args:
            duty_cycle: PWM 듀티 사이클 (0~100)
        """
        duty_cycle = max(0, min(100, duty_cycle))  # 0~100 범위로 제한
        
        if not self.simulation_mode:
            lgpio.tx_pwm(self.handle, self.ena_pin, self.pwm_frequency, duty_cycle)
            print(f"[모터1] 속도 설정: {duty_cycle}%")
        else:
            print(f"[시뮬레이션][모터1] 속도 설정: {duty_cycle}%")
    
    def set_motor2_speed(self, duty_cycle):
        """
        모터2 속도 설정
        
        Args:
            duty_cycle: PWM 듀티 사이클 (0~100)
        """
        duty_cycle = max(0, min(100, duty_cycle))  # 0~100 범위로 제한
        
        if not self.simulation_mode:
            lgpio.tx_pwm(self.handle, self.enb_pin, self.pwm_frequency, duty_cycle)
            print(f"[모터2] 속도 설정: {duty_cycle}%")
        else:
            print(f"[시뮬레이션][모터2] 속도 설정: {duty_cycle}%")
    
    def set_both_speed(self, duty_cycle):
        """
        양쪽 모터 속도 동시 설정
        
        Args:
            duty_cycle: PWM 듀티 사이클 (0~100)
        """
        self.set_motor1_speed(duty_cycle)
        self.set_motor2_speed(duty_cycle)
    
    def stop(self):
        """모든 모터 정지"""
        print("모터 정지")
        self.set_both_speed(0)
    
    def cleanup(self):
        """GPIO 정리"""
        if not self.simulation_mode and self.handle is not None:
            try:
                # PWM 정지
                lgpio.tx_pwm(self.handle, self.ena_pin, self.pwm_frequency, 0)
                lgpio.tx_pwm(self.handle, self.enb_pin, self.pwm_frequency, 0)
                
                # IN 핀들 LOW로 설정
                lgpio.gpio_write(self.handle, self.in1_pin, 0)
                lgpio.gpio_write(self.handle, self.in2_pin, 0)
                lgpio.gpio_write(self.handle, self.in3_pin, 0)
                lgpio.gpio_write(self.handle, self.in4_pin, 0)
                
                # GPIO 핸들 닫기
                lgpio.gpiochip_close(self.handle)
                print("✓ GPIO 정리 완료")
            except Exception as e:
                print(f"⚠️  GPIO 정리 중 오류: {e}")


def detect_raspberry_pi():
    """Raspberry Pi 환경인지 확인"""
    # /proc/cpuinfo 확인
    try:
        with open('/proc/cpuinfo', 'r') as f:
            cpuinfo = f.read()
            if 'BCM' in cpuinfo or 'Raspberry Pi' in cpuinfo or 'BCM2' in cpuinfo:
                return True
    except:
        pass
    
    # /proc/device-tree/model 확인
    try:
        with open('/proc/device-tree/model', 'r') as f:
            model = f.read()
            if 'Raspberry Pi' in model:
                return True
    except:
        pass
    
    # lgpio 라이브러리로 확인
    if LGPIO_AVAILABLE:
        try:
            import lgpio
            handle = lgpio.gpiochip_open(4)
            lgpio.gpiochip_close(handle)
            return True
        except:
            pass
    
    return False


def test_pwm_sweep(controller, duration=5):
    """PWM 스윕 테스트 - 0%에서 100%까지 증가"""
    print("\n" + "=" * 60)
    print("PWM 스윕 테스트 (0% → 100%)")
    print("=" * 60)
    
    steps = 20
    for i in range(steps + 1):
        duty = int(i * 100 / steps)
        print(f"\n진행률: {i}/{steps} - 듀티 사이클: {duty}%")
        controller.set_both_speed(duty)
        time.sleep(duration / steps)
    
    print("\n✓ 스윕 테스트 완료")
    controller.stop()
    time.sleep(1)


def test_step_levels(controller):
    """단계별 속도 테스트"""
    print("\n" + "=" * 60)
    print("단계별 속도 테스트")
    print("=" * 60)
    
    levels = [0, 25, 50, 75, 100]
    
    for level in levels:
        print(f"\n속도: {level}%")
        controller.set_both_speed(level)
        time.sleep(2)
    
    print("\n✓ 단계별 테스트 완료")
    controller.stop()
    time.sleep(1)


def test_individual_motors(controller):
    """개별 모터 테스트"""
    print("\n" + "=" * 60)
    print("개별 모터 테스트")
    print("=" * 60)
    
    print("\n[테스트 1] 모터1만 50% 작동")
    controller.set_motor1_speed(50)
    controller.set_motor2_speed(0)
    time.sleep(3)
    
    print("\n[테스트 2] 모터2만 50% 작동")
    controller.set_motor1_speed(0)
    controller.set_motor2_speed(50)
    time.sleep(3)
    
    print("\n[테스트 3] 양쪽 모터 다른 속도 (모터1: 30%, 모터2: 70%)")
    controller.set_motor1_speed(30)
    controller.set_motor2_speed(70)
    time.sleep(3)
    
    print("\n✓ 개별 모터 테스트 완료")
    controller.stop()
    time.sleep(1)


def test_pulse_pattern(controller):
    """펄스 패턴 테스트"""
    print("\n" + "=" * 60)
    print("펄스 패턴 테스트")
    print("=" * 60)
    
    print("\n빠른 on/off 반복 (5회)")
    for i in range(5):
        print(f"  펄스 {i+1}/5")
        controller.set_both_speed(100)
        time.sleep(0.3)
        controller.set_both_speed(0)
        time.sleep(0.3)
    
    print("\n✓ 펄스 패턴 테스트 완료")
    controller.stop()
    time.sleep(1)


def main():
    """메인 함수 - 다양한 PWM 테스트 실행"""
    print()
    print("=" * 60)
    print("L298N 모터 드라이버 PWM 제어 테스트")
    print("=" * 60)
    print()
    print("하드웨어 설정:")
    print("  [모터1]")
    print("    - ENA: GPIO 12 (PWM)")
    print("    - IN1: GPIO 5 (HIGH=정방향)")
    print("    - IN2: GPIO 6 (LOW)")
    print("  [모터2]")
    print("    - ENB: GPIO 13 (PWM)")
    print("    - IN3: GPIO 16 (HIGH=정방향)")
    print("    - IN4: GPIO 26 (LOW)")
    print("  [전원]")
    print("    - 12V → L298N 12V 입력")
    print("    - GND → 라즈베리파이 GND와 L298N GND 공통 연결 필수!")
    print()
    print("⚠️  문제 해결 체크리스트:")
    print("   1. L298N GND와 라즈베리파이 GND가 연결되어 있나요?")
    print("   2. 12V 외부 전원이 L298N에 제대로 연결되어 있나요?")
    print("   3. 모터가 L298N의 OUT1-OUT2, OUT3-OUT4에 연결되어 있나요?")
    print("   4. GPIO 핀 번호가 BCM 모드 번호인가요? (물리 핀 번호 아님)")
    print()
    
    # Raspberry Pi 환경 감지
    is_raspberry_pi = detect_raspberry_pi()
    simulation_mode = not is_raspberry_pi
    
    if simulation_mode:
        print("⚠️  Raspberry Pi 환경이 아닙니다. 시뮬레이션 모드로 실행합니다.")
    else:
        print("✓ Raspberry Pi 환경 감지됨. 실제 하드웨어 모드로 실행합니다.")
    print()

    controller = None
    
    try:
        # 컨트롤러 초기화
        controller = L298NMotorController(
            ena_pin=12, in1_pin=5, in2_pin=6,
            enb_pin=13, in3_pin=16, in4_pin=26,
            pwm_frequency=1000,
            simulation_mode=simulation_mode,
        )
        print()
        
        # 테스트 메뉴
        print("=" * 60)
        print("테스트 메뉴")
        print("=" * 60)
        print("1. PWM 스윕 테스트 (0% → 100%)")
        print("2. 단계별 속도 테스트 (0%, 25%, 50%, 75%, 100%)")
        print("3. 개별 모터 테스트")
        print("4. 펄스 패턴 테스트")
        print("5. 모든 테스트 순차 실행")
        print("6. 수동 제어 (양쪽 모터 동시)")
        print()
        
        choice = input("선택 (1-6, Enter=5): ").strip()
        if not choice:
            choice = "5"
        
        if choice == "1":
            test_pwm_sweep(controller)
        elif choice == "2":
            test_step_levels(controller)
        elif choice == "3":
            test_individual_motors(controller)
        elif choice == "4":
            test_pulse_pattern(controller)
        elif choice == "5":
            print("\n모든 테스트를 순차적으로 실행합니다...\n")
            test_pwm_sweep(controller)
            test_step_levels(controller)
            test_individual_motors(controller)
            test_pulse_pattern(controller)
        elif choice == "6":
            print("\n수동 제어 모드")
            print("0~100 사이의 숫자를 입력하세요 (종료: q)")
            while True:
                try:
                    user_input = input("\n속도 (0-100): ").strip()
                    if user_input.lower() == 'q':
                        break
                    speed = int(user_input)
                    if 0 <= speed <= 100:
                        controller.set_both_speed(speed)
                    else:
                        print("⚠️  0~100 사이의 값을 입력하세요.")
                except ValueError:
                    print("⚠️  숫자를 입력하세요.")
                except KeyboardInterrupt:
                    break
        else:
            print("⚠️  잘못된 선택입니다.")
        
        print("\n" + "=" * 60)
        print("모든 테스트 완료!")
        print("=" * 60)

    except KeyboardInterrupt:
        print("\n\n사용자에 의해 중단되었습니다.")
    except Exception as e:
        print(f"\n⚠️  오류 발생: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # 정리
        if controller:
            controller.stop()
            controller.cleanup()
            print("\n✓ 모터 드라이버 종료")


if __name__ == "__main__":
    main()

"""
모터 제어 예제 스크립트

GPIO를 통해 모터를 제어하는 예제입니다.
"""

import sys
from pathlib import Path
import time

# 프로젝트 루트를 Python 경로에 추가
sys.path.append(str(Path(__file__).parent.parent))

from modules.motor_controller import MotorController, StepperMotorController


def dc_motor_example():
    """DC 모터 제어 예제"""
    print("=" * 60)
    print("DC 모터 제어 예제")
    print("=" * 60)
    print()

    # 모터 설정
    motor_configs = {
        "motor1": {"enable_pin": 18, "in1_pin": 23, "in2_pin": 24, "type": "l298n"},
        "motor2": {"enable_pin": 12, "in1_pin": 5, "in2_pin": 6, "type": "l298n"},
    }

    # MotorController 초기화 (시뮬레이션 모드)
    # 실제 라즈베리파이에서 실행 시 simulation_mode=False로 설정
    controller = MotorController(
        motor_configs=motor_configs,
        pwm_frequency=1000,
        simulation_mode=True,  # 테스트용 시뮬레이션 모드
    )

    print("✓ 모터 컨트롤러 초기화 완료")
    print()

    try:
        # 예제 1: 단일 모터 제어
        print("예제 1: 모터1을 전진 방향으로 50% 속도로 동작")
        controller.set_motor_speed("motor1", speed=50, direction="forward")
        time.sleep(2)
        controller.stop_motor("motor1")
        print()

        # 예제 2: 부드러운 가속
        print("예제 2: 모터2를 부드럽게 가속")
        controller.set_motor_acceleration(
            "motor2", target_speed=80, direction="forward", accel_time=2.0, steps=20
        )
        time.sleep(1)
        controller.stop_motor("motor2")
        print()

        # 예제 3: 양방향 동작
        print("예제 3: 모터1 전진 → 정지 → 후진")
        controller.move_motor_for_duration("motor1", 60, "forward", 1.5)
        time.sleep(0.5)
        controller.move_motor_for_duration("motor1", 60, "backward", 1.5)
        print()

        # 예제 4: 시퀀스 실행
        print("예제 4: 모터2 시퀀스 실행")
        sequence = [
            {"speed": 40, "direction": "forward", "duration": 1.0},
            {"speed": 0, "direction": "stop", "duration": 0.3},
            {"speed": 60, "direction": "forward", "duration": 1.0},
            {"speed": 0, "direction": "stop", "duration": 0.3},
            {"speed": 30, "direction": "backward", "duration": 1.0},
        ]
        controller.execute_motor_sequence("motor2", sequence)
        print()

        # 예제 5: 두 모터 동시 제어
        print("예제 5: 두 모터 동시 제어")
        controller.set_motor_speed("motor1", 70, "forward")
        controller.set_motor_speed("motor2", 70, "forward")
        print("  두 모터 전진 중...")
        time.sleep(2)
        controller.stop_all_motors()
        print("  모든 모터 정지")
        print()

        # 모터 상태 확인
        print("현재 모터 상태:")
        states = controller.get_all_motor_states()
        for motor_name, state in states.items():
            print(f"  {motor_name}: {state}")

    finally:
        # 정리
        controller.cleanup()
        print()
        print("✓ 모터 컨트롤러 종료")


def stepper_motor_example():
    """스테퍼 모터 제어 예제"""
    print()
    print("=" * 60)
    print("스테퍼 모터 제어 예제")
    print("=" * 60)
    print()

    # StepperMotorController 초기화
    stepper = StepperMotorController(
        step_pin=16,
        dir_pin=20,
        enable_pin=21,
        steps_per_revolution=200,
        microsteps=16,
        simulation_mode=True,  # 테스트용 시뮬레이션 모드
    )

    print("✓ 스테퍼 모터 컨트롤러 초기화 완료")
    print()

    try:
        # 예제 1: 특정 스텝 수만큼 이동
        print("예제 1: 100 스텝 전진")
        stepper.move_steps(100, speed=1.0)
        print(f"  현재 위치: {stepper.current_position} 스텝")
        print()

        # 예제 2: 각도로 회전
        print("예제 2: 180도 회전")
        stepper.move_angle(180, speed=1.0)
        print(f"  현재 위치: {stepper.current_position} 스텝")
        print()

        # 예제 3: 절대 위치로 이동
        print("예제 3: 절대 위치 0으로 이동")
        stepper.move_to_position(0, speed=1.5)
        print(f"  현재 위치: {stepper.current_position} 스텝")
        print()

        # 예제 4: 연속 회전
        print("예제 4: 1회전 (360도)")
        stepper.move_angle(360, speed=2.0)
        print(f"  현재 위치: {stepper.current_position} 스텝")
        print()

        # 위치 리셋
        print("위치 리셋")
        stepper.reset_position()
        print(f"  현재 위치: {stepper.current_position} 스텝")

    finally:
        # 정리
        stepper.cleanup()
        print()
        print("✓ 스테퍼 모터 컨트롤러 종료")


def main():
    """메인 함수"""
    print()
    print("=" * 60)
    print("모터 제어 종합 예제")
    print("=" * 60)
    print()
    print("주의: 이 예제는 시뮬레이션 모드로 동작합니다.")
    print("실제 하드웨어에서 실행하려면 코드에서 simulation_mode=False로 설정하세요.")
    print()

    # DC 모터 예제 실행
    dc_motor_example()

    # 스테퍼 모터 예제 실행
    stepper_motor_example()

    print()
    print("=" * 60)
    print("모든 예제 완료!")
    print("=" * 60)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print()
        print("사용자에 의해 중단되었습니다.")
    except Exception as e:
        print()
        print(f"에러 발생: {e}")
        import traceback

        traceback.print_exc()

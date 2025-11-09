"""
진동모터 제어 예제 스크립트

GPIO를 통해 진동모터를 제어하는 다양한 예제입니다.
"""

import sys
from pathlib import Path
import time

# 프로젝트 루트를 Python 경로에 추가
sys.path.append(str(Path(__file__).parent.parent))

from modules.vibration_motor import (
    VibrationMotor,
    VibrationMotorController,
    VIBRATION_PATTERNS,
)


def single_motor_example():
    """단일 진동모터 제어 예제"""
    print("=" * 60)
    print("단일 진동모터 제어 예제")
    print("=" * 60)
    print()

    # VibrationMotor 초기화 (시뮬레이션 모드)
    # 실제 라즈베리파이에서 실행 시 simulation_mode=False로 설정
    motor = VibrationMotor(
        pin=18,  # GPIO 18번 핀
        pwm_frequency=1000,
        simulation_mode=True,  # 테스트용 시뮬레이션 모드
    )

    print("✓ 진동모터 초기화 완료")
    print()

    try:
        # 예제 1: 기본 진동
        print("예제 1: 100% 강도로 1초 진동")
        motor.start(100)
        time.sleep(1)
        motor.stop()
        time.sleep(0.5)
        print()

        # 예제 2: 강도 조절
        print("예제 2: 다양한 강도로 진동")
        for intensity in [25, 50, 75, 100]:
            print(f"  강도: {intensity}%")
            motor.start(intensity)
            time.sleep(0.5)
        motor.stop()
        time.sleep(0.5)
        print()

        # 예제 3: 짧은 펄스
        print("예제 3: 짧은 펄스 (0.2초)")
        motor.pulse(100, 0.2)
        time.sleep(0.5)
        print()

        # 예제 4: 페이드 인
        print("예제 4: 페이드 인 (2초)")
        motor.fade_in(max_intensity=100, duration=2.0)
        time.sleep(0.5)
        print()

        # 예제 5: 페이드 아웃
        print("예제 5: 페이드 아웃 (2초)")
        motor.start(100)
        time.sleep(0.5)
        motor.fade_out(duration=2.0)
        time.sleep(0.5)
        print()

        # 예제 6: 미리 정의된 패턴 재생
        print("예제 6: 미리 정의된 패턴 재생")

        print("  - Short Pulse")
        motor.vibrate_pattern(VIBRATION_PATTERNS["short_pulse"])
        time.sleep(0.5)

        print("  - Double Pulse")
        motor.vibrate_pattern(VIBRATION_PATTERNS["double_pulse"])
        time.sleep(0.5)

        print("  - Heartbeat")
        motor.vibrate_pattern(VIBRATION_PATTERNS["heartbeat"])
        time.sleep(0.5)

        print("  - Fade")
        motor.vibrate_pattern(VIBRATION_PATTERNS["fade"])
        time.sleep(0.5)
        print()

        # 예제 7: 커스텀 패턴
        print("예제 7: 커스텀 패턴")
        custom_pattern = [
            {"intensity": 100, "duration": 0.1},
            {"intensity": 0, "duration": 0.05},
            {"intensity": 50, "duration": 0.1},
            {"intensity": 0, "duration": 0.05},
            {"intensity": 100, "duration": 0.2},
        ]
        motor.vibrate_pattern(custom_pattern)
        print()

    finally:
        # 정리
        motor.cleanup()
        print("✓ 진동모터 종료")


def multi_motor_example():
    """다중 진동모터 제어 예제"""
    print()
    print("=" * 60)
    print("다중 진동모터 제어 예제")
    print("=" * 60)
    print()

    # 모터 핀 설정
    motor_pins = {"left": 18, "right": 23, "top": 24, "bottom": 25}

    # VibrationMotorController 초기화
    controller = VibrationMotorController(
        motor_pins=motor_pins,
        pwm_frequency=1000,
        simulation_mode=True,  # 테스트용 시뮬레이션 모드
    )

    print("✓ 4개 진동모터 컨트롤러 초기화 완료")
    print()

    try:
        # 예제 1: 개별 모터 제어
        print("예제 1: 개별 모터 순차 진동")
        for motor_name in ["left", "right", "top", "bottom"]:
            print(f"  {motor_name} 모터 진동")
            controller.pulse(motor_name, 100, 0.3)
            time.sleep(0.2)
        print()

        # 예제 2: 모든 모터 동시 진동
        print("예제 2: 모든 모터 동시 진동")
        controller.start_all(100)
        time.sleep(1)
        controller.stop_all()
        time.sleep(0.5)
        print()

        # 예제 3: 순차 시퀀스
        print("예제 3: 순차 시퀀스 재생")
        sequence = [
            {"motor": "left", "intensity": 100, "duration": 0.2},
            {"motor": "top", "intensity": 100, "duration": 0.2},
            {"motor": "right", "intensity": 100, "duration": 0.2},
            {"motor": "bottom", "intensity": 100, "duration": 0.2},
        ]
        controller.pulse_sequence(sequence)
        time.sleep(0.5)
        print()

        # 예제 4: 동기화 패턴
        print("예제 4: 모든 모터에 동기화 패턴 적용")
        controller.vibrate_pattern_all(VIBRATION_PATTERNS["heartbeat"])
        time.sleep(0.5)
        print()

        # 예제 5: 방향 표시 (좌우)
        print("예제 5: 방향 표시 - 왼쪽에서 오른쪽으로")
        for i in range(3):
            controller.pulse("left", 100, 0.15)
            time.sleep(0.1)
            controller.pulse("right", 100, 0.15)
            time.sleep(0.3)
        print()

        # 예제 6: 강도별 피드백
        print("예제 6: 강도별 피드백")
        print("  약함 (25%)")
        controller.start_all(25)
        time.sleep(0.5)
        print("  보통 (50%)")
        controller.set_all_intensity(50)
        time.sleep(0.5)
        print("  강함 (100%)")
        controller.set_all_intensity(100)
        time.sleep(0.5)
        controller.stop_all()
        print()

        # 예제 7: 경고 패턴
        print("예제 7: 경고 패턴 (SOS)")
        controller.vibrate_pattern_all(VIBRATION_PATTERNS["sos"])
        print()

        # 모터 상태 확인
        print("현재 모터 상태:")
        states = controller.get_motor_states()
        for motor_name, state in states.items():
            print(
                f"  {motor_name}: 강도={state['intensity']}%, 동작중={state['is_running']}"
            )

    finally:
        # 정리
        controller.cleanup()
        print()
        print("✓ 진동모터 컨트롤러 종료")


def haptic_feedback_example():
    """햅틱 피드백 시나리오 예제"""
    print()
    print("=" * 60)
    print("햅틱 피드백 시나리오 예제")
    print("=" * 60)
    print()

    motor_pins = {"hand_left": 18, "hand_right": 23}

    controller = VibrationMotorController(motor_pins=motor_pins, simulation_mode=True)

    print("✓ 햅틱 피드백 시스템 초기화 완료")
    print()

    try:
        # 시나리오 1: 버튼 클릭 피드백
        print("시나리오 1: 버튼 클릭 피드백")
        controller.pulse("hand_right", 80, 0.05)
        time.sleep(0.5)
        print()

        # 시나리오 2: 성공 알림
        print("시나리오 2: 성공 알림")
        controller.vibrate_pattern_all(VIBRATION_PATTERNS["double_pulse"])
        time.sleep(0.5)
        print()

        # 시나리오 3: 오류 알림
        print("시나리오 3: 오류 알림")
        controller.vibrate_pattern_all(VIBRATION_PATTERNS["triple_pulse"])
        time.sleep(0.5)
        print()

        # 시나리오 4: 거리 피드백 (가까워질수록 강해짐)
        print("시나리오 4: 거리 피드백 시뮬레이션")
        distances = [100, 80, 60, 40, 20, 10]
        for distance in distances:
            intensity = max(0, 100 - distance)
            print(f"  거리: {distance}cm → 강도: {intensity}%")
            controller.start_all(intensity)
            time.sleep(0.3)
        controller.stop_all()
        time.sleep(0.5)
        print()

        # 시나리오 5: 좌우 방향 안내
        print("시나리오 5: 좌우 방향 안내")
        print("  왼쪽으로!")
        for _ in range(3):
            controller.pulse("hand_left", 100, 0.15)
            time.sleep(0.15)
        time.sleep(0.5)

        print("  오른쪽으로!")
        for _ in range(3):
            controller.pulse("hand_right", 100, 0.15)
            time.sleep(0.15)
        time.sleep(0.5)
        print()

        # 시나리오 6: 주의 집중
        print("시나리오 6: 주의 집중")
        controller.vibrate_pattern_all(VIBRATION_PATTERNS["long_pulse"])
        time.sleep(0.5)
        print()

    finally:
        controller.cleanup()
        print("✓ 햅틱 피드백 시스템 종료")


def main():
    """메인 함수"""
    print()
    print("=" * 60)
    print("진동모터 제어 종합 예제")
    print("=" * 60)
    print()
    print("주의: 이 예제는 시뮬레이션 모드로 동작합니다.")
    print("실제 하드웨어에서 실행하려면 코드에서 simulation_mode=False로 설정하세요.")
    print()

    # 단일 모터 예제
    single_motor_example()

    # 다중 모터 예제
    multi_motor_example()

    # 햅틱 피드백 예제
    haptic_feedback_example()

    print()
    print("=" * 60)
    print("모든 예제 완료!")
    print("=" * 60)
    print()
    print("사용 가능한 미리 정의된 패턴:")
    for pattern_name in VIBRATION_PATTERNS.keys():
        print(f"  - {pattern_name}")


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

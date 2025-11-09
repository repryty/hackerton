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


def detect_raspberry_pi():
    """Raspberry Pi 환경인지 확인 (디버그 정보 포함)"""
    print("[DEBUG] Raspberry Pi 환경 감지 중...")
    
    # 방법 1: /proc/cpuinfo 확인
    try:
        with open('/proc/cpuinfo', 'r') as f:
            cpuinfo = f.read()
            print(f"[DEBUG] /proc/cpuinfo 읽기 성공")
            # BCM, Raspberry Pi 문자열 확인
            if 'BCM' in cpuinfo or 'Raspberry Pi' in cpuinfo or 'BCM2' in cpuinfo:
                print(f"[DEBUG] ✓ /proc/cpuinfo에서 Raspberry Pi 감지됨")
                return True
            else:
                print(f"[DEBUG] /proc/cpuinfo 일부 내용: {cpuinfo[:200]}")
    except FileNotFoundError:
        print("[DEBUG] ⚠️  /proc/cpuinfo 파일을 찾을 수 없음")
    except PermissionError:
        print("[DEBUG] ⚠️  /proc/cpuinfo 읽기 권한 없음")
    except Exception as e:
        print(f"[DEBUG] ⚠️  /proc/cpuinfo 읽기 오류: {e}")
    
    # 방법 2: /proc/device-tree/model 확인
    try:
        with open('/proc/device-tree/model', 'r') as f:
            model = f.read()
            print(f"[DEBUG] /proc/device-tree/model 내용: {model.strip()}")
            if 'Raspberry Pi' in model:
                print(f"[DEBUG] ✓ /proc/device-tree/model에서 Raspberry Pi 감지됨")
                return True
    except FileNotFoundError:
        print("[DEBUG] ⚠️  /proc/device-tree/model 파일을 찾을 수 없음")
    except PermissionError:
        print("[DEBUG] ⚠️  /proc/device-tree/model 읽기 권한 없음")
    except Exception as e:
        print(f"[DEBUG] ⚠️  /proc/device-tree/model 읽기 오류: {e}")
    
    # 방법 3: lgpio 라이브러리로 확인
    try:
        import lgpio
        print("[DEBUG] ✓ lgpio 라이브러리 import 성공")
        # GPIO 핸들 열기 시도
        handle = lgpio.gpiochip_open(4)
        print("[DEBUG] ✓ gpiochip4 열기 성공 - Raspberry Pi 5 환경임")
        lgpio.gpiochip_close(handle)
        return True
    except ImportError:
        print("[DEBUG] ⚠️  lgpio 라이브러리를 찾을 수 없음")
    except Exception as e:
        print(f"[DEBUG] ⚠️  GPIO 확인 오류: {e}")
    
    print("[DEBUG] ✗ Raspberry Pi 환경이 아닌 것으로 판단됨")
    return False


def main():
    """메인 함수 - 양쪽 모터 계속 켜기"""
    print()
    print("=" * 60)
    print("진동모터 연속 동작 스크립트")
    print("=" * 60)
    print()
    
    # Raspberry Pi 환경 감지
    is_raspberry_pi = detect_raspberry_pi()
    simulation_mode = not is_raspberry_pi
    
    if simulation_mode:
        print("⚠️  Raspberry Pi 환경이 아닙니다. 시뮬레이션 모드로 실행합니다.")
    else:
        print("✓ Raspberry Pi 환경 감지됨. 실제 하드웨어 모드로 실행합니다.")
    print()

    # 모터 핀 설정
    motor_pins = {
        "motor_1": 26,  # L298N IN1 (모터 1)
        "motor_2": 13   # L298N IN3 (모터 2)
    }

    controller = None
    
    try:
        # 컨트롤러 초기화
        controller = VibrationMotorController(
            motor_pins=motor_pins,
            pwm_frequency=1000,
            simulation_mode=simulation_mode,
        )

        print("✓ 진동모터 컨트롤러 초기화 완료")
        print()
        
        # 양쪽 모터 100% 강도로 시작
        print("양쪽 모터를 100% 강도로 켭니다...")
        controller.start_all(100)
        print("✓ 모터 동작 중 (Ctrl+C로 종료)")
        print()
        
        # 계속 실행 (무한 루프)
        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        print()
        print("사용자에 의해 중단되었습니다.")
    except Exception as e:
        print(f"⚠️  오류 발생: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # 정리
        if controller:
            controller.stop_all()
            controller.cleanup()
            print("✓ 진동모터 종료")


if __name__ == "__main__":
    main()

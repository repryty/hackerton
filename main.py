"""
라즈베리파이 5 스테레오 비전 및 모터 제어 시스템

메인 애플리케이션 파일
"""

import sys
import logging
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
sys.path.append(str(Path(__file__).parent))

# 모듈 임포트 (실제 사용 시 주석 해제)
# from modules import StereoCalibration, HandTracker3D, MotorController

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def main():
    """메인 함수"""
    logger.info("=" * 60)
    logger.info("라즈베리파이 5 스테레오 비전 및 모터 제어 시스템")
    logger.info("=" * 60)

    # TODO: 여기에 메인 애플리케이션 로직 구현
    # 예제:
    # 1. 캘리브레이션 데이터 로드
    # 2. 카메라 및 손 추적기 초기화
    # 3. 모터 컨트롤러 초기화
    # 4. 메인 루프: 손 위치 추적 → 모터 제어

    logger.info("시스템 초기화 중...")
    logger.info("초기화 완료!")
    logger.info("")
    logger.info("사용 가능한 모듈:")
    logger.info("  - StereoCalibration: 스테레오 카메라 캘리브레이션")
    logger.info("  - HandTracker3D: 3D 손 추적")
    logger.info("  - MotorController: 모터 제어")
    logger.info("")
    logger.info("예제 스크립트를 실행하려면:")
    logger.info("  python examples/calibrate_cameras.py")
    logger.info("  python examples/hand_tracking_demo.py")
    logger.info("  python examples/motor_control_demo.py")
    logger.info("")
    logger.info("=" * 60)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("")
        logger.info("사용자에 의해 중단되었습니다.")
    except Exception as e:
        logger.error(f"에러 발생: {e}")
        import traceback

        traceback.print_exc()

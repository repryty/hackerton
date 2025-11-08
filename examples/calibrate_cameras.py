"""
스테레오 카메라 캘리브레이션 스크립트

두 개의 카메라를 사용하여 스테레오 캘리브레이션을 수행하고
결과를 저장합니다.
"""

import cv2
import sys
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
sys.path.append(str(Path(__file__).parent.parent))

from modules.stereo_calibration import StereoCalibration


def main():
    """캘리브레이션 메인 함수"""

    print("=" * 60)
    print("스테레오 카메라 캘리브레이션 스크립트")
    print("=" * 60)
    print()

    # 카메라 초기화
    print("카메라 초기화 중...")
    cap_left = cv2.VideoCapture(0)
    cap_right = cv2.VideoCapture(1)

    if not cap_left.isOpened() or not cap_right.isOpened():
        print("에러: 카메라를 열 수 없습니다.")
        print("카메라가 연결되어 있는지 확인해주세요.")
        return

    # 해상도 설정
    cap_left.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap_left.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    cap_right.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap_right.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    print("카메라 초기화 완료!")
    print()

    # StereoCalibration 객체 생성
    calibrator = StereoCalibration(
        chessboard_size=(9, 6),  # 체스보드 내부 코너 수
        square_size=25.0,  # 체스보드 한 칸 크기 (mm)
        save_dir="data",
    )

    # 캘리브레이션 이미지 캡처
    print("체스보드 패턴을 준비해주세요.")
    print("체스보드를 다양한 각도와 위치에서 촬영합니다.")
    print()

    images_left, images_right = calibrator.capture_calibration_images(
        cap_left, cap_right, num_images=20, display=True
    )

    # 카메라 해제
    cap_left.release()
    cap_right.release()
    cv2.destroyAllWindows()

    if len(images_left) < 10:
        print()
        print("에러: 충분한 캘리브레이션 이미지를 캡처하지 못했습니다.")
        print(f"캡처된 이미지 수: {len(images_left)}")
        print("최소 10장 이상 필요합니다.")
        return

    print()
    print(f"총 {len(images_left)}장의 이미지를 캡처했습니다.")
    print()

    # 캘리브레이션 수행
    print("캘리브레이션 진행 중...")
    print("(시간이 걸릴 수 있습니다)")
    print()

    success = calibrator.calibrate_cameras(images_left, images_right)

    if success:
        print()
        print("✓ 캘리브레이션 성공!")
        print()

        # 캘리브레이션 정보 출력
        calibrator.print_calibration_info()

        # 결과 저장
        print()
        if calibrator.save_calibration():
            print("✓ 캘리브레이션 데이터가 저장되었습니다.")
            print(f"  저장 위치: data/stereo_calibration.pkl")
        else:
            print("✗ 캘리브레이션 데이터 저장 실패")
    else:
        print()
        print("✗ 캘리브레이션 실패")
        print("다시 시도해주세요.")

    print()
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

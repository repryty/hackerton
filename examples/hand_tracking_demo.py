"""
3D 손 추적 예제 스크립트

스테레오 카메라로부터 실시간으로 손의 3D 위치를 추적합니다.
"""

import cv2
import sys
from pathlib import Path
import numpy as np

# 프로젝트 루트를 Python 경로에 추가
sys.path.append(str(Path(__file__).parent.parent))

from modules.stereo_calibration import StereoCalibration
from modules.hand_tracker_3d import HandTracker3D


def draw_3d_info(frame, hands_3d, fps=0):
    """프레임에 3D 정보를 그립니다."""
    y_offset = 30

    # FPS 표시
    cv2.putText(
        frame,
        f"FPS: {fps:.1f}",
        (10, y_offset),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        (0, 255, 0),
        2,
    )
    y_offset += 30

    # 감지된 손 정보
    cv2.putText(
        frame,
        f"Hands detected: {len(hands_3d)}",
        (10, y_offset),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        (0, 255, 0),
        2,
    )
    y_offset += 40

    # 각 손의 3D 위치 정보
    for i, hand_data in enumerate(hands_3d):
        handedness = hand_data["handedness"]
        confidence = hand_data["confidence"]

        # 손목 위치
        wrist = hand_data["landmarks_3d"][0]

        # 검지 손가락 끝 위치
        index_tip = hand_data["landmarks_3d"][8]

        cv2.putText(
            frame,
            f"{handedness} Hand (conf: {confidence:.2f})",
            (10, y_offset),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (255, 255, 0),
            2,
        )
        y_offset += 25

        cv2.putText(
            frame,
            f"  Wrist: ({wrist[0]:.1f}, {wrist[1]:.1f}, {wrist[2]:.1f}) mm",
            (10, y_offset),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (255, 255, 255),
            1,
        )
        y_offset += 20

        cv2.putText(
            frame,
            f"  Index: ({index_tip[0]:.1f}, {index_tip[1]:.1f}, {index_tip[2]:.1f}) mm",
            (10, y_offset),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (255, 255, 255),
            1,
        )
        y_offset += 30

    return frame


def main():
    """메인 함수"""

    print("=" * 60)
    print("3D 손 추적 예제")
    print("=" * 60)
    print()

    # 캘리브레이션 데이터 로드
    print("캘리브레이션 데이터 로드 중...")
    calibrator = StereoCalibration(save_dir="data")

    if not calibrator.load_calibration():
        print("에러: 캘리브레이션 데이터를 찾을 수 없습니다.")
        print("먼저 calibrate_cameras.py를 실행하여 캘리브레이션을 수행하세요.")
        return

    print("✓ 캘리브레이션 데이터 로드 완료")
    print()

    # 카메라 초기화
    print("카메라 초기화 중...")
    cap_left = cv2.VideoCapture(0)
    cap_right = cv2.VideoCapture(1)

    if not cap_left.isOpened() or not cap_right.isOpened():
        print("에러: 카메라를 열 수 없습니다.")
        return

    # 해상도 설정
    cap_left.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap_left.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    cap_right.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap_right.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    print("✓ 카메라 초기화 완료")
    print()

    # HandTracker3D 초기화
    print("3D 손 추적기 초기화 중...")
    tracker = HandTracker3D(
        stereo_calib=calibrator,
        max_num_hands=2,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5,
    )
    print("✓ 3D 손 추적기 초기화 완료")
    print()

    print("손을 카메라에 비춰보세요!")
    print("ESC 키를 누르면 종료합니다.")
    print()

    # FPS 계산용
    import time

    prev_time = time.time()
    fps = 0

    try:
        while True:
            # 프레임 읽기
            ret_left, frame_left = cap_left.read()
            ret_right, frame_right = cap_right.read()

            if not ret_left or not ret_right:
                print("카메라에서 프레임을 읽을 수 없습니다.")
                break

            # 3D 손 추적 수행
            hands_3d, output_left, output_right = tracker.process_frame(
                frame_left, frame_right
            )

            # FPS 계산
            curr_time = time.time()
            fps = 1 / (curr_time - prev_time)
            prev_time = curr_time

            # 3D 정보 표시
            output_left = draw_3d_info(output_left, hands_3d, fps)

            # 결과 표시
            combined = np.hstack([output_left, output_right])
            cv2.imshow("3D Hand Tracking (Left | Right)", combined)

            # 손 정보 출력 (콘솔)
            if hands_3d:
                for hand_data in hands_3d:
                    handedness = hand_data["handedness"]

                    # 손가락이 펴져있는지 확인
                    fingers = ["THUMB", "INDEX", "MIDDLE", "RING", "PINKY"]
                    extended = [
                        tracker.is_finger_extended(hand_data, f) for f in fingers
                    ]

                    print(f"{handedness} Hand - Fingers: ", end="")
                    for i, finger in enumerate(fingers):
                        if extended[i]:
                            print(f"{finger}✓ ", end="")
                        else:
                            print(f"{finger}✗ ", end="")
                    print()

            # 키 입력 처리
            key = cv2.waitKey(1) & 0xFF
            if key == 27:  # ESC
                break

    finally:
        # 정리
        print()
        print("종료 중...")
        tracker.close()
        cap_left.release()
        cap_right.release()
        cv2.destroyAllWindows()
        print("✓ 종료 완료")


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

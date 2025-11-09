"""
라즈베리파이 5 스테레오 비전 및 모터 제어 시스템

메인 애플리케이션 파일:
- 스테레오 카메라에서 손의 3D 좌표 추적
- 검지손가락이 테이블에 닿을 때 가상 그래프와의 충돌 감지
- 충돌 시 진동모터 작동
"""

import sys
import logging
import time
import yaml
from pathlib import Path
import cv2
import numpy as np

# 프로젝트 루트를 Python 경로에 추가
sys.path.append(str(Path(__file__).parent))

# 모듈 임포트
from modules.stereo_calibration import StereoCalibration
from modules.hand_tracker_3d import HandTracker3D
from modules.vibration_motor import VibrationMotorController

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class VirtualGraph:
    """
    테이블 위의 가상 그래프를 정의하는 클래스
    """

    def __init__(self, graph_points, thickness=20.0):
        """
        Args:
            graph_points: 그래프를 구성하는 3D 점들의 리스트 [(x, y, z), ...]
            thickness: 그래프의 두께 (mm)
        """
        self.graph_points = np.array(graph_points, dtype=np.float32)
        self.thickness = thickness

    def distance_to_graph(self, point):
        """
        주어진 점에서 그래프까지의 최소 거리를 계산

        Args:
            point: 3D 좌표 (x, y, z)

        Returns:
            그래프까지의 최소 거리 (mm)
        """
        point = np.array(point, dtype=np.float32)
        min_distance = float("inf")

        # 그래프의 각 선분에 대해 거리 계산
        for i in range(len(self.graph_points) - 1):
            p1 = self.graph_points[i]
            p2 = self.graph_points[i + 1]

            # 점에서 선분까지의 최소 거리 계산
            distance = self._point_to_segment_distance(point, p1, p2)
            min_distance = min(min_distance, distance)

        return min_distance

    def _point_to_segment_distance(self, point, seg_start, seg_end):
        """
        점에서 선분까지의 최소 거리를 계산

        Args:
            point: 점 좌표
            seg_start: 선분 시작점
            seg_end: 선분 끝점

        Returns:
            최소 거리
        """
        # 선분의 벡터
        seg_vec = seg_end - seg_start
        seg_length_sq = np.dot(seg_vec, seg_vec)

        if seg_length_sq == 0:
            # 선분이 점인 경우
            return np.linalg.norm(point - seg_start)

        # 점을 선분에 투영
        t = max(0, min(1, np.dot(point - seg_start, seg_vec) / seg_length_sq))

        # 선분 위의 가장 가까운 점
        projection = seg_start + t * seg_vec

        # 거리 계산
        return np.linalg.norm(point - projection)

    def is_touching(self, point):
        """
        점이 그래프에 닿았는지 확인

        Args:
            point: 3D 좌표 (x, y, z)

        Returns:
            그래프에 닿았으면 True
        """
        return self.distance_to_graph(point) <= self.thickness


def load_config(config_path="config/config.yaml"):
    """설정 파일을 로드합니다."""
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
        return config
    except Exception as e:
        logger.warning(f"설정 파일 로드 실패: {e}")
        return {}


def draw_info(frame, hands_3d, table_height, graph, vibration_state, fps=0):
    """프레임에 정보를 표시합니다."""
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

    # 테이블 높이 표시
    cv2.putText(
        frame,
        f"Table Height: {table_height:.1f} mm",
        (10, y_offset),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.6,
        (255, 255, 0),
        2,
    )
    y_offset += 30

    # 진동 상태 표시
    color = (0, 0, 255) if vibration_state else (100, 100, 100)
    status = "VIBRATING!" if vibration_state else "Off"
    cv2.putText(
        frame,
        f"Motor: {status}",
        (10, y_offset),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        color,
        2,
    )
    y_offset += 40

    # 손 정보 표시
    for i, hand_data in enumerate(hands_3d):
        handedness = hand_data["handedness"]
        index_tip = hand_data["landmarks_3d"][8]  # 검지손가락 끝

        cv2.putText(
            frame,
            f"{handedness} Index Tip:",
            (10, y_offset),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (255, 255, 0),
            2,
        )
        y_offset += 25

        # 3D 위치
        cv2.putText(
            frame,
            f"  Pos: ({index_tip[0]:.1f}, {index_tip[1]:.1f}, {index_tip[2]:.1f})",
            (10, y_offset),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (255, 255, 255),
            1,
        )
        y_offset += 20

        # 높이 상태
        height = index_tip[1]
        if height >= table_height:
            status = "ON TABLE"
            color = (0, 255, 0)

            # 그래프와의 거리
            distance = graph.distance_to_graph(index_tip)
            cv2.putText(
                frame,
                f"  Graph Dist: {distance:.1f} mm",
                (10, y_offset),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (255, 255, 255),
                1,
            )
            y_offset += 20

            if graph.is_touching(index_tip):
                cv2.putText(
                    frame,
                    f"  Status: TOUCHING GRAPH!",
                    (10, y_offset),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.5,
                    (0, 0, 255),
                    2,
                )
            else:
                cv2.putText(
                    frame,
                    f"  Status: {status}",
                    (10, y_offset),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.5,
                    color,
                    1,
                )
        else:
            status = "ABOVE TABLE"
            color = (100, 100, 100)
            cv2.putText(
                frame,
                f"  Status: {status}",
                (10, y_offset),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                color,
                1,
            )

        y_offset += 30

    return frame


def main():
    """메인 함수"""
    logger.info("=" * 60)
    logger.info("라즈베리파이 5 스테레오 비전 및 모터 제어 시스템")
    logger.info("=" * 60)
    logger.info("")

    # 설정 로드
    config = load_config()

    # 테이블 높이 설정 (mm) - 이 값보다 y 좌표가 크면 테이블에 닿은 것으로 판단
    # y축은 아래로 향하므로 큰 값이 테이블에 가까움
    TABLE_HEIGHT_THRESHOLD = 200.0  # mm (캘리브레이션에 따라 조정 필요)

    # 가상 그래프 정의 (예: 테이블 위의 간단한 곡선)
    # 좌표는 (x, y, z) 형식, y는 테이블 높이에 맞춰 설정
    graph_points = [
        (-100, TABLE_HEIGHT_THRESHOLD, 500),  # 시작점
        (-50, TABLE_HEIGHT_THRESHOLD, 450),
        (0, TABLE_HEIGHT_THRESHOLD, 400),
        (50, TABLE_HEIGHT_THRESHOLD, 450),
        (100, TABLE_HEIGHT_THRESHOLD, 500),  # 끝점
    ]

    virtual_graph = VirtualGraph(graph_points, thickness=30.0)
    logger.info(f"가상 그래프 생성 완료 ({len(graph_points)} 포인트)")

    # 캘리브레이션 데이터 로드
    logger.info("캘리브레이션 데이터 로드 중...")
    calibrator = StereoCalibration(save_dir="data")

    if not calibrator.load_calibration():
        logger.error("캘리브레이션 데이터를 찾을 수 없습니다.")
        logger.error("먼저 examples/calibrate_cameras.py를 실행하세요.")
        return

    logger.info("✓ 캘리브레이션 데이터 로드 완료")

    # 카메라 초기화
    logger.info("카메라 초기화 중...")
    camera_config = config.get("camera", {})
    left_cam_idx = camera_config.get("left_camera_index", 0)
    right_cam_idx = camera_config.get("right_camera_index", 1)

    cap_left = cv2.VideoCapture(left_cam_idx)
    cap_right = cv2.VideoCapture(right_cam_idx)

    if not cap_left.isOpened() or not cap_right.isOpened():
        logger.error("카메라를 열 수 없습니다.")
        return

    # 해상도 설정
    resolution = camera_config.get("resolution", {"width": 640, "height": 480})
    cap_left.set(cv2.CAP_PROP_FRAME_WIDTH, resolution["width"])
    cap_left.set(cv2.CAP_PROP_FRAME_HEIGHT, resolution["height"])
    cap_right.set(cv2.CAP_PROP_FRAME_WIDTH, resolution["width"])
    cap_right.set(cv2.CAP_PROP_FRAME_HEIGHT, resolution["height"])

    logger.info("✓ 카메라 초기화 완료")

    # 3D 손 추적기 초기화
    logger.info("3D 손 추적기 초기화 중...")
    hand_config = config.get("hand_tracking", {})
    tracker = HandTracker3D(
        stereo_calib=calibrator,
        max_num_hands=hand_config.get("max_num_hands", 2),
        min_detection_confidence=hand_config.get("min_detection_confidence", 0.5),
        min_tracking_confidence=hand_config.get("min_tracking_confidence", 0.5),
    )
    logger.info("✓ 3D 손 추적기 초기화 완료")

    # 진동모터 컨트롤러 초기화
    logger.info("진동모터 컨트롤러 초기화 중...")
    motor_config = config.get("motors", {})
    motor_pins = motor_config.get("vibration_motors", {"hand_left": 18, "hand_right": 23})
    simulation_mode = config.get("general", {}).get("simulation_mode", False)

    motor_controller = VibrationMotorController(
        motor_pins=motor_pins,
        pwm_frequency=motor_config.get("pwm_frequency", 1000),
        simulation_mode=simulation_mode,
    )
    logger.info("✓ 진동모터 컨트롤러 초기화 완료")

    logger.info("")
    logger.info("시스템 시작!")
    logger.info("손을 카메라에 비춰주세요.")
    logger.info("검지손가락을 테이블의 그래프 위에 올려보세요.")
    logger.info("ESC 키를 누르면 종료합니다.")
    logger.info("")

    # FPS 계산용
    prev_time = time.time()
    fps = 0

    # 진동 상태 추적
    vibration_active = False

    try:
        while True:
            # 프레임 읽기
            ret_left, frame_left = cap_left.read()
            ret_right, frame_right = cap_right.read()

            if not ret_left or not ret_right:
                logger.error("카메라에서 프레임을 읽을 수 없습니다.")
                break

            # 3D 손 추적 수행
            hands_3d, output_left, output_right = tracker.process_frame(
                frame_left, frame_right
            )

            # FPS 계산
            curr_time = time.time()
            fps = 1 / (curr_time - prev_time)
            prev_time = curr_time

            # 진동 제어 로직
            should_vibrate = False

            for hand_data in hands_3d:
                # 검지손가락 끝 좌표 (인덱스 8)
                index_tip = hand_data["landmarks_3d"][8]
                index_height = index_tip[1]  # y 좌표

                # 검지손가락이 테이블에 닿았는지 확인
                if index_height >= TABLE_HEIGHT_THRESHOLD:
                    # 그래프와의 충돌 확인
                    if virtual_graph.is_touching(index_tip):
                        should_vibrate = True
                        break

            # 진동 상태 업데이트
            if should_vibrate and not vibration_active:
                # 진동 시작
                motor_controller.start_all(intensity=80.0)
                vibration_active = True
                logger.info("진동 시작!")
            elif not should_vibrate and vibration_active:
                # 진동 정지
                motor_controller.stop_all()
                vibration_active = False
                logger.info("진동 정지")

            # 정보 표시
            output_left = draw_info(
                output_left, hands_3d, TABLE_HEIGHT_THRESHOLD, virtual_graph, vibration_active, fps
            )

            # 결과 표시
            combined = np.hstack([output_left, output_right])
            cv2.imshow("Hand Tracking & Vibration Control", combined)

            # 키 입력 처리
            key = cv2.waitKey(1) & 0xFF
            if key == 27:  # ESC
                break

    except KeyboardInterrupt:
        logger.info("\n사용자에 의해 중단되었습니다.")

    finally:
        # 정리
        logger.info("")
        logger.info("시스템 종료 중...")
        motor_controller.stop_all()
        motor_controller.cleanup()
        tracker.close()
        cap_left.release()
        cap_right.release()
        cv2.destroyAllWindows()
        logger.info("✓ 시스템 종료 완료")
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

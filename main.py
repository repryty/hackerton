"""
라즈베리파이 5 스테레오 비전 및 모터 제어 시스템 (Advanced)

메인 애플리케이션 파일:
- Gemini API 음성 명령으로 수학 방정식 입력
- 다중 그래프 동시 표시 및 관리
- 스테레오 카메라에서 손의 3D 좌표 추적 (단일 손)
- 2개 진동모터로 세기 조절 (테이블 진동 전파)
- 카메라 인식 범위 실시간 조절
"""

import sys
import logging
import time
import yaml
import os
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import cv2
import numpy as np
import RPi.GPIO as GPIO

# 프로젝트 루트를 Python 경로에 추가
sys.path.append(str(Path(__file__).parent))

# 모듈 임포트
from modules.stereo_calibration import StereoCalibration
from modules.hand_tracker_3d import HandTracker3D
from modules.vibration_motor import VibrationMotorController
from modules.gemini_agent_multimodal import GeminiAudioAgent

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class CoordinateSystem:
    """
    카메라 인식 범위 좌표계 관리 클래스
    """
    
    def __init__(self, x_min=-300, x_max=300, z_min=200, z_max=800, table_height=200):
        """
        Args:
            x_min, x_max: X축 범위 (mm)
            z_min, z_max: Z축 범위 (mm)
            table_height: 테이블 높이 (mm)
        """
        self.x_min = x_min
        self.x_max = x_max
        self.z_min = z_min
        self.z_max = z_max
        self.table_height = table_height
    
    def adjust_x_range(self, delta: float):
        """X축 범위 조절"""
        self.x_min -= delta
        self.x_max += delta
    
    def adjust_z_range(self, delta: float):
        """Z축 범위 조절"""
        self.z_min -= delta
        self.z_max += delta
    
    def get_range(self) -> Tuple[float, float, float, float]:
        """범위 반환"""
        return self.x_min, self.x_max, self.z_min, self.z_max
    
    def get_info(self) -> str:
        """범위 정보 문자열"""
        return f"X[{self.x_min:.0f}, {self.x_max:.0f}] Z[{self.z_min:.0f}, {self.z_max:.0f}]"


class VirtualGraph:
    """
    테이블 위의 가상 그래프를 정의하는 클래스
    다중 그래프 지원 및 색상 구분
    """

    def __init__(self, name: str, equation=None, x_range=None, 
                 table_height=200.0, z_offset=400.0, thickness=20.0, 
                 num_points=100, color=(255, 255, 255)):
        """
        Args:
            name: 그래프 이름
            equation: y = f(x) 형태의 함수
            x_range: (x_min, x_max) x축 범위 (mm)
            table_height: 테이블 높이 y 좌표 (mm)
            z_offset: 그래프의 z축 기준점 (mm)
            thickness: 그래프의 두께 (mm)
            num_points: 그래프를 구성할 점의 개수
            color: RGB 색상
        """
        self.name = name
        self.table_height = table_height
        self.z_offset = z_offset
        self.thickness = thickness
        self.color = color
        self.equation_str = ""
        self.visible = True
        
        if equation is not None and x_range is not None:
            # 수학 방정식으로부터 그래프 점 생성
            self.graph_points = self._generate_graph_from_equation(
                equation, x_range, num_points
            )
        else:
            # 기본 그래프 (없음)
            self.graph_points = np.array([], dtype=np.float32).reshape(0, 3)
    
    def _generate_graph_from_equation(self, equation, x_range, num_points):
        """
        수학 방정식으로부터 3D 그래프 점들을 생성
        
        Args:
            equation: y = f(x) 함수
            x_range: (x_min, x_max)
            num_points: 생성할 점의 개수
            
        Returns:
            numpy array of shape (num_points, 3) with (x, y, z) coordinates
        """
        x_min, x_max = x_range
        x_values = np.linspace(x_min, x_max, num_points)
        
        graph_points = []
        for x in x_values:
            try:
                # y = f(x) 계산
                y_value = equation(x)
                
                # 3D 좌표 생성: (x, table_height, z)
                # z 좌표는 y_value를 z_offset에 더해서 표현
                z = self.z_offset + y_value
                
                graph_points.append([x, self.table_height, z])
            except:
                # 계산 오류 시 스킵
                continue
        
        return np.array(graph_points, dtype=np.float32)
        
        if equation is not None and x_range is not None:
            # 수학 방정식으로부터 그래프 점 생성
            self.graph_points = self._generate_graph_from_equation(
                equation, x_range, num_points
            )
        else:
            # 기본 그래프 (없음)
            self.graph_points = np.array([], dtype=np.float32).reshape(0, 3)
    
    def _generate_graph_from_equation(self, equation, x_range, num_points):
        """
        수학 방정식으로부터 3D 그래프 점들을 생성
        
        Args:
            equation: y = f(x) 함수
            x_range: (x_min, x_max)
            num_points: 생성할 점의 개수
            
        Returns:
            numpy array of shape (num_points, 3) with (x, y, z) coordinates
        """
        x_min, x_max = x_range
        x_values = np.linspace(x_min, x_max, num_points)
        
        graph_points = []
        for x in x_values:
            try:
                # y = f(x) 계산
                y_value = equation(x)
                
                # 3D 좌표 생성: (x, table_height, z)
                # z 좌표는 y_value를 z_offset에 더해서 표현
                z = self.z_offset + y_value
                
                graph_points.append([x, self.table_height, z])
            except:
                # 계산 오류 시 스킵
                continue
        
        return np.array(graph_points, dtype=np.float32)
    
    def set_equation(self, equation, x_range, num_points=100, equation_str=""):
        """
        새로운 방정식으로 그래프 업데이트
        
        Args:
            equation: y = f(x) 함수
            x_range: (x_min, x_max)
            num_points: 생성할 점의 개수
            equation_str: 방정식 문자열 (표시용)
        """
        self.graph_points = self._generate_graph_from_equation(
            equation, x_range, num_points
        )
        self.equation_str = equation_str
    
    def toggle_visibility(self):
        """가시성 토글"""
        self.visible = not self.visible


class MultiGraphManager:
    """
    다중 그래프 관리자
    """
    
    def __init__(self, coordinate_system: CoordinateSystem):
        """
        Args:
            coordinate_system: 좌표계 객체
        """
        self.graphs: List[VirtualGraph] = []
        self.coordinate_system = coordinate_system
        self.active_graph_index = 0
    
    def add_graph(self, name: str, equation, equation_str: str, 
                  color: Optional[Tuple[int, int, int]] = None) -> VirtualGraph:
        """
        그래프 추가
        
        Args:
            name: 그래프 이름
            equation: y = f(x) 함수
            equation_str: 방정식 문자열
            color: RGB 색상 (None이면 자동 생성)
        """
        if color is None:
            # 무지개 색상 자동 생성
            hue = (len(self.graphs) * 60) % 360
            color = self._hsv_to_rgb(hue, 0.8, 0.9)
        
        graph = VirtualGraph(
            name=name,
            table_height=self.coordinate_system.table_height,
            color=color
        )
        
        x_min, x_max, z_min, z_max = self.coordinate_system.get_range()
        graph.set_equation(equation, (x_min, x_max), equation_str=equation_str)
        
        self.graphs.append(graph)
        logger.info(f"✓ 그래프 추가: {name} ({len(graph.graph_points)} 점)")
        return graph
    
    def remove_graph(self, index: int):
        """그래프 제거"""
        if 0 <= index < len(self.graphs):
            removed = self.graphs.pop(index)
            logger.info(f"✓ 그래프 제거: {removed.name}")
            if self.active_graph_index >= len(self.graphs) and self.graphs:
                self.active_graph_index = len(self.graphs) - 1
    
    def clear_all(self):
        """모든 그래프 제거"""
        self.graphs.clear()
        self.active_graph_index = 0
        logger.info("✓ 모든 그래프 제거")
    
    def get_graph_by_name(self, name: str) -> Optional[VirtualGraph]:
        """이름으로 그래프 찾기"""
        for graph in self.graphs:
            if graph.name == name:
                return graph
        return None
    
    def check_collision(self, point: Tuple[float, float, float]) -> List[Tuple[VirtualGraph, float]]:
        """
        점과 모든 그래프의 충돌 감지
        
        Args:
            point: 3D 좌표 (x, y, z)
            
        Returns:
            [(그래프, 거리), ...] 리스트 (거리 오름차순)
        """
        collisions = []
        
        for graph in self.graphs:
            if not graph.visible or len(graph.graph_points) == 0:
                continue
            
            distance = graph.distance_to_graph(point)
            if distance <= graph.thickness:
                collisions.append((graph, distance))
        
        # 거리 오름차순 정렬
        collisions.sort(key=lambda x: x[1])
        return collisions
    
    def _hsv_to_rgb(self, h: float, s: float, v: float) -> Tuple[int, int, int]:
        """HSV를 RGB로 변환"""
        import colorsys
        r, g, b = colorsys.hsv_to_rgb(h / 360, s, v)
        return (int(r * 255), int(g * 255), int(b * 255))

    def distance_to_graph(self, point):
        """
        주어진 점에서 그래프까지의 최소 거리를 계산

        Args:
            point: 3D 좌표 (x, y, z)

        Returns:
            그래프까지의 최소 거리 (mm)
        """
        if len(self.graph_points) == 0:
            return float("inf")
        
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


def draw_info(frame, hands_3d, graph_manager: MultiGraphManager, 
              coord_system: CoordinateSystem, motor_states: Dict[str, float], 
              fps=0, collision_info: Optional[Tuple] = None):
    """프레임에 정보를 표시합니다."""
    y_offset = 30

    # FPS 표시
    cv2.putText(
        frame,
        f"FPS: {fps:.1f}",
        (10, y_offset),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.6,
        (0, 255, 0),
        2,
    )
    y_offset += 25

    # 좌표계 범위 표시
    cv2.putText(
        frame,
        f"Range: {coord_system.get_info()}",
        (10, y_offset),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.5,
        (255, 255, 255),
        1,
    )
    y_offset += 25

    # 그래프 목록 표시
    cv2.putText(
        frame,
        f"Graphs: {len(graph_manager.graphs)}",
        (10, y_offset),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.5,
        (255, 255, 0),
        1,
    )
    y_offset += 20
    
    for i, graph in enumerate(graph_manager.graphs):
        status_mark = "●" if graph.visible else "○"
        text = f"  {status_mark} {graph.name}: {graph.equation_str}"
        cv2.putText(
            frame,
            text[:50],  # 길이 제한
            (10, y_offset),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.4,
            graph.color,
            1,
        )
        y_offset += 18
    
    y_offset += 10

    # 진동모터 상태 표시
    cv2.putText(
        frame,
        "Motors:",
        (10, y_offset),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.5,
        (255, 255, 255),
        1,
    )
    y_offset += 20
    
    for motor_name, intensity in motor_states.items():
        bar_width = int(intensity * 2)  # 0~200px
        color = (0, 0, 255) if intensity > 0 else (100, 100, 100)
        
        cv2.putText(
            frame,
            f"  {motor_name[-1]}: ",
            (10, y_offset),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.4,
            (255, 255, 255),
            1,
        )
        cv2.rectangle(frame, (50, y_offset - 10), (50 + bar_width, y_offset), color, -1)
        cv2.putText(
            frame,
            f"{intensity:.0f}%",
            (255, y_offset),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.4,
            color,
            1,
        )
        y_offset += 20
    
    y_offset += 10

    # 손 정보 표시 (단일 손만)
    if hands_3d:
        hand_data = hands_3d[0]  # 첫 번째 손만 사용
        index_tip = hand_data["landmarks_3d"][8]  # 검지손가락 끝

        cv2.putText(
            frame,
            "Index Finger:",
            (10, y_offset),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (255, 255, 0),
            1,
        )
        y_offset += 20

        # 3D 위치
        cv2.putText(
            frame,
            f"  Pos: ({index_tip[0]:.0f}, {index_tip[1]:.0f}, {index_tip[2]:.0f})",
            (10, y_offset),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.4,
            (255, 255, 255),
            1,
        )
        y_offset += 18

        # 충돌 정보
        if collision_info:
            graph, distance = collision_info
            cv2.putText(
                frame,
                f"  Touching: {graph.name}",
                (10, y_offset),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.4,
                graph.color,
                2,
            )
            y_offset += 18
            cv2.putText(
                frame,
                f"  Distance: {distance:.1f}mm",
                (10, y_offset),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.4,
                (0, 255, 0),
                1,
            )
        else:
            # 테이블 접촉 상태
            height = index_tip[1]
            if height >= coord_system.table_height:
                status = "ON TABLE"
                color = (0, 255, 0)
            else:
                status = "ABOVE TABLE"
                color = (100, 100, 100)
            
            cv2.putText(
                frame,
                f"  Status: {status}",
                (10, y_offset),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.4,
                color,
                1,
            )

    return frame


def calculate_motor_intensity(collisions: List[Tuple], num_motors: int = 2) -> List[float]:
    """
    충돌 정보로부터 모터 강도 계산
    
    Args:
        collisions: [(그래프, 거리), ...] 리스트
        num_motors: 모터 개수
        
    Returns:
        [motor1_intensity, motor2_intensity, ...] (0~100)
    """
    intensities = [0.0] * num_motors
    
    if not collisions:
        return intensities
    
    # 가장 가까운 그래프 기준
    graph, distance = collisions[0]
    
    # 거리에 반비례하는 강도 (0mm = 100%, thickness = 0%)
    base_intensity = max(0, 100 * (1 - distance / graph.thickness))
    
    # 다중 그래프 접촉 시 강도 분산
    if len(collisions) == 1:
        # 단일 그래프: 모든 모터에 같은 강도
        intensities = [base_intensity] * num_motors
    else:
        # 다중 그래프: 모터별로 차등 강도
        for i in range(min(len(collisions), num_motors)):
            graph_i, dist_i = collisions[i]
            intensity_i = max(0, 100 * (1 - dist_i / graph_i.thickness))
            intensities[i] = intensity_i
    
    return intensities


class ButtonController:
    """
    GPIO 버튼 입력 컨트롤러
    단일 버튼으로 음성 녹음 제어
    """
    
    def __init__(self, button_pin=17):
        """
        Args:
            button_pin: 음성 녹음 버튼 (GPIO 17)
        """
        self.button_pin = button_pin
        self.recording = False
        self.record_start_time = 0
        
        # GPIO 초기화
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.button_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        
        # 디바운싱
        self.last_press = 0
        self.debounce_time = 0.3
        
        logger.info(f"✓ GPIO 버튼 초기화: RecordButton={button_pin}")
    
    def is_button_pressed(self) -> bool:
        """버튼 눌림 감지"""
        current_time = time.time()
        if GPIO.input(self.button_pin) == GPIO.LOW:
            if current_time - self.last_press > self.debounce_time:
                self.last_press = current_time
                return True
        return False
    
    def cleanup(self):
        """GPIO 정리"""
        GPIO.cleanup([self.button_pin])


def main():
    """메인 함수"""
    logger.info("=" * 60)
    logger.info("수학 방정식 그래프 햅틱 피드백 시스템 (Standalone)")
    logger.info("Gemini API 음성 명령 지원 - GPIO 버튼 제어")
    logger.info("=" * 60)
    logger.info("")

    # 설정 로드
    config = load_config()

    # Gemini API 키 로드
    gemini_api_key = os.environ.get('GEMINI_API_KEY', config.get('gemini', {}).get('api_key', None))
    
    # 좌표계 초기화 (조절 가능)
    coord_system = CoordinateSystem(
        x_min=-300, x_max=300,
        z_min=200, z_max=800,
        table_height=200
    )
    logger.info(f"좌표계: {coord_system.get_info()}")
    
    # 다중 그래프 관리자 초기화
    graph_manager = MultiGraphManager(coord_system)
    
    # Gemini 에이전트 초기화
    logger.info("Gemini Audio Agent 초기화 중...")
    gemini_agent = GeminiAudioAgent(api_key=gemini_api_key)
    logger.info("✓ Gemini Agent 초기화 완료")
    
    # GPIO 버튼 컨트롤러 초기화
    button_controller = ButtonController(
        button_pin=config.get('buttons', {}).get('record_pin', 17)
    )

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

    # 3D 손 추적기 초기화 (단일 손만)
    logger.info("3D 손 추적기 초기화 중...")
    hand_config = config.get("hand_tracking", {})
    tracker = HandTracker3D(
        stereo_calib=calibrator,
        max_num_hands=1,  # 한 개의 손만 추적
        min_detection_confidence=hand_config.get("min_detection_confidence", 0.5),
        min_tracking_confidence=hand_config.get("min_tracking_confidence", 0.5),
    )
    logger.info("✓ 3D 손 추적기 초기화 완료 (단일 손 모드)")

    # 진동모터 컨트롤러 초기화 (L298N 모터드라이버 - 2개 모터)
    logger.info("진동모터 컨트롤러 초기화 중...")
    motor_config = config.get("motors", {})
    
    # L298N 모터드라이버: IN1 (GPIO 26), IN2 (GPIO 19), IN3 (GPIO 13), IN4 (GPIO 6)
    # 각 모터는 2개의 IN 핀을 사용하지만, 진동 제어는 IN1과 IN3만 사용
    motor_pins = {
        'motor_1': 26,  # L298N IN1 (모터 1 제어)
        'motor_2': 13   # L298N IN3 (모터 2 제어)
    }
    simulation_mode = config.get("general", {}).get("simulation_mode", False)

    motor_controller = VibrationMotorController(
        motor_pins=motor_pins,
        pwm_frequency=motor_config.get("pwm_frequency", 1000),
        simulation_mode=simulation_mode,
    )
    logger.info(f"✓ 진동모터 초기화 완료 ({len(motor_pins)}개)")

    logger.info("")
    logger.info("=" * 60)
    logger.info("시스템 시작!")
    logger.info("=" * 60)
    logger.info("키보드 단축키:")
    logger.info("  V: 음성으로 방정식 추가")
    logger.info("  T: 텍스트로 방정식 추가")
    logger.info("  D: 마지막 그래프 삭제")
    logger.info("  C: 모든 그래프 삭제")
    logger.info("  +/-: X축 범위 조절")
    logger.info("  [/]: Z축 범위 조절")
    logger.info("  1-9: 그래프 가시성 토글")
    logger.info("  ESC: 종료")
    logger.info("=" * 60)
    logger.info("")

    # FPS 계산용
    prev_time = time.time()
    fps = 0

    # 모터 상태 추적
    motor_states = {name: 0.0 for name in motor_pins.keys()}

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

            # 햅틱 피드백 로직 (다중 그래프 지원)
            collision_info = None
            motor_intensities = [0.0] * len(motor_pins)

            if hands_3d:
                hand_data = hands_3d[0]
                index_tip = hand_data["landmarks_3d"][8]
                index_height = index_tip[1]

                # 테이블 접촉 확인
                if index_height >= coord_system.table_height:
                    # 모든 그래프와 충돌 확인
                    collisions = graph_manager.check_collision(index_tip)
                    
                    if collisions:
                        collision_info = collisions[0]  # 가장 가까운 그래프
                        
                        # 모터 강도 계산
                        motor_intensities = calculate_motor_intensity(collisions, len(motor_pins))

            # 모터 제어
            for i, (motor_name, intensity) in enumerate(zip(motor_pins.keys(), motor_intensities)):
                if intensity > 0:
                    if motor_states[motor_name] == 0:
                        logger.info(f"{motor_name} 시작: {intensity:.0f}%")
                    motor_controller.set_intensity(motor_name, intensity)
                    motor_states[motor_name] = intensity
                else:
                    if motor_states[motor_name] > 0:
                        motor_controller.stop(motor_name)
                        motor_states[motor_name] = 0

            # 정보 표시
            output_left = draw_info(
                output_left, hands_3d, graph_manager, coord_system, 
                motor_states, fps, collision_info
            )

            # 결과 표시
            combined = np.hstack([output_left, output_right])
            
            # 녹음 상태 표시
            if gemini_agent.is_recording:
                cv2.putText(combined, "RECORDING...", (10, 30), 
                           cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
            
            cv2.imshow("Math Graph Haptic System (Gemini)", combined)
            
            # 녹음 중이면 계속 청크 읽기
            if gemini_agent.is_recording:
                gemini_agent.record_chunk()

            # GPIO 버튼 입력 처리 (토글)
            if button_controller.is_button_pressed():
                if not gemini_agent.is_recording:
                    # 녹음 시작
                    gemini_agent.start_recording()
                else:
                    # 녹음 종료 및 처리
                    logger.info("\n🔄 녹음 종료 및 분석 중...")
                    audio_data = gemini_agent.stop_recording()
                    
                    if audio_data:
                        # Gemini로 처리
                        command = gemini_agent.process_audio_command(audio_data)
                        
                        if command:
                            action = command.get('action')
                            
                            if action == 'add_graph':
                                # 그래프 추가
                                graph_manager.add_graph(
                                    name=command['name'],
                                    equation=command['function'],
                                    equation_str=command['equation_str'],
                                    color=command['color']
                                )
                                logger.info(f"✅ 그래프 추가: {command['name']}")
                            
                            elif action == 'delete_graph':
                                # 그래프 삭제
                                mode = command.get('mode', 'last')
                                if mode == 'all':
                                    graph_manager.clear_all()
                                    logger.info("✅ 모든 그래프 삭제")
                                else:
                                    if graph_manager.graphs:
                                        graph_manager.remove_graph(len(graph_manager.graphs) - 1)
                                        logger.info("✅ 마지막 그래프 삭제")
                            
                            elif action == 'toggle_graph':
                                # 그래프 토글
                                idx = command.get('index', 0)
                                if 0 <= idx < len(graph_manager.graphs):
                                    graph_manager.graphs[idx].toggle_visibility()
                                    status = "표시" if graph_manager.graphs[idx].visible else "숨김"
                                    logger.info(f"✅ 그래프 {idx+1} {status}")
                        else:
                            logger.warning("❌ 명령을 인식하지 못했습니다")

            # ESC 키만 유지 (비상 종료용)
            key = cv2.waitKey(1) & 0xFF
            if key == 27:  # ESC
                break

    except KeyboardInterrupt:
        logger.info("\n사용자에 의해 중단되었습니다.")

    finally:
        # 정리
        logger.info("")
        logger.info("시스템 종료 중...")
        gemini_agent.cleanup()
        button_controller.cleanup()
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

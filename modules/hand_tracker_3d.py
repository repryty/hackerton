"""
3D 손 추적 모듈

Mediapipe를 사용하여 스테레오 카메라로부터 실시간으로 손의 3D 위치를 추적합니다.
"""

import cv2
import numpy as np
import mediapipe as mp
from typing import List, Tuple, Optional, Dict
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class HandTracker3D:
    """
    3D 손 추적 클래스

    Mediapipe Hand Landmarker를 사용하여 양손의 2D 랜드마크를 감지하고,
    스테레오 비전을 통해 3D 좌표를 계산합니다.
    """

    def __init__(
        self,
        stereo_calib,
        max_num_hands: int = 2,
        min_detection_confidence: float = 0.5,
        min_tracking_confidence: float = 0.5,
    ):
        """
        Args:
            stereo_calib: StereoCalibration 객체 (캘리브레이션 데이터 필요)
            max_num_hands: 감지할 최대 손 개수
            min_detection_confidence: 손 감지 최소 신뢰도
            min_tracking_confidence: 손 추적 최소 신뢰도
        """
        self.stereo_calib = stereo_calib
        self.max_num_hands = max_num_hands

        # Mediapipe Hands 초기화
        self.mp_hands = mp.solutions.hands
        self.mp_drawing = mp.solutions.drawing_utils
        self.mp_drawing_styles = mp.solutions.drawing_styles

        self.hands_left = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=max_num_hands,
            min_detection_confidence=min_detection_confidence,
            min_tracking_confidence=min_tracking_confidence,
        )

        self.hands_right = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=max_num_hands,
            min_detection_confidence=min_detection_confidence,
            min_tracking_confidence=min_tracking_confidence,
        )

        # 손가락 관절 이름 (Mediapipe 순서)
        self.landmark_names = [
            "WRIST",
            "THUMB_CMC",
            "THUMB_MCP",
            "THUMB_IP",
            "THUMB_TIP",
            "INDEX_FINGER_MCP",
            "INDEX_FINGER_PIP",
            "INDEX_FINGER_DIP",
            "INDEX_FINGER_TIP",
            "MIDDLE_FINGER_MCP",
            "MIDDLE_FINGER_PIP",
            "MIDDLE_FINGER_DIP",
            "MIDDLE_FINGER_TIP",
            "RING_FINGER_MCP",
            "RING_FINGER_PIP",
            "RING_FINGER_DIP",
            "RING_FINGER_TIP",
            "PINKY_MCP",
            "PINKY_PIP",
            "PINKY_DIP",
            "PINKY_TIP",
        ]

        logger.info("HandTracker3D 초기화 완료")

    def process_frame(
        self, frame_left: np.ndarray, frame_right: np.ndarray
    ) -> Tuple[List[Dict], np.ndarray, np.ndarray]:
        """
        스테레오 프레임을 처리하여 3D 손 랜드마크를 추출합니다.

        Args:
            frame_left: 왼쪽 카메라 프레임
            frame_right: 오른쪽 카메라 프레임

        Returns:
            (3D 손 데이터 리스트, 처리된 왼쪽 프레임, 처리된 오른쪽 프레임)

            3D 손 데이터 형식:
            {
                'handedness': 'Left' 또는 'Right',
                'landmarks_3d': [(x, y, z), ...],  # 21개 랜드마크의 3D 좌표 (mm)
                'landmarks_2d_left': [(x, y), ...],  # 왼쪽 이미지의 2D 좌표
                'landmarks_2d_right': [(x, y), ...],  # 오른쪽 이미지의 2D 좌표
                'confidence': float  # 감지 신뢰도
            }
        """
        # 이미지를 rectify
        rect_left, rect_right = self.stereo_calib.rectify_images(
            frame_left, frame_right
        )

        # RGB로 변환 (Mediapipe 입력)
        rgb_left = cv2.cvtColor(rect_left, cv2.COLOR_BGR2RGB)
        rgb_right = cv2.cvtColor(rect_right, cv2.COLOR_BGR2RGB)

        # 손 감지 수행
        results_left = self.hands_left.process(rgb_left)
        results_right = self.hands_right.process(rgb_right)

        hands_3d = []

        # 시각화용 프레임 복사
        output_left = rect_left.copy()
        output_right = rect_right.copy()

        # 양쪽 카메라에서 손이 감지된 경우
        if results_left.multi_hand_landmarks and results_right.multi_hand_landmarks:
            # 각 손에 대해 매칭 시도
            for idx_left, (hand_landmarks_left, handedness_left) in enumerate(
                zip(results_left.multi_hand_landmarks, results_left.multi_handedness)
            ):
                # 가장 유사한 오른쪽 손 찾기
                best_match_idx = self._find_matching_hand(
                    hand_landmarks_left, results_right.multi_hand_landmarks
                )

                if best_match_idx is not None:
                    hand_landmarks_right = results_right.multi_hand_landmarks[
                        best_match_idx
                    ]

                    # 3D 좌표 계산
                    landmarks_3d = self._triangulate_landmarks(
                        hand_landmarks_left, hand_landmarks_right, rect_left.shape
                    )

                    if landmarks_3d is not None:
                        hand_data = {
                            "handedness": handedness_left.classification[0].label,
                            "landmarks_3d": landmarks_3d,
                            "landmarks_2d_left": self._extract_2d_landmarks(
                                hand_landmarks_left, rect_left.shape
                            ),
                            "landmarks_2d_right": self._extract_2d_landmarks(
                                hand_landmarks_right, rect_right.shape
                            ),
                            "confidence": handedness_left.classification[0].score,
                        }
                        hands_3d.append(hand_data)

                        # 시각화
                        self.mp_drawing.draw_landmarks(
                            output_left,
                            hand_landmarks_left,
                            self.mp_hands.HAND_CONNECTIONS,
                            self.mp_drawing_styles.get_default_hand_landmarks_style(),
                            self.mp_drawing_styles.get_default_hand_connections_style(),
                        )

                        self.mp_drawing.draw_landmarks(
                            output_right,
                            hand_landmarks_right,
                            self.mp_hands.HAND_CONNECTIONS,
                            self.mp_drawing_styles.get_default_hand_landmarks_style(),
                            self.mp_drawing_styles.get_default_hand_connections_style(),
                        )

        return hands_3d, output_left, output_right

    def _extract_2d_landmarks(
        self, hand_landmarks, image_shape: Tuple[int, int, int]
    ) -> List[Tuple[float, float]]:
        """
        Mediapipe 랜드마크를 픽셀 좌표로 변환합니다.

        Args:
            hand_landmarks: Mediapipe hand landmarks
            image_shape: 이미지 크기 (height, width, channels)

        Returns:
            [(x, y), ...] 픽셀 좌표 리스트
        """
        h, w = image_shape[:2]
        landmarks_2d = []

        for landmark in hand_landmarks.landmark:
            x = landmark.x * w
            y = landmark.y * h
            landmarks_2d.append((x, y))

        return landmarks_2d

    def _find_matching_hand(self, hand_left, hands_right: List) -> Optional[int]:
        """
        왼쪽 카메라의 손과 가장 유사한 오른쪽 카메라의 손을 찾습니다.

        Args:
            hand_left: 왼쪽 카메라의 손 랜드마크
            hands_right: 오른쪽 카메라의 손 랜드마크 리스트

        Returns:
            가장 유사한 손의 인덱스 (None이면 매칭 실패)
        """
        if not hands_right:
            return None

        # 손목(WRIST) 위치를 기준으로 y 좌표가 유사한 손을 찾음
        wrist_y_left = hand_left.landmark[0].y

        min_diff = float("inf")
        best_idx = None

        for idx, hand_right in enumerate(hands_right):
            wrist_y_right = hand_right.landmark[0].y
            diff = abs(wrist_y_left - wrist_y_right)

            if diff < min_diff:
                min_diff = diff
                best_idx = idx

        # y 좌표 차이가 0.1 (정규화 좌표) 이하인 경우만 매칭으로 인정
        if min_diff < 0.1:
            return best_idx

        return None

    def _triangulate_landmarks(
        self, landmarks_left, landmarks_right, image_shape: Tuple[int, int, int]
    ) -> Optional[List[Tuple[float, float, float]]]:
        """
        스테레오 삼각측량을 통해 3D 좌표를 계산합니다.

        Args:
            landmarks_left: 왼쪽 카메라의 손 랜드마크
            landmarks_right: 오른쪽 카메라의 손 랜드마크
            image_shape: 이미지 크기

        Returns:
            [(x, y, z), ...] 3D 좌표 리스트 (mm 단위) 또는 None
        """
        if self.stereo_calib.Q is None:
            logger.error("캘리브레이션 데이터가 없습니다.")
            return None

        h, w = image_shape[:2]
        landmarks_3d = []

        for lm_left, lm_right in zip(landmarks_left.landmark, landmarks_right.landmark):
            # 픽셀 좌표로 변환
            x_left = lm_left.x * w
            y_left = lm_left.y * h
            x_right = lm_right.x * w
            # y_right = lm_right.y * h  # disparity 계산에는 x만 사용

            # Disparity 계산
            disparity = x_left - x_right

            if abs(disparity) < 1.0:  # disparity가 너무 작으면 스킵
                landmarks_3d.append((0.0, 0.0, 0.0))
                continue

            # 3D 좌표 재구성
            # Q 행렬을 사용한 역투영
            point_3d = cv2.perspectiveTransform(
                np.array([[[x_left, y_left, disparity]]], dtype=np.float32),
                self.stereo_calib.Q,
            )[0][0]

            # 동차 좌표를 일반 좌표로 변환
            if point_3d[3] != 0:
                x = point_3d[0] / point_3d[3]
                y = point_3d[1] / point_3d[3]
                z = point_3d[2] / point_3d[3]
                landmarks_3d.append((float(x), float(y), float(z)))
            else:
                landmarks_3d.append((0.0, 0.0, 0.0))

        return landmarks_3d

    def get_fingertip_positions(
        self, hand_data: Dict
    ) -> Dict[str, Tuple[float, float, float]]:
        """
        손가락 끝의 3D 위치를 추출합니다.

        Args:
            hand_data: process_frame에서 반환된 손 데이터

        Returns:
            {'THUMB': (x, y, z), 'INDEX': (x, y, z), ...}
        """
        fingertip_indices = {
            "THUMB": 4,
            "INDEX": 8,
            "MIDDLE": 12,
            "RING": 16,
            "PINKY": 20,
        }

        fingertips = {}
        landmarks_3d = hand_data["landmarks_3d"]

        for finger_name, idx in fingertip_indices.items():
            fingertips[finger_name] = landmarks_3d[idx]

        return fingertips

    def get_wrist_position(self, hand_data: Dict) -> Tuple[float, float, float]:
        """
        손목의 3D 위치를 반환합니다.

        Args:
            hand_data: process_frame에서 반환된 손 데이터

        Returns:
            (x, y, z) 손목 좌표 (mm)
        """
        return hand_data["landmarks_3d"][0]

    def is_finger_extended(self, hand_data: Dict, finger: str) -> bool:
        """
        특정 손가락이 펴져있는지 판단합니다.

        Args:
            hand_data: process_frame에서 반환된 손 데이터
            finger: 손가락 이름 ('THUMB', 'INDEX', 'MIDDLE', 'RING', 'PINKY')

        Returns:
            손가락이 펴져있으면 True
        """
        finger_indices = {
            "THUMB": [1, 2, 3, 4],
            "INDEX": [5, 6, 7, 8],
            "MIDDLE": [9, 10, 11, 12],
            "RING": [13, 14, 15, 16],
            "PINKY": [17, 18, 19, 20],
        }

        if finger not in finger_indices:
            return False

        indices = finger_indices[finger]
        landmarks_3d = hand_data["landmarks_3d"]

        # 손가락 관절들의 z 좌표를 비교
        # 엄지는 x 좌표로 비교 (다른 방향)
        if finger == "THUMB":
            handedness = hand_data["handedness"]
            tip_x = landmarks_3d[indices[-1]][0]
            base_x = landmarks_3d[indices[0]][0]

            if handedness == "Right":
                return tip_x > base_x
            else:
                return tip_x < base_x
        else:
            # 다른 손가락은 끝이 기저부보다 멀리 있는지 확인
            tip_y = landmarks_3d[indices[-1]][1]
            base_y = landmarks_3d[indices[0]][1]
            return tip_y < base_y  # y축이 아래로 향하므로

    def close(self):
        """리소스를 해제합니다."""
        self.hands_left.close()
        self.hands_right.close()
        logger.info("HandTracker3D 종료")

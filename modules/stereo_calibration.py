"""
스테레오 카메라 캘리브레이션 모듈

두 개의 카메라 사이의 상대적인 위치 정보를 계산하고 저장합니다.
체스보드 패턴을 사용하여 카메라 파라미터와 스테레오 관계를 추출합니다.
"""

import cv2
import numpy as np
import pickle
from pathlib import Path
from typing import Tuple, List
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class StereoCalibration:
    """
    스테레오 카메라 캘리브레이션 클래스

    체스보드 패턴을 사용하여 두 카메라의 내부/외부 파라미터를 계산하고
    스테레오 비전을 위한 rectification 맵을 생성합니다.
    """

    def __init__(
        self,
        chessboard_size: Tuple[int, int] = (9, 6),
        square_size: float = 25.0,  # mm
        save_dir: str = "data",
    ):
        """
        Args:
            chessboard_size: 체스보드 내부 코너 수 (가로, 세로)
            square_size: 체스보드 한 칸의 크기 (mm)
            save_dir: 캘리브레이션 데이터를 저장할 디렉토리
        """
        self.chessboard_size = chessboard_size
        self.square_size = square_size
        self.save_dir = Path(save_dir)
        self.save_dir.mkdir(exist_ok=True)

        # 캘리브레이션 결과 저장 변수
        self.camera_matrix_left = None
        self.dist_coeffs_left = None
        self.camera_matrix_right = None
        self.dist_coeffs_right = None
        self.R = None  # Rotation matrix
        self.T = None  # Translation vector
        self.E = None  # Essential matrix
        self.F = None  # Fundamental matrix

        # Rectification 맵
        self.map1_left = None
        self.map2_left = None
        self.map1_right = None
        self.map2_right = None
        self.Q = None  # Disparity-to-depth mapping matrix

        # 3D 좌표 계산용
        self._object_points = self._create_object_points()

    def _create_object_points(self) -> np.ndarray:
        """체스보드의 3D 좌표를 생성합니다."""
        objp = np.zeros(
            (self.chessboard_size[0] * self.chessboard_size[1], 3), np.float32
        )
        objp[:, :2] = np.mgrid[
            0 : self.chessboard_size[0], 0 : self.chessboard_size[1]
        ].T.reshape(-1, 2)
        objp *= self.square_size
        return objp

    def capture_calibration_images(
        self, cap_left, cap_right, num_images: int = 20, display: bool = True
    ) -> Tuple[List[np.ndarray], List[np.ndarray]]:
        """
        캘리브레이션용 이미지를 캡처합니다.

        Args:
            cap_left: 왼쪽 카메라 VideoCapture 객체
            cap_right: 오른쪽 카메라 VideoCapture 객체
            num_images: 캡처할 이미지 수
            display: 이미지를 화면에 표시할지 여부

        Returns:
            (왼쪽 이미지 리스트, 오른쪽 이미지 리스트)
        """
        images_left = []
        images_right = []

        logger.info(f"체스보드 패턴을 감지하여 {num_images}장의 이미지를 캡처합니다.")
        logger.info("스페이스바: 이미지 캡처, ESC: 종료")

        while len(images_left) < num_images:
            ret_left, frame_left = cap_left.read()
            ret_right, frame_right = cap_right.read()

            if not ret_left or not ret_right:
                logger.error("카메라에서 프레임을 읽을 수 없습니다.")
                break

            gray_left = cv2.cvtColor(frame_left, cv2.COLOR_BGR2GRAY)
            gray_right = cv2.cvtColor(frame_right, cv2.COLOR_BGR2GRAY)

            # 체스보드 코너 찾기
            ret_left, corners_left = cv2.findChessboardCorners(
                gray_left, self.chessboard_size, None
            )
            ret_right, corners_right = cv2.findChessboardCorners(
                gray_right, self.chessboard_size, None
            )

            # 디스플레이용 프레임 복사
            display_left = frame_left.copy()
            display_right = frame_right.copy()

            if ret_left and ret_right:
                cv2.drawChessboardCorners(
                    display_left, self.chessboard_size, corners_left, ret_left
                )
                cv2.drawChessboardCorners(
                    display_right, self.chessboard_size, corners_right, ret_right
                )
                status_text = f"체스보드 감지! [{len(images_left)}/{num_images}] - 스페이스바로 캡처"
                color = (0, 255, 0)
            else:
                status_text = f"체스보드를 찾는 중... [{len(images_left)}/{num_images}]"
                color = (0, 0, 255)

            cv2.putText(
                display_left,
                status_text,
                (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                color,
                2,
            )
            cv2.putText(
                display_right,
                status_text,
                (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                color,
                2,
            )

            if display:
                cv2.imshow("Left Camera", display_left)
                cv2.imshow("Right Camera", display_right)

            key = cv2.waitKey(1) & 0xFF

            if key == 32 and ret_left and ret_right:  # 스페이스바
                images_left.append(gray_left)
                images_right.append(gray_right)
                logger.info(f"이미지 {len(images_left)}/{num_images} 캡처됨")

            elif key == 27:  # ESC
                logger.warning("사용자에 의해 캡처가 중단되었습니다.")
                break

        if display:
            cv2.destroyAllWindows()

        return images_left, images_right

    def calibrate_cameras(
        self, images_left: List[np.ndarray], images_right: List[np.ndarray]
    ) -> bool:
        """
        스테레오 카메라 캘리브레이션을 수행합니다.

        Args:
            images_left: 왼쪽 카메라 이미지 리스트
            images_right: 오른쪽 카메라 이미지 리스트

        Returns:
            캘리브레이션 성공 여부
        """
        if len(images_left) == 0 or len(images_right) == 0:
            logger.error("캘리브레이션용 이미지가 없습니다.")
            return False

        logger.info("카메라 캘리브레이션을 시작합니다...")

        # 3D 포인트와 2D 포인트 수집
        obj_points = []  # 3D points in real world space
        img_points_left = []  # 2D points in left image plane
        img_points_right = []  # 2D points in right image plane

        criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)

        for img_left, img_right in zip(images_left, images_right):
            ret_left, corners_left = cv2.findChessboardCorners(
                img_left, self.chessboard_size, None
            )
            ret_right, corners_right = cv2.findChessboardCorners(
                img_right, self.chessboard_size, None
            )

            if ret_left and ret_right:
                obj_points.append(self._object_points)

                # 서브픽셀 정확도로 코너 위치 개선
                corners_left = cv2.cornerSubPix(
                    img_left, corners_left, (11, 11), (-1, -1), criteria
                )
                corners_right = cv2.cornerSubPix(
                    img_right, corners_right, (11, 11), (-1, -1), criteria
                )

                img_points_left.append(corners_left)
                img_points_right.append(corners_right)

        if len(obj_points) < 10:
            logger.error(
                f"충분한 캘리브레이션 이미지가 없습니다. (감지된 이미지: {len(obj_points)}개)"
            )
            return False

        img_size = images_left[0].shape[::-1]

        # 개별 카메라 캘리브레이션
        logger.info("왼쪽 카메라 캘리브레이션 중...")
        ret_left, self.camera_matrix_left, self.dist_coeffs_left, _, _ = (
            cv2.calibrateCamera(obj_points, img_points_left, img_size, None, None)
        )

        logger.info("오른쪽 카메라 캘리브레이션 중...")
        ret_right, self.camera_matrix_right, self.dist_coeffs_right, _, _ = (
            cv2.calibrateCamera(obj_points, img_points_right, img_size, None, None)
        )

        # 스테레오 캘리브레이션
        logger.info("스테레오 캘리브레이션 중...")
        flags = cv2.CALIB_FIX_INTRINSIC

        ret_stereo, _, _, _, _, self.R, self.T, self.E, self.F = cv2.stereoCalibrate(
            obj_points,
            img_points_left,
            img_points_right,
            self.camera_matrix_left,
            self.dist_coeffs_left,
            self.camera_matrix_right,
            self.dist_coeffs_right,
            img_size,
            flags=flags,
            criteria=criteria,
        )

        if ret_stereo:
            logger.info(f"스테레오 캘리브레이션 완료! RMS 에러: {ret_stereo:.4f}")

            # Stereo rectification
            R1, R2, P1, P2, self.Q, _, _ = cv2.stereoRectify(
                self.camera_matrix_left,
                self.dist_coeffs_left,
                self.camera_matrix_right,
                self.dist_coeffs_right,
                img_size,
                self.R,
                self.T,
                alpha=0,
            )

            # Rectification 맵 생성
            self.map1_left, self.map2_left = cv2.initUndistortRectifyMap(
                self.camera_matrix_left,
                self.dist_coeffs_left,
                R1,
                P1,
                img_size,
                cv2.CV_32FC1,
            )
            self.map1_right, self.map2_right = cv2.initUndistortRectifyMap(
                self.camera_matrix_right,
                self.dist_coeffs_right,
                R2,
                P2,
                img_size,
                cv2.CV_32FC1,
            )

            logger.info("Rectification 맵 생성 완료")
            return True
        else:
            logger.error("스테레오 캘리브레이션 실패")
            return False

    def save_calibration(self, filename: str = "stereo_calibration.pkl") -> bool:
        """
        캘리브레이션 결과를 파일로 저장합니다.

        Args:
            filename: 저장할 파일명

        Returns:
            저장 성공 여부
        """
        if self.camera_matrix_left is None:
            logger.error("저장할 캘리브레이션 데이터가 없습니다.")
            return False

        filepath = self.save_dir / filename

        calib_data = {
            "camera_matrix_left": self.camera_matrix_left,
            "dist_coeffs_left": self.dist_coeffs_left,
            "camera_matrix_right": self.camera_matrix_right,
            "dist_coeffs_right": self.dist_coeffs_right,
            "R": self.R,
            "T": self.T,
            "E": self.E,
            "F": self.F,
            "map1_left": self.map1_left,
            "map2_left": self.map2_left,
            "map1_right": self.map1_right,
            "map2_right": self.map2_right,
            "Q": self.Q,
            "chessboard_size": self.chessboard_size,
            "square_size": self.square_size,
        }

        try:
            with open(filepath, "wb") as f:
                pickle.dump(calib_data, f)
            logger.info(f"캘리브레이션 데이터 저장 완료: {filepath}")
            return True
        except Exception as e:
            logger.error(f"캘리브레이션 데이터 저장 실패: {e}")
            return False

    def load_calibration(self, filename: str = "stereo_calibration.pkl") -> bool:
        """
        저장된 캘리브레이션 결과를 불러옵니다.

        Args:
            filename: 불러올 파일명

        Returns:
            로드 성공 여부
        """
        filepath = self.save_dir / filename

        if not filepath.exists():
            logger.error(f"캘리브레이션 파일을 찾을 수 없습니다: {filepath}")
            return False

        try:
            with open(filepath, "rb") as f:
                calib_data = pickle.load(f)

            self.camera_matrix_left = calib_data["camera_matrix_left"]
            self.dist_coeffs_left = calib_data["dist_coeffs_left"]
            self.camera_matrix_right = calib_data["camera_matrix_right"]
            self.dist_coeffs_right = calib_data["dist_coeffs_right"]
            self.R = calib_data["R"]
            self.T = calib_data["T"]
            self.E = calib_data["E"]
            self.F = calib_data["F"]
            self.map1_left = calib_data["map1_left"]
            self.map2_left = calib_data["map2_left"]
            self.map1_right = calib_data["map1_right"]
            self.map2_right = calib_data["map2_right"]
            self.Q = calib_data["Q"]
            self.chessboard_size = calib_data["chessboard_size"]
            self.square_size = calib_data["square_size"]

            logger.info(f"캘리브레이션 데이터 로드 완료: {filepath}")
            return True
        except Exception as e:
            logger.error(f"캘리브레이션 데이터 로드 실패: {e}")
            return False

    def rectify_images(
        self, img_left: np.ndarray, img_right: np.ndarray
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        스테레오 이미지를 rectify합니다.

        Args:
            img_left: 왼쪽 카메라 이미지
            img_right: 오른쪽 카메라 이미지

        Returns:
            (rectified 왼쪽 이미지, rectified 오른쪽 이미지)
        """
        if self.map1_left is None:
            logger.error(
                "Rectification 맵이 없습니다. 먼저 캘리브레이션을 수행하거나 로드하세요."
            )
            return img_left, img_right

        rect_left = cv2.remap(
            img_left, self.map1_left, self.map2_left, cv2.INTER_LINEAR
        )
        rect_right = cv2.remap(
            img_right, self.map1_right, self.map2_right, cv2.INTER_LINEAR
        )

        return rect_left, rect_right

    def get_baseline(self) -> float:
        """
        두 카메라 사이의 거리(baseline)를 반환합니다.

        Returns:
            Baseline (mm)
        """
        if self.T is None:
            logger.error("캘리브레이션 데이터가 없습니다.")
            return 0.0

        baseline = np.linalg.norm(self.T)
        return baseline

    def print_calibration_info(self):
        """캘리브레이션 정보를 출력합니다."""
        if self.camera_matrix_left is None:
            logger.warning("캘리브레이션 데이터가 없습니다.")
            return

        print("\n=== 스테레오 캘리브레이션 정보 ===")
        print(f"\n베이스라인 (두 카메라 간 거리): {self.get_baseline():.2f} mm")
        print(f"\n왼쪽 카메라 매트릭스:\n{self.camera_matrix_left}")
        print(f"\n오른쪽 카메라 매트릭스:\n{self.camera_matrix_right}")
        print(f"\n회전 행렬 R:\n{self.R}")
        print(f"\n이동 벡터 T:\n{self.T.flatten()}")

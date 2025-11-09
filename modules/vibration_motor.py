"""
진동모터 제어 모듈

라즈베리파이의 GPIO 핀을 사용하여 진동모터를 제어합니다.
PWM을 통한 진동 강도 조절과 패턴 재생을 지원합니다.
"""

import time
from typing import Dict, List
import logging

try:
    import RPi.GPIO as GPIO

    GPIO_AVAILABLE = True
except (ImportError, RuntimeError):
    GPIO_AVAILABLE = False
    logging.warning("RPi.GPIO를 사용할 수 없습니다. 시뮬레이션 모드로 동작합니다.")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class VibrationMotor:
    """
    진동모터 제어 클래스

    PWM을 사용하여 진동모터의 강도를 제어하고,
    다양한 진동 패턴을 재생할 수 있습니다.
    """

    def __init__(
        self, pin: int, pwm_frequency: int = 1000, simulation_mode: bool = False
    ):
        """
        Args:
            pin: 진동모터가 연결된 GPIO 핀 번호 (BCM)
            pwm_frequency: PWM 주파수 (Hz)
            simulation_mode: 시뮬레이션 모드 (GPIO 없이 테스트용)
        """
        self.pin = pin
        self.pwm_frequency = pwm_frequency
        self.simulation_mode = simulation_mode or not GPIO_AVAILABLE

        self.pwm = None
        self.current_intensity = 0  # 현재 진동 강도 (0-100%)
        self.is_running = False

        if not self.simulation_mode:
            self._setup_gpio()
        else:
            logger.warning("시뮬레이션 모드로 동작합니다.")

        logger.info(f"VibrationMotor 초기화 완료 (Pin: {pin})")

    def _setup_gpio(self):
        """GPIO 핀을 초기화합니다."""
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        GPIO.setup(self.pin, GPIO.OUT)

        # PWM 설정
        self.pwm = GPIO.PWM(self.pin, self.pwm_frequency)
        self.pwm.start(0)

        logger.info(f"GPIO {self.pin} 초기화 완료")

    def set_intensity(self, intensity: float) -> bool:
        """
        진동 강도를 설정합니다.

        Args:
            intensity: 진동 강도 (0.0 ~ 100.0 %)

        Returns:
            설정 성공 여부
        """
        # 강도 범위 제한
        intensity = max(0.0, min(100.0, intensity))

        if not self.simulation_mode and self.pwm:
            self.pwm.ChangeDutyCycle(intensity)

        self.current_intensity = intensity
        self.is_running = intensity > 0

        if self.simulation_mode:
            logger.info(f"[SIM] 진동 강도: {intensity:.1f}%")
        else:
            logger.debug(f"진동 강도: {intensity:.1f}%")

        return True

    def start(self, intensity: float = 100.0):
        """
        진동을 시작합니다.

        Args:
            intensity: 진동 강도 (0.0 ~ 100.0 %)
        """
        self.set_intensity(intensity)
        logger.info(f"진동 시작 (강도: {intensity}%)")

    def stop(self):
        """진동을 정지합니다."""
        self.set_intensity(0)
        logger.info("진동 정지")

    def pulse(self, intensity: float, duration: float):
        """
        일정 시간 동안 진동합니다.

        Args:
            intensity: 진동 강도 (0.0 ~ 100.0 %)
            duration: 진동 시간 (초)
        """
        self.start(intensity)
        time.sleep(duration)
        self.stop()

    def vibrate_pattern(self, pattern: List[Dict]):
        """
        진동 패턴을 재생합니다.

        Args:
            pattern: 진동 패턴 리스트
                예: [
                    {'intensity': 100, 'duration': 0.2},
                    {'intensity': 0, 'duration': 0.1},
                    {'intensity': 50, 'duration': 0.3}
                ]
        """
        logger.info(f"진동 패턴 재생 시작 ({len(pattern)}단계)")

        for i, step in enumerate(pattern):
            intensity = step.get("intensity", 0)
            duration = step.get("duration", 0.1)

            logger.debug(f"  단계 {i + 1}: {intensity}% for {duration}s")
            self.set_intensity(intensity)
            time.sleep(duration)

        self.stop()
        logger.info("진동 패턴 재생 완료")

    def fade_in(
        self, max_intensity: float = 100.0, duration: float = 1.0, steps: int = 20
    ):
        """
        진동을 서서히 증가시킵니다.

        Args:
            max_intensity: 최대 진동 강도 (0.0 ~ 100.0 %)
            duration: 페이드 인 시간 (초)
            steps: 페이드 단계 수
        """
        logger.info(f"페이드 인 시작 (목표: {max_intensity}%, {duration}초)")

        step_delay = duration / steps
        intensity_increment = max_intensity / steps

        for i in range(steps + 1):
            intensity = intensity_increment * i
            self.set_intensity(intensity)
            time.sleep(step_delay)

    def fade_out(self, duration: float = 1.0, steps: int = 20):
        """
        진동을 서서히 감소시킵니다.

        Args:
            duration: 페이드 아웃 시간 (초)
            steps: 페이드 단계 수
        """
        start_intensity = self.current_intensity
        logger.info(f"페이드 아웃 시작 ({start_intensity}% → 0%, {duration}초)")

        step_delay = duration / steps
        intensity_decrement = start_intensity / steps

        for i in range(steps + 1):
            intensity = start_intensity - (intensity_decrement * i)
            self.set_intensity(intensity)
            time.sleep(step_delay)

    def get_intensity(self) -> float:
        """
        현재 진동 강도를 반환합니다.

        Returns:
            현재 진동 강도 (0.0 ~ 100.0 %)
        """
        return self.current_intensity

    def is_vibrating(self) -> bool:
        """
        진동 중인지 확인합니다.

        Returns:
            진동 중이면 True
        """
        return self.is_running

    def cleanup(self):
        """리소스를 정리하고 GPIO를 해제합니다."""
        logger.info("VibrationMotor 종료 중...")

        self.stop()

        if not self.simulation_mode and self.pwm:
            self.pwm.stop()
            GPIO.cleanup(self.pin)
            logger.info("GPIO 정리 완료")

        logger.info("VibrationMotor 종료 완료")

    def __del__(self):
        """소멸자에서 리소스 정리"""
        try:
            self.cleanup()
        except Exception:
            pass


class VibrationMotorController:
    """
    다중 진동모터 제어 클래스

    여러 개의 진동모터를 독립적으로 또는 동기화하여 제어합니다.
    """

    def __init__(
        self,
        motor_pins: Dict[str, int],
        pwm_frequency: int = 1000,
        simulation_mode: bool = False,
    ):
        """
        Args:
            motor_pins: 모터 이름과 핀 번호 딕셔너리
                예: {
                    'left': 18,
                    'right': 23,
                    'top': 24,
                    'bottom': 25
                }
            pwm_frequency: PWM 주파수 (Hz)
            simulation_mode: 시뮬레이션 모드
        """
        self.motor_pins = motor_pins
        self.pwm_frequency = pwm_frequency
        self.simulation_mode = simulation_mode

        # 각 모터 초기화
        self.motors: Dict[str, VibrationMotor] = {}
        for name, pin in motor_pins.items():
            self.motors[name] = VibrationMotor(
                pin=pin, pwm_frequency=pwm_frequency, simulation_mode=simulation_mode
            )

        logger.info(f"VibrationMotorController 초기화 완료 ({len(self.motors)}개 모터)")

    def set_intensity(self, motor_name: str, intensity: float) -> bool:
        """
        특정 모터의 진동 강도를 설정합니다.

        Args:
            motor_name: 모터 이름
            intensity: 진동 강도 (0.0 ~ 100.0 %)

        Returns:
            설정 성공 여부
        """
        if motor_name not in self.motors:
            logger.error(f"존재하지 않는 모터: {motor_name}")
            return False

        return self.motors[motor_name].set_intensity(intensity)

    def set_all_intensity(self, intensity: float):
        """
        모든 모터의 진동 강도를 동시에 설정합니다.

        Args:
            intensity: 진동 강도 (0.0 ~ 100.0 %)
        """
        for motor in self.motors.values():
            motor.set_intensity(intensity)
        logger.info(f"모든 모터 강도 설정: {intensity}%")

    def start(self, motor_name: str, intensity: float = 100.0) -> bool:
        """
        특정 모터를 시작합니다.

        Args:
            motor_name: 모터 이름
            intensity: 진동 강도

        Returns:
            시작 성공 여부
        """
        if motor_name not in self.motors:
            logger.error(f"존재하지 않는 모터: {motor_name}")
            return False

        self.motors[motor_name].start(intensity)
        return True

    def start_all(self, intensity: float = 100.0):
        """모든 모터를 시작합니다."""
        for motor in self.motors.values():
            motor.start(intensity)
        logger.info("모든 모터 시작")

    def stop(self, motor_name: str) -> bool:
        """
        특정 모터를 정지합니다.

        Args:
            motor_name: 모터 이름

        Returns:
            정지 성공 여부
        """
        if motor_name not in self.motors:
            logger.error(f"존재하지 않는 모터: {motor_name}")
            return False

        self.motors[motor_name].stop()
        return True

    def stop_all(self):
        """모든 모터를 정지합니다."""
        for motor in self.motors.values():
            motor.stop()
        logger.info("모든 모터 정지")

    def pulse(self, motor_name: str, intensity: float, duration: float) -> bool:
        """
        특정 모터를 일정 시간 진동시킵니다.

        Args:
            motor_name: 모터 이름
            intensity: 진동 강도
            duration: 진동 시간 (초)

        Returns:
            실행 성공 여부
        """
        if motor_name not in self.motors:
            logger.error(f"존재하지 않는 모터: {motor_name}")
            return False

        self.motors[motor_name].pulse(intensity, duration)
        return True

    def pulse_sequence(self, sequence: List[Dict]):
        """
        여러 모터를 순차적으로 진동시킵니다.

        Args:
            sequence: 진동 시퀀스
                예: [
                    {'motor': 'left', 'intensity': 100, 'duration': 0.2},
                    {'motor': 'right', 'intensity': 100, 'duration': 0.2},
                ]
        """
        logger.info(f"시퀀스 재생 시작 ({len(sequence)}단계)")

        for i, step in enumerate(sequence):
            motor_name = step.get("motor")
            intensity = step.get("intensity", 100)
            duration = step.get("duration", 0.1)

            if motor_name in self.motors:
                logger.debug(
                    f"  단계 {i + 1}: {motor_name} {intensity}% for {duration}s"
                )
                self.motors[motor_name].pulse(intensity, duration)
            else:
                logger.warning(
                    f"  단계 {i + 1}: 모터 '{motor_name}'을 찾을 수 없습니다."
                )

        logger.info("시퀀스 재생 완료")

    def vibrate_pattern_all(self, pattern: List[Dict]):
        """
        모든 모터에 동일한 패턴을 동기화하여 재생합니다.

        Args:
            pattern: 진동 패턴
        """
        logger.info(f"동기화 패턴 재생 시작 ({len(pattern)}단계)")

        for i, step in enumerate(pattern):
            intensity = step.get("intensity", 0)
            duration = step.get("duration", 0.1)

            logger.debug(f"  단계 {i + 1}: 모든 모터 {intensity}% for {duration}s")
            self.set_all_intensity(intensity)
            time.sleep(duration)

        self.stop_all()
        logger.info("동기화 패턴 재생 완료")

    def get_motor_states(self) -> Dict[str, Dict]:
        """
        모든 모터의 상태를 반환합니다.

        Returns:
            {motor_name: {'intensity': float, 'is_running': bool}, ...}
        """
        states = {}
        for name, motor in self.motors.items():
            states[name] = {
                "intensity": motor.get_intensity(),
                "is_running": motor.is_vibrating(),
            }
        return states

    def cleanup(self):
        """모든 모터를 정리합니다."""
        logger.info("VibrationMotorController 종료 중...")

        for motor in self.motors.values():
            motor.cleanup()

        logger.info("VibrationMotorController 종료 완료")

    def __del__(self):
        """소멸자에서 리소스 정리"""
        try:
            self.cleanup()
        except Exception:
            pass


# 미리 정의된 진동 패턴
VIBRATION_PATTERNS = {
    "short_pulse": [{"intensity": 100, "duration": 0.1}],
    "double_pulse": [
        {"intensity": 100, "duration": 0.1},
        {"intensity": 0, "duration": 0.1},
        {"intensity": 100, "duration": 0.1},
    ],
    "triple_pulse": [
        {"intensity": 100, "duration": 0.1},
        {"intensity": 0, "duration": 0.1},
        {"intensity": 100, "duration": 0.1},
        {"intensity": 0, "duration": 0.1},
        {"intensity": 100, "duration": 0.1},
    ],
    "long_pulse": [{"intensity": 100, "duration": 0.5}],
    "fade": [
        {"intensity": 0, "duration": 0.05},
        {"intensity": 20, "duration": 0.05},
        {"intensity": 40, "duration": 0.05},
        {"intensity": 60, "duration": 0.05},
        {"intensity": 80, "duration": 0.05},
        {"intensity": 100, "duration": 0.1},
        {"intensity": 80, "duration": 0.05},
        {"intensity": 60, "duration": 0.05},
        {"intensity": 40, "duration": 0.05},
        {"intensity": 20, "duration": 0.05},
        {"intensity": 0, "duration": 0.05},
    ],
    "heartbeat": [
        {"intensity": 100, "duration": 0.1},
        {"intensity": 0, "duration": 0.1},
        {"intensity": 100, "duration": 0.1},
        {"intensity": 0, "duration": 0.5},
    ],
    "sos": [
        # S: ...
        {"intensity": 100, "duration": 0.1},
        {"intensity": 0, "duration": 0.1},
        {"intensity": 100, "duration": 0.1},
        {"intensity": 0, "duration": 0.1},
        {"intensity": 100, "duration": 0.1},
        {"intensity": 0, "duration": 0.3},
        # O: ---
        {"intensity": 100, "duration": 0.3},
        {"intensity": 0, "duration": 0.1},
        {"intensity": 100, "duration": 0.3},
        {"intensity": 0, "duration": 0.1},
        {"intensity": 100, "duration": 0.3},
        {"intensity": 0, "duration": 0.3},
        # S: ...
        {"intensity": 100, "duration": 0.1},
        {"intensity": 0, "duration": 0.1},
        {"intensity": 100, "duration": 0.1},
        {"intensity": 0, "duration": 0.1},
        {"intensity": 100, "duration": 0.1},
    ],
}

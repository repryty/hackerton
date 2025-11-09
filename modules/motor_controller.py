"""
GPIO 모터 제어 모듈

라즈베리파이의 GPIO 핀을 사용하여 모터 드라이버를 제어합니다.
다양한 모터 드라이버 (L298N, TB6612, DRV8825 등)를 지원합니다.
"""

import time
from typing import Optional, Dict
import logging

try:
    import lgpio

    GPIO_AVAILABLE = True
except (ImportError, RuntimeError):
    GPIO_AVAILABLE = False
    logging.warning("lgpio를 사용할 수 없습니다. 시뮬레이션 모드로 동작합니다.")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MotorController:
    """
    GPIO 모터 제어 클래스

    PWM을 사용하여 모터의 속도와 방향을 제어합니다.
    여러 개의 모터를 독립적으로 제어할 수 있습니다.
    """

    def __init__(
        self,
        motor_configs: Dict[str, Dict],
        pwm_frequency: int = 1000,
        simulation_mode: bool = False,
    ):
        """
        Args:
            motor_configs: 모터 설정 딕셔너리
                예: {
                    'motor1': {
                        'enable_pin': 18,  # PWM 핀
                        'in1_pin': 23,     # 방향 제어 핀 1
                        'in2_pin': 24,     # 방향 제어 핀 2
                        'type': 'l298n'    # 모터 드라이버 타입
                    },
                    ...
                }
            pwm_frequency: PWM 주파수 (Hz)
            simulation_mode: 시뮬레이션 모드 (GPIO 없이 테스트용)
        """
        self.motor_configs = motor_configs
        self.pwm_frequency = pwm_frequency
        self.simulation_mode = simulation_mode or not GPIO_AVAILABLE

        # lgpio 핸들
        self.handle = None
        
        # 모터별 PWM 객체 저장
        self.pwm_objects: Dict[str, Optional[object]] = {}

        # 모터 상태 저장
        self.motor_states: Dict[str, Dict] = {}

        if not self.simulation_mode:
            self._setup_gpio()
        else:
            logger.warning("시뮬레이션 모드로 동작합니다.")
            self._setup_simulation()

        logger.info(f"MotorController 초기화 완료 ({len(motor_configs)}개 모터)")

    def _setup_gpio(self):
        """GPIO 핀을 초기화합니다."""
        try:
            # lgpio 핸들 열기 (gpiochip4는 라즈베리파이 5용)
            self.handle = lgpio.gpiochip_open(4)

            for motor_name, config in self.motor_configs.items():
                enable_pin = config["enable_pin"]
                in1_pin = config["in1_pin"]
                in2_pin = config["in2_pin"]

                # 핀을 출력으로 설정
                lgpio.gpio_claim_output(self.handle, enable_pin)
                lgpio.gpio_claim_output(self.handle, in1_pin)
                lgpio.gpio_claim_output(self.handle, in2_pin)

                # PWM 설정 (초기 duty cycle 0%)
                lgpio.tx_pwm(self.handle, enable_pin, self.pwm_frequency, 0)
                
                # 방향 핀 초기화
                lgpio.gpio_write(self.handle, in1_pin, 0)
                lgpio.gpio_write(self.handle, in2_pin, 0)
                
                self.pwm_objects[motor_name] = enable_pin  # PWM 핀 번호 저장

                # 초기 상태
                self.motor_states[motor_name] = {
                    "speed": 0,
                    "direction": "stop",
                    "enabled": True,
                }

                logger.info(
                    f"모터 '{motor_name}' GPIO 설정 완료 (Enable: {enable_pin}, IN1: {in1_pin}, IN2: {in2_pin})"
                )
        except Exception as e:
            logger.error(f"GPIO 초기화 실패: {e}")
            raise

    def _setup_simulation(self):
        """시뮬레이션 모드를 초기화합니다."""
        for motor_name in self.motor_configs.keys():
            self.pwm_objects[motor_name] = None
            self.motor_states[motor_name] = {
                "speed": 0,
                "direction": "stop",
                "enabled": True,
            }

    def set_motor_speed(
        self, motor_name: str, speed: float, direction: str = "forward"
    ) -> bool:
        """
        모터의 속도와 방향을 설정합니다.

        Args:
            motor_name: 모터 이름
            speed: 속도 (0.0 ~ 100.0 %)
            direction: 방향 ('forward', 'backward', 'stop')

        Returns:
            설정 성공 여부
        """
        if motor_name not in self.motor_configs:
            logger.error(f"존재하지 않는 모터: {motor_name}")
            return False

        # 속도 범위 제한
        speed = max(0.0, min(100.0, speed))

        # 방향 검증
        if direction not in ["forward", "backward", "stop"]:
            logger.error(f"잘못된 방향: {direction}")
            return False

        config = self.motor_configs[motor_name]

        if not self.simulation_mode:
            # 방향 설정
            if direction == "forward":
                lgpio.gpio_write(self.handle, config["in1_pin"], 1)
                lgpio.gpio_write(self.handle, config["in2_pin"], 0)
            elif direction == "backward":
                lgpio.gpio_write(self.handle, config["in1_pin"], 0)
                lgpio.gpio_write(self.handle, config["in2_pin"], 1)
            else:  # stop
                lgpio.gpio_write(self.handle, config["in1_pin"], 0)
                lgpio.gpio_write(self.handle, config["in2_pin"], 0)
                speed = 0

            # 속도 설정 (PWM duty cycle)
            enable_pin = self.pwm_objects[motor_name]
            if enable_pin:
                lgpio.tx_pwm(self.handle, enable_pin, self.pwm_frequency, speed)

        # 상태 업데이트
        self.motor_states[motor_name]["speed"] = speed
        self.motor_states[motor_name]["direction"] = direction

        if self.simulation_mode:
            logger.info(
                f"[SIM] 모터 '{motor_name}': {direction} 방향, 속도 {speed:.1f}%"
            )
        else:
            logger.debug(f"모터 '{motor_name}': {direction} 방향, 속도 {speed:.1f}%")

        return True

    def stop_motor(self, motor_name: str) -> bool:
        """
        특정 모터를 정지시킵니다.

        Args:
            motor_name: 모터 이름

        Returns:
            정지 성공 여부
        """
        return self.set_motor_speed(motor_name, 0, "stop")

    def stop_all_motors(self):
        """모든 모터를 정지시킵니다."""
        for motor_name in self.motor_configs.keys():
            self.stop_motor(motor_name)
        logger.info("모든 모터 정지")

    def move_motor_for_duration(
        self, motor_name: str, speed: float, direction: str, duration: float
    ) -> bool:
        """
        모터를 지정된 시간 동안 동작시킵니다.

        Args:
            motor_name: 모터 이름
            speed: 속도 (0.0 ~ 100.0 %)
            direction: 방향 ('forward', 'backward')
            duration: 동작 시간 (초)

        Returns:
            동작 성공 여부
        """
        if not self.set_motor_speed(motor_name, speed, direction):
            return False

        time.sleep(duration)
        self.stop_motor(motor_name)

        return True

    def get_motor_state(self, motor_name: str) -> Optional[Dict]:
        """
        모터의 현재 상태를 반환합니다.

        Args:
            motor_name: 모터 이름

        Returns:
            모터 상태 딕셔너리 또는 None
        """
        return self.motor_states.get(motor_name)

    def get_all_motor_states(self) -> Dict[str, Dict]:
        """
        모든 모터의 상태를 반환합니다.

        Returns:
            {motor_name: state, ...}
        """
        return self.motor_states.copy()

    def enable_motor(self, motor_name: str) -> bool:
        """
        모터를 활성화합니다.

        Args:
            motor_name: 모터 이름

        Returns:
            활성화 성공 여부
        """
        if motor_name not in self.motor_configs:
            logger.error(f"존재하지 않는 모터: {motor_name}")
            return False

        self.motor_states[motor_name]["enabled"] = True
        logger.info(f"모터 '{motor_name}' 활성화")
        return True

    def disable_motor(self, motor_name: str) -> bool:
        """
        모터를 비활성화합니다.

        Args:
            motor_name: 모터 이름

        Returns:
            비활성화 성공 여부
        """
        if motor_name not in self.motor_configs:
            logger.error(f"존재하지 않는 모터: {motor_name}")
            return False

        self.stop_motor(motor_name)
        self.motor_states[motor_name]["enabled"] = False
        logger.info(f"모터 '{motor_name}' 비활성화")
        return True

    def set_motor_acceleration(
        self,
        motor_name: str,
        target_speed: float,
        direction: str,
        accel_time: float = 1.0,
        steps: int = 20,
    ) -> bool:
        """
        모터를 부드럽게 가속시킵니다.

        Args:
            motor_name: 모터 이름
            target_speed: 목표 속도 (0.0 ~ 100.0 %)
            direction: 방향 ('forward', 'backward')
            accel_time: 가속 시간 (초)
            steps: 가속 단계 수

        Returns:
            가속 성공 여부
        """
        if motor_name not in self.motor_configs:
            logger.error(f"존재하지 않는 모터: {motor_name}")
            return False

        current_speed = self.motor_states[motor_name]["speed"]
        speed_increment = (target_speed - current_speed) / steps
        step_delay = accel_time / steps

        for i in range(steps + 1):
            speed = current_speed + (speed_increment * i)
            self.set_motor_speed(motor_name, speed, direction)
            time.sleep(step_delay)

        return True

    def execute_motor_sequence(self, motor_name: str, sequence: list) -> bool:
        """
        모터 동작 시퀀스를 실행합니다.

        Args:
            motor_name: 모터 이름
            sequence: 동작 시퀀스 리스트
                예: [
                    {'speed': 50, 'direction': 'forward', 'duration': 2.0},
                    {'speed': 0, 'direction': 'stop', 'duration': 0.5},
                    {'speed': 30, 'direction': 'backward', 'duration': 1.0}
                ]

        Returns:
            실행 성공 여부
        """
        if motor_name not in self.motor_configs:
            logger.error(f"존재하지 않는 모터: {motor_name}")
            return False

        logger.info(f"모터 '{motor_name}' 시퀀스 실행 시작 ({len(sequence)}단계)")

        for i, step in enumerate(sequence):
            speed = step.get("speed", 0)
            direction = step.get("direction", "stop")
            duration = step.get("duration", 1.0)

            logger.debug(f"  단계 {i + 1}: {direction} {speed}% for {duration}s")
            self.move_motor_for_duration(motor_name, speed, direction, duration)

        logger.info(f"모터 '{motor_name}' 시퀀스 실행 완료")
        return True

    def cleanup(self):
        """리소스를 정리하고 GPIO를 해제합니다."""
        logger.info("MotorController 종료 중...")

        # 모든 모터 정지
        self.stop_all_motors()

        if not self.simulation_mode and self.handle is not None:
            try:
                # 모든 핀에 대해 PWM 중지 및 정리
                for motor_name, config in self.motor_configs.items():
                    enable_pin = config["enable_pin"]
                    in1_pin = config["in1_pin"]
                    in2_pin = config["in2_pin"]
                    
                    # PWM 중지
                    lgpio.tx_pwm(self.handle, enable_pin, self.pwm_frequency, 0)
                    
                    # 핀 해제
                    lgpio.gpio_free(self.handle, enable_pin)
                    lgpio.gpio_free(self.handle, in1_pin)
                    lgpio.gpio_free(self.handle, in2_pin)
                
                # 핸들 닫기
                lgpio.gpiochip_close(self.handle)
                logger.info("GPIO 정리 완료")
            except Exception as e:
                logger.error(f"GPIO 정리 중 오류: {e}")

        logger.info("MotorController 종료 완료")

    def __del__(self):
        """소멸자에서 리소스 정리"""
        try:
            self.cleanup()
        except Exception:
            pass


class StepperMotorController:
    """
    스테퍼 모터 제어 클래스

    스테퍼 모터 드라이버 (DRV8825, A4988 등)를 사용하여
    정밀한 위치 제어를 수행합니다.
    """

    def __init__(
        self,
        step_pin: int,
        dir_pin: int,
        enable_pin: Optional[int] = None,
        steps_per_revolution: int = 200,
        microsteps: int = 1,
        simulation_mode: bool = False,
    ):
        """
        Args:
            step_pin: STEP 신호 핀
            dir_pin: DIR (방향) 신호 핀
            enable_pin: ENABLE 핀 (선택사항)
            steps_per_revolution: 1회전당 스텝 수
            microsteps: 마이크로스텝 설정 (1, 2, 4, 8, 16, 32)
            simulation_mode: 시뮬레이션 모드
        """
        self.step_pin = step_pin
        self.dir_pin = dir_pin
        self.enable_pin = enable_pin
        self.steps_per_revolution = steps_per_revolution
        self.microsteps = microsteps
        self.simulation_mode = simulation_mode or not GPIO_AVAILABLE

        self.handle = None  # lgpio 핸들
        self.current_position = 0  # 현재 위치 (스텝)
        self.enabled = True

        if not self.simulation_mode:
            self._setup_gpio()
        else:
            logger.warning("스테퍼 모터: 시뮬레이션 모드로 동작합니다.")

        logger.info("StepperMotorController 초기화 완료")

    def _setup_gpio(self):
        """GPIO 핀을 초기화합니다."""
        try:
            # lgpio 핸들 열기 (gpiochip4는 라즈베리파이 5용)
            self.handle = lgpio.gpiochip_open(4)
            
            # 핀을 출력으로 설정
            lgpio.gpio_claim_output(self.handle, self.step_pin)
            lgpio.gpio_claim_output(self.handle, self.dir_pin)

            if self.enable_pin:
                lgpio.gpio_claim_output(self.handle, self.enable_pin)
                lgpio.gpio_write(self.handle, self.enable_pin, 0)  # 활성화
        except Exception as e:
            logger.error(f"StepperMotor GPIO 초기화 실패: {e}")
            raise

    def move_steps(
        self, steps: int, speed: float = 1.0, direction: Optional[str] = None
    ):
        """
        지정된 스텝 수만큼 이동합니다.

        Args:
            steps: 이동할 스텝 수 (양수 또는 음수)
            speed: 속도 배율 (1.0 = 기본 속도)
            direction: 명시적 방향 ('forward' or 'backward', None이면 steps 부호 사용)
        """
        if direction:
            actual_steps = abs(steps)
            clockwise = direction == "forward"
        else:
            actual_steps = abs(steps)
            clockwise = steps >= 0

        # 방향 설정
        if not self.simulation_mode:
            lgpio.gpio_write(self.handle, self.dir_pin, 1 if clockwise else 0)

        # 스텝 신호 생성
        delay = (1.0 / (self.steps_per_revolution * self.microsteps)) / speed

        for i in range(actual_steps):
            if not self.simulation_mode:
                lgpio.gpio_write(self.handle, self.step_pin, 1)
                time.sleep(delay / 2)
                lgpio.gpio_write(self.handle, self.step_pin, 0)
                time.sleep(delay / 2)
            else:
                time.sleep(delay)

        # 위치 업데이트
        if clockwise:
            self.current_position += actual_steps
        else:
            self.current_position -= actual_steps

        if self.simulation_mode:
            logger.info(
                f"[SIM] 스테퍼 모터: {actual_steps} 스텝 이동, 현재 위치: {self.current_position}"
            )

    def move_angle(self, angle: float, speed: float = 1.0):
        """
        지정된 각도만큼 회전합니다.

        Args:
            angle: 회전 각도 (도, degree)
            speed: 속도 배율
        """
        steps = int((angle / 360.0) * self.steps_per_revolution * self.microsteps)
        self.move_steps(steps, speed)

    def move_to_position(self, target_position: int, speed: float = 1.0):
        """
        절대 위치로 이동합니다.

        Args:
            target_position: 목표 위치 (스텝)
            speed: 속도 배율
        """
        steps = target_position - self.current_position
        self.move_steps(steps, speed)

    def reset_position(self):
        """현재 위치를 0으로 리셋합니다."""
        self.current_position = 0
        logger.info("스테퍼 모터 위치 리셋")

    def enable(self):
        """모터를 활성화합니다."""
        if not self.simulation_mode and self.enable_pin:
            lgpio.gpio_write(self.handle, self.enable_pin, 0)
        self.enabled = True
        logger.info("스테퍼 모터 활성화")

    def disable(self):
        """모터를 비활성화합니다."""
        if not self.simulation_mode and self.enable_pin:
            lgpio.gpio_write(self.handle, self.enable_pin, 1)
        self.enabled = False
        logger.info("스테퍼 모터 비활성화")

    def cleanup(self):
        """리소스를 정리합니다."""
        if not self.simulation_mode and self.handle is not None:
            try:
                lgpio.gpio_free(self.handle, self.step_pin)
                lgpio.gpio_free(self.handle, self.dir_pin)
                if self.enable_pin:
                    lgpio.gpio_free(self.handle, self.enable_pin)
                
                lgpio.gpiochip_close(self.handle)
                logger.info("스테퍼 모터 GPIO 정리 완료")
            except Exception as e:
                logger.error(f"스테퍼 모터 GPIO 정리 중 오류: {e}")
        logger.info("StepperMotorController 종료")

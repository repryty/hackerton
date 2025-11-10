import lgpio
import time

# 사용할 GPIO 핀 설정 (BCM 번호 기준)
PWM_GPIO_A = 12  # 모터 A의 속도 제어 (L298N의 ENA 핀에 연결)
PWM_GPIO_B = 13  # 모터 B의 속도 제어 (L298N의 ENB 핀에 연결)

# PWM 설정
PWM_FREQUENCY = 1000  # PWM 주파수 (Hz), L298N은 1~2kHz가 일반적

# 사용할 GPIO 칩 번호 (라즈베리파이 5는 4번 칩을 사용)
CHIP = 4

try:
    # GPIO 칩 열기
    h = lgpio.gpiochip_open(CHIP)

    # GPIO 핀을 출력으로 설정
    lgpio.gpio_claim_output(h, PWM_GPIO_A)
    lgpio.gpio_claim_output(h, PWM_GPIO_B)

    print("PWM 신호를 시작합니다. Ctrl+C를 눌러 종료하세요.")

    # 속도를 0%에서 100%까지 서서히 증가
    print("속도 증가...")
    for duty_cycle in range(0, 101, 5):  # 0부터 100까지 5씩 증가
        # tx_pwm(핸들, GPIO핀, 주파수, 듀티 사이클)
        lgpio.tx_pwm(h, PWM_GPIO_A, PWM_FREQUENCY, duty_cycle)
        lgpio.tx_pwm(h, PWM_GPIO_B, PWM_FREQUENCY, duty_cycle)
        print(f"듀티 사이클: {duty_cycle}%")
        time.sleep(0.1)

    print("\n최고 속도로 2초간 유지...")
    time.sleep(2)

    # 속도를 100%에서 0%까지 서서히 감소
    print("\n속도 감소...")
    for duty_cycle in range(100, -1, -5):  # 100부터 0까지 5씩 감소
        lgpio.tx_pwm(h, PWM_GPIO_A, PWM_FREQUENCY, duty_cycle)
        lgpio.tx_pwm(h, PWM_GPIO_B, PWM_FREQUENCY, duty_cycle)
        print(f"듀티 사이클: {duty_cycle}%")
        time.sleep(0.1)

    print("\n테스트 완료.")

except KeyboardInterrupt:
    print("\n프로그램을 종료합니다.")

finally:
    # PWM 정지 (듀티 사이클 0으로 설정)
    if 'h' in locals() and h >= 0:
        lgpio.tx_pwm(h, PWM_GPIO_A, PWM_FREQUENCY, 0)
        lgpio.tx_pwm(h, PWM_GPIO_B, PWM_FREQUENCY, 0)
        # GPIO 리소스 해제
        lgpio.gpiochip_close(h)
        print("GPIO 리소스가 해제되었습니다.")
# Raspberry Pi 5용 Docker 이미지
# 스테레오 비전, Mediapipe 3D 손 추적, GPIO 모터 제어 지원

FROM python:3.11-bookworm

WORKDIR /app

# 시스템 의존성 설치
RUN apt-get update && apt-get install -y \
    # OpenCV 의존성
    libopencv-dev \
    libatlas-base-dev \
    libhdf5-dev \
    libharfbuzz0b \
    libwebp-dev \
    libtiff-dev \
    libjpeg-dev \
    libopenjp2-7 \
    libavcodec-dev \
    libavformat-dev \
    libswscale-dev \
    libv4l-dev \
    libxvidcore-dev \
    libx264-dev \
    # Qt5 (Qt4는 더 이상 지원되지 않음)
    libqt5gui5 \
    libqt5test5 \
    # 라즈베리파이 카메라 지원
    python3-picamera2 \
    # GPIO 지원
    python3-rpi.gpio \
    python3-lgpio \
    # 기타 유틸리티
    v4l-utils \
    && rm -rf /var/lib/apt/lists/*

# Python 의존성 설치
COPY pyproject.toml ./
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir \
    opencv-python==4.8.1.78 \
    mediapipe==0.10.8 \
    numpy==1.24.3 \
    picamera2 \
    RPi.GPIO

# 애플리케이션 파일 복사
COPY . .

# 권한 설정 (GPIO, 카메라 접근용)
RUN chmod -R 755 /app

# 환경 변수 설정
ENV PYTHONUNBUFFERED=1
ENV DISPLAY=:0

# 컨테이너 시작 시 실행할 명령
CMD ["python", "main.py"]
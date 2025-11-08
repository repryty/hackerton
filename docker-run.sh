# Docker run 옵션 설정
# 라즈베리파이에서 실행 시 필요한 옵션들

# GPIO, 카메라 접근을 위한 privileged 모드
# 디스플레이 지원을 위한 DISPLAY 환경변수

docker run -d \
  --privileged \
  --device /dev/gpiomem \
  --device /dev/video0 \
  --device /dev/video1 \
  -v /dev:/dev \
  -v /sys:/sys \
  -v /tmp/.X11-unix:/tmp/.X11-unix \
  -v $(pwd)/data:/app/data \
  -e DISPLAY=$DISPLAY \
  --name hackerton \
  hackerton:latest

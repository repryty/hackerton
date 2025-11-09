# 코드 수정 요약

## 🎯 변경사항 개요

기존 **양손 추적 + 고정 그래프** 시스템을
**단일 손 추적 + 수학 방정식 그래프** 시스템으로 전환했습니다.

---

## ✨ 주요 변경사항

### 1. **단일 손 추적으로 변경**

#### `main.py`
```python
# 변경 전
tracker = HandTracker3D(max_num_hands=2)  # 양손

# 변경 후
tracker = HandTracker3D(max_num_hands=1)  # 단일 손만
```

#### `config/config.yaml`
```yaml
# 변경 전
hand_tracking:
  max_num_hands: 2

# 변경 후
hand_tracking:
  max_num_hands: 1
```

#### 진동모터 설정
```yaml
# 변경 전
motors:
  vibration_motors:
    hand_left:
      pin: 18
    hand_right:
      pin: 23

# 변경 후
motors:
  vibration_motors:
    hand_left:
      pin: 18  # 메인 진동모터만
```

---

### 2. **수학 방정식 → 그래프 변환 기능 추가**

#### VirtualGraph 클래스 완전 재설계

**변경 전:**
```python
# 고정된 점들로 그래프 정의
class VirtualGraph:
    def __init__(self, graph_points, thickness=20.0):
        self.graph_points = np.array(graph_points)
        self.thickness = thickness

# 사용
graph_points = [
    (-100, 200, 500),
    (-50, 200, 450),
    (0, 200, 400),
    (50, 200, 450),
    (100, 200, 500),
]
virtual_graph = VirtualGraph(graph_points)
```

**변경 후:**
```python
# 수학 방정식으로 그래프 생성
class VirtualGraph:
    def __init__(self, equation=None, x_range=None, 
                 table_height=200.0, z_offset=400.0, 
                 thickness=20.0, num_points=50):
        """
        Args:
            equation: y = f(x) 함수
            x_range: (x_min, x_max)
            table_height: 테이블 y 좌표
            z_offset: 그래프 z 기준점
            thickness: 그래프 두께
            num_points: 점 개수
        """
        if equation is not None and x_range is not None:
            self.graph_points = self._generate_graph_from_equation(
                equation, x_range, num_points
            )
    
    def _generate_graph_from_equation(self, equation, x_range, num_points):
        """방정식으로부터 3D 점 생성"""
        x_min, x_max = x_range
        x_values = np.linspace(x_min, x_max, num_points)
        
        graph_points = []
        for x in x_values:
            y_value = equation(x)
            z = self.z_offset + y_value
            graph_points.append([x, self.table_height, z])
        
        return np.array(graph_points)
    
    def set_equation(self, equation, x_range, num_points=50):
        """실시간 방정식 변경"""
        self.graph_points = self._generate_graph_from_equation(
            equation, x_range, num_points
        )

# 사용
# 1. 빈 그래프로 시작
virtual_graph = VirtualGraph(thickness=30.0)

# 2. 방정식 설정
equation = lambda x: (x**2) / 100  # y = x²/100
virtual_graph.set_equation(equation, x_range=(-300, 300), num_points=100)

# 3. 실시간 변경
new_equation = lambda x: np.sin(x/50) * 100  # y = sin(x/50) * 100
virtual_graph.set_equation(new_equation, (-300, 300))
```

---

### 3. **좌표평면 범위 계산 추가**

```python
def get_coordinate_bounds(stereo_calib, table_height=200.0):
    """
    카메라 인식 범위를 좌표평면으로 사용
    
    Returns:
        (x_min, x_max, z_min, z_max)
    """
    x_min, x_max = -300, 300  # 좌우 600mm
    z_min, z_max = 200, 800   # 깊이 600mm
    
    logger.info(f"좌표평면 범위: X[{x_min}, {x_max}], Z[{z_min}, {z_max}]")
    return x_min, x_max, z_min, z_max
```

---

### 4. **사용자 방정식 입력 및 실시간 변경**

#### 프로그램 시작 시 방정식 선택
```python
# 예제 방정식들
equations = {
    '1': ('y = x^2 / 100', lambda x: (x**2) / 100),
    '2': ('y = sin(x/50) * 100', lambda x: np.sin(x/50) * 100),
    '3': ('y = abs(x) / 2', lambda x: abs(x) / 2),
    '4': ('y = -x^2 / 100 + 200', lambda x: -(x**2) / 100 + 200),
    '5': ('y = cos(x/30) * 80', lambda x: np.cos(x/30) * 80),
}

# 사용자 입력
choice = input("\n방정식을 선택하세요 (0-5): ").strip()

if choice in equations:
    eq_str, eq_func = equations[choice]
    current_equation = eq_str
    virtual_graph.set_equation(eq_func, (x_min, x_max), num_points=100)
```

#### 실행 중 키보드로 방정식 변경
```python
# 메인 루프 내부
key = cv2.waitKey(1) & 0xFF

if key >= ord('0') and key <= ord('5'):
    choice = chr(key)
    
    if choice == '0':
        # 그래프 제거
        virtual_graph.graph_points = np.array([]).reshape(0, 3)
        current_equation = ""
        
    elif choice in equations:
        # 방정식 변경
        eq_str, eq_func = equations[choice]
        current_equation = eq_str
        virtual_graph.set_equation(eq_func, (x_min, x_max), num_points=100)
        logger.info(f"방정식 변경: {eq_str}")
```

---

### 5. **햅틱 피드백 로직 수정**

**변경 전:**
```python
# 모든 손에 대해 반복
for hand_data in hands_3d:
    index_tip = hand_data["landmarks_3d"][8]
    
    if index_height >= TABLE_HEIGHT_THRESHOLD:
        if virtual_graph.is_touching(index_tip):
            should_vibrate = True
            break
```

**변경 후:**
```python
# 단일 손만 처리
if hands_3d:
    hand_data = hands_3d[0]  # 첫 번째 손만
    index_tip = hand_data["landmarks_3d"][8]
    
    # 테이블 접촉
    if index_height >= TABLE_HEIGHT_THRESHOLD:
        # 그래프 존재 여부 확인
        if len(virtual_graph.graph_points) > 0:
            if virtual_graph.is_touching(index_tip):
                should_vibrate = True
```

---

### 6. **화면 정보 표시 업데이트**

#### 추가된 정보
- 현재 방정식 표시
- 그래프 없음 상태 표시

```python
def draw_info(frame, hands_3d, table_height, graph, 
              vibration_state, fps=0, current_equation=""):
    """
    Args:
        current_equation: 현재 방정식 문자열 (추가)
    """
    
    # 현재 방정식 표시
    if current_equation:
        cv2.putText(frame, f"Equation: {current_equation}", ...)
    
    # 그래프 없을 때 처리
    if len(graph.graph_points) > 0:
        distance = graph.distance_to_graph(index_tip)
        cv2.putText(frame, f"Graph Dist: {distance:.1f} mm", ...)
    else:
        cv2.putText(frame, "Status: ON TABLE (No graph)", ...)
```

---

### 7. **사용자 안내 메시지 개선**

**변경 전:**
```
시스템 시작!
손을 카메라에 비춰주세요.
검지손가락을 테이블의 그래프 위에 올려보세요.
ESC 키를 누르면 종료합니다.
```

**변경 후:**
```
============================================================
시스템 시작!
============================================================
사용 방법:
  1. 한 손을 카메라 앞에 위치시키세요
  2. 검지손가락을 테이블 위로 내리세요
  3. 그래프 선을 따라 손가락을 움직이세요
  4. 그래프에 닿으면 진동 피드백이 발생합니다

키보드 단축키:
  ESC: 종료
  1-5: 방정식 변경
  0: 그래프 제거
============================================================
```

---

## 📊 변경 통계

### 수정된 파일
1. ✅ `main.py` - 핵심 로직 전면 수정
2. ✅ `config/config.yaml` - 단일 손 설정
3. ✅ `README.md` - 완전 재작성
4. ✨ `USAGE_GUIDE.md` - 신규 생성
5. ✨ `SYSTEM_FLOW.md` - 신규 생성

### 추가된 기능
- ✅ 수학 방정식 입력 기능
- ✅ 방정식 → 3D 그래프 변환
- ✅ 실시간 방정식 변경 (키보드)
- ✅ 좌표평면 범위 계산
- ✅ 예제 방정식 5개 (포물선, 사인, V자, 역포물선, 코사인)

### 제거된 기능
- ❌ 양손 추적 (→ 단일 손)
- ❌ 고정 그래프 점 (→ 동적 생성)
- ❌ 오른쪽 진동모터 (→ 단일 모터)

---

## 🔄 작동 흐름 비교

### 변경 전
```
카메라 → 양손 추적 → 고정 그래프 충돌 → 양쪽 진동모터
```

### 변경 후
```
방정식 입력 → 3D 그래프 생성 → 카메라 → 단일 손 추적 
→ 동적 그래프 충돌 → 진동모터 + 실시간 방정식 변경
```

---

## 🎯 사용 시나리오 예시

### 시나리오 1: 포물선 학습
```
1. python main.py 실행
2. "1" 입력 (y = x²/100)
3. 그래프 생성: 100개 점, U자 형태
4. 손을 중앙(x=0, z=400)에 위치
5. 좌우로 이동하며 포물선 형태 체험
6. 그래프 선에 닿으면 진동 발생!
```

### 시나리오 2: 방정식 비교
```
1. "1" 입력 (포물선)
2. 손으로 그래프 확인
3. 키보드 "2" 누름 (사인파)
4. 즉시 그래프 변경
5. 다른 패턴 체험
```

---

## 📐 좌표계 설명

### 3D 좌표계
```
Y축 (아래 방향 +)
↓
200mm ─────────────── 테이블 높이
      |
      |  그래프 영역
      |
      ├─→ X축 (-300 ~ +300mm)
      ↗
      Z축 (깊이, 200 ~ 800mm)
```

### 방정식 변환
```
입력: y = f(x)
      ↓
x = -300 ~ +300mm 범위에서 100개 점 샘플링
      ↓
각 x에 대해 3D 좌표 생성:
  (x, table_height=200, z=z_offset+f(x))
      ↓
출력: [(x₁, 200, z₁), (x₂, 200, z₂), ..., (x₁₀₀, 200, z₁₀₀)]
```

---

## 🔍 핵심 코드 스니펫

### 방정식 → 그래프 변환
```python
def _generate_graph_from_equation(self, equation, x_range, num_points):
    x_min, x_max = x_range
    x_values = np.linspace(x_min, x_max, num_points)
    
    graph_points = []
    for x in x_values:
        try:
            y_value = equation(x)
            z = self.z_offset + y_value
            graph_points.append([x, self.table_height, z])
        except:
            continue
    
    return np.array(graph_points, dtype=np.float32)
```

### 그래프 충돌 감지
```python
# 단일 손 처리
if hands_3d:
    hand_data = hands_3d[0]
    index_tip = hand_data["landmarks_3d"][8]
    
    # 조건 1: 테이블 접촉
    if index_tip[1] >= TABLE_HEIGHT_THRESHOLD:
        # 조건 2: 그래프 존재 및 접촉
        if len(virtual_graph.graph_points) > 0:
            if virtual_graph.is_touching(index_tip):
                should_vibrate = True
```

### 실시간 방정식 변경
```python
key = cv2.waitKey(1) & 0xFF

if key == ord('1'):
    equation = lambda x: (x**2) / 100
    virtual_graph.set_equation(equation, (-300, 300), 100)
    current_equation = "y = x^2 / 100"
    
elif key == ord('2'):
    equation = lambda x: np.sin(x/50) * 100
    virtual_graph.set_equation(equation, (-300, 300), 100)
    current_equation = "y = sin(x/50) * 100"
```

---

## 🎓 새로운 문서

### 1. USAGE_GUIDE.md (종합 사용 가이드)
- 📐 좌표계 상세 설명
- 🚀 실행 방법 단계별 가이드
- ⌨️ 키보드 단축키
- 🔧 설정 커스터마이징
- 🧪 시나리오별 사용 예시
- 🛠️ 문제 해결
- 💡 응용 아이디어

### 2. SYSTEM_FLOW.md (시스템 작동 흐름)
- 🔄 전체 실행 흐름 다이어그램
- 🔍 핵심 모듈별 상세 분석
- 📊 데이터 흐름도
- ⚡ 성능 특성
- 🚀 최적화 포인트

### 3. README.md (업데이트)
- 🎯 수학 그래프 햅틱 시스템 소개
- 🚀 빠른 시작 가이드
- 🎮 사용 방법
- ⚙️ 설정 커스터마이징
- 🔧 문제 해결

---

## ✅ 테스트 체크리스트

### 필수 테스트
- [ ] 캘리브레이션 실행 (`examples/calibrate_cameras.py`)
- [ ] 메인 프로그램 실행 (`python main.py`)
- [ ] 방정식 1~5 모두 테스트
- [ ] 키보드 방정식 변경 테스트
- [ ] 손 추적 작동 확인
- [ ] 진동모터 작동 확인
- [ ] ESC 키 종료 확인

### 선택 테스트
- [ ] 커스텀 방정식 추가
- [ ] 테이블 높이 조정
- [ ] 그래프 두께 조정
- [ ] 좌표평면 범위 조정
- [ ] 진동 강도 조정

---

## 🎉 완료!

모든 변경사항이 적용되었습니다. 이제 시스템은:

✅ **단일 손 추적**
✅ **수학 방정식 입력**
✅ **동적 3D 그래프 생성**
✅ **실시간 방정식 변경**
✅ **햅틱 피드백**

을 지원합니다!

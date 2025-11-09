"""
Gemini API 음성 인식 및 방정식 변환 에이전트

Gemini 멀티모달 기능으로 오디오를 직접 처리하여 명령 실행
"""

import logging
import json
import re
import io
import wave
from typing import Optional, Dict, Any, List, Tuple
import numpy as np

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Gemini API 관련 임포트 (설치 필요: pip install google-generativeai)
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    logger.warning("google-generativeai 패키지가 설치되지 않았습니다.")
    logger.warning("설치: pip install google-generativeai")
    GEMINI_AVAILABLE = False

# PyAudio로 직접 녹음
try:
    import pyaudio
    PYAUDIO_AVAILABLE = True
except ImportError:
    logger.warning("pyaudio 패키지가 설치되지 않았습니다.")
    logger.warning("설치: pip install pyaudio")
    PYAUDIO_AVAILABLE = False


class GeminiMathAgent:
    """
    Gemini API를 사용한 수학 방정식 에이전트
    
    Gemini 멀티모달로 오디오를 직접 처리하여 명령 실행
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Args:
            api_key: Gemini API 키 (환경변수 GEMINI_API_KEY 사용 가능)
        """
        self.api_key = api_key
        self.model = None
        
        if GEMINI_AVAILABLE and api_key:
            try:
                genai.configure(api_key=api_key)
                # 멀티모달 모델 사용 (오디오 지원)
                self.model = genai.GenerativeModel('gemini-1.5-flash')
                logger.info("✓ Gemini API 초기화 완료 (멀티모달)")
            except Exception as e:
                logger.error(f"Gemini API 초기화 실패: {e}")
                self.model = None
        else:
            logger.warning("Gemini API 사용 불가 (API 키 없음 또는 라이브러리 미설치)")
        
        # PyAudio 설정
        self.pyaudio = pyaudio.PyAudio() if PYAUDIO_AVAILABLE else None
        self.sample_rate = 16000  # Gemini 권장 샘플레이트
        self.channels = 1
        self.chunk = 1024
        
        # 방정식 히스토리
        self.equation_history: List[Dict[str, Any]] = []
    
    def record_audio(self, duration: int = 5) -> Optional[bytes]:
        """
        마이크로부터 오디오를 녹음합니다.
        
        Args:
            duration: 녹음 시간 (초)
            
        Returns:
            WAV 형식의 오디오 바이트 데이터
        """
        if not self.pyaudio:
            logger.error("PyAudio 사용 불가 (라이브러리 미설치)")
            return None
        
        logger.info(f"🎤 {duration}초 동안 녹음을 시작합니다...")
        
        try:
            # 오디오 스트림 열기
            stream = self.pyaudio.open(
                format=pyaudio.paInt16,
                channels=self.channels,
                rate=self.sample_rate,
                input=True,
                frames_per_buffer=self.chunk
            )
            
            frames = []
            num_chunks = int(self.sample_rate / self.chunk * duration)
            
            # 녹음
            for i in range(num_chunks):
                data = stream.read(self.chunk)
                frames.append(data)
                
                # 진행 표시
                if i % (num_chunks // 10) == 0:
                    progress = int((i / num_chunks) * 100)
                    logger.info(f"📊 녹음 중... {progress}%")
            
            logger.info("✓ 녹음 완료")
            
            # 스트림 닫기
            stream.stop_stream()
            stream.close()
            
            # WAV 파일로 변환
            wav_buffer = io.BytesIO()
            with wave.open(wav_buffer, 'wb') as wf:
                wf.setnchannels(self.channels)
                wf.setsampwidth(self.pyaudio.get_sample_size(pyaudio.paInt16))
                wf.setframerate(self.sample_rate)
                wf.writeframes(b''.join(frames))
            
            return wav_buffer.getvalue()
            
        except Exception as e:
            logger.error(f"❌ 녹음 오류: {e}")
            return None
    
    def process_audio_command(self, audio_data: bytes) -> Optional[Dict[str, Any]]:
        """
        오디오 데이터를 Gemini 멀티모달로 처리하여 명령 실행
        
        Args:
            audio_data: WAV 형식 오디오 바이트
            
        Returns:
            실행할 명령 정보 또는 None
        """
        if not self.model:
            logger.error("Gemini API 사용 불가")
            return None
        
        try:
            logger.info("🔄 Gemini로 오디오 분석 중...")
            
            # Gemini에 오디오와 프롬프트 전송
            prompt = self._create_audio_prompt()
            
            # 오디오 파일 객체 생성
            audio_file = {
                'mime_type': 'audio/wav',
                'data': audio_data
            }
            
            # Gemini 멀티모달 요청
            response = self.model.generate_content([prompt, audio_file])
            
            # 응답 파싱
            result = self._parse_audio_response(response.text)
            
            if result:
                logger.info(f"✓ 명령 인식: {result['action']} - {result.get('description', '')}")
                return result
            else:
                logger.warning("❌ 명령을 인식하지 못했습니다")
                return None
                
        except Exception as e:
            logger.error(f"❌ Gemini 오디오 처리 오류: {e}")
            return None
    
    def text_to_equation(self, text: str) -> Optional[Dict[str, Any]]:
        """
        텍스트 명령을 수학 방정식으로 변환합니다.
        
        Args:
            text: 자연어 명령 (예: "x 제곱 그래프 그려줘")
            
        Returns:
            {
                'name': str,           # 방정식 이름
                'equation_str': str,   # 수식 문자열 (표시용)
                'lambda_str': str,     # Lambda 함수 문자열
                'function': callable,  # 실행 가능한 함수
                'color': tuple         # RGB 색상
            }
        """
        if not self.model:
            logger.warning("Gemini API 사용 불가 - 기본 파서 사용")
            return self._fallback_parser(text)
        
        try:
            # Gemini에게 프롬프트 전송
            prompt = self._create_conversion_prompt(text)
            response = self.model.generate_content(prompt)
            
            # 응답 파싱
            result = self._parse_gemini_response(response.text)
            
            if result:
                # 히스토리에 추가
                self.equation_history.append({
                    'input': text,
                    'result': result
                })
                logger.info(f"✓ 방정식 생성: {result['name']} = {result['equation_str']}")
                return result
            else:
                logger.warning("Gemini 응답 파싱 실패 - 기본 파서 사용")
                return self._fallback_parser(text)
                
        except Exception as e:
            logger.error(f"Gemini API 오류: {e}")
            return self._fallback_parser(text)
    
    def _create_audio_prompt(self) -> str:
        """
        오디오 처리를 위한 Gemini 프롬프트 생성
        """
        prompt = """
당신은 수학 그래프 시스템을 제어하는 음성 어시스턴트입니다.
사용자의 음성 명령을 듣고 다음 중 하나의 작업을 수행해야 합니다:

1. **그래프 추가**: 수학 방정식을 그래프로 그리기
   - 예: "x 제곱", "사인 함수", "코사인 x", "x의 세제곱"
   
2. **그래프 삭제**: 마지막 그래프 또는 모든 그래프 삭제
   - 예: "마지막 삭제", "그래프 지워", "전부 삭제", "모두 지워"

3. **그래프 표시/숨김**: 특정 그래프 토글
   - 예: "첫 번째 숨겨", "두 번째 보여줘"

음성을 듣고 JSON 형식으로 응답하세요:

**그래프 추가인 경우:**
{
    "action": "add_graph",
    "name": "방정식 이름 (한글)",
    "equation_str": "수학 표현식 (예: x², sin(x))",
    "lambda_str": "lambda x: 파이썬 표현식",
    "description": "무엇을 그렸는지 설명"
}

예시:
- "x 제곱" → {"action": "add_graph", "name": "제곱함수", "equation_str": "x²", "lambda_str": "lambda x: x**2"}
- "사인 x" → {"action": "add_graph", "name": "사인함수", "equation_str": "sin(x)", "lambda_str": "lambda x: np.sin(x)"}

**그래프 삭제인 경우:**
{
    "action": "delete_graph",
    "mode": "last" 또는 "all",
    "description": "무엇을 삭제했는지"
}

**그래프 토글인 경우:**
{
    "action": "toggle_graph",
    "index": 숫자 (1부터 시작),
    "description": "무엇을 했는지"
}

**인식 불가인 경우:**
{
    "action": "unknown",
    "description": "들은 내용 설명"
}

주의사항:
- lambda_str에서 수학 함수는 np.를 붙여주세요 (np.sin, np.cos, np.tan, np.exp, np.log, np.sqrt)
- 반드시 JSON 형식으로만 응답하세요
- 설명은 짧고 명확하게
"""
        return prompt
    
    def _parse_audio_response(self, response_text: str) -> Optional[Dict[str, Any]]:
        """
        Gemini 오디오 응답 파싱
        """
        try:
            # JSON 추출 (코드 블록 제거)
            json_text = response_text.strip()
            if '```json' in json_text:
                json_text = json_text.split('```json')[1].split('```')[0].strip()
            elif '```' in json_text:
                json_text = json_text.split('```')[1].split('```')[0].strip()
            
            data = json.loads(json_text)
            action = data.get('action', 'unknown')
            
            if action == 'add_graph':
                # 그래프 추가 명령
                name = data.get('name', '새 그래프')
                equation_str = data.get('equation_str', 'f(x)')
                lambda_str = data.get('lambda_str', 'lambda x: x')
                
                # Lambda 함수 생성
                try:
                    func = eval(lambda_str, {'np': np, '__builtins__': {}})
                    
                    # 색상 생성 (히스토리 기반)
                    import colorsys
                    hue = (len(self.equation_history) * 0.17) % 1.0
                    rgb = colorsys.hsv_to_rgb(hue, 0.8, 0.9)
                    color = tuple(int(c * 255) for c in rgb)
                    
                    result = {
                        'action': 'add_graph',
                        'name': name,
                        'equation_str': equation_str,
                        'lambda_str': lambda_str,
                        'function': func,
                        'color': color,
                        'description': data.get('description', '')
                    }
                    
                    self.equation_history.append(result)
                    return result
                    
                except Exception as e:
                    logger.error(f"Lambda 함수 생성 실패: {e}")
                    return None
            
            elif action == 'delete_graph':
                return {
                    'action': 'delete_graph',
                    'mode': data.get('mode', 'last'),
                    'description': data.get('description', '')
                }
            
            elif action == 'toggle_graph':
                return {
                    'action': 'toggle_graph',
                    'index': data.get('index', 1) - 1,  # 0-based
                    'description': data.get('description', '')
                }
            
            else:
                logger.warning(f"알 수 없는 명령: {data.get('description', '')}")
                return None
                
        except json.JSONDecodeError as e:
            logger.error(f"JSON 파싱 실패: {e}")
            logger.debug(f"응답 텍스트: {response_text}")
            return None
        except Exception as e:
            logger.error(f"응답 처리 오류: {e}")
            return None
    "equation_str": "수식 표현 (예: y = x^2)",
    "lambda_str": "lambda x: ...",
    "description": "설명"
}}

규칙:
1. lambda 함수는 x를 입력받아 y 값을 반환해야 합니다
2. numpy는 np로 사용 가능합니다 (예: np.sin, np.cos, np.exp)
3. 수식은 가능한 간단하게 작성하세요
4. x 범위는 -300 ~ 300mm입니다

예시:
- "x 제곱" → {{"name": "포물선", "equation_str": "y = x^2 / 100", "lambda_str": "lambda x: (x**2) / 100"}}
- "사인 함수" → {{"name": "사인파", "equation_str": "y = sin(x/50) * 100", "lambda_str": "lambda x: np.sin(x/50) * 100"}}
- "일차 함수" → {{"name": "직선", "equation_str": "y = 2*x", "lambda_str": "lambda x: 2 * x"}}

JSON만 출력하세요:
"""
        return prompt
    
    def _parse_gemini_response(self, response_text: str) -> Optional[Dict[str, Any]]:
        """
        Gemini 응답을 파싱합니다.
        """
        try:
            # JSON 추출 (코드 블록 제거)
            json_match = re.search(r'\{[^}]+\}', response_text, re.DOTALL)
            if not json_match:
                logger.warning("JSON 형식을 찾을 수 없습니다")
                return None
            
            json_str = json_match.group(0)
            data = json.loads(json_str)
            
            # 필수 필드 확인
            required_fields = ['name', 'equation_str', 'lambda_str']
            if not all(field in data for field in required_fields):
                logger.warning(f"필수 필드 누락: {data}")
                return None
            
            # Lambda 함수 생성
            try:
                func = eval(data['lambda_str'])
                
                # 함수 테스트
                test_value = func(0)
                if not isinstance(test_value, (int, float, np.number)):
                    logger.warning(f"잘못된 함수 반환 타입: {type(test_value)}")
                    return None
                
            except Exception as e:
                logger.error(f"Lambda 함수 생성 실패: {e}")
                return None
            
            # 색상 생성 (랜덤)
            color = tuple(np.random.randint(50, 255, 3).tolist())
            
            return {
                'name': data['name'],
                'equation_str': data['equation_str'],
                'lambda_str': data['lambda_str'],
                'function': func,
                'color': color,
                'description': data.get('description', '')
            }
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON 파싱 오류: {e}")
            return None
        except Exception as e:
            logger.error(f"응답 파싱 오류: {e}")
            return None
    
    def _fallback_parser(self, text: str) -> Optional[Dict[str, Any]]:
        """
        Gemini API 사용 불가 시 기본 파서
        
        간단한 키워드 매칭으로 방정식 생성
        """
        text_lower = text.lower()
        
        # 키워드 매칭
        patterns = {
            '제곱|이차|포물선|parabola': {
                'name': '포물선',
                'equation_str': 'y = x^2 / 100',
                'lambda_str': 'lambda x: (x**2) / 100',
                'function': lambda x: (x**2) / 100
            },
            '사인|sin': {
                'name': '사인파',
                'equation_str': 'y = sin(x/50) * 100',
                'lambda_str': 'lambda x: np.sin(x/50) * 100',
                'function': lambda x: np.sin(x/50) * 100
            },
            '코사인|cos': {
                'name': '코사인파',
                'equation_str': 'y = cos(x/30) * 80',
                'lambda_str': 'lambda x: np.cos(x/30) * 80',
                'function': lambda x: np.cos(x/30) * 80
            },
            '직선|일차|선형': {
                'name': '직선',
                'equation_str': 'y = 2*x',
                'lambda_str': 'lambda x: 2 * x',
                'function': lambda x: 2 * x
            },
            '절댓값|절대값|absolute': {
                'name': 'V자 그래프',
                'equation_str': 'y = |x| / 2',
                'lambda_str': 'lambda x: abs(x) / 2',
                'function': lambda x: abs(x) / 2
            },
            '세제곱|삼차|cubic': {
                'name': '삼차함수',
                'equation_str': 'y = x^3 / 10000',
                'lambda_str': 'lambda x: (x**3) / 10000',
                'function': lambda x: (x**3) / 10000
            },
        }
        
        for pattern, equation_data in patterns.items():
            if re.search(pattern, text_lower):
                color = tuple(np.random.randint(50, 255, 3).tolist())
                return {
                    **equation_data,
                    'color': color,
                    'description': f'"{text}"로부터 생성'
                }
        
        # 매칭 실패
        logger.warning(f"'{text}'에 해당하는 방정식을 찾을 수 없습니다")
        return None
    
    def get_equation_by_voice(self) -> Optional[Dict[str, Any]]:
        """
        음성 명령으로 방정식 생성 (통합 메서드)
        
        Returns:
            방정식 딕셔너리 또는 None
        """
        # 1. 음성 듣기
        text = self.listen_voice_command()
        if not text:
            return None
        
        # 2. 텍스트를 방정식으로 변환
        equation = self.text_to_equation(text)
        return equation
    
    def get_equation_history(self) -> List[Dict[str, Any]]:
        """
        방정식 생성 히스토리 반환
        """
        return self.equation_history
    
    def clear_history(self):
        """
        히스토리 초기화
        """
        self.equation_history.clear()
        logger.info("히스토리 초기화 완료")


# 테스트 코드
if __name__ == "__main__":
    import os
    
    # API 키 설정 (환경변수 또는 직접 입력)
    api_key = os.environ.get('GEMINI_API_KEY', None)
    
    if not api_key:
        print("⚠️ GEMINI_API_KEY 환경변수가 설정되지 않았습니다")
        print("기본 파서만 사용합니다\n")
    
    # 에이전트 생성
    agent = GeminiMathAgent(api_key=api_key)
    
    print("=" * 60)
    print("Gemini Math Agent 테스트")
    print("=" * 60)
    
    # 테스트 명령들
    test_commands = [
        "x 제곱 그래프 그려줘",
        "사인 함수 보여줘",
        "일차 함수",
        "절댓값 함수"
    ]
    
    for i, command in enumerate(test_commands, 1):
        print(f"\n테스트 {i}: '{command}'")
        equation = agent.text_to_equation(command)
        
        if equation:
            print(f"✓ 이름: {equation['name']}")
            print(f"✓ 수식: {equation['equation_str']}")
            print(f"✓ Lambda: {equation['lambda_str']}")
            
            # 함수 테스트
            test_x = 100
            test_y = equation['function'](test_x)
            print(f"✓ 테스트: f({test_x}) = {test_y}")
        else:
            print("✗ 방정식 생성 실패")
    
    # 음성 테스트 (선택)
    if SPEECH_AVAILABLE:
        print("\n" + "=" * 60)
        choice = input("음성 명령 테스트를 하시겠습니까? (y/n): ")
        if choice.lower() == 'y':
            equation = agent.get_equation_by_voice()
            if equation:
                print(f"\n✓ 생성된 방정식: {equation['name']}")
                print(f"✓ 수식: {equation['equation_str']}")
    
    print("\n" + "=" * 60)
    print("테스트 완료!")

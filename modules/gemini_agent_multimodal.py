"""
Gemini API 멀티모달 음성 인식 에이전트

Gemini의 오디오 처리 기능으로 음성 명령을 직접 처리
"""

import logging
import json
import io
import wave
import time
from typing import Optional, Dict, Any, List
import numpy as np

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Gemini API
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    logger.warning("google-generativeai 패키지 미설치")
    GEMINI_AVAILABLE = False

# PyAudio
try:
    import pyaudio
    PYAUDIO_AVAILABLE = True
except ImportError:
    logger.warning("pyaudio 패키지 미설치")
    PYAUDIO_AVAILABLE = False


class GeminiAudioAgent:
    """
    Gemini 멀티모달 오디오 처리 에이전트
    """
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        self.model = None
        
        if GEMINI_AVAILABLE and api_key:
            try:
                genai.configure(api_key=api_key)
                self.model = genai.GenerativeModel('gemini-1.5-flash')
                logger.info("✓ Gemini 멀티모달 초기화 완료")
            except Exception as e:
                logger.error(f"Gemini 초기화 실패: {e}")
        
        self.pyaudio = pyaudio.PyAudio() if PYAUDIO_AVAILABLE else None
        self.sample_rate = 16000
        self.channels = 1
        self.chunk = 1024
        self.equation_history = []
        
        # 녹음 상태
        self.is_recording = False
        self.stream = None
        self.frames = []
    
    def start_recording(self) -> bool:
        """
        녹음 시작 (논블로킹)
        
        Returns:
            성공 여부
        """
        if not self.pyaudio:
            logger.error("PyAudio 사용 불가")
            return False
        
        if hasattr(self, 'stream') and self.stream:
            logger.warning("이미 녹음 중입니다")
            return False
        
        try:
            logger.info("🎤 녹음 시작... (버튼을 다시 누르면 종료)")
            
            self.stream = self.pyaudio.open(
                format=pyaudio.paInt16,
                channels=self.channels,
                rate=self.sample_rate,
                input=True,
                frames_per_buffer=self.chunk
            )
            
            self.frames = []
            self.is_recording = True
            return True
            
        except Exception as e:
            logger.error(f"녹음 시작 오류: {e}")
            return False
    
    def record_chunk(self):
        """
        녹음 중 한 청크 읽기 (메인 루프에서 호출)
        """
        if not self.is_recording or not self.stream:
            return
        
        try:
            data = self.stream.read(self.chunk, exception_on_overflow=False)
            self.frames.append(data)
        except Exception as e:
            logger.error(f"녹음 청크 읽기 오류: {e}")
    
    def stop_recording(self) -> Optional[bytes]:
        """
        녹음 종료 및 데이터 반환
        
        Returns:
            WAV 바이트 데이터
        """
        if not self.is_recording:
            logger.warning("녹음 중이 아닙니다")
            return None
        
        try:
            self.is_recording = False
            
            if self.stream:
                self.stream.stop_stream()
                self.stream.close()
                self.stream = None
            
            if not self.frames:
                logger.warning("녹음된 데이터가 없습니다")
                return None
            
            # WAV 변환
            wav_buffer = io.BytesIO()
            with wave.open(wav_buffer, 'wb') as wf:
                wf.setnchannels(self.channels)
                wf.setsampwidth(self.pyaudio.get_sample_size(pyaudio.paInt16))
                wf.setframerate(self.sample_rate)
                wf.writeframes(b''.join(self.frames))
            
            duration = len(self.frames) * self.chunk / self.sample_rate
            logger.info(f"✓ 녹음 완료 ({duration:.1f}초)")
            
            return wav_buffer.getvalue()
            
        except Exception as e:
            logger.error(f"녹음 종료 오류: {e}")
            return None
    
    def process_audio_command(self, audio_data: bytes) -> Optional[Dict[str, Any]]:
        """
        오디오를 Gemini로 처리
        
        Args:
            audio_data: WAV 바이트
            
        Returns:
            명령 딕셔너리
        """
        if not self.model:
            logger.error("Gemini API 사용 불가")
            return None
        
        try:
            logger.info("🔄 Gemini 오디오 분석...")
            
            prompt = """
당신은 수학 그래프 시스템 음성 어시스턴트입니다.
사용자 음성을 듣고 JSON으로 응답하세요.

**명령 타입:**
1. **그래프 추가** (수학 방정식)
2. **그래프 삭제** (마지막 또는 전체)
3. **그래프 토글** (특정 그래프 숨김/표시)

**응답 형식:**

그래프 추가:
{
  "action": "add_graph",
  "name": "방정식 이름",
  "equation_str": "수학 표현식",
  "lambda_str": "lambda x: 파이썬 표현식"
}

예시:
- "x 제곱" → {"action": "add_graph", "name": "제곱함수", "equation_str": "x²", "lambda_str": "lambda x: x**2"}
- "사인 x" → {"action": "add_graph", "name": "사인함수", "equation_str": "sin(x)", "lambda_str": "lambda x: np.sin(x/50)*100"}

그래프 삭제:
{
  "action": "delete_graph",
  "mode": "last" 또는 "all"
}

그래프 토글:
{
  "action": "toggle_graph",
  "index": 숫자 (1부터)
}

인식 불가:
{
  "action": "unknown"
}

주의: numpy 함수는 np. 접두사 필요 (np.sin, np.cos, np.tan, np.exp, np.log, np.sqrt)
JSON만 출력하세요.
"""
            
            # 오디오 파일 업로드
            audio_file = genai.upload_file(
                io.BytesIO(audio_data),
                mime_type='audio/wav'
            )
            
            # Gemini 요청
            response = self.model.generate_content([prompt, audio_file])
            
            # 파일 삭제
            genai.delete_file(audio_file.name)
            
            # 파싱
            result = self._parse_response(response.text)
            
            if result:
                logger.info(f"✓ 명령 인식: {result['action']}")
                return result
            
            logger.warning("명령 인식 실패")
            return None
            
        except Exception as e:
            logger.error(f"Gemini 오디오 처리 오류: {e}")
            return None
    
    def _parse_response(self, response_text: str) -> Optional[Dict[str, Any]]:
        """응답 파싱"""
        try:
            # JSON 추출
            json_text = response_text.strip()
            if '```json' in json_text:
                json_text = json_text.split('```json')[1].split('```')[0].strip()
            elif '```' in json_text:
                json_text = json_text.split('```')[1].split('```')[0].strip()
            
            data = json.loads(json_text)
            action = data.get('action', 'unknown')
            
            if action == 'add_graph':
                # Lambda 함수 생성
                lambda_str = data.get('lambda_str', 'lambda x: x')
                try:
                    func = eval(lambda_str, {'np': np, '__builtins__': {}})
                    
                    # 색상 생성
                    import colorsys
                    hue = (len(self.equation_history) * 0.17) % 1.0
                    rgb = colorsys.hsv_to_rgb(hue, 0.8, 0.9)
                    color = tuple(int(c * 255) for c in rgb)
                    
                    result = {
                        'action': 'add_graph',
                        'name': data.get('name', '새 그래프'),
                        'equation_str': data.get('equation_str', 'f(x)'),
                        'function': func,
                        'color': color
                    }
                    
                    self.equation_history.append(result)
                    return result
                    
                except Exception as e:
                    logger.error(f"Lambda 생성 실패: {e}")
                    return None
            
            elif action == 'delete_graph':
                return {
                    'action': 'delete_graph',
                    'mode': data.get('mode', 'last')
                }
            
            elif action == 'toggle_graph':
                return {
                    'action': 'toggle_graph',
                    'index': data.get('index', 1) - 1
                }
            
            else:
                return None
                
        except Exception as e:
            logger.error(f"파싱 오류: {e}")
            return None
    
    def cleanup(self):
        """리소스 정리"""
        if self.is_recording:
            self.stop_recording()
        if self.pyaudio:
            self.pyaudio.terminate()

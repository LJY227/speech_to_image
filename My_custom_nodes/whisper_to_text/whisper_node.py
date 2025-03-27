import os
import sys
import numpy as np
import time
import threading
import tempfile
import json
from queue import Queue
import folder_paths

# 添加当前目录到Python路径，确保能导入主程序中的模块
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# 尝试导入语音识别相关模块
try:
    import pyaudio
    import wave
    from faster_whisper import WhisperModel
    WHISPER_AVAILABLE = True
except ImportError:
    print("Whisper依赖模块未安装，请先安装依赖。")
    WHISPER_AVAILABLE = False

# 语音识别结果队列
recognition_queue = Queue()

class SpeechRecorder:
    def __init__(self):
        if not WHISPER_AVAILABLE:
            raise ImportError("语音识别依赖模块未安装")
            
        # 音频参数设置
        self.CHUNK = 1024
        self.FORMAT = pyaudio.paFloat32
        self.CHANNELS = 1
        self.RATE = 16000
        self.RECORD_SECONDS = 5  # 每次录音时长（秒）
        
        # 初始化PyAudio
        self.p = pyaudio.PyAudio()
        
        # 初始化Whisper模型
        self.model = WhisperModel("base", device="cpu", compute_type="int8")
        
        # 录音和识别线程
        self.recording_thread = None
        self.is_recording = False
        
    def start_recording(self):
        """开始录音和识别线程"""
        if self.recording_thread is not None and self.recording_thread.is_alive():
            print("已经在录音中...")
            return
        
        self.is_recording = True
        self.recording_thread = threading.Thread(target=self._record_and_recognize)
        self.recording_thread.daemon = True
        self.recording_thread.start()
        
    def stop_recording(self):
        """停止录音"""
        self.is_recording = False
        if self.recording_thread is not None:
            self.recording_thread.join(timeout=1.0)
            
    def _record_and_recognize(self):
        """录音和识别线程"""
        while self.is_recording:
            # 创建临时文件
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
                temp_filename = temp_file.name
            
            print("开始录音...")
            # 录制音频
            stream = self.p.open(format=self.FORMAT,
                               channels=self.CHANNELS,
                               rate=self.RATE,
                               input=True,
                               frames_per_buffer=self.CHUNK)
            
            frames = []
            
            for i in range(0, int(self.RATE / self.CHUNK * self.RECORD_SECONDS)):
                if not self.is_recording:
                    break
                data = stream.read(self.CHUNK)
                frames.append(data)
                
            print("录音结束")
            
            stream.stop_stream()
            stream.close()
            
            # 保存录音文件
            wf = wave.open(temp_filename, 'wb')
            wf.setnchannels(self.CHANNELS)
            wf.setsampwidth(self.p.get_sample_size(self.FORMAT))
            wf.setframerate(self.RATE)
            wf.writeframes(b''.join(frames))
            wf.close()
            
            # 进行语音识别
            print("开始识别...")
            try:
                segments, info = self.model.transcribe(temp_filename, language="zh")
                
                # 收集识别结果
                result_text = ""
                for segment in segments:
                    result_text += segment.text + " "
                
                if result_text.strip():
                    print(f"识别结果: {result_text}")
                    # 将识别结果放入队列
                    recognition_queue.put(result_text.strip())
            except Exception as e:
                print(f"识别出错: {str(e)}")
            
            # 删除临时文件
            try:
                os.unlink(temp_filename)
            except:
                pass
    
    def close(self):
        """关闭资源"""
        self.stop_recording()
        self.p.terminate()

# 录音机单例
recorder = None

def get_recorder():
    """获取录音机单例"""
    global recorder
    if recorder is None and WHISPER_AVAILABLE:
        try:
            recorder = SpeechRecorder()
        except Exception as e:
            print(f"初始化录音机失败: {str(e)}")
    return recorder

class WhisperRecordingNode:
    """语音录制和识别节点"""
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "action": (["start", "stop"], {"default": "start"}),
                "recording_seconds": ("INT", {"default": 5, "min": 1, "max": 60}),
            },
        }

    RETURN_TYPES = ()
    FUNCTION = "record_audio"
    CATEGORY = "whisper"
    
    def record_audio(self, action, recording_seconds):
        r = get_recorder()
        if r is None:
            print("录音机初始化失败，请确保安装了所有依赖")
            return ()
        
        # 设置录音时长
        r.RECORD_SECONDS = recording_seconds
        
        if action == "start":
            r.start_recording()
            print(f"开始录音，时长{recording_seconds}秒...")
        else:
            r.stop_recording()
            print("停止录音")
            
        return ()

class WhisperTextOutputNode:
    """语音识别文本输出节点"""
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "timeout_seconds": ("FLOAT", {"default": 1.0, "min": 0.1, "max": 10.0}),
            },
        }

    RETURN_TYPES = ("STRING",)
    FUNCTION = "get_text"
    CATEGORY = "whisper"
    
    def get_text(self, timeout_seconds):
        # 尝试从队列获取最新识别结果
        try:
            text = recognition_queue.get(block=True, timeout=timeout_seconds)
            print(f"获取到识别文本: {text}")
            return (text,)
        except:
            # 超时返回空字符串
            print("未获取到新的识别文本，返回空字符串")
            return ("",)

# 保存识别结果到文件的节点
class WhisperSaveTextNode:
    """保存识别文本到文件"""
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "text": ("STRING", {}),
                "filename": ("STRING", {"default": "whisper_result.txt"}),
            },
        }

    RETURN_TYPES = ("STRING",)
    FUNCTION = "save_text"
    CATEGORY = "whisper"
    
    def save_text(self, text, filename):
        if not text:
            return (text,)
            
        # 确保文件名有效
        if not filename.endswith('.txt'):
            filename += '.txt'
            
        output_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "outputs")
        os.makedirs(output_dir, exist_ok=True)
        
        output_path = os.path.join(output_dir, filename)
        
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(text)
            print(f"已保存识别文本到: {output_path}")
        except Exception as e:
            print(f"保存文本失败: {str(e)}")
            
        return (text,)

# 节点映射
NODE_CLASS_MAPPINGS = {
    "WhisperRecording": WhisperRecordingNode,
    "WhisperTextOutput": WhisperTextOutputNode,
    "WhisperSaveText": WhisperSaveTextNode,
}

# 节点显示名称映射
NODE_DISPLAY_NAME_MAPPINGS = {
    "WhisperRecording": "语音录制与识别",
    "WhisperTextOutput": "语音识别文本输出",
    "WhisperSaveText": "保存识别文本",
} 
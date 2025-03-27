# Whisper语音识别ComfyUI节点

这是一个用于在ComfyUI中集成Faster Whisper语音识别功能的自定义节点。通过这个节点，你可以直接在ComfyUI工作流中录制语音并将识别出的文本用于提示词生成。

## 功能特点

- 实时录制语音并使用Faster Whisper进行识别
- 将识别的文本直接输出到ComfyUI工作流
- 支持中文和其他语言识别
- 可调节录音时长和超时设置
- 可保存识别结果到文本文件

## 安装方法

1. 确保已安装ComfyUI

2. 安装所需的Python依赖:
```bash
pip install pyaudio faster-whisper numpy
```

3. 将`whisper_to_text`文件夹复制到ComfyUI的`custom_nodes`目录下

4. 重启ComfyUI

## 节点说明

### 1. 语音录制与识别 (WhisperRecording)

此节点负责开始或停止语音录制和识别过程。

**输入**:
- `action`: 选择开始或停止录音 (start/stop)
- `recording_seconds`: 录音时长(秒)，默认为5秒

**输出**: 无直接输出，但会将识别结果放入内部队列中

### 2. 语音识别文本输出 (WhisperTextOutput)

此节点从识别队列中获取最新的识别文本并输出。

**输入**:
- `timeout_seconds`: 等待新识别结果的超时时间(秒)，默认为1秒

**输出**:
- `text`: 识别出的文本，可连接到需要文本输入的节点

### 3. 保存识别文本 (WhisperSaveText)

此节点将识别的文本保存到文件。

**输入**:
- `text`: 要保存的文本
- `filename`: 保存的文件名，默认为"whisper_result.txt"

**输出**:
- `text`: 原始文本(透传)，可连接到其他需要文本的节点

## 使用示例

1. 添加`语音录制与识别`节点，设置为"start"开始录音
2. 添加`语音识别文本输出`节点，连接到需要文本输入的节点(如CLIP Text Encode)
3. 语音录制完成后，识别出的文本将被发送到下游节点

## 工作流示例

一个典型的语音到图像工作流:

1. 语音录制与识别 (开始录音)
2. 语音识别文本输出 (获取识别文本)
3. CLIP Text Encode (将文本编码为嵌入)
4. KSampler (使用编码生成图像)
5. 保存识别文本 (可选，保存识别的文本)

## 注意事项

- 首次使用时会下载Whisper模型，这可能需要一些时间
- 确保系统有可用的麦克风设备
- 如果遇到录音问题，请检查系统麦克风权限设置 
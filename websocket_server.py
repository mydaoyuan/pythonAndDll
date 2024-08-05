'''
LastEditors: tangdy tdy853839625@qq.com
FilePath: /UE_Python_Sdk_Server/websocket_server.py
'''
import asyncio
import websockets
from dll_interface import init_msdk, speak_by_audio
# from dll_interface_mock import init_msdk, speak_by_audio
# from dll_doc_cdoe import init_msdk
from message_handle import messageHandler
import json
import asyncio
from functools import partial
import uuid
import wave
import os

def initialize_audio_file(client_id):
    # 确保目录存在
    if not os.path.exists('audio_logs'):
        os.makedirs('audio_logs')
    # 文件名使用客户端ID标识
    filename = f"audio_data_{client_id}.wav"
    # 完整的文件路径
    file_path = os.path.join('audio_logs', filename)
    
    # 初始化WAV文件
    wf = wave.open(file_path, 'wb')
    wf.setnchannels(1)  # 单通道
    wf.setsampwidth(2)  # 16-bit PCM
    wf.setframerate(16000)  # 采样率16000Hz
    return wf

def finalize_audio_file(wf):
    wf.close()

# 用于存储连接的全局字典
connected = {}

async def msdk_handler(websocket, path):
    # 生成一个随机ID 
    # 生成一个随机的UUID
    random_id = uuid.uuid4()
    # 将UUID转换为字符串格式
    random_id_str = str(random_id)
    connected[random_id_str] = {
        'websocket': websocket,
        'client_id': "",
        "audio_buffer": bytearray(),
        "frame_id": 0,
        "is_final": False,
        "audioDone": True,
        "id": random_id_str
    }
    wf = initialize_audio_file(connected[random_id_str]['client_id'])
    connected[random_id_str]['wav_file'] = wf

    try:
        async for message in websocket:
            data = json.loads(message)
            # 设置默认值防止报错
            # print(data)
            await messageHandler(data, connected[random_id_str])
    except websockets.exceptions.ConnectionClosed:
        print(f"连接关闭: {random_id_str}")
    finally:
        # 执行清理工作
        # 关闭UE进程
        finalize_audio_file(connected[random_id_str]['wav_file'])
        if random_id_str in connected:
            del connected[random_id_str]
        print(f"Cleaned up resources for Client ID: {random_id_str}")


async def main():
    async with websockets.serve(msdk_handler, "0.0.0.0", 8765):
        print("WebSocket服务器启动在 ws://localhost:8765")
        await asyncio.Future()  # 运行直到被取消

if __name__ == "__main__":
    asyncio.run(main())


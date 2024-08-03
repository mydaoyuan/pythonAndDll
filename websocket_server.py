'''
LastEditors: tangdy tdy853839625@qq.com
FilePath: /UE_Python_Sdk_Server/websocket_server.py
'''
import asyncio
import websockets
from dll_interface import init_msdk, speak_by_audio
# from dll_interface_mock import init_msdk, speak_by_audio
# from dll_doc_cdoe import init_msdk
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


def convert_to_bytes(data, addMute=False):
    result = bytes(data)
    # data是整数列表，例如：[252, 231, 148, ...]
    if addMute:
        # 前面0.2秒替换为静音数据
        result = bytes([0] * 320) + result[320:]
    return result
        
     

async def async_init_msdk(content, json_config):
    print("async_init_msdk run")
    loop = asyncio.get_event_loop()
    # 使用partial来传递参数给同步函数
    return await loop.run_in_executor(None, partial(init_msdk, content, json_config))

# 用于存储连接的全局字典
connected = {}
FRAME_SIZE = 8320  # 每帧固定大小

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
        "audioDone": True
    }
    wf = initialize_audio_file(connected[random_id_str]['client_id'])
    connected[random_id_str]['wav_file'] = wf
    def send_frame(frame_data, frame_id, wf):
        # 若是最后一帧，则FrameID设置为-1
        if len(frame_data) == 0 and  frame_id != -1:
            print(f"No data to send for frame ID: {frame_id}  如果数据为空，则不发送")
            return  # 如果数据为空，则不发送
        json_config = {
            "FrameNum": len(frame_data),
            "FrameID": frame_id,
            # "Subtitle": "",  # 根据需要添加字幕
            "Data": frame_data  # bytearray
        }
        # 将数据写入WAV文件
        wf.writeframes(frame_data)
        speak_by_audio(connected[random_id_str]['client_id'], json_config)

    async def process_audio_data(data):
        connected[random_id_str]['audio_buffer'].extend(data)

        while len(connected[random_id_str]['audio_buffer']) >= FRAME_SIZE:
            send_frame(connected[random_id_str]['audio_buffer'][:FRAME_SIZE], connected[random_id_str]['frame_id'], connected[random_id_str]['wav_file'])
            connected[random_id_str]['frame_id'] += 1
            connected[random_id_str]['audio_buffer'] = connected[random_id_str]['audio_buffer'][FRAME_SIZE:]

        if connected[random_id_str]['is_final'] and not connected[random_id_str]['audioDone']:
            # 发送所有剩余数据，无论其大小
            if len(connected[random_id_str]['audio_buffer']) > 0:
                send_frame(connected[random_id_str]['audio_buffer'], connected[random_id_str]['frame_id'], connected[random_id_str]['wav_file'])
                # await asyncio.sleep(0.1)  # 使用异步sleep
            # 重置
            print("发送最后一帧")
            connected[random_id_str]['audio_buffer'] = bytearray()
            connected[random_id_str]['frame_id'] = 0
            send_frame(connected[random_id_str]['audio_buffer'], -1, connected[random_id_str]['wav_file'])
            connected[random_id_str]['is_final'] = False
            connected[random_id_str]['audioDone'] = True
           

    try:
        async for message in websocket:
            data = json.loads(message)
            # 设置默认值防止报错
            # print(data)
            if 'type' not in data:
                data['type'] = ''
            if 'action' not in data:
                data['action'] = ''
            if data["type"] == 'audio':
                audio_data = data['data']['data']  # 获取音频数据整数列表
                if connected[random_id_str]['audioDone']:
                    audio_bytes = convert_to_bytes(audio_data, addMute=True)  # 转换为字节
                else: 
                    audio_bytes = convert_to_bytes(audio_data)
                connected[random_id_str]['audioDone'] = False
                await process_audio_data(audio_bytes)

            if data['type'] == 'audioEnd':
                connected[random_id_str]['is_final'] = True
                await process_audio_data(b'')

            if data['action'] == 'init':
                print("初始化DLL")
                json_config = json.dumps({
                    "display_ue_window": True,
                    "play_ue_sound": True,
                    "ws_server_port": 26217,
                    "ue_fullpath": "F:/Windows_Release/UE/Windows/RenderBody/Binaries/win64/RenderBody-Win64-Shipping.exe"
                })
                try:
                    await async_init_msdk(connected[random_id_str], json_config)
                except Exception as e:
                    await websocket.send(f"初始化失败: {e}")
                await websocket.send("DLL初始化已发送")
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


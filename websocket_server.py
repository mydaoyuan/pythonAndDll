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



def convert_to_bytes(data):
    # data是整数列表，例如：[252, 231, 148, ...]
    return bytes(data)

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
        "is_final": False
    }
    def send_frame(frame_data, frame_id):
        # 若是最后一帧，则FrameID设置为-1
        json_config = {
            "FrameNum": len(frame_data),
            "FrameID": frame_id,
            # "Subtitle": "",  # 根据需要添加字幕
            "Data": frame_data  # bytearray
        }
        speak_by_audio(connected[random_id_str]['client_id'], json_config)

    def process_audio_data(data):
        audio_buffer = connected[random_id_str]['audio_buffer']
        audio_buffer.extend(data)

        # 当缓冲区数据足够时，发送完整帧
        while len(audio_buffer) >= FRAME_SIZE and not connected[random_id_str]['is_final']:
            send_frame(audio_buffer[:FRAME_SIZE], connected[random_id_str]['frame_id'])
            connected[random_id_str]['frame_id'] += 1
            audio_buffer = audio_buffer[FRAME_SIZE:]
        # 发送结束数据
        if connected[random_id_str]['is_final']:
            send_frame(audio_buffer, -1)
            connected[random_id_str]['audio_buffer'] = bytearray()
            connected[random_id_str]['frame_id'] = 0
            connected[random_id_str]['is_final'] = False


    try:
        async for message in websocket:
            data = json.loads(message)
            # 设置默认值防止报错
            print(data)
            if 'type' not in data:
                data['type'] = ''
            if 'action' not in data:
                data['action'] = ''
            if data["type"] == 'audio':
                audio_data = data['data']['data']  # 获取音频数据整数列表
                audio_bytes = convert_to_bytes(audio_data)  # 转换为字节
                process_audio_data(audio_bytes)

            if data['type'] == 'audioEnd':
                connected[random_id_str]['is_final'] = True

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
        if random_id_str in connected:
            del connected[random_id_str]
        print(f"Cleaned up resources for Client ID: {random_id_str}")


async def main():
    async with websockets.serve(msdk_handler, "0.0.0.0", 8765):
        print("WebSocket服务器启动在 ws://localhost:8765")
        await asyncio.Future()  # 运行直到被取消

if __name__ == "__main__":
    asyncio.run(main())

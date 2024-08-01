'''
LastEditors: tangdy tdy853839625@qq.com
FilePath: /UE_Python_Sdk_Server/websocket_server.py
'''
import asyncio
import websockets
from dll_interface import init_msdk
# from dll_doc_cdoe import init_msdk
import json
import asyncio
from functools import partial
import uuid



async def async_init_msdk(json_config):
    loop = asyncio.get_event_loop()
    # 使用partial来传递参数给同步函数
    return await loop.run_in_executor(None, partial(init_msdk, json_config))

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
        'client_id': ""
    }
    try:
        async for message in websocket:
            data = json.loads(message)
            if data['action'] == 'init':
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

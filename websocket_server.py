'''
LastEditors: tangdy tdy853839625@qq.com
FilePath: /UE_Python_Sdk_Server/websocket_server.py
'''
import asyncio
import websockets
from dll_interface import init_msdk
import json

async def msdk_handler(websocket, path):
    async for message in websocket:
        data = json.loads(message)
        if data['action'] == 'init':
            json_config = json.dumps({
                "display_ue_window": True,
                "play_ue_sound": True,
                "ws_server_port": 26217,
                "ue_fullpath": "E:/WorkSpace/YIV/METAH/MSDK/UEMETAHC loud /Windows/RenderBody/Binaries/win64/RenderBody-Win64-Shipping.exe"
            })
            init_msdk(json_config)
            await websocket.send("DLL初始化已发送")

async def main():
    async with websockets.serve(msdk_handler, "localhost", 8765):
        print("WebSocket服务器启动在 ws://localhost:8765")
        await asyncio.Future()  # 运行直到被取消

if __name__ == "__main__":
    asyncio.run(main())

'''
LastEditors: tangdy tdy853839625@qq.com
FilePath: /UE_Python_Sdk_Server/websocket_server.py
'''
import asyncio
import websockets
import aioredis
from message_handle import messageHandler
import json
import os
import uuid
import wave

# 读取 JSON 文件
with open('config-dev.json', 'r') as config_file:
    config = json.load(config_file)
redis_host = config['REDIS_HOST']
redis_port = config['REDIS_PORT']
redis_password = config['REDIS_PASSWORD']

# async def messageHandler(data, connection_info):
#     await asyncio.sleep(0.1)
#     print(f"收到消息: {data}")

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

async def msdk_handler(websocket):
    random_id = uuid.uuid4()
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
            await messageHandler(data, connected[random_id_str])
    except websockets.exceptions.ConnectionClosed:
        print(f"连接关闭: {random_id_str}")
    finally:
        finalize_audio_file(connected[random_id_str]['wav_file'])
        if random_id_str in connected:
            del connected[random_id_str]
        print(f"Cleaned up resources for Client ID: {random_id_str}")

async def redis_subscriber_start_websocket(redis):
    channel_name = 'videohuman'  # 你需要订阅的频道名称
    pubsub = redis.pubsub()
    await pubsub.subscribe(channel_name)
    try:
        async for message in pubsub.listen():
            print(f"来自Redis的消息 {message}")
            if message['type'] == 'message':
                # 解析消息内容 这里是初始化一个UE
                data = json.loads(message['data'])
                print(f"收到消息: {data}")
                # 检查消息类型
                if data.get('type') == 'init':
                    # 获取 URI
                    print(f"连接到 {data.get('url')}")
                    uri = data.get('url')  # 假设有一个默认值
                    # 启动 WebSocket 客户端
                    await start_websocket_client(uri)
    finally:
        await pubsub.unsubscribe(channel_name)

async def start_websocket_client(uri):
    print(f"连接到 {uri}")
    async with websockets.connect(uri) as websocket:
        random_id = uuid.uuid4()
        random_id_str = str(random_id)
        connected[random_id_str] = {
            'websocket': websocket,
            'client_id': "",
            "audio_buffer": bytearray(),
            "frame_id": 0,
            "is_final": False,
            "audioDone": True,
            "id": random_id_str,
            "audio_future": None
        }
        wf = initialize_audio_file(connected[random_id_str]['client_id'])
        connected[random_id_str]['wav_file'] = wf

        try:
            async for message in websocket:
                data = json.loads(message)
                print(f"收到websocket消息: {data}")
                await messageHandler(data, connected[random_id_str])
            print("WebSocket连接正常关闭")  # 添加这行来确认循环是否正常结束
            await clearnWebscoket(random_id_str)
        except Exception as e:
             print(f"发生了意外的异常: {e}")
             await clearnWebscoket(random_id_str)
        except websockets.exceptions.ConnectionClosed as e:
            await clearnWebscoket(random_id_str)
            print(f"WebSocket connection closed with error: {e}")

async def clearnWebscoket(random_id_str):
    print(f"WebSocket连接关闭")
    await messageHandler({
        "action": "shutdown"
    }, connected[random_id_str])
    # 清理 connected[random_id_str]
    if random_id_str in connected:
        del connected[random_id_str]
    print(f"WebSocket connection closed with clearnWebscoket")


async def main():
    redis = aioredis.from_url(f'redis://:{redis_password}@{redis_host}:{redis_port}', encoding='utf-8')
    redis_task = asyncio.create_task(redis_subscriber_start_websocket(redis))
    server_task = websockets.serve(msdk_handler, "0.0.0.0", 8765)
    
    print("WebSocket服务器启动在 ws://localhost:8765")
    await asyncio.gather(server_task, redis_task)

if __name__ == "__main__":
    asyncio.run(main())

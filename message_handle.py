
import json
import asyncio
from dll_interface import shutdown,stop_audio, remove_prop, add_prop,init_msdk, speak_by_audio, stop_streaming,change_character,change_background,start_streaming,is_streaming,change_character_scale,change_character_pos,change_character_cloth
from functools import partial

FRAME_SIZE = 8320  # 每帧固定大小
UE_PATH = 'F:/Windows_Release/UE/Windows/RenderBody/Binaries/win64/RenderBody-Win64-Shipping.exe'
UE_PROT = 26217
push_config = {
            "rtmp_address": "rtmp://121.41.5.20:1937/live/tang",
            "resolution": {
                "width": 1080,
                "height": 1920
            },
            "framerate": 30,
            "videoBitrate": 2048000,
            "channelCount": 2,
            "sampleRate": 48000,
            "audioBitrate": 196608,
            "frame_number": 1,
            "gop_size": 12,
            "profile": 66,
            "me_range": 16,
            "max_b_frames": 2,
            "qcompress": 0.8,
            "max_qdiff": 4,
            "level": 62,
            "qmin": 18,
            "qmax": 28,
            "sws_getContext_image_flag": 4,
            "chroma_keying": {
                "transparent_streaming": True,
                "ue_chroma_keying": False,
                "ue_chroma_keying_deep": True,
                "fill_color_rgba": [
                    0,
                    255,
                    0,
                    255
                ],
                "gaussian_blur": {
                    "apply_blur": True,
                    "ksize": {
                        "width": 5,
                        "height": 5
                    },
                    "sigmaX": 0,
                    "sigmaY": 0,
                    "borderType": 4
                }
            }
        }

async def sendAudioEndData(connected, feature):
    print("发送音频结束数据")
    try:
        loop = asyncio.get_running_loop()
        start_time = loop.time()
        result = await feature  # 等待 feature 完成
        print(f"发送音频结束数据: {result}")
        await connected['websocket'].send(json.dumps(result))
    except Exception as e:
        print(f"发送数据时发生错误: {e}")
    finally:
        connected["audio_future"] = None  # 确保音频 future 被正确重置


async def messageHandler(data, connected):
      # 设置默认值防止报错
    # print(data)
    if 'type' not in data:
        data['type'] = ''
    if 'action' not in data:
        data['action'] = ''
    if data["type"] == 'audio':
        audio_data = data['data']['data']  # 获取音频数据整数列表
        if connected['audioDone']:
            audio_bytes = convert_to_bytes(audio_data, addMute=True)  # 转换为字节
        else: 
            audio_bytes = convert_to_bytes(audio_data)
        connected['audioDone'] = False
        if connected["audio_future"] is None:
            feature = asyncio.Future()
            connected["audio_future"] = feature
            print("Creating sendAudioEndData task")
            asyncio.create_task(sendAudioEndData(connected, feature))
        await process_audio_data(connected, audio_bytes)



    if data['type'] == 'audioEnd':
        connected['is_final'] = True
        await process_audio_data(connected, b'')
        # result = await connected["audio_future"]
        # await connected['websocket'].send(json.dumps(result))
        # if feature:
            # await asyncio.sleep(5)
            # feature.set_result({"code": 0, "status": {}, "name": "speak_by_audio", "success": True, "client_id": connected['client_id']})
        # 5s后发送音频结束消息
        # await asyncio.sleep(5)
        # await connected['websocket'].send(json.dumps({"code": 0, "status": {}, "name": "speak_by_audio", "success": True, "client_id": connected['client_id']}))

    if data['action'] == 'stop':
        # 停止推流
        results = await stop_streaming(connected['client_id'])
        await connected['websocket'].send(json.dumps(results))
    if data['action'] == 'isStreaming':
        # 查询是否推流
        results = await is_streaming(connected['client_id'])
        await connected['websocket'].send(json.dumps(results))

    if data['action'] == 'change_background':
        # 切换背景
        results = await change_background(connected['client_id'], data['type'], data['url'])
        await connected['websocket'].send(json.dumps(results))

    if data['action'] == 'change_character_scale':
        # 切换背景
        results = await change_character_scale(connected['client_id'], data['scale'])
        await connected['websocket'].send(json.dumps(results))

    if data['action'] == 'change_character_pos':
        # 切换位置
        results = await change_character_pos(connected['client_id'], data['x'], data['y'])
        await connected['websocket'].send(json.dumps(results))

    if data['action'] == 'change_character_cloth':
        # 切换衣服
        results = await change_character_cloth(connected['client_id'], data['clothName'])
        await connected['websocket'].send(json.dumps(results))

    if data['action'] == 'add_prop':
        # 新增道具
        results = await add_prop(connected['client_id'], data['url'],data['pos_x'], data['pos_y'], data['size_x'], data['size_y'])
        await connected['websocket'].send(json.dumps(results))

    if data['action'] == 'remove_prop':
        # 移除道具
        results = await remove_prop(connected['client_id'], data['prop_id'])
        await connected['websocket'].send(json.dumps(results))

    if data['action'] == 'stop_audio':
        # 结束UE
        stop_audio(connected['client_id'])

    if data['action'] == 'shutdown':
        # 结束UE
        results = await shutdown(connected['client_id'])

    if data['action'] == 'change_character':
        # 切换角色
        results = await change_character(connected['client_id'], data['character'])
        await connected['websocket'].send(json.dumps(results))

    if data['action'] == 'start_streaming':
        # 开始推流
        print("开始推流")
        merge_config = merge_dicts(push_config, data['config'])
        results = await start_streaming(connected['client_id'], json.dumps(merge_config))
        print(f"推流结果: {results}")
        await connected['websocket'].send(json.dumps(results))

    if data['action'] == 'init':
        print("初始化DLL")
        baseConfig = {
            "display_ue_window": True,
            "play_ue_sound": True,
            "ws_server_port": UE_PROT,
            "ue_fullpath": UE_PATH
        }
        json_config = merge_dicts(baseConfig, data['data'])
        json_config = json.dumps(json_config)
        try:
            results = await async_init_msdk(connected, json_config)
            print(f"初始化结果: {results}")
            await connected['websocket'].send(json.dumps(results))
        except Exception as e:
        #     await websocket.send(f"初始化失败: {e}")
        # await websocket.send("DLL初始化已发送")
        # 把错误信息上报
            print(f"初始化失败: {e}")

def send_frame(frame_data, frame_id, connected):
    wf = connected['wav_file']
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
    speak_by_audio(connected['client_id'], json_config, connected["audio_future"])

async def process_audio_data(connected, data):
    connected['audio_buffer'].extend(data)

    while len(connected['audio_buffer']) >= FRAME_SIZE:
        send_frame(connected['audio_buffer'][:FRAME_SIZE], connected['frame_id'], connected)
        connected['frame_id'] += 1
        connected['audio_buffer'] = connected['audio_buffer'][FRAME_SIZE:]

    if connected['is_final'] and not connected['audioDone']:
        # 发送所有剩余数据，无论其大小
        if len(connected['audio_buffer']) > 0:
            send_frame(connected['audio_buffer'], connected['frame_id'], connected)
            # await asyncio.sleep(0.1)  # 使用异步sleep
        # 重置
        print("发送最后一帧")
        connected['audio_buffer'] = bytearray()
        connected['frame_id'] = 0
        send_frame(connected['audio_buffer'], -1, connected)
        connected['is_final'] = False
        connected['audioDone'] = True
           
async def async_init_msdk(content, json_config):
    print("async_init_msdk run")
    try:
        result = await init_msdk(content, json_config)
        print(f"async_init_msdk result: {result}")
        return result
    except Exception as e:
        print(f"Error during MSDK initialization: {e}")
        return None


def convert_to_bytes(data, addMute=False):
    result = bytes(data)
    # data是整数列表，例如：[252, 231, 148, ...]
    if addMute:
        # 前面0.2秒替换为静音数据
        result = bytes([0] * 320) + result[320:]
    return result
        
def merge_dicts(dict1, dict2):
    """
    Recursively merge two dictionaries.
    """
    result = dict1.copy()  # Start with dict1's keys and values
    for key, value in dict2.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            # If both dictionaries have a dictionary for this key, recurse
            result[key] = merge_dicts(result[key], value)
        else:
            # If not, use dict2's value, overwriting dict1's value if key exists
            result[key] = value
    return result
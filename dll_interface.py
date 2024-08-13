import ctypes
from ctypes import c_char_p, c_void_p, c_float,CFUNCTYPE, c_int
from enuminfo import MSDKStatus
import json
import asyncio
import time
from concurrent.futures import ThreadPoolExecutor

executor = ThreadPoolExecutor()

curConfig = {}
websocketAll = {}
# 定义全局字典来存储不同指令的Future对象
futures_streaming = {}
futures_init_finish = {}
futures_start_streaming = {}
futures_stop_streaming = {}
futures_isStreaming = {}
futures_change_character = {}
futures_change_chara_pos = {}
futures_change_character_cloth = {}
futures_change_background = {}
futures_play_character_anim = {}
futures_change_character_scale = {}
futures_add_prop = {}
futures_remove_prop = {}
futures_speak_by_audio_file = {}
futures_shutdown = {}

def set_futures_status(client_id, futures_obj, data):
    if client_id in futures_obj:
        future = futures_obj.pop(client_id)
        if not future.done():
            future.set_result(data)

# 定义C++中的结构体 MSDKJsonParams_SpeakByAudio 对应的Python结构体
class MSDKJsonParamsSpeakByAudio(ctypes.Structure):
    _fields_ = [
        ("FrameNum", ctypes.c_int),
        ("FrameID", ctypes.c_int),
        ("Subtitle", ctypes.c_char_p),
        ("Data", ctypes.c_void_p)
    ]



# 加载DLL
msdk = ctypes.CDLL('F:/Windows_Release/MSDK.dll')

# 定义回调函数类型
# MSDKCallback_InitProgress = ctypes.CFUNCTYPE(c_void_p, c_float)
CALLBACK_PROGRESS = CFUNCTYPE(None, c_int, c_float)
CALLBACK_FINISH = CFUNCTYPE(None, c_int, c_char_p, c_char_p)

# 定义回调函数
def callback_progress(code, progress):
    print(f"初始化进度: {progress:.2f}")
    print(f"初始化状态: {code}")

def callback_finish(code, status, client_id):
    status = json.loads(status.decode('utf-8'))  # 假设status是UTF-8编码的字符串
    client_id = client_id.decode('utf-8')  # 解码客户端ID
    global curConfig
    curConfig['client_id'] = client_id
    print(f"初始化完成: {code}, {MSDKStatus.MSDK_SUCCESS_INIT.value} ")
    print(f"初始化完成: {curConfig['id']}, 客户端ID: {client_id}")
    if code == MSDKStatus.MSDK_SUCCESS_INIT.value:
        set_futures_status(client_id, futures_init_finish, {"code": code, "success": True , "status": status, 'name': 'init', "client_id": client_id})
        print(f"初始化成功: {status}, 客户端ID: {client_id}")
        # change_character(client_id, "xiaogang")
    else:
        set_futures_status(client_id, futures_init_finish, {"code": code, "success": False , "client_id": client_id})
        print(f"初始化失败: {status}, 客户端ID: {client_id}")

# 创建回调函数实例---初始化
callback_progress_instance = CALLBACK_PROGRESS(callback_progress)
callback_finish_instance = CALLBACK_FINISH(callback_finish)
msdk.MSDK_Init.restype = c_char_p

# 初始化函数
async def init_msdk(content, json_config):
    # 调用DLL中的初始化函数
    global curConfig
    curConfig = content
    print(f"初始化DLL:init_msdk run ")
    try:
        future = asyncio.Future()
        init_result = msdk.MSDK_Init(c_char_p(json_config.encode('utf-8')), callback_progress_instance, callback_finish_instance)
        # 输出返回的 c_char_p 类型的数据
        if init_result:
            try:
                init_result = ctypes.cast(init_result, c_char_p).value.decode('utf-8')
                websocketAll[init_result] = content
                print("Returned data:")
                print(init_result)
            except Exception as e:
                print(f"Error occurred: {e}")
        else:
            print("No data returned or error occurred")
        await_start_time = time.time()
        futures_init_finish[init_result] = future
        while not future.done():
            await asyncio.sleep(0)
        result = await future
        await_end_time = time.time()
        print(f"await开始时间: {await_start_time}, 结束时间: {await_end_time}, 耗时: {await_end_time - await_start_time}秒")
        return result
    except Exception as e:
        print(f"初始化失败: {e}")
        
# MSDK_API void MSDK_ChangeCharacter(const char* ClientID, const char* Name, bool WithTranslucentFX, MSDKCallback CallBack);

    
# MSDK_API void MSDK_StartStreaming(const char* ClientID, const char* JsonConfig, MSDKCallback Callback);
# 定义回调函数类型---开始直播
CALLBACK_START_STREAMING = CFUNCTYPE(None, c_int, c_char_p, c_char_p)
def callback_start_streaming(code, status ,client_id):
    client_id = client_id.decode('utf-8')  # 解码客户端ID
    status = json.loads(status.decode('utf-8'))  # 假设status是UTF-8编码的字符串
    if code == MSDKStatus.MSDK_SUCCESS_START_STREAMING.value:
        print(f"开始直播成功: {code}, 客户端ID: {client_id}")
        set_futures_status(client_id, futures_start_streaming, {"code": code, "status": status, "success": True, "client_id": client_id})
    else:
        print(f"开始直播失败: {code}, 客户端ID: {client_id}")
        set_futures_status(client_id, futures_start_streaming, {"code": code, "success": False,"status": status,  "client_id": client_id})


    
callback_start_streaming_instance = CALLBACK_START_STREAMING(callback_start_streaming)

async def start_streaming(client_id, json_config):
    # 调用DLL中的开始直播函数
    future = asyncio.Future()
    futures_start_streaming[client_id] = future
    try:
        msdk.MSDK_StartStreaming(c_char_p(client_id.encode('utf-8')), c_char_p(json_config.encode('utf-8')), callback_start_streaming_instance)
    except Exception as e:
        print(f"开始直播 start_streaming 失败: {e}")
    while not future.done():
        await asyncio.sleep(0)
    result = await future
    print(f"开始start_streaming直播结果===>: {result}")
    return result
    
    
    
#MSDK_API void MSDK_SpeakByAudio(const char* ClientID, const MSDKJsonParams_SpeakByAudio& JsonConfig, MSDKCallback_SpeakByAudio CallBack);
#回调函数 typedef void(*MSDKCallback_SpeakByAudio)(MSDKStatusCode /*Code*/, const char* /*Status*/, int /*FrameID*/, const char* /*ClientID*/);
#语音说话
# typedef struct MSDKSpeakByAudio {
#     int FrameNum; // 一帧数据量，建议为8320
#     int FrameID;// 帧ID
#     const char* Subtitle;// 字幕
#     void* Data;// 音频数据
# } MSDKJsonParams_SpeakByAudio;
    # ○ 音频数据流，采样率为16000，单通道。
    # ○ 最后一帧需要传入FrameId为-1
CALLBACK_SPEAK_BY_AUDIO = CFUNCTYPE(None, c_int, c_char_p, c_int, c_char_p)
def callback_speak_by_audio(code, status, frame_id, client_id):
    client_id = client_id.decode('utf-8')  # 解码客户端ID
    status = status.decode('utf-8')  # 解码角色名
    print(f"语音说话: {code}, 客户端ID: {client_id}, info: {status}")
    if code == MSDKStatus.MSDK_ERROR_SPEAK_BY_AUDIO.value:
        print(f"播放失败: {client_id},")
    
callback_speak_by_audio_instance = CALLBACK_SPEAK_BY_AUDIO(callback_speak_by_audio)


def speak_by_audio(client_id, config):
    # typedef struct MSDKSpeakByAudio {
    #     int FrameNum; // 一帧数据量，建议为8320
    #     int FrameID;// 帧ID
    #     const char* Subtitle;// 字幕
    #     void* Data;// 音频数据
    # } MSDKJsonParams_SpeakByAudio;
        # ○ 音频数据流，采样率为16000，单通道。
        # ○ 最后一帧需要传入FrameId为-1
    json_config = MSDKJsonParamsSpeakByAudio()
    json_config.FrameNum = config['FrameNum']
    json_config.FrameID = config['FrameID']
    print(f"FrameID====send: {json_config.FrameID}")
    json_config.Data = ctypes.cast(ctypes.create_string_buffer(bytes(config['Data'])), ctypes.c_void_p)
    msdk.MSDK_SpeakByAudioData(c_char_p(client_id.encode('utf-8')), ctypes.byref(json_config), callback_speak_by_audio_instance)
    


# MSDK_API void MSDK_StopStreaming(const char* ClientID, MSDKCallback Callback);
# 回调 typedef void(*MSDKCallback)(MSDKStatusCode /*Code*/, const char* /*Status*/, const char* /*ClientID*/);
# 停止直播
CALLBACK_STOP_STREAMING = CFUNCTYPE(None, c_int, c_char_p, c_char_p)
def callback_stop_streaming(code, status, client_id):
    client_id = client_id.decode('utf-8')  # 解码客户端ID
    status = json.loads(status.decode('utf-8'))  # 假设status是UTF-8编码的字符串
    print(f"停止直播: {status}, 客户端ID: {client_id}")
    if code == MSDKStatus.MSDK_SUCCESS_STOP_STREAMING.value:
        print(f"停止直播: {code}, 客户端ID: {client_id}")
        set_futures_status(client_id, futures_stop_streaming, {"code": code, "status": status, "success": True, "client_id": client_id})
    else:
        set_futures_status(client_id, futures_stop_streaming, {"code": code, "success": False, "status": status, "client_id": client_id})
        print(f"停止直播失败: {code}, 客户端ID: {client_id}")
        

callback_stop_streaming_instance = CALLBACK_STOP_STREAMING(callback_stop_streaming)

async def stop_streaming(client_id):
        # 调用DLL中的开始直播函数
    future = asyncio.Future()
    futures_stop_streaming[client_id] = future
    try:
        msdk.MSDK_StopStreaming(c_char_p(client_id.encode('utf-8')), callback_stop_streaming_instance)
    except Exception as e:
        print(f"停止直播 start_streaming 失败: {e}")
    while not future.done():
        await asyncio.sleep(0)
    result = await future
    print(f"开始start_streaming直播结果===>: {result}")
    return result

# MSDK_API void MSDK_IsStreaming(const char* ClientID, MSDKCallback Callback);
# typedef void(*MSDKCallback)(MSDKStatusCode /*Code*/, const char* /*Status*/, const char* /*ClientID*/);

# 查询是否正在推流
CALLBACK_IS_STREAMING = CFUNCTYPE(None, c_int, c_char_p, c_char_p)
def callback_is_streaming(code, status, client_id):
    client_id = client_id.decode('utf-8')  # 解码客户端ID
    status = json.loads(status.decode('utf-8'))  # 假设status是UTF-8编码的字符串
    if code == MSDKStatus.MSDK_SUCCESS_GET_IS_STREAMING_DOING.value:
        print(f"查询是否正在推流: {code}, 客户端ID: {client_id}, status: {status}")
        set_futures_status(client_id, futures_isStreaming, {"code": code, "success": True, "client_id": client_id})
    else:
        print(f"查询是否正在推流: {code}, 客户端ID: {client_id}, status: {status}")
        set_futures_status(client_id, futures_isStreaming, {"code": code, "success": False,  "client_id": client_id})



callback_is_streaming_instance = CALLBACK_IS_STREAMING(callback_is_streaming)

async def is_streaming(client_id):
    future = asyncio.Future()
    futures_isStreaming[client_id] = future
    msdk.MSDK_IsStreaming(c_char_p(client_id.encode('utf-8')), callback_is_streaming_instance)
    while not future.done():
        await asyncio.sleep(0)
    result = await future
    return result


# MSDK_API void MSDK_PlayCharacterAnim(const char* ClientID, const char* AnimName, MSDKCallback CallBack);
# typedef void(*MSDKCallback)(MSDKStatusCode /*Code*/, const char* /*Status*/, const char* /*ClientID*/);

# 播放角色指定动画
CALLBACK_PLAY_CHARACTER_ANIM = CFUNCTYPE(None, c_int, c_char_p, c_char_p)
def callback_play_character_anim(code, status, client_id):
    client_id = client_id.decode('utf-8')  # 解码客户端ID
    status = json.loads(status.decode('utf-8'))  # 假设status是UTF-8编码的字符串
    print(f"播放角色指定动画: {code}, 客户端ID: {client_id}, info: {status}")
    if code == MSDKStatus.MSDK_SUCCESS_STOP_STREAMING.value:
        print(f"播放角色指定动画: {code}, 客户端ID: {client_id}")
        set_futures_status(client_id, futures_play_character_anim, {"code": code, "status": status, "success": True, "client_id": client_id})
    else:
        set_futures_status(client_id, futures_play_character_anim, {"code": code, "success": False, "status": status, "client_id": client_id})
        print(f"播放角色指定动画失败: {code}, 客户端ID: {client_id}")
    

callback_play_character_anim_instance = CALLBACK_PLAY_CHARACTER_ANIM(callback_play_character_anim)

async def play_character_anim(client_id, anim_name):
    future = asyncio.Future()
    futures_play_character_anim[client_id] = future
    msdk.MSDK_PlayCharacterAnim(c_char_p(client_id.encode('utf-8')), c_char_p(anim_name.encode('utf-8')), callback_play_character_anim_instance)
    while not future.done():
        await asyncio.sleep(0)
    result = await future
    return result



# 定义回调函数类型---切换角色
CALLBACK_CHANGE_CHARACTER = CFUNCTYPE(None, c_int, c_char_p, c_char_p)
def callback_change_character(code, status, client_id):
    client_id = client_id.decode('utf-8')  # 解码客户端ID
    status = json.loads(status.decode('utf-8'))  # 假设status是UTF-8编码的字符串
    if code == MSDKStatus.MSDK_SUCCESS_CHANGE_CHARACTER.value:
        set_futures_status(client_id, futures_change_character, {"code": code, "success": True , "status": status, "client_id": client_id})
        print(f"切换角色成功: {code},")
    else:
        set_futures_status(client_id, futures_change_character, {"code": code, "success": False , "client_id": client_id})
        print(f"切换角色失败: {code},")
    print(f"切换角色: {code}, 客户端ID: {client_id}, info: {status}")
    # change_character_pos(client_id, int(1920 / 2) , 1080 - 100)
    # start_streaming(client_id, json.dumps(push_config))
    
# xiaogang    
callback_change_character_instance = CALLBACK_CHANGE_CHARACTER(callback_change_character)

async def change_character(client_id, name):
    # 创建回调函数实例
    # 调用DLL中的切换角色函数
    future = asyncio.Future()
    futures_change_character[client_id] = future
    msdk.MSDK_ChangeCharacter(c_char_p(client_id.encode('utf-8')), c_char_p(name.encode('utf-8')), True, callback_change_character_instance)
    while not future.done():
        await asyncio.sleep(0)
    result = await future
    return result
    
# MSDK_API void MSDK_ChangeCharacterPos(const char* ClientID, int X, int Y, MSDKCallback CallBack);
# typedef void(*MSDKCallback)(MSDKStatusCode /*Code*/, const char* /*Status*/, const char* /*ClientID*/);  回调
# 更改角色位置
CALLBACK_CHANGE_CHARACTER_POS = CFUNCTYPE(None, c_int, c_char_p, c_char_p)
def callback_change_character_pos(code, status, client_id):
    client_id = client_id.decode('utf-8')  # 解码客户端ID
    status = json.loads(status.decode('utf-8'))  # 假设status是UTF-8编码的字符串
    if code == MSDKStatus.MSDK_SUCCESS_CHANGE_CHARACTER_POSITION.value:
        set_futures_status(client_id, futures_change_chara_pos, {"code": code, "success": True , "status": status, "client_id": client_id})
        print(f"更改角色位置: {code},")
    else:
        set_futures_status(client_id, futures_change_chara_pos, {"code": code, "success": False , "client_id": client_id})
        print(f"更改角色位置失败: {code},")

callback_change_character_pos_instance = CALLBACK_CHANGE_CHARACTER_POS(callback_change_character_pos)

async def change_character_pos(client_id, x, y):
    future = asyncio.Future()
    futures_change_chara_pos[client_id] = future
    # 调用DLL中的更改角色位置函数
    msdk.MSDK_ChangeCharacterPos(c_char_p(client_id.encode('utf-8')), x, y, callback_change_character_pos_instance)    
    while not future.done():
        await asyncio.sleep(0)
    result = await future
    return result
    

# MSDK_ChangeCharacterScale
# MSDK_API void MSDK_ChangeCharacterScale(const char* ClientID, float Scale, MSDKCallback CallBack);
# typedef void(*MSDKCallback)(MSDKStatusCode /*Code*/, const char* /*Status*/, const char* /*ClientID*/);

# 更改角色大小

CALLBACK_CHANGE_CHARACTER_SCALE = CFUNCTYPE(None, c_int, c_char_p, c_char_p)

def callback_change_character_scale(code, status, client_id):
    client_id = client_id.decode('utf-8')  # 解码客户端ID
    status = json.loads(status.decode('utf-8'))  # 假设status是UTF-8编码的字符串
    print(f"更改角色大小: {code}, 客户端ID: {client_id}, info: {status}")
    if code == MSDKStatus.MSDK_SUCCESS_CHANGE_CHARACTER_SCALE.value:
        set_futures_status(client_id, futures_change_character_scale, {"code": code, "success": True , "status": status, "client_id": client_id})
        print(f"更改角色大小: {code},")
    else:
        set_futures_status(client_id, futures_change_character_scale, {"code": code, "success": False , "client_id": client_id})
        print(f"更改角色大小失败: {code},")

callback_change_character_scale_instance = CALLBACK_CHANGE_CHARACTER_SCALE(callback_change_character_scale)

async def change_character_scale(client_id, scale):
    # futures_change_character_scale
    # 调用DLL中的更改角色大小函数
    future = asyncio.Future()
    futures_change_character_scale[client_id] = future
    msdk.MSDK_ChangeCharacterScale(c_char_p(client_id.encode('utf-8')), c_float(scale), callback_change_character_scale_instance)
    while not future.done():
        await asyncio.sleep(0)
    result = await future
    return result


#MSDK_API void MSDK_ChangeCharacterCloth(const char* ClientID, const char* ClothName, MSDKCallback CallBack);
# typedef void(*MSDKCallback)(MSDKStatusCode /*Code*/, const char* /*Status*/, const char* /*ClientID*/);
# 更改角色服装
CALLBACK_CHANGE_CHARACTER_CLOTH = CFUNCTYPE(None, c_int, c_char_p, c_char_p)
def callback_change_character_cloth(code, status, client_id):
    client_id = client_id.decode('utf-8')  # 解码客户端ID
    status = json.loads(status.decode('utf-8'))  # 假设status是UTF-8编码的字符串
    print(f"更改角色服装: {code}, 客户端ID: {client_id}, info: {status}")
    if code == MSDKStatus.MSDK_SUCCESS_CHANGE_CHARACTER_CLOTH.value:
        set_futures_status(client_id, futures_change_character_cloth, {"code": code, "success": True , "status": status, "client_id": client_id})
        print(f"更改角色服装: {code},")
    else:
        set_futures_status(client_id, futures_change_character_cloth, {"code": code, "success": False , "client_id": client_id})
        print(f"更改角色服装失败: {code},")

callback_change_character_cloth_instance = CALLBACK_CHANGE_CHARACTER_CLOTH(callback_change_character_cloth)

async def change_character_cloth(client_id, cloth_name):
    # 调用DLL中的更改角色服装函数
    # futures_change_character_cloth
    future = asyncio.Future()
    futures_change_character_cloth[client_id] = future
    msdk.MSDK_ChangeCharacterCloth(c_char_p(client_id.encode('utf-8')), c_char_p(cloth_name.encode('utf-8')), callback_change_character_cloth_instance)
    while not future.done():
        await asyncio.sleep(0)
    result = await future
    return result

# 道具管理
#MSDK_API void MSDK_AddProp(const char* ClientID, const char* Url, int POS_X, int POS_Y, int SIZE_X, int SIZE_Y, MSDKCallback CallBack);
#typedef void(*MSDKCallback)(MSDKStatusCode /*Code*/, const char* /*Status*/, const char* /*ClientID*/);

# ● ClientID：客户端 ID。
# ● Url：道具 URL 地址。
# ● POS_X：道具的 X 轴位置，像素坐标，左上角为0,0，右下角为分辨率，传入的参数限制在分辨率之内。
# ● POS_Y：道具的 Y 轴位置。
# ● SIZE_X：道具的宽度，像素大小。
# ● SIZE_Y：道具的高度，像素大小。

CALLBACK_ADD_PROP = CFUNCTYPE(None, c_int, c_char_p)

def callback_add_prop(code, status):
    status = json.loads(status.decode('utf-8'))  # 假设status是UTF-8编码的字符串
    print(f"添加道具: {code},  info: {status}")
    if code == MSDKStatus.MSDK_SUCCESS_ADD_PROP.value:
        set_futures_status(status["clientId"], futures_add_prop, {"code": code, "success": True , "status": status, "client_id": status["clientId"]})
        print(f"添加道具: {code},")
    else:
        set_futures_status(status["clientId"], futures_add_prop, {"code": code, "success": False , "client_id": status["clientId"]})
        print(f"添加道具失败: {code},")

callback_add_prop_instance = CALLBACK_ADD_PROP(callback_add_prop)

async def add_prop(client_id, url, pos_x, pos_y, size_x, size_y):
    # 调用DLL中的添加道具函数
    # futures_add_prop
    future = asyncio.Future()
    futures_add_prop[client_id] = future
    msdk.MSDK_AddProp(c_char_p(client_id.encode('utf-8')), c_char_p(url.encode('utf-8')), pos_x, pos_y, size_x, size_y, callback_add_prop_instance)
    while not future.done():
        await asyncio.sleep(0)
    result = await future
    return result

# 移除道具
# MSDK_API void MSDK_RemoveProp(const char* ClientID, int PropId, MSDKCallback CallBack);
# ● ClientID：客户端 ID。
# ● PropId：道具 ID。
# ● CallBack：移除结果的回调函数。
#     ○ Code：状态码
#         ■ MSDK_SUCCESS_REMOVE_PROP：删除道具成功
#         ■ MSDK_ERROR_REMOVE_PROP：删除道具失败
#     ○ Status：具体的消息信息
CALLBACK_REMOVE_PROP = CFUNCTYPE(None, c_int, c_char_p)

def callback_remove_prop(code, status):
    status = json.loads(status.decode('utf-8'))  # 假设status是UTF-8编码的字符串
    print(f"移除道具: {code},  info: {status}")
    if code == MSDKStatus.MSDK_SUCCESS_REMOVE_PROP.value:
        set_futures_status(status["clientId"], futures_remove_prop, {"code": code, "success": True , "status": status, "client_id": status["clientId"]})
        print(f"移除道具: {code},")
    else:
        set_futures_status(status["clientId"], futures_remove_prop, {"code": code, "success": False , "client_id": status["clientId"]})
        print(f"移除道具失败: {code},")

callback_remove_prop_instance = CALLBACK_REMOVE_PROP(callback_remove_prop)

async def remove_prop(client_id, prop_id):
    # 调用DLL中的移除道具函数
    future = asyncio.Future()
    futures_remove_prop[client_id] = future
    msdk.MSDK_RemoveProp(c_char_p(client_id.encode('utf-8')), prop_id, callback_remove_prop_instance)
    while not future.done():
        await asyncio.sleep(0)
    result = await future
    return result


# 背景管理
# MSDK_ChangeBackground

# MSDK_API void MSDK_ChangeBackground(const char* ClientID, const char* Type, const char* Url, MSDKCallback CallBack);
# typedef void(*MSDKCallback)(MSDKStatusCode /*Code*/, const char* /*Status*/, const char* /*ClientID*/);
# to
# 更改TODO
# ● CallBack：更换结果的回调函数。
#     ○ MSDKStatusCode：：切换背景成功/失败：MSDK_SUCCESS_CHANGE_BACKGROUND /MSDK_ERROR_CHANGE_BACKGROUND
#     ○ data：
#         ■ Message：成功失败以及失败原因。
#             ● 成功：Chang background successfully.
#             ● 未成功及原因：
#                 ○ Consistent with the current background image URL.与当前背景URL一致。
#                 ○ Now in the process of changing the background.当前正在换背景过程中。
#             ● 失败及原因：
#                 ○ Video player texture issue.视频播放器纹理出错。
#                 ○ Video URL playback failed.视频URL播放失败。
#                 ○ The video link cannot be played.视频URL解析失败，或者无法播放。
#                 ○ Unknow media type.无效的媒体类型，传入的type值不是Image或video。
#                 ○ Failed to download image.图片下载失败。
#                 ○ Can not download image by url “图片链接”.无法下载的图片链接。
#                 ○ Image no pixel data.图片没有像素。
#                 ○ Load background failed.背景加载失败。
#         ■ Background now：当前使用的背景URL
#     ○ success：是否成功
#     ○ clientId：返回客户端ID
CALLBACK_CHANGE_BACKGROUND = CFUNCTYPE(None, c_int, c_char_p, c_char_p, c_char_p)

def callback_change_background(code, status, success, client_id):
    print(f"更改背景===>callback_change_background: {code}, 客户端ID: {client_id}, info: {status}")
    client_id = client_id.decode('utf-8')  # 解码客户端ID
    status = json.loads(status.decode('utf-8'))  # 假设status是UTF-8编码的字符串
    success = success.decode('utf-8')  # 假设status是UTF-8编码的字符串
    print(success)
    if code == MSDKStatus.MSDK_SUCCESS_CHANGE_BACKGROUND.value:
        set_futures_status(client_id, futures_change_background, {"code": code, "success": True , "status": status, "client_id": client_id})
        print(f"更改背景: {code},")
    else:
        set_futures_status(client_id, futures_change_background, {"code": code, "success": False , "client_id": client_id})
        print(f"更改背景失败: {code},")

callback_change_background_instance = CALLBACK_CHANGE_BACKGROUND(callback_change_background)

async def change_background(client_id, type, url):
    # 调用DLL中的更改背景函数
    future = asyncio.Future()
    futures_change_background[client_id] = future
    msdk.MSDK_ChangeBackground(c_char_p(client_id.encode('utf-8')), c_char_p(type.encode('utf-8')), c_char_p(url.encode('utf-8')), callback_change_background_instance)
    while not future.done():
        await asyncio.sleep(0)
    result = await future
    return result


# # MSDK_SpeakByAudioByFile
# # MSDK_API void MSDK_SpeakByAudioFile(const char* ClientID, const char* AudioPath, MSDKCallback CallBack);
# #typedef void(*MSDKCallback)(MSDKStatusCode /*Code*/, const char* /*Status*/, const char* /*ClientID*/);

# # 语音文件说话
CALLBACK_SPEAK_BY_AUDIO_FILE = CFUNCTYPE(None, c_int, c_char_p, c_char_p)
def callback_speak_by_audio_file(code, status, client_id):
    client_id = client_id.decode('utf-8')  # 解码客户端ID
    status = json.loads(status.decode('utf-8'))  # 假设status是UTF-8编码的字符串
    if code == MSDKStatus.MSDK_SUCCESS_SPEAK_BY_AUDIO_FINISH.value:
        set_futures_status(client_id, futures_speak_by_audio_file, {"code": code, "success": True , "status": status, "client_id": client_id})
        print(f"文件说话: {code},")
    else:
        set_futures_status(client_id, futures_speak_by_audio_file, {"code": code, "success": False , "client_id": client_id})
        print(f"文件说话失败: {code},")

callback_speak_by_audio_file_instance = CALLBACK_SPEAK_BY_AUDIO_FILE(callback_speak_by_audio_file)

async def speak_by_audio_file(client_id, audio_path):
        # 调用DLL中的更改背景函数
    future = asyncio.Future()
    futures_speak_by_audio_file[client_id] = future
    msdk.MSDK_SpeakByAudioFile(c_char_p(client_id.encode('utf-8')), c_char_p(audio_path.encode('utf-8')), callback_speak_by_audio_file_instance)
    while not future.done():
        await asyncio.sleep(0)
    result = await future
    return result
    # 调用DLL中的语音文件说话函数



# 关闭SDK

CALLBACK_SHUTDOWN = CFUNCTYPE(None, c_int, c_char_p, c_char_p)

def callback_shutdown(code, status, client_id):
    client_id = client_id.decode('utf-8')  # 解码客户端ID
    status = json.loads(status.decode('utf-8'))  # 假设status是UTF-8编码的字符串
    if code == MSDKStatus.MSDK_SUCCESS_SHUTDOWN.value:
        set_futures_status(client_id, futures_shutdown, {"code": code, "success": True , "status": status, "client_id": client_id})
        print(f"关闭SDK: {code},")
    else:
        set_futures_status(client_id, futures_shutdown, {"code": code, "success": False , "client_id": client_id})
        print(f"关闭SDK失败: {code},")

callback_shutdown_instance = CALLBACK_SHUTDOWN(callback_shutdown)

async def shutdown(client_id):
    # 调用DLL中的关闭SDK函数
    future = asyncio.Future()
    futures_shutdown[client_id] = future
    msdk.MSDK_Shutdown(c_char_p(client_id.encode('utf-8')), callback_shutdown_instance)
    while not future.done():
        await asyncio.sleep(0)
    result = await future
    return result

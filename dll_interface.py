import ctypes
from ctypes import c_char_p, c_void_p, c_float,CFUNCTYPE, c_int
from enuminfo import MSDKStatus
import json


push_config = {
            "rtmp_address": "rtmp://192.168.0.64/live/livestream",
            "resolution": {
                "width": 1920,
                "height": 1080
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
    status = status.decode('utf-8')  # 假设status是UTF-8编码的字符串
    client_id = client_id.decode('utf-8')  # 解码客户端ID
    print(f"初始化完成: {code}, {MSDKStatus.MSDK_SUCCESS_INIT.value} ")
    if code == MSDKStatus.MSDK_SUCCESS_INIT.value:
        print(f"初始化成功: {status}, 客户端ID: {client_id}")
        change_character(client_id, "xiaogang")
    else:
        print(f"初始化失败: {status}, 客户端ID: {client_id}")

# 创建回调函数实例---初始化
callback_progress_instance = CALLBACK_PROGRESS(callback_progress)
callback_finish_instance = CALLBACK_FINISH(callback_finish)

# 初始化函数
def init_msdk(json_config):
    # 调用DLL中的初始化函数
    try:
        msdk.MSDK_Init(c_char_p(json_config.encode('utf-8')), callback_progress_instance, callback_finish_instance)
    except Exception as e:
        print(f"初始化失败: {e}")
        
# MSDK_API void MSDK_ChangeCharacter(const char* ClientID, const char* Name, bool WithTranslucentFX, MSDKCallback CallBack);

# 定义回调函数类型---切换角色
CALLBACK_CHANGE_CHARACTER = CFUNCTYPE(None, c_int, c_char_p, c_char_p)
def callback_change_character(code, status, client_id):
    client_id = client_id.decode('utf-8')  # 解码客户端ID
    status = status.decode('utf-8')  # 解码角色名
    if code == MSDKStatus.MSDK_SUCCESS_CHANGE_CHARACTER.value:
        print(f"切换角色成功: {code},")
    print(f"切换角色: {code}, 客户端ID: {client_id}, info: {status}")
    change_character_pos(client_id, int(1920 / 2) , 1080 - 100)
    start_streaming(client_id, json.dumps(push_config))
    
# xiaogang    
callback_change_character_instance = CALLBACK_CHANGE_CHARACTER(callback_change_character)

def change_character(client_id, name):
    # 创建回调函数实例
    # 调用DLL中的切换角色函数
    msdk.MSDK_ChangeCharacter(c_char_p(client_id.encode('utf-8')), c_char_p(name.encode('utf-8')), True, callback_change_character_instance)
    
# MSDK_API void MSDK_ChangeCharacterPos(const char* ClientID, int X, int Y, MSDKCallback CallBack);
# typedef void(*MSDKCallback)(MSDKStatusCode /*Code*/, const char* /*Status*/, const char* /*ClientID*/);  回调
# 更改角色位置
CALLBACK_CHANGE_CHARACTER_POS = CFUNCTYPE(None, c_int, c_char_p, c_char_p)
def callback_change_character_pos(code, status, client_id):
    client_id = client_id.decode('utf-8')  # 解码客户端ID
    status = status.decode('utf-8')  # 解码角色名
    print(f"更改角色位置: {code}, 客户端ID: {client_id}, info: {status}")

callback_change_character_pos_instance = CALLBACK_CHANGE_CHARACTER_POS(callback_change_character_pos)

def change_character_pos(client_id, x, y):
    # 调用DLL中的更改角色位置函数
    msdk.MSDK_ChangeCharacterPos(c_char_p(client_id.encode('utf-8')), x, y, callback_change_character_pos_instance)    
    
    
# MSDK_API void MSDK_StartStreaming(const char* ClientID, const char* JsonConfig, MSDKCallback Callback);
# 定义回调函数类型---开始直播
CALLBACK_START_STREAMING = CFUNCTYPE(None, c_int, c_char_p)
def callback_start_streaming(code, client_id):
    client_id = client_id.decode('utf-8')  # 解码客户端ID
    print(f"开始直播: {code}, 客户端ID: {client_id}")
    
callback_start_streaming_instance = CALLBACK_START_STREAMING(callback_start_streaming)

def start_streaming(client_id, json_config):
    # 调用DLL中的开始直播函数
    msdk.MSDK_StartStreaming(c_char_p(client_id.encode('utf-8')), c_char_p(json_config.encode('utf-8')), callback_start_streaming_instance)
    
    
    
#MSDK_API void MSDK_SpeakByAudio(const char* ClientID, const MSDKJsonParams_SpeakByAudio& JsonConfig, MSDKCallback_SpeakByAudio CallBack);
#回调函数 typedef void(*MSDKCallback_SpeakByAudio)(MSDKStatusCode /*Code*/, const char* /*Status*/, int /*FrameID*/, const char* /*ClientID*/);
#语音说话
CALLBACK_SPEAK_BY_AUDIO = CFUNCTYPE(None, c_int, c_char_p, c_int, c_char_p)
def callback_speak_by_audio(code, status, frame_id, client_id):
    client_id = client_id.decode('utf-8')  # 解码客户端ID
    status = status.decode('utf-8')  # 解码角色名
    print(f"语音说话: {code}, 客户端ID: {client_id}, info: {status}")
    
callback_speak_by_audio_instance = CALLBACK_SPEAK_BY_AUDIO(callback_speak_by_audio)

def speak_by_audio(client_id, json_config):
    msdk.MSDK_SpeakByAudio(c_char_p(client_id.encode('utf-8')), c_char_p(json_config.encode('utf-8')), callback_speak_by_audio_instance)
    
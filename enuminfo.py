from enum import Enum, auto

class MSDKStatus(Enum):
    MSDK_SUCCESS_INIT_AUTH = 0                           # Init授权成功
    MSDK_SUCCESS_INIT_JSON_PARSE = auto()                 # InitJSON解析成功
    MSDK_SUCCESS_INIT_WS_SERVER = auto()                  # InitMSDK创建WS服务器成功
    MSDK_SUCCESS_INIT_STARTUE = auto()                    # InitUE启动成功
    MSDK_SUCCESS_INIT_WS_UECLIENT_CONNECT = auto()        # InitUE与MSDK成功建立连接
    MSDK_SUCCESS_INIT = auto()                            # Init函数成功

    MSDK_SUCCESS_START_STREAMING = auto()                 # 开始推流成功
    MSDK_SUCCESS_STOP_STREAMING = auto()                  # 停止推流成功
    MSDK_SUCCESS_GET_IS_STREAMING_DOING = auto()          # 获取推流状态成功, 正在推流中
    MSDK_SUCCESS_GET_IS_STREAMING_NOT = auto()            # 获取推流状态成功, 不在推流中

    MSDK_SUCCESS_SPECIAL_ANIMATION_PLAY_FINISH = auto()   # 指定动画播放完成
    MSDK_SUCCESS_CHANGE_CHARACTER = auto()                # 切换角色成功
    MSDK_SUCCESS_CHANGE_CHARACTER_POSITION = auto()       # 设置角色位置成功
    MSDK_SUCCESS_CHANGE_CHARACTER_SCALE = auto()          # 设置角色缩放成功
    MSDK_SUCCESS_CHANGE_CHARACTER_CLOTH = auto()
    MSDK_SUCCESS_CHANGE_BACKGROUND = auto()
    MSDK_SUCCESS_CHANGE_BACKGROUND_TRANSFORM = auto()
    MSDK_SUCCESS_ADD_PROP = auto()
    MSDK_SUCCESS_REMOVE_PROP = auto()

    MSDK_SUCCESS_SPEAK_BY_AUDIO_PLAYING = auto()
    MSDK_SUCCESS_SPEAK_BY_AUDIO_FINISH = auto()

    MSDK_SUCCESS_SHUTDOWN = auto()                        # 流程停止成功

# 使用枚举示例
print(MSDKStatus.MSDK_SUCCESS_INIT_AUTH)
print(MSDKStatus.MSDK_SUCCESS_INIT_AUTH.value)
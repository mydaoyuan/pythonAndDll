'''
LastEditors: tangdy tdy853839625@qq.com
FilePath: /UE_Python_Sdk_Server/dll_interface.py
'''
import ctypes
from ctypes import c_char_p, c_void_p

# 加载DLL
msdk = ctypes.CDLL('path_to_your_dll.dll')

# 定义回调函数类型
MSDKCallback_InitProgress = ctypes.CFUNCTYPE(c_void_p, c_int)
MSDKCallback = ctypes.CFUNCTYPE(c_void_p)

# 初始化函数
def init_msdk(json_config):
    # 定义回调函数
    def callback_progress(progress):
        print(f"初始化进度: {progress}%")

    def callback_finish():
        print("初始化完成")

    # 创建回调函数实例
    callback_progress_instance = MSDKCallback_InitProgress(callback_progress)
    callback_finish_instance = MSDKCallback(callback_finish)

    # 调用DLL中的初始化函数
    msdk.MSDK_Init(c_char_p(json_config.encode('utf-8')), callback_progress_instance, callback_finish_instance)

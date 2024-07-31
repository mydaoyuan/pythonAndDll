import ctypes
from ctypes import c_int, c_char_p, c_float, c_void_p
import time
# 加载 MSDK 动态库
msdk = ctypes.CDLL('F:/Windows_Release/MSDK.dll')

# 定义回调函数类型
MSDKCallback_InitProgress = ctypes.CFUNCTYPE(None, c_int, c_float)
MSDKCallback = ctypes.CFUNCTYPE(None, c_int, c_char_p, c_char_p)
  # 定义回调函数
def progress_callback(code, progress):
    print(f'Init Progress - Code: {code}, Progress: {progress}')

def finish_callback(code, status, client_id):
    print(f'Init Finish - Code: {code}, Status: {status.decode()}, ClientID: {client_id}')

  # 转换为 C 函数指针
progress_callback_c = MSDKCallback_InitProgress(progress_callback)
finish_callback_c = MSDKCallback(finish_callback)

def init_msdk(json_config):
  # 调用初始化函数
  msdk.MSDK_Init(c_char_p(json_config.encode()), progress_callback_c, finish_callback_c)
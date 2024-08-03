<!--
 * @LastEditors: tangdy tdy853839625@qq.com
 * @FilePath: /UE_Python_Sdk_Server/readme.md
-->

python -v venv .venv

# Mac OS

source .venv/bin/activate

# Windows PowerShell

.venv\Scripts\Activate.ps1

# Newly install libraries

pip install <library name>

# Install libraries using requirements.txt

pip install -r requirements.txt

# Create requirements.txt

pip freeze > requirements.txt

def decode_output(output):
try:
return output.decode('utf-8')
except UnicodeDecodeError:
return output.decode('gbk') # 或其他可能的编码
chcp 65001

### 通信

实际情况应该是 AI 模块调用 启动器

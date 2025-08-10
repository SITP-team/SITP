# 路径配置文件

# 模型模板文件路径
MODEL_FILE = r"c:/SITP/大语言模型建模/refactor1/test2.spp"

# 生成的模型保存路径
SAVED_MODEL_FILE = r"c:/SITP/大语言模型建模/refactor1/saved.spp"

# 数据输出文件路径
DATA_OUTPUT_FILE = "data_output.txt"

"""
个人配置文件
集中存放所有与环境相关的配置项，包括：
- 本地软件路径
- API端点配置
- 其他个人敏感信息

此文件不应提交到版本控制(已在.gitignore中配置)
"""

# Plant Simulation可执行文件路径
PLANT_SIM_PATHS = [
    r"D:\Program Files\siemens\Tecnomatix Plant Simulation 15\PlantSimulation.exe",
    r"C:\Program Files\Siemens\Tecnomatix Plant Simulation 2404\PlantSimulation.exe",
    r"C:\Program Files (x86)\Siemens\Tecnomatix Plant Simulation 2404\PlantSimulation.exe",
]

# API配置
API_URL = "https://api.deepseek.com/v1/chat/completions"
API_KEY = "sk-2e4c58db2ce246bbb01914b81f6e2bab"  # DeepSeek API密钥

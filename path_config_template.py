"""
配置模板文件 - 可提交到版本控制
实际使用的个人配置请修改path_config.py文件
"""

# 模型模板文件路径 (示例)
MODEL_FILE = "model_template.spp"  # 你的模板文件

# 生成的模型保存路径 (示例)
SAVED_MODEL_FILE = "saved_model.spp"  # 你的保存路径

# 数据输出文件路径 (示例)
DATA_OUTPUT_FILE = "data_output.txt"  # 你的数据输出路径

# Plant Simulation可执行文件路径 (可保留此值或修改)
PLANT_SIM_PATHS = [
    r"D:\Program Files\siemens\Tecnomatix Plant Simulation 15\PlantSimulation.exe",
    r"C:\Program Files\Siemens\Tecnomatix Plant Simulation 2404\PlantSimulation.exe",
    r"C:\Program Files (x86)\Siemens\Tecnomatix Plant Simulation 2404\PlantSimulation.exe",
]

# API配置(可保留此值或修改)
API_URL = "https://api.deepseek.com/v1/chat/completions"
API_KEY = "sk-2e4c58db2ce246bbb01914b81f6e2bab"  # 可保留或替换为您的API密钥

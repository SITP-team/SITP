#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Jul 17 12:33:39 2025
@author: chunlongyu
整合版本：支持故障、传送器、数据读写分离分离及容量0传送器处理
重构版本：适配新的节点数据结构（使用name作为标识）
"""

import time
import json
import uuid
import pythoncom
from api_utils import make_api_request
from json_utils import extract_json_from_response
from graph_preprocessor import convert_zero_capacity_conveyors_to_edges
from simtalk_generator import json_to_simtalk
from plant_simulator import create_plant_simulation_model
# 新增：导入可视化类
from visualize import ProductionLineVisualizer  # 导入可视化工具类

from prompt_config import SYSTEM_PROMPT

# 对话历史存储
conversation_history = []

print("🎯 欢迎使用 Plant Simulation 自动化建模工具！")
print("📝 请输入您的生产线描述，我将自动生成Plant Simulation模型")
print("💡 例如：源节点每10分钟生成一个产品，加工工位处理时间5分钟，缓冲区容量10...")
print("🚪 输入 'exit' 或 'quit' 可退出程序\n")

# 初始化COM环境
pythoncom.CoInitialize()
try:
    while True:
        user_input = input("👤 请输入生产线描述: ")
        if user_input.strip().lower() in ["exit", "quit"]:
            print("👋 再见！")
            break

        conversation_history.append({"role": "user", "content": user_input})

        # 构造请求消息
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        messages.extend(conversation_history)

        try:
            print("⏳ 正在生成有向图数据结构...")
            result = make_api_request(messages)
            reply = result["choices"][0]["message"]["content"]

            conversation_history.append({"role": "assistant", "content": reply})

            print("🔍 提取模型数据结构...")
            graph_data = extract_json_from_response(reply)

            # 检查API回复是否是询问而不是JSON
            if "?" in reply or "请" in reply or "需要" in reply or "缺少" in reply:
                print("\n❓ 需要补充信息:")
                print(reply)
                continue  # 继续对话循环，等待用户回答

            if graph_data:
                print("✅ 成功解析有向图数据结构！")

                # 处理并验证图数据
                print("🔍 处理并验证图数据结构...")
                is_valid, process_msg, processed_graph = ProductionLineVisualizer.process_and_validate_graph_data(
                    graph_data)
                if not is_valid:
                    print(f"❌ 图数据结构无效: {process_msg}")
                    print("请检查输入描述或API响应格式")
                    continue

                print(process_msg)
                graph_data = processed_graph  # 使用处理后的图数据

                print("🔄 检查容量为0的传送器节点...")
                graph_data = convert_zero_capacity_conveyors_to_edges(graph_data)
                print("✅ 成功处理容量为0的传送器节点")

                print("提取的JSON数据:")
                print(json.dumps(graph_data, indent=2, ensure_ascii=False))

                # 新增：初始化字体配置（生产环境可去掉print_fonts参数）
                ProductionLineVisualizer.initialize_fonts(print_fonts=False)

                # 新增：可视化有向图
                print("📊 正在可视化有向图...")
                visualizer = ProductionLineVisualizer()
                visualizer.show_static(graph_data, title="生产线有向图可视化")

                print("⏳ 正在生成Plant Simulation代码...")
                model_setup_code, data_writing_code = json_to_simtalk(graph_data)

                print("\n生成的模型建立代码:")
                print(model_setup_code)
                print("\n生成的数据写入代码:")
                print(data_writing_code)
                print()

                print("⏳ 正在创建Plant Simulation模型...")
                if create_plant_simulation_model(model_setup_code, data_writing_code):
                    print("🎉 模型创建及数据处理成功！Plant Simulation即将启动...")
                else:
                    print("❌ 操作失败，请检查错误信息")
            else:
                print("❌ 无法从响应中提取有效的JSON数据")
                print("原始API响应:")
                print(reply)

        except Exception as e:
            print(f"❌ 处理过程中发生错误: {str(e)}")
finally:
    # 释放COM环境
    pythoncom.CoUninitialize()

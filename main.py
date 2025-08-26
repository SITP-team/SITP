#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Jul 17 12:33:39 2025
@author: chunlongyu

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
from visualize import ProductionLineVisualizer
from visualization_confirm import visualize_and_confirm


from dynamic_prompt import DynamicPromptGenerator

# 新增：导入标准化处理模块
from standardization import standardize_text

# 对话历史存储
conversation_history = []

print("🎯 欢迎使用 Plant Simulation 自动化建模工具！")
print("📝 请输入您的生产线描述，我将自动生成Plant Simulation模型")
print("💡 例如：源节点每10分钟生成一个产品，加工工位处理时间5分钟，缓冲区容量10...")
print("🚪 输入 'exit' 或 'quit' 可退出程序\n")

# 调试模式开关 - 设置为True可查看AI完整思考过程
DEBUG_MODE = 1

# 初始化COM环境
pythoncom.CoInitialize()
try:
    while True:
        prompt_generator = DynamicPromptGenerator()
        user_input = input("👤 请输入生产线描述: ")
        if user_input.strip().lower() in ["exit", "quit"]:
            print("👋 再见！")
            break

        # 先进行文本标准化处理
        print("🔄 正在进行文本标准化处理...")
        standardized_text = standardize_text(user_input)

        if standardized_text:
            print("✅ 文本标准化完成！")
            print(f"标准化后的文本: {standardized_text}")
            processed_text = standardized_text
        else:
            print("⚠️  标准化处理失败，使用原始文本")
            processed_text = user_input

        # 创建循环用于支持用户确认流程
        confirmed = False
        current_graph = None
        while not confirmed:
            conversation_history.append({"role": "user", "content": user_input})
            dynamic_prompt = prompt_generator.generate_dynamic_prompt(user_input)
            print(dynamic_prompt)

            # 构造请求消息
            messages = [{"role": "system", "content": dynamic_prompt}]
            messages.extend(conversation_history)

            try:
                print("⏳ 正在生成有向图数据结构...")
                result = make_api_request(messages)
                reply = result["choices"][0]["message"]["content"]

                conversation_history.append({"role": "assistant", "content": reply})

                if DEBUG_MODE:
                    print("\nAI完整响应:")
                    print(reply)
                    print()

                print("🔍 提取模型数据结构...")
                graph_data = extract_json_from_response(reply)

                # 检查API回复是否是询问而不是JSON
                if not graph_data and (
                    "?" in reply or "请" in reply or "需要" in reply or "缺少" in reply
                ):
                    print("\n❓ 需要补充信息:")
                    print(reply)
                    user_input = input("👤 请补充相关信息: ")  # 接收补充信息
                    # 移除刚添加的用户输入，因为需要替换为新的补充信息
                    conversation_history.pop()
                    continue

                if graph_data:
                    print("✅ 成功解析有向图数据结构！")

                    # 处理并验证图数据
                    print("🔍 处理并验证图数据结构...")
                    is_valid, process_msg, processed_graph = (
                        ProductionLineVisualizer.process_and_validate_graph_data(
                            graph_data
                        )
                    )
                    if not is_valid:
                        print(f"❌ 图数据结构无效: {process_msg}")
                        print("请检查输入描述或API响应格式")
                        break

                    print(process_msg)
                    graph_data = processed_graph  # 使用处理后的图数据

                    print("🔄 检查容量为0的传送器节点...")
                    graph_data = convert_zero_capacity_conveyors_to_edges(graph_data)
                    print("✅ 成功处理容量为0的传送器节点")

                    print("提取的JSON数据:")
                    print(json.dumps(graph_data, indent=2, ensure_ascii=False))

                    # 新增：初始化字体配置
                    ProductionLineVisualizer.initialize_fonts(print_fonts=False)

                    # 替换原有可视化代码为确认流程
                    print("📊 正在可视化并确认有向图...")
                    confirmed, current_graph = visualize_and_confirm(
                        graph_data, conversation_history
                    )

                    if not confirmed:
                        # 获取用户最新修改意见
                        user_input = conversation_history[-1]["content"]
                        # 保留对话历史但重置当前循环状态
                        continue
                    else:
                        # 用户确认后跳出确认循环
                        break
                else:
                    print("❌ 无法从响应中提取有效的JSON数据")
                    print("原始API响应:")
                    print(reply)
                    break

            except Exception as e:
                print(f"❌ 处理过程中发生错误: {str(e)}")
                break

        # 确认后继续生成模型代码
        if confirmed and current_graph:
            print("⏳ 正在生成Plant Simulation代码...")
            model_setup_code, data_writing_code = json_to_simtalk(current_graph)

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

finally:
    # 释放COM环境
    pythoncom.CoUninitialize()

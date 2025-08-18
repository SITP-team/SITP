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
import networkx as nx
import matplotlib.pyplot as plt
from api_utils import make_api_request
from json_utils import extract_json_from_response
from graph_preprocessor import convert_zero_capacity_conveyors_to_edges
from simtalk_generator import json_to_simtalk
from plant_simulator import create_plant_simulation_model
# 新增：导入可视化类
from visualize import ProductionLineVisualizer  # <-- 新增导入

from prompt_config import SYSTEM_PROMPT
from visualize import visualize_directed_graph

# 全局字体配置，覆盖所有文本元素
plt.rcParams.update({
    "font.family": ["SimHei", "WenQuanYi Micro Hei", "Heiti TC", "Arial Unicode MS"],
    "axes.unicode_minus": False,  # 解决负号显示问题
    "text.usetex": False  # 禁用 LaTeX 渲染（避免与中文字体冲突）
})

import matplotlib.font_manager as fm
# 打印所有可用字体（调试用）
fonts = fm.findSystemFonts(fontpaths=None, fontext='ttf')
for font in fonts:
    try:
        font_name = fm.FontProperties(fname=font).get_name()
        print(font_name)
    except:
        pass

# 对话历史存储
conversation_history = []

print("🎯 欢迎使用 Plant Simulation 自动化建模工具！")
print("📝 请输入您的生产线描述，我将自动生成Plant Simulation模型")
print("💡 例如：源节点每10分钟生成一个产品，加工工位处理时间5分钟，缓冲区容量10...")
print("🚪 输入 'exit' 或 'quit' 可退出程序\n")

# 初始化COM环境
pythoncom.CoInitialize()


def process_and_validate_graph_data(graph_data):
    """处理并验证图数据结构，适配使用name作为节点标识的格式"""
    if not isinstance(graph_data, dict):
        return False, "图数据不是有效的字典", None

    # 确保nodes字段存在
    if 'nodes' not in graph_data:
        graph_data['nodes'] = []
        print("警告：图数据中缺少nodes字段，已自动创建空节点列表")

    # 处理节点 - 检查name属性（替代id作为标识）
    node_names = []
    for i, node in enumerate(graph_data['nodes']):
        if not isinstance(node, dict):
            print(f"警告：节点 {i} 不是有效的字典，已转换为字典")
            graph_data['nodes'][i] = {"name": f"节点{i}", "type": "unknown"}
            node = graph_data['nodes'][i]

        # 检查name属性（替代id作为唯一标识）
        if 'name' not in node:
            generated_name = f"自动节点_{uuid.uuid4().hex[:8]}"
            node['name'] = generated_name
            print(f"警告：节点 {i} 缺少'name'属性，已自动生成: {generated_name}")

        # 检查名称唯一性
        if node['name'] in node_names:
            original_name = node['name']
            node['name'] = f"{original_name}_{uuid.uuid4().hex[:4]}"
            print(f"警告：节点名称 '{original_name}' 重复，已重命名为: {node['name']}")

        node_names.append(node['name'])

        # 为缺少type的节点设置默认类型
        if 'type' not in node:
            node['type'] = 'unknown'
            print(f"警告：节点 {node['name']} 缺少'type'属性，已设置为'unknown'")

    # 验证并处理边（使用from和to替代source和target）
    if 'edges' in graph_data:
        valid_edges = []
        for i, edge in enumerate(graph_data['edges']):
            if not isinstance(edge, dict):
                print(f"警告：边 {i} 不是有效的字典，已跳过")
                continue

            # 检查边的from和to（替代source和target）
            if 'from' not in edge or 'to' not in edge:
                print(f"警告：边 {i} 缺少'from'或'to'属性，已跳过")
                continue

            # 检查连接的节点是否存在
            if edge['from'] not in node_names:
                print(f"警告：边 {i} 的源节点 '{edge['from']}' 不存在，已跳过")
                continue

            if edge['to'] not in node_names:
                print(f"警告：边 {i} 的目标节点 '{edge['to']}' 不存在，已跳过")
                continue

            valid_edges.append(edge)

        graph_data['edges'] = valid_edges
    else:
        graph_data['edges'] = []
        print("警告：图数据中缺少edges字段，已自动创建空边列表")

    return True, "图数据处理完成", graph_data


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
                is_valid, process_msg, processed_graph = process_and_validate_graph_data(graph_data)
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

                # 新增：可视化有向图
                print("📊 正在可视化有向图...")  # <-- 新增提示
                visualizer = ProductionLineVisualizer()  # <-- 实例化可视化工具
                visualizer.show_static(graph_data, title="生产线有向图可视化")  # <-- 显示图形

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

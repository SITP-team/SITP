#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
import json
import os
from typing import Dict, List, Optional
from dataclasses import dataclass


@dataclass
class BackgroundModule:
    """背景文档模块数据类"""
    name: str
    content: str
    version: str = "1.0.0"
    dependencies: List[str] = None

    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []


class DynamicPromptGenerator:
    """动态提示词生成器，完全替代prompt_config.py的功能"""

    def __init__(self,
                 background_doc_path: str = "background document.md",
                 sample_lib_path: str = "sample library.md"):
        self.background_modules = self._parse_background_document(background_doc_path)
        self.sample_library = self._parse_sample_library(sample_lib_path)

    def _parse_background_document(self, file_path: str) -> Dict[str, BackgroundModule]:
        """解析背景文档，提取所有模块"""
        modules = {}

        if not os.path.exists(file_path):
            print(f"警告: 背景文档文件 {file_path} 不存在")
            return modules

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # 使用更精确的正则表达式提取JSON对象
            json_pattern = r'\{[^{}]*"module"[^{}]*\}'
            matches = re.findall(json_pattern, content, re.DOTALL)

            for match in matches:
                try:
                    # 清理JSON字符串
                    clean_json = match.strip()
                    if not clean_json.startswith('{'):
                        continue

                    module_data = json.loads(clean_json)
                    module_name = module_data.get("module")

                    if module_name:
                        # 提取内容
                        module_content = module_data.get("content", "")
                        if isinstance(module_content, dict):
                            module_content = json.dumps(module_content, ensure_ascii=False, indent=2)

                        # 创建模块对象
                        module = BackgroundModule(
                            name=module_name,
                            content=module_content,
                            version=module_data.get("version", "1.0.0"),
                            dependencies=module_data.get("dependencies", [])
                        )

                        modules[module_name] = module
                except json.JSONDecodeError as e:
                    print(f"解析JSON失败: {e}, 内容: {match[:100]}...")
                    continue

        except Exception as e:
            print(f"解析背景文档失败: {e}")

        return modules

    def _parse_sample_library(self, file_path: str) -> List[Dict]:
        """解析示例库"""
        examples = []

        if not os.path.exists(file_path):
            print(f"警告: 示例库文件 {file_path} 不存在")
            return examples

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # 提取JSON示例
            json_pattern = r'```json\s*(\{.*?\})\s*```'
            matches = re.findall(json_pattern, content, re.DOTALL)

            for match in matches:
                try:
                    example = json.loads(match)
                    examples.append(example)
                except json.JSONDecodeError:
                    continue

        except Exception as e:
            print(f"解析示例库失败: {e}")

        return examples

    def _find_relevant_examples(self, user_input: str, max_examples: int = 2) -> List[Dict]:
        """查找与用户输入相关的示例"""
        relevant_examples = []

        # 简单关键词匹配
        keywords = re.findall(r'\b\w+\b', user_input.lower())

        for example in self.sample_library:
            # 检查示例名称和描述中是否包含关键词
            name = example.get("name", "").lower()
            description = example.get("description", "").lower()

            # 计算相关性分数
            score = 0
            for keyword in keywords:
                if len(keyword) < 3:  # 忽略短词
                    continue
                if keyword in name:
                    score += 3
                if keyword in description:
                    score += 2

            if score > 0:
                relevant_examples.append((score, example))

        # 按分数排序并返回前几个
        relevant_examples.sort(key=lambda x: x[0], reverse=True)
        return [ex[1] for ex in relevant_examples[:max_examples]]

    def _get_module_content(self, module_name: str) -> Optional[str]:
        """获取指定模块的内容"""
        module = self.background_modules.get(module_name)
        return module.content if module else None

    def _identify_relevant_modules(self, user_input: str) -> List[str]:
        """识别与用户输入相关的模块"""
        # 始终包含的核心模块
        relevant_modules = ["core_rules", "role_definition", "node_types", "time_formats"]

        # 根据关键词添加相关模块
        keyword_mapping = {
            "故障": "failure_models",
            "坏": "failure_models",
            "维修": "failure_models",
            "分布": "time_formats",
            "正态": "time_formats",
            "指数": "time_formats",
            "均匀": "time_formats",
            "连接": "connection_rules",
            "边": "connection_rules",
            "完整性": "data_integrity",
            "缺少": "data_integrity",
            "缺失": "data_integrity"
        }

        # 检查用户输入中的关键词
        for keyword, module in keyword_mapping.items():
            if keyword in user_input and module not in relevant_modules:
                relevant_modules.append(module)

        return relevant_modules

    def generate_dynamic_prompt(self, user_input: str) -> str:
        """生成完整的动态提示词"""
        # 识别相关模块
        relevant_modules = self._identify_relevant_modules(user_input)

        # 查找相关示例
        relevant_examples = self._find_relevant_examples(user_input)

        # 构建提示词
        prompt_parts = []

        # 1. 角色定义和核心任务
        role_definition = self._get_module_content("role_definition") or """
你是一个格式转换专家，擅长将自然语言转换为规定格式的有向图。根据输入的自然语言描述和后续的补充回答，
你需要提取出图中的节点（nodes）和边（edges）信息，并按照指定的JSON格式输出，以便于后续代码生成。
"""
        prompt_parts.append(role_definition)

        # 2. 添加相关模块的内容
        for module_name in relevant_modules:
            content = self._get_module_content(module_name)
            if content:
                prompt_parts.append(f"\n# {module_name.upper()} 模块规则:")
                prompt_parts.append(content)

        # 3. 添加输出格式要求
        prompt_parts.append("""
# 输出要求:
- 输出必须为严格的JSON格式，不包含任何额外说明或XML标签
- 所有字段的时间格式在未选择分布的情况下为"天:小时:分钟:秒"
- 在已选择分布的情况下时间的单位均为秒
- 节点类型必须是"源"、"工位"、"缓冲区"、"物料终结"、"传送器"中的一种
- 在输出有向图之前一定要逐步思考得出结果，并且给出你的思考过程，使用中文

# 关键规则:
1. 如果输入中缺少仿真所必需的 data 数据（例如源节点缺少 interval_time，工位缺少 processing_time），
   请不要自行填写数据，而是询问用户缺少的数据。
2. 若缺少节点也需询问用户是否需要添加（如缺失物料终结）。
3. 在数据和节点完整前只能询问用户，禁止输出有向图。
4. 禁止过度提问（如长度单位等，这些在有向图中无用的数据），只需保证数据能够生成有向图即可。
5. 将用户的所有回答相结合生成有向图。
6. 若用户仍然未给出一些不影响有向图生成的数据，不要默认其值为0，尤其是传送器的宽度和速度。
""")

        # 4. 添加相关示例
        if relevant_examples:
            prompt_parts.append("\n# 相关示例参考:")
            for i, example in enumerate(relevant_examples, 1):
                prompt_parts.append(f"\n示例 {i}: {example.get('name', '未命名示例')}")
                prompt_parts.append(f"描述: {example.get('description', '无描述')}")

                graph_data = example.get('graph', {})
                if graph_data:
                    prompt_parts.append("有向图结构:")
                    prompt_parts.append(json.dumps(graph_data, ensure_ascii=False, indent=2))

        # 5. 添加完整示例（来自prompt_config.py）
        prompt_parts.append("""
# 完整输入输出示例:

示例输入: 为我生成一个有向图，节点包括源（源），缓冲区，加工工位（工位），传送器（传送器），测试工位（工位），合格库存（物料终结）和废品库存（物料终结），
源，加工工位，缓冲区，传送器，测试工位，依次为串联结构，测试工位分别连接合格库存与废品库存，源的时间间隔为10分钟，起始时间为0，结束时间为1天，
缓冲区容量为8，传送器长度为2米，宽度为0.5米，速度为1m/s，容量为2，
加工工位处理时间为正态分布平均值200，标准差30，故障间隔为2000，持续时间为200，缓冲区容量为8，测试工位的处理时间为1分钟，故障间隔时间为负指数分布，均值为2000，
持续时间为负指数分布，均值为200，测试结果为合格率是70%，合格的产品输入合格库存，不合格的产品输入废品库存。

示例输出:
{
    "nodes":[
        {
            "name":"源",
            "type":"源",
            "data":{
                "time": {
                    "interval_time":"0:0:10:0",
                    "start_time":"0:0:0:0",
                    "stop_time":"1:0:0:0"
                }
            }
        },
        {
            "name":"缓冲区",
            "type":"缓冲区",
            "data":{
                "capacity":8
            }
        },
        {
            "name":"加工工位",
            "type":"工位",
            "data":{
                "time": {
                    "processing_time": {
                        "distribution_pattern": "normal",
                        "parameters": {
                            "mean": 200,
                            "sigma": 900
                        }
                    }
                },
                "failure": {
                    "failure_name":"failure1",
                    "interval_time":"0:0:33:20",
                    "duration_time":"0:0:3:20"
                }
            }
        },
        {
            "name":"传送器",
            "type":"传送器",
            "data":{
                "capacity": "2",
                "length": "2",
                "width": "0.5",
                "speed": "1"
            }
        },
        {
            "name":"测试工位",
            "type":"工位",
            "data":{
                "time": {
                    "processing_time": "0:0:1:0"
                },
                "failure": {
                    "failure_name":"failure2",
                    "interval_time": {
                        "distribution_pattern": "negexp",
                        "parameters": {
                            "mean": 2000
                        }
                    },
                    "duration_time": {
                        "distribution_pattern": "negexp",
                        "parameters": {
                            "mean": 200
                        }
                    }
                },
                "production_status":{
                    "qualified":0.7,
                    "unqualified":0.3
                },
                "production_destination":{
                    "qualified":"合格库存",
                    "unqualified":"废品库存"
                }
            }
        },
        {
            "name":"合格库存",
            "type":"物料终结",
            "data": {}
        },
        {
            "name":"废品库存",
            "type":"物料终结",
            "data": {}
        }
    ],
    "edges":[
        {"from":"源", "to":"缓冲区"},
        {"from":"缓冲区", "to":"加工工位"},
        {"from":"加工工位", "to":"传送器"},
        {"from":"传送器", "to":"测试工位"},
        {"from":"测试工位", "to":"合格库存"},
        {"from":"测试工位", "to":"废品库存"}
    ]
}
""")

        return "\n".join(prompt_parts)


# 使用示例
if __name__ == "__main__":
    # 初始化动态提示词生成器
    prompt_generator = DynamicPromptGenerator()

    # 测试不同的用户输入
    test_inputs = [
        "我想建一个简单的生产线，有一个源节点每5分钟生成一个产品，一个加工工位处理时间3分钟，最后送到成品仓库",
        "我需要一个有故障模型的生产线，源节点每10分钟生成一个产品，加工工位处理时间正态分布，平均值200秒，标准差30秒，故障间隔2000秒",
        "请帮我设计一个带传送带的生产线，源节点每15分钟生成产品，装配工位处理8分钟，传送带长度10米，速度0.5m/s，容量5个"
    ]

    for i, user_input in enumerate(test_inputs, 1):
        print(f"\n{'=' * 50}")
        print(f"测试 {i}: {user_input}")
        print(f"{'=' * 50}")

        dynamic_prompt = prompt_generator.generate_dynamic_prompt(user_input)
        print(f"生成的提示词长度: {len(dynamic_prompt)} 字符")
        print(f"提示词预览:\n{dynamic_prompt[:500]}...")
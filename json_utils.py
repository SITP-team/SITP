#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import re


def extract_json_from_response(response_text):
    """从API响应中提取纯JSON内容"""
    # 尝试直接解析整个响应
    try:
        return json.loads(response_text)
    except json.JSONDecodeError:
        pass

    # 尝试提取被```json ... ```包裹的内容
    json_match = re.search(r"```json\s*(.*?)\s*```", response_text, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group(1))
        except json.JSONDecodeError:
            pass

    # 尝试提取被```包裹的内容
    code_match = re.search(r"```(.*?)```", response_text, re.DOTALL)
    if code_match:
        try:
            return json.loads(code_match.group(1))
        except json.JSONDecodeError:
            pass

    # 最后尝试解析整个响应
    try:
        return json.loads(response_text)
    except json.JSONDecodeError as e:
        print(f"JSON解析失败: {str(e)}")
        print("原始响应内容:")
        print(response_text)
        return None

#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import json
from path_config import API_URL, API_KEY

# 请求头
headers = {"Content-Type": "application/json", "Authorization": f"Bearer {API_KEY}"}


def make_api_request(messages):
    """发送API请求并返回响应"""
    payload = {
        "model": "deepseek-chat",
        "messages": messages,
        "temperature": 0.3,
        "max_tokens": 4096,
    }
    response = requests.post(API_URL, headers=headers, json=payload)
    response.raise_for_status()
    return response.json()

#!/usr/bin/env python3
# -*- coding: utf-8 -*-


def format_time_value(time_data):
    """
    格式化时间值，支持传统时间格式和分布对象
    返回适合SimTalk的字符串表示
    """
    if isinstance(time_data, dict):
        # 分布类型
        dist_type = time_data["distribution_pattern"]
        params = time_data["parameters"]
        param_values = []

        # 获取参数值
        for key in params:
            value = params[key]
            # 处理概率值（保持浮点格式）
            if isinstance(value, float) and "probability" in key:
                param_values.append(str(value))
            # 整数值转换为整数格式
            elif isinstance(value, int) or float(value).is_integer():
                param_values.append(str(int(value)))
            else:
                param_values.append(str(value))

        param_str = ", ".join(param_values)
        return f'"{dist_type}", 1, {param_str}'
    else:
        # 传统时间格式
        time_parts = time_data.split(":")
        if len(time_parts) == 4:  # 天:小时:分钟:秒
            return f'"{time_parts[0]}:{time_parts[1]}:{time_parts[2]}:{time_parts[3]}"'
        elif len(time_parts) == 3:  # 小时:分钟:秒
            return f'"{time_parts[0]}:{time_parts[1]}:{time_parts[2]}:00"'
        else:
            # 默认格式化为分钟
            return f'"{time_data}:00"'

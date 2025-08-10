#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from time_utils import format_time_value


def write_data(json_data):
    """
    数据写入部分：数据表创建和数据写入逻辑
    """
    nodes = json_data.get("nodes", [])
    data_writing = []

    # 创建数据表实体
    data_writing.append('.信息流.数据表.createObject(.模型.模型, 350, 200, "数据表")')
    data_writing.append("")

    row = 1  # 数据表起始行
    for node in nodes:
        if node["type"] == "物料终结":
            node_name = node["name"]
            # 写入物料终结名称（每个物料终结前添加）
            data_writing.append(f'.模型.模型.数据表[1, {row}] := "{node_name}"')
            row += 1
            # 写入四个属性数据
            data_writing.append(f'.模型.模型.数据表[1, {row}] := "平均寿命"')
            data_writing.append(
                f".模型.模型.数据表[2, {row}] := To_str(.模型.模型.{node_name}.statavglifespan)"
            )
            row += 1
            data_writing.append(f'.模型.模型.数据表[1, {row}] := "平均退出间隔"')
            data_writing.append(
                f".模型.模型.数据表[2, {row}] := To_str(.模型.模型.{node_name}.statavgexitinterval)"
            )
            row += 1
            data_writing.append(f'.模型.模型.数据表[1, {row}] := "总吞吐量"')
            data_writing.append(
                f".模型.模型.数据表[2, {row}] := To_str(.模型.模型.{node_name}.statdeleted)"
            )
            row += 1
            data_writing.append(f'.模型.模型.数据表[1, {row}] := "每天吞吐量"')
            data_writing.append(
                f".模型.模型.数据表[2, {row}] := To_str(.模型.模型.{node_name}.statthroughputperday)"
            )
            row += 2  # 不同物料终结间空一行

    # 数据表写入Excel
    data_writing.append(r'.模型.模型.数据表.writefile("data_output.txt")')

    return "\n".join(data_writing)

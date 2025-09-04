#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from time_utils import format_time_value


def json_to_simtalk(json_data):
    """
    将JSON格式的有向图转换为两部分SimTalk代码：模型建立 + 数据写入
    """
    nodes = json_data.get("nodes", [])
    edges = json_data.get("edges", [])

    # 第一部分：模型建立（实体创建、属性设置、连接、事件控制）
    model_setup = []

    # 计算节点坐标（根据边的连接顺序）
    # 1. 构建节点连接关系
    node_connections = {node["name"]: {"outgoing": [], "incoming": 0} for node in nodes}
    for edge in edges:
        node_connections[edge["from"]]["outgoing"].append(edge["to"])
        node_connections[edge["to"]]["incoming"] += 1

    # 2. 确定节点顺序（拓扑排序）
    node_order = []
    # 找到所有入度为0的节点作为起点
    start_nodes = [name for name, conn in node_connections.items() if conn["incoming"] == 0]
    # 使用队列处理节点顺序
    from collections import deque
    queue = deque(start_nodes)

    while queue:
        current = queue.popleft()
        node_order.append(current)
        # 处理下游节点
        for neighbor in node_connections[current]["outgoing"]:
            node_connections[neighbor]["incoming"] -= 1
            if node_connections[neighbor]["incoming"] == 0:
                queue.append(neighbor)

    # 3. 计算坐标
    node_positions = {}
    base_x = 50  # 基础X坐标
    base_y = 200  # 基础Y坐标
    x_step = 100  # X方向步长
    y_branch_step = 50  # 分支Y方向步长

    for idx, node_name in enumerate(node_order):
        # 计算X坐标（按顺序递增）
        x_pos = base_x + idx * x_step

        # 计算Y坐标
        # 找到父节点
        parent_nodes = [edge["from"] for edge in edges if edge["to"] == node_name]
        if not parent_nodes:  # 起始节点
            y_pos = base_y
        else:
            parent_name = parent_nodes[0]
            parent_y = node_positions[parent_name]["y"]
            # 检查父节点的子节点数量
            siblings = node_connections[parent_name]["outgoing"]
            if len(siblings) <= 1:
                y_pos = parent_y
            else:
                # 有多个分支，计算偏移
                sibling_idx = siblings.index(node_name)
                # 居中偏移计算（确保分支对称）
                mid = (len(siblings) - 1) / 2
                y_pos = parent_y + (sibling_idx - mid) * y_branch_step

        node_positions[node_name] = {"x": x_pos, "y": y_pos}

    # 提取源节点的时间属性（用于故障设置）
    source_start_time = "0:0:0:0"
    source_stop_time = "8:0:0:0"
    for node in nodes:
        if node["type"] == "源" and "data" in node and "time" in node["data"]:
            time_data = node["data"]["time"]
            if "start_time" in time_data:
                source_start_time = time_data["start_time"]
            if "stop_time" in time_data:
                source_stop_time = time_data["stop_time"]
            break

    # 1. 创建实体（按计算的坐标）
    for node in nodes:
        node_type = node["type"]
        node_name = node["name"]
        pos = node_positions[node_name]
        x_pos = pos["x"]
        y_pos = pos["y"]

        if node_type == "源":
            model_setup.append(
                f'.物料流.源.createObject(.模型.模型, {x_pos}, {y_pos}, "{node_name}")'
            )
        elif node_type == "工位":
            model_setup.append(
                f'.物料流.工位.createObject(.模型.模型, {x_pos}, {y_pos}, "{node_name}")'
            )
        elif node_type == "缓冲区":
            model_setup.append(
                f'.物料流.缓冲区.createObject(.模型.模型, {x_pos}, {y_pos}, "{node_name}")'
            )
        elif node_type == "传送器":
            model_setup.append(
                f'.物料流.传送器.createObject(.模型.模型, {x_pos}, {y_pos}, "{node_name}")'
            )
        elif node_type == "物料终结":
            model_setup.append(
                f'.物料流.物料终结.createObject(.模型.模型, {x_pos}, {y_pos}, "{node_name}")'
            )

    model_setup.append("")  # 空行分隔

    # 2. 设置实体属性（保持原有逻辑）
    for node in nodes:
        node_name = node["name"]
        node_type = node["type"]
        data = node.get("data", {})

        if node_type == "源" and "time" in data:
            time_data = data["time"]
            for time_type in ["interval_time", "start_time", "stop_time"]:
                if time_type in time_data:
                    time_value = time_data[time_type]
                    simtalk_property = time_type.replace("_time", "")

                    if (
                            isinstance(time_value, dict)
                            and "distribution_pattern" in time_value
                    ):
                        formatted_value = format_time_value(time_value)
                        model_setup.append(
                            f".模型.模型.{node_name}.{simtalk_property}.setParam({formatted_value})"
                        )
                    else:
                        model_setup.append(
                            f".模型.模型.{node_name}.{simtalk_property} := {time_value}"
                        )

        elif node_type == "工位":
            if "time" in data and "processing_time" in data["time"]:
                proc_time = data["time"]["processing_time"]
                if isinstance(proc_time, dict) and "distribution_pattern" in proc_time:
                    formatted_value = format_time_value(proc_time)
                    model_setup.append(
                        f".模型.模型.{node_name}.ProcTime.setParam({formatted_value})"
                    )
                else:
                    model_setup.append(
                        f".模型.模型.{node_name}.ProcTime := {proc_time}"
                    )

            if "failure" in data:
                failure_data = data["failure"]
                failure_name = failure_data.get("failure_name", "default_failure")
                failure_start = failure_data.get("start_time", source_start_time)
                failure_stop = failure_data.get("stop_time", source_stop_time)

                interval_time = failure_data.get("interval_time")
                if (
                        isinstance(interval_time, dict)
                        and "distribution_pattern" in interval_time
                ):
                    formatted = format_time_value(interval_time)
                    cleaned = formatted.replace('"', "")
                    interval_str = f'"{cleaned}"'
                else:
                    interval_str = str(interval_time)

                duration_time = failure_data.get("duration_time", "0:0:0:0")
                if (
                        isinstance(duration_time, dict)
                        and "distribution_pattern" in duration_time
                ):
                    formatted = format_time_value(duration_time)
                    cleaned = formatted.replace('"', "")
                    duration_str = f'"{cleaned}"'
                else:
                    duration_str = str(duration_time)

                model_setup.append(
                    f'.模型.模型.{node_name}.Failures.createFailure("{failure_name}", {interval_str}, {duration_str}, "SimulationTime", {failure_start}, {failure_stop}, false)'
                )
                model_setup.append(
                    f".模型.模型.{node_name}.Failures.{failure_name}.Active := true"
                )

            if "production_status" in data:
                qualified = int(data["production_status"]["qualified"] * 100)
                unqualified = int(data["production_status"]["unqualified"] * 100)
                model_setup.append(
                    f".模型.模型.{node_name}.exitstrategyblocking := true"
                )
                model_setup.append(
                    f'.模型.模型.{node_name}.exitstrategy := "percentage"'
                )
                model_setup.append(
                    f".模型.模型.{node_name}.exitstrategypercentagevalues := [{qualified}, {unqualified}]"
                )

        elif node_type == "缓冲区" and "capacity" in data:
            model_setup.append(f'.模型.模型.{node_name}.capacity := {data["capacity"]}')

        elif node_type == "传送器":
            if "capacity" in data:
                model_setup.append(
                    f'.模型.模型.{node_name}.capacity := {data["capacity"]}'
                )
            if "length" in data:
                model_setup.append(
                    f'.模型.模型.{node_name}.length := {data["length"]}m'
                )
            if "width" in data:
                model_setup.append(f'.模型.模型.{node_name}.width := {data["width"]}m')
            if "speed" in data:
                model_setup.append(f'.模型.模型.{node_name}.speed := {data["speed"]}')

        elif node_type == "物料终结":
            if "time" in data and "processing_time" in data["time"]:
                proc_time = data["time"]["processing_time"]
                if isinstance(proc_time, dict) and "distribution_pattern" in proc_time:
                    formatted_value = format_time_value(proc_time)
                    model_setup.append(
                        f".模型.模型.{node_name}.ProcTime.setParam({formatted_value})"
                    )
                else:
                    model_setup.append(
                        f".模型.模型.{node_name}.ProcTime := {proc_time}"
                    )

            if "failure" in data:
                failure_data = data["failure"]
                failure_name = failure_data.get("failure_name", "default_failure")
                failure_start = failure_data.get("start_time", source_start_time)
                failure_stop = failure_data.get("stop_time", source_stop_time)
                interval_time = failure_data.get("interval_time")
                if (
                        isinstance(interval_time, dict)
                        and "distribution_pattern" in interval_time
                ):
                    formatted = format_time_value(interval_time)
                    cleaned = formatted.replace('"', "")
                    interval_str = f'"{cleaned}"'
                else:
                    interval_str = str(interval_time)
                duration_time = failure_data.get("duration_time", "0:0:0:0")
                if (
                        isinstance(duration_time, dict)
                        and "distribution_pattern" in duration_time
                ):
                    formatted = format_time_value(duration_time)
                    cleaned = formatted.replace('"', "")
                    duration_str = f'"{cleaned}"'
                else:
                    duration_str = str(duration_time)
                model_setup.append(
                    f'.模型.模型.{node_name}.Failures.createFailure("{failure_name}", {interval_str}, {duration_str}, "SimulationTime", {failure_start}, {failure_stop}, false)'
                )
                model_setup.append(
                    f".模型.模型.{node_name}.Failures.{failure_name}.Active := true"
                )

    model_setup.append("")  # 空行分隔

    # 3. 实体连接（使用完整路径）
    for edge in edges:
        from_node = edge["from"]
        to_node = edge["to"]
        model_setup.append(
            f".物料流.连接器.connect(.模型.模型.{from_node}, .模型.模型.{to_node});"
        )

    model_setup.append("")  # 空行分隔

    # 4. 事件控制器设置
    model_setup.append(f".模型.模型.事件控制器.end := {source_stop_time}")
    model_setup.append(".模型.模型.事件控制器.startwithoutanimation")

    # 第二部分：数据写入（独立执行）
    data_writing = []
    data_writing.append('.信息流.数据表.createObject(.模型.模型, 100, 250, "数据表")')
    data_writing.append("")

    row = 1  # 数据表起始行
    for node in nodes:
        if node["type"] == "物料终结":
            node_name = node["name"]
            data_writing.append(f'.模型.模型.数据表[1, {row}] := "{node_name}"')
            row += 1
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

    data_writing.append(r'.模型.模型.数据表.writefile("data_output.txt")')

    return "\n".join(model_setup), "\n".join(data_writing)

def capacity_json_to_simtalk(json_data):

    model_setup=[]
    nodes = json_data.get("nodes", [])

    for node in nodes:
        node_name = node["name"]
        node_type = node["type"]
        data = node.get("data", {})
        model_setup.append(f".模型.模型.{node_name}.capacity:={data['capacity']}")

        data_writing = [
            '.信息流.数据表.createObject(.模型.模型, 100, 250, "数据表")',
            '.模型.模型.数据表[1, 1] := "总吞吐量"',
            '.模型.模型.数据表[2, 1] := To_str(.模型.模型.OP130.statdeleted)',
            r'.模型.模型.数据表.writefile("data_output.txt")',
            'sleep(3)'
        ]
    return "\n".join(model_setup), "\n".join(data_writing)
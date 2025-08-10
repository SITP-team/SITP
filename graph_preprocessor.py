#!/usr/bin/env python3
# -*- coding: utf-8 -*-


def convert_zero_capacity_conveyors_to_edges(graph_data):
    """
    将容量为0的传送器节点转换为直接连接器（边）
    """
    nodes = graph_data.get("nodes", [])
    edges = graph_data.get("edges", [])

    # 1. 找出所有容量为0的传送器节点
    zero_capacity_conveyors = []
    for node in nodes:
        if node["type"] == "传送器":
            capacity = node.get("data", {}).get("capacity")
            # 处理不同类型的容量值（字符串或数字）
            if capacity is not None:
                try:
                    # 尝试转换为整数
                    capacity_int = int(capacity)
                    if capacity_int == 0:
                        zero_capacity_conveyors.append(node["name"])
                except (ValueError, TypeError):
                    # 如果转换失败，保持原样
                    pass

    # 2. 如果没有容量为0的传送器，直接返回原数据
    if not zero_capacity_conveyors:
        return graph_data

    # 3. 处理每个容量为0的传送器
    for conveyer_name in zero_capacity_conveyors:
        # 找到所有进入该传送器的边
        incoming_edges = [edge for edge in edges if edge["to"] == conveyer_name]
        # 找到所有从该传送器出去的边
        outgoing_edges = [edge for edge in edges if edge["from"] == conveyer_name]

        # 4. 为每对入边和出边创建直接连接
        for in_edge in incoming_edges:
            for out_edge in outgoing_edges:
                # 创建新的直接连接（跳过传送器）
                new_edge = {"from": in_edge["from"], "to": out_edge["to"]}

                # 5. 避免重复添加相同的边
                if new_edge not in edges:
                    edges.append(new_edge)

        # 6. 移除与传送器相关的所有边
        edges = [
            edge
            for edge in edges
            if edge["from"] != conveyer_name and edge["to"] != conveyer_name
        ]

    # 7. 移除传送器节点本身
    nodes = [node for node in nodes if node["name"] not in zero_capacity_conveyors]

    # 8. 返回更新后的图数据
    return {"nodes": nodes, "edges": edges}

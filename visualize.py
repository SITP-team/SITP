import networkx as nx
import matplotlib.pyplot as plt
import os


class ProductionLineVisualizer:
    """生产线有向图可视化工具，支持静态展示"""

    def __init__(self):
        # 初始化节点样式配置
        self.node_style = {
            '源': {'color': '#4CAF50', 'shape': 'circle'},  # 绿色
            '缓冲区': {'color': '#FFEB3B', 'shape': 'box'},  # 黄色
            '工位': {'color': '#2196F3', 'shape': 'diamond'},  # 蓝色
            '传送器': {'color': '#9C27B0', 'shape': 'triangle'},  # 紫色
            '物料终结': {'color': '#F44336', 'shape': 'ellipse'},  # 红色
            'unknown': {'color': '#9E9E9E', 'shape': 'circle'}  # 灰色
        }

        # 初始化Matplotlib字体配置（确保中文显示）
        plt.rcParams.update({
            "font.family": ["SimHei", "WenQuanYi Micro Hei", "Heiti TC", "Arial Unicode MS"],
            "axes.unicode_minus": False,
            "text.usetex": False
        })

    def _get_node_style(self, node_type):
        """获取节点类型对应的样式"""
        return self.node_style.get(node_type, self.node_style['unknown'])

    def show_static(self, graph_data, title="生产线有向图模型"):
        """
        显示静态有向图（Matplotlib）
        :param graph_data: 包含nodes和edges的图数据字典
        :param title: 图表标题
        """
        # 创建有向图
        G = nx.DiGraph()

        # 添加节点
        valid_nodes = []
        for node in graph_data.get('nodes', []):
            try:
                node_name = node['name']
                node_type = node.get('type', 'unknown')

                G.add_node(
                    node_name,
                    type=node_type,
                    failure=node.get('data', {}).get('failure') is not None
                )
                valid_nodes.append(node_name)
            except Exception as e:
                print(f"处理节点时出错: {str(e)} - 节点数据: {node}")

        # 添加边
        for edge in graph_data.get('edges', []):
            try:
                source = edge['from']
                target = edge['to']

                if source in valid_nodes and target in valid_nodes:
                    G.add_edge(source, target)
                else:
                    print(f"跳过无效边: {source} -> {target}")
            except Exception as e:
                print(f"处理边时出错: {str(e)} - 边数据: {edge}")

        if not valid_nodes:
            print("没有有效的节点数据，无法绘制图形")
            return

        # 计算节点层级，用于横平竖直布局
        def _calculate_node_levels(G):
            """计算节点层级，用于有序布局"""
            # 找到所有源节点（入度为0的节点）
            sources = [node for node, in_degree in G.in_degree() if in_degree == 0]
            if not sources:
                sources = [next(iter(G.nodes))]  # 若无源节点，默认第一个节点为起点

            # 初始化层级字典
            levels = {node: 0 for node in G.nodes}
            visited = set(sources)
            queue = sources.copy()

            # BFS计算层级（从左到右的层级）
            while queue:
                current = queue.pop(0)
                for neighbor in G.successors(current):
                    if neighbor not in visited:
                        levels[neighbor] = levels[current] + 1
                        visited.add(neighbor)
                        queue.append(neighbor)
                    else:
                        # 确保层级递增
                        if levels[neighbor] <= levels[current]:
                            levels[neighbor] = levels[current] + 1
            return levels

        # 计算层级并设置为节点属性
        levels = _calculate_node_levels(G)
        for node, level in levels.items():
            G.nodes[node]['level'] = level  # 给每个节点添加level属性

        # 使用层级布局（更横平竖直）
        pos = nx.multipartite_layout(
            G,
            subset_key='level',  # 使用节点的level属性作为分组依据
            align='horizontal',  # 水平对齐
            scale=2  # 扩大布局间距
        )

        # 准备节点样式
        node_colors = [self._get_node_style(G.nodes[node]['type'])['color'] for node in G.nodes]
        node_sizes = [900 if G.nodes[node]['failure'] else 700 for node in G.nodes]

        # 绘制节点
        nx.draw_networkx_nodes(G, pos, node_size=node_sizes, node_color=node_colors,
                               edgecolors='black', linewidths=1)

        # 绘制边（使用直线，更横平竖直）
        nx.draw_networkx_edges(G, pos, arrowstyle='->', arrowsize=20,
                               edge_color='gray', width=1.5, connectionstyle='arc3,rad=0')

        # 绘制节点标签
        nx.draw_networkx_labels(
            G, pos, font_size=10,
            font_family=['SimHei', 'WenQuanYi Micro Hei', 'Heiti TC']
        )

        # 添加图例
        legend_elements = []
        for node_type, style in self.node_style.items():
            legend_elements.append(
                plt.Line2D([0], [0], marker='o', color='w', label=node_type,
                           markerfacecolor=style['color'], markersize=10)
            )

        plt.legend(
            handles=legend_elements,
            loc='best',
            fontsize=8,
            prop={'family': ['SimHei', 'WenQuanYi Micro Hei', 'Heiti TC']}
        )

        # 显示图形
        plt.title(title)
        plt.axis('off')
        plt.tight_layout()
        plt.show()


# 示例用法
if __name__ == "__main__":
    # 示例图数据
    sample_graph_data = {
        "nodes": [
            {
                "name": "源",
                "type": "源",
                "data": {
                    "time": {
                        "interval_time": "0:0:10:0",
                        "start_time": "0:0:0:0",
                        "stop_time": "1:0:0:0"
                    }
                }
            },
            {
                "name": "缓冲区",
                "type": "缓冲区",
                "data": {
                    "capacity": 8
                }
            },
            {
                "name": "加工工位",
                "type": "工位",
                "data": {
                    "time": {
                        "processing_time": {
                            "distribution_pattern": "normal",
                            "parameters": {
                                "mean": 200,
                                "sigma": 30
                            }
                        }
                    },
                    "failure": {
                        "failure_name": "failure1",
                        "interval_time": "2000",
                        "duration_time": "200"
                    }
                }
            },
            {
                "name": "传送器",
                "type": "传送器",
                "data": {
                    "capacity": "2",
                    "length": "2",
                    "width": "0.5",
                    "speed": "1"
                }
            },
            {
                "name": "测试工位",
                "type": "工位",
                "data": {
                    "time": {
                        "processing_time": "0:0:1:0"
                    },
                    "failure": {
                        "failure_name": "failure2",
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
                    "production_status": {
                        "qualified": 0.7,
                        "unqualified": 0.3
                    },
                    "production_destination": {
                        "qualified": "合格库存",
                        "unqualified": "废品库存"
                    }
                }
            },
            {
                "name": "合格库存",
                "type": "物料终结",
                "data": {}
            },
            {
                "name": "废品库存",
                "type": "物料终结",
                "data": {}
            }
        ],
        "edges": [
            {"from": "源", "to": "缓冲区"},
            {"from": "缓冲区", "to": "加工工位"},
            {"from": "加工工位", "to": "传送器"},
            {"from": "传送器", "to": "测试工位"},
            {"from": "测试工位", "to": "合格库存"},
            {"from": "测试工位", "to": "废品库存"}
        ]
    }

    # 创建可视化器实例
    visualizer = ProductionLineVisualizer()

    # 显示静态图（Matplotlib）
    print("显示静态图...")
    visualizer.show_static(sample_graph_data)
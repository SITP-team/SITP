import networkx as nx
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import uuid
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import tkinter as tk
from tkinter import ttk


class ProductionLineVisualizer:
    """生产线有向图可视化工具，支持点击节点展示属性"""

    @staticmethod
    def initialize_fonts(print_fonts=False):
        """初始化Matplotlib字体配置（确保中文显示）"""
        plt.rcParams.update({
            "font.family": ["SimHei", "WenQuanYi Micro Hei", "Heiti TC", "Arial Unicode MS"],
            "axes.unicode_minus": False,
            "text.usetex": False
        })

        if print_fonts:
            print("可用字体列表：")
            fonts = fm.findSystemFonts(fontpaths=None, fontext='ttf')
            for font in fonts:
                try:
                    font_name = fm.FontProperties(fname=font).get_name()
                    print(font_name)
                except:
                    pass

    @staticmethod
    def process_and_validate_graph_data(graph_data):
        """处理并验证图数据结构"""
        if not isinstance(graph_data, dict):
            return False, "图数据不是有效的字典", None

        if 'nodes' not in graph_data:
            graph_data['nodes'] = []
            print("警告：图数据中缺少nodes字段，已自动创建空节点列表")

        node_names = []
        for i, node in enumerate(graph_data['nodes']):
            if not isinstance(node, dict):
                print(f"警告：节点 {i} 不是有效的字典，已转换为字典")
                graph_data['nodes'][i] = {"name": f"节点{i}", "type": "unknown"}
                node = graph_data['nodes'][i]

            if 'name' not in node:
                generated_name = f"自动节点_{uuid.uuid4().hex[:8]}"
                node['name'] = generated_name
                print(f"警告：节点 {i} 缺少'name'属性，已自动生成: {generated_name}")

            if node['name'] in node_names:
                original_name = node['name']
                node['name'] = f"{original_name}_{uuid.uuid4().hex[:4]}"
                print(f"警告：节点名称 '{original_name}' 重复，已重命名为: {node['name']}")

            node_names.append(node['name'])

            if 'type' not in node:
                node['type'] = 'unknown'
                print(f"警告：节点 {node['name']} 缺少'type'属性，已设置为'unknown'")

        if 'edges' in graph_data:
            valid_edges = []
            for i, edge in enumerate(graph_data['edges']):
                if not isinstance(edge, dict):
                    print(f"警告：边 {i} 不是有效的字典，已跳过")
                    continue

                if 'from' not in edge or 'to' not in edge:
                    print(f"警告：边 {i} 缺少'from'或'to'属性，已跳过")
                    continue

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

    def __init__(self):
        self.node_style = {
            '源': {'color': '#4CAF50', 'shape': 'circle'},
            '缓冲区': {'color': '#FFEB3B', 'shape': 'box'},
            '工位': {'color': '#2196F3', 'shape': 'diamond'},
            '传送器': {'color': '#9C27B0', 'shape': 'triangle'},
            '物料终结': {'color': '#F44336', 'shape': 'ellipse'},
            'unknown': {'color': '#9E9E9E', 'shape': 'circle'}
        }

        # 配置属性文本样式参数
        self.attr_style = {
            'max_line_length': 18,
            'base_offset': -0.7,
            'line_spacing': 0.35,
            'font_size': 9,
            'even_offset': 0,
            'odd_offset': 0.3,
            'box_pad': 0.15
        }

        # 存储节点数据用于交互
        self.node_info = {}
        # 存储当前显示的属性窗口
        self.attr_window = None

    def _get_node_style(self, node_type):
        return self.node_style.get(node_type, self.node_style['unknown'])

    def _wrap_text(self, text):
        """智能文本换行"""
        max_len = self.attr_style['max_line_length']
        wrapped = []
        current_line = []
        current_length = 0

        words = text.split(' ')

        for word in words:
            if len(word) > max_len:
                if current_line:
                    wrapped.append(' '.join(current_line))
                    current_line = []
                    current_length = 0
                for i in range(0, len(word), max_len):
                    wrapped.append(word[i:i + max_len])
                continue

            word_len = len(word) + (1 if current_line else 0)

            if current_length + word_len <= max_len:
                current_line.append(word)
                current_length += word_len
            else:
                wrapped.append(' '.join(current_line))
                current_line = [word]
                current_length = len(word)

        if current_line:
            wrapped.append(' '.join(current_line))

        return wrapped

    def _on_node_click(self, event):
        """节点点击事件处理函数"""
        if event.inaxes is None:
            return

        # 关闭已有的属性窗口
        if self.attr_window and isinstance(self.attr_window, tk.Toplevel):
            self.attr_window.destroy()

        # 查找被点击的节点
        click_x, click_y = event.xdata, event.ydata
        closest_node = None
        min_distance = float('inf')
        node_threshold = 0.5  # 点击检测阈值

        for node, (x, y) in self.pos.items():
            distance = ((x - click_x) ** 2 + (y - click_y) ** 2) ** 0.5
            if distance < min_distance and distance < node_threshold:
                min_distance = distance
                closest_node = node

        # 如果找到节点，显示属性窗口
        if closest_node:
            self._show_node_attributes(closest_node)

    def _show_node_attributes(self, node_name):
        """显示节点属性的弹出窗口"""
        # 获取节点属性数据
        node_data = self.node_info.get(node_name, {})
        if not node_data:
            return

        # 创建顶级窗口
        self.attr_window = tk.Toplevel()
        self.attr_window.title(f"节点属性: {node_name}")
        self.attr_window.geometry("400x300")
        self.attr_window.resizable(True, True)

        # 创建滚动条
        scrollbar = ttk.Scrollbar(self.attr_window)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # 创建文本框显示属性
        text_widget = tk.Text(
            self.attr_window,
            wrap=tk.WORD,
            yscrollcommand=scrollbar.set,
            padx=10,
            pady=10,
            font=("SimHei", 10)
        )
        text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=text_widget.yview)

        # 格式化属性文本
        attr_text = []
        for key, value in node_data.items():
            if isinstance(value, dict):
                attr_text.append(f"【{key}】")
                for sub_key, sub_val in value.items():
                    if isinstance(sub_val, dict):
                        sub_str = ", ".join([f"{k}={v}" for k, v in sub_val.items()])
                        attr_text.append(f"  - {sub_key}: {sub_str}")
                    else:
                        attr_text.append(f"  - {sub_key}: {sub_val}")
                attr_text.append("")  # 空行分隔不同属性
            else:
                attr_text.append(f"{key}: {value}")
                attr_text.append("")

        text_widget.insert(tk.END, "\n".join(attr_text))
        text_widget.config(state=tk.DISABLED)  # 设置为只读

    def show_static(self, graph_data, title="生产线有向图模型"):
        """显示静态有向图，支持点击节点查看属性"""
        G = nx.DiGraph()
        valid_nodes = []
        self.node_info = {}  # 重置节点信息

        # 添加节点并存储完整数据
        for node in graph_data.get('nodes', []):
            try:
                node_name = node['name']
                node_type = node.get('type', 'unknown')
                node_data = node.get('data', {})

                G.add_node(
                    node_name,
                    type=node_type,
                    data=node_data,
                    failure=node_data.get('failure') is not None
                )

                valid_nodes.append(node_name)
                self.node_info[node_name] = node_data  # 存储节点属性
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

        # 计算节点层级
        def _calculate_node_levels(G):
            sources = [node for node, in_degree in G.in_degree() if in_degree == 0]
            if not sources:
                sources = [next(iter(G.nodes))]

            levels = {node: 0 for node in G.nodes}
            visited = set(sources)
            queue = sources.copy()

            while queue:
                current = queue.pop(0)
                for neighbor in G.successors(current):
                    if neighbor not in visited:
                        levels[neighbor] = levels[current] + 1
                        visited.add(neighbor)
                        queue.append(neighbor)
                    else:
                        if levels[neighbor] <= levels[current]:
                            levels[neighbor] = levels[current] + 1
            return levels

        levels = _calculate_node_levels(G)
        for node, level in levels.items():
            G.nodes[node]['level'] = level

        # 生成布局
        self.pos = nx.multipartite_layout(  # 存储位置信息用于点击检测
            G,
            subset_key='level',
            align='vertical',
            scale=22
        )

        # 节点样式配置
        node_colors = [self._get_node_style(G.nodes[node]['type'])['color'] for node in G.nodes]
        node_sizes = []
        for node in G.nodes:
            name_length = len(node)
            base_size = 400
            per_char_size = 500
            node_size = base_size + name_length * per_char_size
            node_sizes.append(node_size)

        # 创建图形和轴
        fig, ax = plt.subplots(figsize=(10, 6))

        # 绘制节点
        nodes = nx.draw_networkx_nodes(
            G, self.pos,
            node_color=node_colors,
            node_size=node_sizes,
            edgecolors='black',
            linewidths=1.2,
            ax=ax
        )

        # 绘制节点标签
        nx.draw_networkx_labels(
            G, self.pos,
            font_size=12,
            font_family=['SimHei', 'WenQuanYi Micro Hei', 'Heiti TC'],
            verticalalignment='center',
            horizontalalignment='center',
            ax=ax
        )

        # 绘制边
        nx.draw_networkx_edges(
            G, self.pos,
            arrowstyle='->',
            arrowsize=20,
            edge_color='#666666',
            width=1.2,
            ax=ax
        )

        # 添加图例
        legend_elements = []
        for node_type, style in self.node_style.items():
            legend_elements.append(
                plt.Line2D(
                    [0], [0],
                    marker='o',
                    color='w',
                    label=node_type,
                    markerfacecolor=style['color'],
                    markersize=12,
                    markeredgecolor='black',
                    markeredgewidth=1.2
                )
            )

        ax.legend(
            handles=legend_elements,
            loc='best',
            fontsize=10,
            prop={'family': ['SimHei', 'WenQuanYi Micro Hei', 'Heiti TC']},
            frameon=True,
            framealpha=0.9,
            edgecolor='lightgray'
        )

        # 设置标题和显示参数
        ax.set_title(title, fontsize=14, pad=20)
        ax.axis('off')
        plt.tight_layout()

        # 绑定点击事件
        fig.canvas.mpl_connect('button_press_event', self._on_node_click)

        plt.show()


if __name__ == "__main__":
    ProductionLineVisualizer.initialize_fonts(print_fonts=False)
    sample_graph_data = {
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
    visualizer = ProductionLineVisualizer()
    visualizer.show_static(sample_graph_data)

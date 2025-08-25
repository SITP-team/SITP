"""
可视化确认模块：处理图形展示及用户确认流程
"""
import json
from visualize import ProductionLineVisualizer


def visualize_and_confirm(graph_data, conversation_history):
    """
    展示可视化图形并获取用户确认，支持多次修改循环

    参数:
        graph_data: 图形数据结构
        conversation_history: 对话历史列表（引用传递，会被修改）

    返回:
        bool: 用户是否最终确认（True/False）
        dict: 最终确认的图形数据（仅当确认时有效）
    """
    try:
        while True:
            # 初始化字体配置
            ProductionLineVisualizer.initialize_fonts(print_fonts=False)

            # 可视化有向图
            print("📊 正在可视化有向图...")
            visualizer = ProductionLineVisualizer()
            visualizer.show_static(graph_data, title="生产线有向图可视化")

            # 用户确认流程
            while True:
                confirm = input("\n👀 请查看可视化图形，是否符合预期？(yes/no): ").strip().lower()
                if confirm in ["yes", "y"]:
                    print("👍 确认符合预期，继续生成模型...")
                    return True, graph_data
                elif confirm in ["no", "n"]:
                    # 获取用户修改意见并加入对话历史
                    user_input = input("✏️ 请描述需要修改的地方: ")
                    conversation_history.append({"role": "user", "content": user_input})
                    print("🔄 正在根据您的反馈重新生成图形...")
                    return False, None  # 未确认，需要重新生成
                else:
                    print("❌ 输入无效，请输入 'yes' 或 'no'")

    except Exception as e:
        print(f"❌ 可视化确认过程中发生错误: {str(e)}")
        return False, None
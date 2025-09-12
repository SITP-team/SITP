import time
import pythoncom
import json
from typing import Dict
from algorithm4 import Algorithm4
from plant_simulator01 import create_plant_simulation_model, init_plant_sim_instance, add_production_line,reset_and_increment,modify_buffer_capacity,run_simulation,get_simulation_results
from path_config import MODEL_FILE


def load_production_line_data(file_path: str) -> dict:
    """加载生产线描述数据"""
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)

def extract_conveyor_capacities(graph_data: dict) -> dict:
    """提取传送带固定容量（key：传送带名，value：固定容量）"""
    conveyor_cap = {}
    for node in graph_data["nodes"]:
        if node["type"] == "传送器":
            conveyor_cap[node["name"]] = node["data"]["capacity"]
    return conveyor_cap


def create_buffer_conveyor_map(conveyor_cap: dict) -> dict:
    """建立线边缓冲区与传送带固定容量的映射关系"""
    return {
        "B1": conveyor_cap["L1"],  # B1→L1，固定容量1
        "B2": conveyor_cap["L2"],  # B2→L2，固定容量1
        "B3": conveyor_cap["L3"],  # B3→L3，固定容量3
        "B4": conveyor_cap["L4"],  # B4→L4，固定容量2
        "B5": conveyor_cap["L5"],  # B5→L5，固定容量1
        "B6": 0,  # B6无传送带，固定容量0
        "B7": 0,  # B7无传送带，固定容量0
        "B8": conveyor_cap["L8"],  # B8→L8，固定容量2
        "B9": conveyor_cap["L9"],  # B9→L9，固定容量2
        "B10": conveyor_cap["L10"]  # B10→L10，固定容量1
    }


def initialize_algorithm(buffer_names: list, max_buffer: int, conv_map: dict) -> Algorithm4:
    """初始化优化算法实例"""
    return Algorithm4(
        buffer_names=buffer_names,
        max_buffer_per_slot=max_buffer,
        buffer_conveyor_map=conv_map
    )


def validate_solution(solution: dict, end_time: str, num_simulations: int = 5) -> tuple[bool, int]:
    """验证解决方案的产能是否达标（多次仿真取平均值）"""
    total_throughput = 0
    # 执行多次仿真
    for i in range(num_simulations):
        print(f"--- 第 {i + 1}/{num_simulations} 次仿真 ---")
        qualified, throughput = create_plant_simulation_model(buffer_solution=solution)
        total_throughput += throughput

    # 计算平均吞吐量
    avg_throughput = int(round(total_throughput / num_simulations))
    # 判断是否达标（基于平均吞吐量）
    target_total = 29000  # 月产能目标
    is_qualified = avg_throughput >= target_total
    print(f"📊 {num_simulations}次仿真平均吞吐量: {avg_throughput}，是否达标: {is_qualified}")
    return is_qualified, avg_throughput


def main():
    # 初始化COM组件
    pythoncom.CoInitialize()
    DEBUG_MODE = False
    SIMULATION_END_TIME = "2592000"  # 仿真结束时间（秒）
    TARGET_DAILY_THROUGHPUT = 29000 / 30  # 目标日产能
    BUFFER_NAMES = ["B1", "B2", "B3", "B4", "B5", "B6", "B7", "B8", "B9", "B10"]

    try:
        # 显示欢迎信息
        print("=" * 50)
        print("发动机缸盖生产线缓冲区优化系统")
        print(f"目标：月产能≥29000件，最小化总缓冲区容量")
        print("=" * 50)

        # 加载生产线数据
        graph_data = load_production_line_data("default_production_line.json")

        # 处理传送带与缓冲区映射关系
        conveyor_capacities = extract_conveyor_capacities(graph_data)
        buffer_conveyor_map = create_buffer_conveyor_map(conveyor_capacities)

        # 初始化优化算法
        algo4 = initialize_algorithm(
            buffer_names=BUFFER_NAMES,
            max_buffer=5,
            conv_map=buffer_conveyor_map
        )

        # 设置迭代参数
        max_iterations = 500  # 最大迭代次数
        stop_temperature = 0.1  # 停止温度

        print(f"\n=== 启动Algorithm 4缓冲区优化 ===")
        print(f"目标：月产能≥29000件")
        print(f"迭代参数：最大迭代次数={max_iterations}, 停止温度={stop_temperature}")

        # 验证初始解
        initial_solution = algo4.current_solution
        initial_total = algo4.current_total_buffer
        print(f"\n验证初始解：{initial_solution}")

        # 初始化仿真环境
        if not init_plant_sim_instance(MODEL_FILE):
            print("❌ 初始化Plant Simulation失败，退出程序")
            return

        # 加载生产线（仅一次，后续只修改缓冲区）
        if not add_production_line():
            print("❌ 添加生产线失败，退出程序")
            return

        reset_and_increment()  # 移到这里，作为初始化步骤执行一次

        # 将初始缓冲区方案注入到有向图数据
        for node in graph_data["nodes"]:
            if node["name"] in BUFFER_NAMES and node["type"] == "缓冲区":
                node["data"]["capacity"] = initial_solution[node["name"]]

        time.sleep(10)

        # 运行仿真验证初始解
        current_qualified, current_throughput = validate_solution(
            solution=initial_solution,
            end_time=SIMULATION_END_TIME
        )

        # 更新观测记录和历史
        algo4._update_observations(initial_solution, current_throughput)
        algo4.add_history_solution(initial_solution, initial_total, current_qualified, current_throughput)

        # 主迭代循环
        while (algo4.iteration < max_iterations
               and algo4.temperature > stop_temperature
               and algo4.no_improve_count < algo4.no_improve_threshold):  # 新增条件
            print(f"\n--- 迭代 {algo4.iteration + 1}/{max_iterations}，温度：{algo4.temperature:.2f} ---")
            print(f"连续无更优解次数：{algo4.no_improve_count}/{algo4.no_improve_threshold}")  # 新增：打印计数器

            # 1. 生成候选解
            candidate_solution = algo4._generate_candidate_solution()
            candidate_total = algo4._calculate_total_buffer(candidate_solution)

            # 显示当前解与候选解信息
            print(
                f"当前解：{algo4.current_solution}（总容量：{algo4.current_total_buffer}，"
                f"达标：{current_qualified}，吞吐量：{current_throughput:.2f}）"
            )
            print(f"候选解：{candidate_solution}（总容量：{candidate_total}）")

            # 2. 验证候选解
            candidate_qualified, candidate_throughput = validate_solution(
                solution=candidate_solution,
                end_time=SIMULATION_END_TIME
            )

            # 3. 更新观测记录
            algo4._update_observations(candidate_solution, candidate_throughput)
            algo4.add_history_solution(candidate_solution, candidate_total, candidate_qualified, candidate_throughput)

            # 4. 判断是否接受候选解
            accept = algo4._accept_candidate(
                candidate_total=candidate_total,
                candidate_qualified=candidate_qualified,
                current_qualified=current_qualified,
            )

            if accept:
                print(f"✅ 接受候选解，总容量从 {algo4.current_total_buffer} 变为 {candidate_total}")
                algo4.update_current_solution(candidate_solution, candidate_total)
                current_qualified = candidate_qualified
                current_throughput = candidate_throughput
            else:
                algo4.reject_candidate()  # 调用拒绝处理方法
                print(f"❌ 拒绝候选解")

            # 无论接受与否，都递增迭代次数并冷却温度
            algo4.iteration += 1
            algo4.cool_temperature()

        # 优化结束时，打印终止原因
        if algo4.no_improve_count >= algo4.no_improve_threshold:
            print(f"\n提前终止：连续{algo4.no_improve_threshold}次迭代无更优解")

        # 优化结束，输出结果
        print(f"\n=== Algorithm 4优化结束 ===")
        best_solution, best_total, best_throughput = algo4.get_best_solution()
        print(f"最优缓冲区方案：{best_solution}")
        print(f"最优总缓冲区容量：{best_total} 件")
        print(f"最优方案吞吐量：{best_throughput} 件")
        print(f"是否达标：{best_throughput >= TARGET_DAILY_THROUGHPUT}")
        print(f"历史达标方案数量：{len([s for s in algo4.history_solutions if s[2]])}")

        # 生成最终模型
        print("\n=== 生成最终优化模型 ===")
        create_plant_simulation_model(
            buffer_solution=best_solution,
            end_time=SIMULATION_END_TIME,
        )

    except Exception as e:
        print(f"发生错误：{str(e)}")
    finally:
        # 释放COM资源
        pythoncom.CoUninitialize()


if __name__ == "__main__":
    main()
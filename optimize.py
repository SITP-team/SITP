import win32com.client
import pythoncom
import numpy as np
import math
import random
import time
import json
import os


class PlantSimulationOptimizer:
    def __init__(self, model_path):
        """
        初始化Plant Simulation优化器

        Args:
            model_path: Plant Simulation模型文件路径
        """
        self.model_path = model_path
        self.plant_sim = None

        # 各工位固定缓冲容量(辊道折算容量)
        self.inherent_capacities = [1, 1, 3, 2, 1, 0, 0, 2, 2, 1]

        # 工位名称(L1-L10)
        self.workstation_names = ["L1", "L2", "L3", "L4", "L5", "L6", "L7", "L8", "L9", "L10"]

        # 每个工位总缓冲容量限制(固有+线边)
        self.min_total_capacity = 1  # 最小总容量
        self.max_total_capacity = 10  # 最大总容量

        # 目标吞吐量(件/月)
        self.target_monthly_throughput = 29000
        # 转换为日吞吐量(每月30天)
        self.target_daily_throughput = self.target_monthly_throughput / 30

        # 数据文件路径
        self.data_file_path = r"C:\Users\ThinkPad\Desktop\sitp\plant simulation\data_output.txt"

    def connect_to_plant_sim(self):
        """连接到Plant Simulation"""
        try:
            pythoncom.CoInitialize()
            # 尝试不同版本的Plant Simulation
            versions = [
                "Tecnomatix.PlantSimulation.RemoteControl.2404",
                "Tecnomatix.PlantSimulation.RemoteControl",
                "PlantSimulation.RemoteControl",
            ]

            for prog_id in versions:
                try:
                    self.plant_sim = win32com.client.Dispatch(prog_id)
                    print(f"✅ 成功连接到Plant Simulation: {prog_id}")
                    return True
                except Exception as e:
                    print(f"连接失败 {prog_id}: {str(e)}")
                    continue

            # 尝试通过COM应用程序启动
            try:
                plant_sim_app = win32com.client.Dispatch("Tecnomatix.PlantSimulation.Application")
                plant_sim_app.Visible = True
                self.plant_sim = plant_sim_app.RemoteControl
                print("✅ 成功通过COM应用程序启动Plant Simulation")
                return True
            except Exception as e:
                print(f"通过COM应用程序启动失败: {str(e)}")
                return False

        except Exception as e:
            print(f"❌ 连接Plant Simulation失败: {str(e)}")
            return False

    def load_model(self):
        """加载模型"""
        try:
            self.plant_sim.loadModel(self.model_path)
            print("✅ 成功加载模型")
            # 等待模型加载完成
            time.sleep(5)
            return True
        except Exception as e:
            print(f"❌ 加载模型失败: {str(e)}")
            return False

    def setup_simulation(self, capacity_config):
        """
        设置仿真参数并启动仿真

        Args:
            capacity_config: 长度为10的列表，表示L1-L10的容量
        """
        try:
            # 构建SimTalk代码，设置工位容量
            simtalk_code = ""

            for i, capacity in enumerate(capacity_config):
                workstation_name = self.workstation_names[i]
                simtalk_code += f".模型.模型.{workstation_name}.capacity := {capacity};\n"

            # 添加重置和启动仿真代码
            simtalk_code += """
            .模型.模型.事件控制器.reset;
            .模型.模型.事件控制器.start;
            .模型.模型.事件控制器.startwithoutanimation;
            """

            # 执行SimTalk代码
            self.plant_sim.ExecuteSimTalk(simtalk_code)
            print("✅ 仿真参数设置完成，仿真已启动")
            return True
        except Exception as e:
            print(f"❌ 设置仿真参数失败: {str(e)}")
            return False

    def get_simulation_result(self):
        """
        获取仿真结果

        Returns:
            throughput: 吞吐量(件/天)
        """
        try:
            # 等待仿真完成
            timeout = 300  # 5分钟超时
            start_time = time.time()

            while True:
                is_running = self.plant_sim.ExecuteSimTalk(".模型.模型.事件控制器.isrunning")
                if not is_running:
                    break

                if time.time() - start_time > timeout:
                    print("❌ 仿真运行超时")
                    return 0

                time.sleep(1)

            # 等待3秒确保仿真完全结束
            time.sleep(3)

            # 执行获取结果的SimTalk代码
            simtalk_code = f"""
            .模型.模型.数据表[1,1] := To_str(.模型.模型.OP130.statthroughputperday);
            .模型.模型.数据表.writefile("{self.data_file_path}");
            """

            self.plant_sim.ExecuteSimTalk(simtalk_code)

            # 等待文件写入完成
            time.sleep(2)

            # 从文件中读取数据
            if os.path.exists(self.data_file_path):
                with open(self.data_file_path, encoding="utf_8_sig") as fp:
                    data = fp.read()
                    # 解析数据，获取吞吐量
                    # 文件格式可能是表格形式，需要提取第一行第一列的数据
                    lines = data.strip().split('\n')
                    if len(lines) > 0:
                        # 假设数据在第二行第一列
                        throughput_str = lines[0].split('\t')[0]
                        throughput = float(data)
                        print(f"✅ 仿真完成，日吞吐量: {throughput} 件/天")
                        return throughput
                    else:
                        print("❌ 数据文件格式不正确")
                        return 0
            else:
                print("❌ 数据文件不存在")
                return 0

        except Exception as e:
            print(f"❌ 获取仿真结果失败: {str(e)}")
            return 0

    def get_capacity_range(self, index):
        """
        获取指定工位的容量可选范围

        Args:
            index: 工位索引(0-9)

        Returns:
            min_cap: 最小可选容量
            max_cap: 最大可选容量
        """
        # 固有容量
        inherent_cap = self.inherent_capacities[index]

        # 最小容量至少为1，最大容量为10
        min_cap = max(1, inherent_cap)  # 确保总容量至少为1
        max_cap = self.max_total_capacity

        return min_cap, max_cap

    def evaluate(self, capacity_config):
        """
        评估给定容量配置的性能

        Args:
            capacity_config: 容量配置

        Returns:
            total_capacity: 总容量
            throughput: 吞吐量
            fitness: 适应度值(越小越好)
        """
        # 计算总容量
        total_capacity = sum(capacity_config)

        # 检查每个工位的容量是否在允许范围内
        for i in range(10):
            capacity = capacity_config[i]
            min_cap, max_cap = self.get_capacity_range(i)

            if capacity < min_cap or capacity > max_cap:
                print(f"❌ 工位{i + 1}的容量{capacity}超出允许范围[{min_cap}, {max_cap}]")
                return total_capacity, 0, float('inf')

        # 设置仿真参数并启动仿真
        if not self.setup_simulation(capacity_config):
            return total_capacity, 0, float('inf')

        # 获取仿真结果
        throughput = self.get_simulation_result()

        # 计算适应度值
        # 如果吞吐量达到目标，适应度值为总容量
        # 如果未达到目标，适应度值为总容量加上惩罚项
        if throughput >= self.target_daily_throughput:
            fitness = total_capacity
        else:
            # 惩罚项：目标吞吐量与实际吞吐量的差距
            penalty = (self.target_daily_throughput - throughput) * 10
            fitness = total_capacity + penalty

        return total_capacity, throughput, fitness

    def generate_initial_solution(self):
        """生成初始解，确保每个工位容量至少为1"""
        initial_config = []
        for i in range(10):
            min_cap, max_cap = self.get_capacity_range(i)
            # 初始容量设为最小容量
            initial_config.append(min_cap)
        return initial_config

    def generate_neighbor_solution(self, current_config):
        """生成邻域解"""
        new_config = current_config.copy()

        # 随机选择一个工位进行修改
        idx = random.randint(0, 9)

        # 获取该工位的容量范围
        min_cap, max_cap = self.get_capacity_range(idx)

        # 在当前值基础上进行小幅调整
        current_value = new_config[idx]
        delta = random.choice([-1, 1])
        new_value = max(min_cap, min(max_cap, current_value + delta))

        new_config[idx] = new_value

        return new_config

    def simulated_annealing(self, initial_temp=1000, cooling_rate=0.95, max_iter=50):
        """
        模拟退火算法优化容量配置

        Args:
            initial_temp: 初始温度
            cooling_rate: 冷却速率
            max_iter: 最大迭代次数

        Returns:
            best_config: 最佳容量配置
            best_fitness: 最佳适应度值
            history: 优化历史记录
            best_throughput: 最佳吞吐量
        """
        # 连接到Plant Simulation
        if not self.connect_to_plant_sim():
            return None, float('inf'), [], 0

        # 加载模型
        if not self.load_model():
            return None, float('inf'), [], 0

        # 初始化当前解(确保每个工位容量至少为1)
        current_config = self.generate_initial_solution()
        current_capacity, current_throughput, current_fitness = self.evaluate(current_config)

        # 初始化最佳解
        best_config = current_config.copy()
        best_capacity = current_capacity
        best_throughput = current_throughput
        best_fitness = current_fitness

        # 记录优化历史
        history = [{
            'iteration': 0,
            'config': current_config.copy(),
            'capacity': current_capacity,
            'throughput': current_throughput,
            'fitness': current_fitness,
            'temperature': initial_temp
        }]

        # 开始模拟退火
        temperature = initial_temp

        for iteration in range(1, max_iter + 1):
            print(f"\n=== 迭代 {iteration}/{max_iter} ===")
            print(f"当前温度: {temperature:.2f}")

            # 生成新解
            new_config = self.generate_neighbor_solution(current_config)

            # 评估新解
            new_capacity, new_throughput, new_fitness = self.evaluate(new_config)

            # 决定是否接受新解
            delta_f = new_fitness - current_fitness

            if delta_f < 0:
                # 新解更好，直接接受
                accept = True
                print(f"✅ 接受更好解: Δf = {delta_f:.2f}")
            else:
                # 新解更差，以一定概率接受
                probability = math.exp(-delta_f / temperature)
                accept = random.random() < probability
                print(f"🔄 以概率 {probability:.4f} 接受更差解: Δf = {delta_f:.2f}")

            # 如果接受新解，更新当前解
            if accept:
                current_config = new_config
                current_capacity = new_capacity
                current_throughput = new_throughput
                current_fitness = new_fitness

                # 更新最佳解
                if current_fitness < best_fitness:
                    best_config = current_config.copy()
                    best_capacity = current_capacity
                    best_throughput = current_throughput
                    best_fitness = current_fitness
                    print(f"🎉 更新最佳解: 容量={best_capacity}, 吞吐量={best_throughput}")

            # 降低温度
            temperature *= cooling_rate

            # 记录历史
            history.append({
                'iteration': iteration,
                'config': current_config.copy(),
                'capacity': current_capacity,
                'throughput': current_throughput,
                'fitness': current_fitness,
                'temperature': temperature
            })

            # 打印当前状态
            print(
                f"当前解: {current_config}, 容量={current_capacity}, 吞吐量={current_throughput}, 适应度={current_fitness:.2f}")
            print(f"最佳解: {best_config}, 容量={best_capacity}, 吞吐量={best_throughput}, 适应度={best_fitness:.2f}")

            # 如果找到满足目标的解且总容量最小，可以提前终止
            if best_throughput >= self.target_daily_throughput and best_capacity == sum(self.inherent_capacities):
                print("🎯 找到最优解!")
                break

        return best_config, best_fitness, history, best_throughput

    def save_results(self, best_config, best_throughput, history):
        """保存优化结果"""
        # 保存最佳配置
        result = {
            'best_config': best_config,
            'total_capacity': sum(best_config),
            'target_daily_throughput': self.target_daily_throughput,
            'actual_daily_throughput': best_throughput,
            'target_monthly_throughput': self.target_monthly_throughput,
            'actual_monthly_throughput': best_throughput * 30,
            'optimization_history': history
        }

        with open('optimization_results.json', 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=4, ensure_ascii=False)

        print("✅ 优化结果已保存到 optimization_results.json")


def main():
    # 模型文件路径(请根据实际情况修改)
    model_path = r"C:\Users\ThinkPad\Desktop\sitp\模型.spp"

    # 创建优化器
    optimizer = PlantSimulationOptimizer(model_path)

    # 运行模拟退火算法
    best_config, best_fitness, history, best_throughput = optimizer.simulated_annealing(
        initial_temp=1000,
        cooling_rate=0.95,
        max_iter=50
    )

    # 保存结果
    optimizer.save_results(best_config, best_throughput, history)

    print("\n=== 优化完成 ===")
    print(f"最佳工位容量配置: {best_config}")
    print(f"总容量: {sum(best_config)}")
    print(f"日吞吐量: {best_throughput} 件/天")
    print(f"月吞吐量: {best_throughput * 30} 件/月")

    # 释放COM资源
    pythoncom.CoUninitialize()


if __name__ == "__main__":
    main()
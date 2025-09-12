# algorithm4.py（优化版）
import random
import math
import json
from typing import List, Dict, Tuple, Any


class Algorithm4:
    def __init__(self, buffer_names: List[str], max_buffer_per_slot: int, buffer_conveyor_map: Dict[str, int]):
        """
                初始化带平均化的模拟退火算法
                :param buffer_names: 线边缓冲区名称列表（如 ["B1", "B2", ..., "B10"]）
                :param max_buffer_per_slot: 每个缓冲区的最大容量
                :param buffer_conveyor_map: 缓冲区→传送带固定容量映射
                """
        # 新增参数：连续无更优解的终止阈值
        self.no_improve_threshold = 100  # 可自定义，如连续10次无改进则终止
        self.no_improve_count = 0  # 连续无改进计数器
        self.best_total_so_far = float('inf')  # 记录历史最优解的总容量（初始设为无穷大）
        self.buffer_names = buffer_names
        self.max_buffer = max_buffer_per_slot
        self.buffer_conveyor_map = buffer_conveyor_map
        self.current_solution: Dict[str, int] = {}
        self.current_total_buffer: int = 0
        self.temperature: float = 0.0
        self.initial_temperature = self.temperature  # 保存初始温度
        self.cooling_rate: float = 0.95  # 温度衰减系数
        self.iteration: int = 0
        # 历史方案: (方案, 总容量, 是否达标, 吞吐量)
        self.history_solutions: List[Tuple[Dict[str, int], int, bool, int]] = []
        # 方案吞吐量历史记录（键: 排序后的方案元组, 值: 吞吐量列表）
        self.observations: Dict[Tuple[Tuple[str, int], ...], List[int]] = {}

        self._init_initial_solution()
        self.temperature = max(self.current_total_buffer * 5, 100)  # 保证最低温度

    def _init_initial_solution(self) -> None:
        """从JSON文件加载初始缓冲区容量配置"""
        try:
            with open("default_production_line.json", "r", encoding="utf-8") as f:
                data = json.load(f)
        except FileNotFoundError:
            raise FileNotFoundError("配置文件 default_production_line.json 未找到")

        for node in data.get("nodes", []):
            if node.get("type") == "缓冲区" and node.get("name") in self.buffer_names:
                buf_name = node["name"]
                self.current_solution[buf_name] = node["data"]["capacity"]
        self.current_total_buffer = sum(self.current_solution.values())
        self.current_total_buffer = sum(self.current_solution.values())
        print(f"Algorithm 4 初始解：{self.current_solution}，总容量：{self.current_total_buffer}")

    def _generate_candidate_solution(self) -> Dict[str, int]:
        """生成满足约束条件的候选解（可同时调整多个缓冲区）"""
        candidate = self.current_solution.copy()
        num_to_change = random.randint(1, 2)  # 少修改缓冲区，精细优化
        # 从所有缓冲区中随机选择不重复的num_to_change个
        selected_bufs = random.sample(self.buffer_names, num_to_change)

        for buf in selected_bufs:
            fixed_cap = self.buffer_conveyor_map[buf]
            current_cap = candidate[buf]
            new_cap = current_cap

            # 为每个选中的缓冲区寻找符合约束的新容量值
            while True:
                delta = random.choice([-1, 1])  # 小步微调
                new_cap = current_cap + delta
                # 确保容量非负且总容量（固定+缓冲）在[1, 10]范围内
                if new_cap >= 0 and 1 <= (fixed_cap + new_cap) <= 10:
                    break

            candidate[buf] = new_cap

        return candidate

    def _calculate_total_buffer(self, solution: Dict[str, int]) -> int:
        """计算方案的总缓冲区容量"""
        return sum(solution.values())

    def _get_solution_key(self, solution: Dict[str, int]) -> Tuple[Tuple[str, int], ...]:
        """将方案转换为可哈希的元组键（按名称排序）"""
        return tuple(sorted(solution.items()))

    def update_current_solution(self, candidate: Dict[str, int], candidate_total: int) -> None:
        """更新当前解（接受候选解时调用）"""
        self.current_solution = candidate.copy()
        self.current_total_buffer = candidate_total

    def _get_averaged_throughput(self, solution: Dict[str, int]) -> int:
        """获取方案的历史平均吞吐量（基于多次仿真的平均值）"""
        solution_key = self._get_solution_key(solution)
        observations = self.observations.get(solution_key, [])
        return sum(observations) // len(observations) if observations else 0

    def _accept_candidate(self, candidate_total: int, candidate_qualified: bool, current_qualified: bool) -> bool:
        """模拟退火接受准则"""
        # 候选解达标且总容量更小：直接接受
        if candidate_qualified and candidate_total < self.current_total_buffer:
            return True

        # 候选解达标但总容量更大：按概率接受
        if candidate_qualified and candidate_total >= self.current_total_buffer:
            accept_prob = math.exp(-(candidate_total - self.current_total_buffer) / self.temperature)
            return random.random() < accept_prob

        # 候选解不达标但当前解达标：极低概率接受
        if not candidate_qualified and current_qualified:
            accept_prob = math.exp(-(self.current_total_buffer - candidate_total) / self.temperature) * 0.1
            return random.random() < accept_prob

        # 两者都不达标：拒绝
        return False

    def reject_candidate(self) -> None:
        """处理拒绝候选解的情况"""
        pass  # 空实现，仅用于统一流程

    def cool_temperature(self) -> None:
        """冷却温度（最低保留0.1）"""
        self.temperature = max(self.temperature * self.cooling_rate, 0.1)

    def update_current_solution(self, candidate: Dict[str, int], candidate_total: int) -> None:
        """更新当前解并冷却温度"""
        self.current_solution = candidate.copy()
        self.current_total_buffer = candidate_total
        self.iteration += 1
        self.cool_temperature()

    def add_history_solution(self, solution: Dict[str, int], total: int, qualified: bool, throughput: int) -> None:
        """记录历史方案"""
        self.history_solutions.append((solution, total, qualified, throughput))

    def get_best_solution(self) -> Tuple[Dict[str, int], int, int]:
        """获取最优解（达标且总容量最小）"""
        qualified_solutions = [s for s in self.history_solutions if s[2]]

        if not qualified_solutions:
            return self.current_solution, self.current_total_buffer, 0.0

        # 按总容量升序排序，取第一个
        qualified_solutions.sort(key=lambda x: x[1])
        best_sol, best_total, _, best_throughput = qualified_solutions[0]
        # 新增：若当前最优解优于历史记录，重置计数器
        if best_total < self.best_total_so_far:
            self.best_total_so_far = best_total
            self.no_improve_count = 0  # 重置计数器
        else:
            self.no_improve_count += 1  # 无改进，计数器+1
        return best_sol, best_total, best_throughput

    def _update_observations(self, solution: Dict[str, int], throughput: int) -> None:
        """更新方案的吞吐量观测记录"""
        solution_key = self._get_solution_key(solution)
        if solution_key not in self.observations:
            self.observations[solution_key] = []
        self.observations[solution_key].append(throughput)
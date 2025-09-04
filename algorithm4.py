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
        self.buffer_names = buffer_names
        self.max_buffer = max_buffer_per_slot
        self.buffer_conveyor_map = buffer_conveyor_map
        self.current_solution: Dict[str, int] = {}
        self.current_total_buffer: int = 0
        self.temperature: float = 0.0
        self.cooling_rate: float = 0.95  # 温度衰减系数
        self.iteration: int = 0
        # 历史方案: (方案, 总容量, 是否达标, 吞吐量)
        self.history_solutions: List[Tuple[Dict[str, int], int, bool, float]] = []
        # 方案吞吐量历史记录（键: 排序后的方案元组, 值: 吞吐量列表）
        self.observations: Dict[Tuple[Tuple[str, int], ...], List[float]] = {}

        self._init_initial_solution()
        self.temperature = self.current_total_buffer * 2  # 初始温度

    def _init_initial_solution(self) -> None:
        """从JSON文件加载初始缓冲区容量配置"""
        try:
            with open("production_line02.json", "r", encoding="utf-8") as f:
                data = json.load(f)
        except FileNotFoundError:
            raise FileNotFoundError("配置文件 production_line02.json 未找到")

        for node in data.get("nodes", []):
            if node.get("type") == "缓冲区" and node.get("name") in self.buffer_names:
                buf_name = node["name"]
                self.current_solution[buf_name] = node["data"]["capacity"]

        self.current_total_buffer = sum(self.current_solution.values())
        print(f"Algorithm 4 初始解：{self.current_solution}，总容量：{self.current_total_buffer}")

    def _generate_candidate_solution(self) -> Dict[str, int]:
        """生成满足约束条件的候选解"""
        candidate = self.current_solution.copy()
        selected_buf = random.choice(self.buffer_names)
        fixed_cap = self.buffer_conveyor_map[selected_buf]
        current_cap = candidate[selected_buf]
        new_cap = current_cap

        # 寻找符合约束的新容量值
        while True:
            delta = random.choice([-1, 1])
            new_cap = current_cap + delta
            # 确保容量非负且总容量在[1, 10]范围内
            if new_cap >= 0 and 1 <= (fixed_cap + new_cap) <= 10:
                break

        candidate[selected_buf] = new_cap
        return candidate

    def _calculate_total_buffer(self, solution: Dict[str, int]) -> int:
        """计算方案的总缓冲区容量"""
        return sum(solution.values())

    def _get_solution_key(self, solution: Dict[str, int]) -> Tuple[Tuple[str, int], ...]:
        """将方案转换为可哈希的元组键（按名称排序）"""
        return tuple(sorted(solution.items()))

    def _update_observations(self, solution: Dict[str, int], throughput: float) -> None:
        """累积方案的吞吐量历史记录"""
        solution_key = self._get_solution_key(solution)
        self.observations.setdefault(solution_key, []).append(throughput)

    def _get_averaged_throughput(self, solution: Dict[str, int]) -> float:
        """获取方案的平均吞吐量（至少3次观测）"""
        solution_key = self._get_solution_key(solution)
        observations = self.observations.get(solution_key, [])
        return sum(observations) / len(observations) if len(observations) >= 3 else 0.0

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

    def cool_temperature(self) -> None:
        """冷却温度（最低保留0.1）"""
        self.temperature = max(self.temperature * self.cooling_rate, 0.1)

    def update_current_solution(self, candidate: Dict[str, int], candidate_total: int) -> None:
        """更新当前解并冷却温度"""
        self.current_solution = candidate.copy()
        self.current_total_buffer = candidate_total
        self.iteration += 1
        self.cool_temperature()

    def add_history_solution(self, solution: Dict[str, int], total: int, qualified: bool, throughput: float) -> None:
        """记录历史方案"""
        self.history_solutions.append((solution, total, qualified, throughput))

    def get_best_solution(self) -> Tuple[Dict[str, int], int, float]:
        """获取最优解（达标且总容量最小）"""
        qualified_solutions = [s for s in self.history_solutions if s[2]]

        if not qualified_solutions:
            return self.current_solution, self.current_total_buffer, 0.0

        # 按总容量升序排序，取第一个
        qualified_solutions.sort(key=lambda x: x[1])
        best_sol, best_total, _, best_throughput = qualified_solutions[0]
        return best_sol, best_total, best_throughput
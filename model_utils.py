#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from time_utils import format_time_value


class ModelUtils:
    @staticmethod
    def create_entity(
        entity_type, x_pos, y_pos, name, conveyer_y=None, material_end_y=None
    ):
        """创建实体工厂方法"""
        if entity_type == "源":
            return f'.物料流.源.createObject(.模型.模型, {x_pos}, {y_pos}, "{name}")'
        elif entity_type == "工位":
            return f'.物料流.工位.createObject(.模型.模型, {x_pos}, {y_pos}, "{name}")'
        elif entity_type == "缓冲区":
            return (
                f'.物料流.缓冲区.createObject(.模型.模型, {x_pos}, {y_pos}, "{name}")'
            )
        elif entity_type == "传送器":
            result = f'.物料流.传送器.createObject(.模型.模型, {x_pos}, {conveyer_y}, "{name}")'
            conveyer_y += 50
            return result, conveyer_y
        elif entity_type == "物料终结":
            result = f'.物料流.物料终结.createObject(.模型.模型, 300, {material_end_y}, "{name}")'
            material_end_y += 50
            return result, material_end_y
        return ""

    @staticmethod
    def setup_failure(node_name, failure_data, source_start_time, source_stop_time):
        """设置故障的统一方法"""
        failure_name = failure_data.get("failure_name", "default_failure")
        failure_start = failure_data.get("start_time", source_start_time)
        failure_stop = failure_data.get("stop_time", source_stop_time)

        interval_time = failure_data.get("interval_time")
        if isinstance(interval_time, dict) and "distribution_pattern" in interval_time:
            formatted = format_time_value(interval_time)
            cleaned = formatted.replace('"', "")
            interval_str = f'"{cleaned}"'
        else:
            interval_str = str(interval_time)

        duration_time = failure_data.get("duration_time", "0:0:0:0")
        if isinstance(duration_time, dict) and "distribution_pattern" in duration_time:
            formatted = format_time_value(duration_time)
            cleaned = formatted.replace('"', "")
            duration_str = f'"{cleaned}"'
        else:
            duration_str = str(duration_time)

        return [
            f'.模型.模型.{node_name}.Failures.createFailure("{failure_name}", {interval_str}, {duration_str}, "SimulationTime", {failure_start}, {failure_stop}, false)',
            f".模型.模型.{node_name}.Failures.{failure_name}.Active := true",
        ]

    @staticmethod
    def write_material_end_stats(node_name, row):
        """写入物料终结统计数据的统一方法"""
        return [
            f'.模型.模型.数据表[1, {row}] := "{node_name}"',
            f'.模型.模型.数据表[1, {row+1}] := "平均寿命"',
            f".模型.模型.数据表[2, {row+1}] := To_str(.模型.模型.{node_name}.statavglifespan)",
            f'.模型.模型.数据表[1, {row+2}] := "平均退出间隔"',
            f".模型.模型.数据表[2, {row+2}] := To_str(.模型.模型.{node_name}.statavgexitinterval)",
            f'.模型.模型.数据表[1, {row+3}] := "总吞吐量"',
            f".模型.模型.数据表[2, {row+3}] := To_str(.模型.模型.{node_name}.statdeleted)",
            f'.模型.模型.数据表[1, {row+4}] := "每天吞吐量"',
            f".模型.模型.数据表[2, {row+4}] := To_str(.模型.模型.{node_name}.statthroughputperday)",
        ]

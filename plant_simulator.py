#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time
import win32com.client
import subprocess
import os
import pythoncom


def create_plant_simulation_model(model_setup_code, data_writing_code):
    """分两步执行：先建立模型，再写入数据"""
    try:
        # 初始化COM环境
        pythoncom.CoInitialize()

        # 尝试不同版本的Plant Simulation
        versions = [
            "Tecnomatix.PlantSimulation.RemoteControl.2404",  # 2404版本
            "Tecnomatix.PlantSimulation.RemoteControl",  # 通用版本
            "PlantSimulation.RemoteControl",  # 旧版本
        ]

        plant_sim = None
        for prog_id in versions:
            try:
                # 尝试启动Plant Simulation
                print(f"尝试连接 Plant Simulation: {prog_id}")
                plant_sim = win32com.client.Dispatch(prog_id)
                print(f"✅ 成功连接 Plant Simulation: {prog_id}")
                break
            except Exception as e:
                print(f"连接失败 {prog_id}: {str(e)}")
                continue

        if plant_sim is None:
            # 尝试通过COM应用程序启动
            print("尝试通过COM应用程序启动Plant Simulation...")
            try:
                plant_sim_app = win32com.client.Dispatch(
                    "Tecnomatix.PlantSimulation.Application"
                )
                plant_sim_app.Visible = True
                plant_sim = plant_sim_app.RemoteControl
                print("✅ 成功通过COM应用程序启动Plant Simulation")
            except Exception as e:
                print(f"通过COM应用程序启动失败: {str(e)}")
                print("❌ 无法连接任何Plant Simulation版本，请尝试以下解决方案：")
                print("1. 确保Plant Simulation 2404已正确安装")
                print("2. 以管理员身份运行此脚本")
                print("3. 检查Plant Simulation的COM设置")
                return False

        # 打开模板模型
        from path_config import MODEL_FILE, SAVED_MODEL_FILE

        plant_sim.loadModel(MODEL_FILE)

        # 第一步：执行模型建立代码
        print("⏳ 正在建立模型结构...")
        plant_sim.ExecuteSimTalk(model_setup_code)
        time.sleep(1)
        # 第二步：执行数据写入代码
        print("⏳ 正在写入仿真数据...")
        plant_sim.ExecuteSimTalk(data_writing_code)

        # 保存模型
        from path_config import SAVED_MODEL_FILE

        save_path = SAVED_MODEL_FILE
        plant_sim.SaveModel(save_path)
        print(f"✅ 模型已成功保存至：{save_path}")

        # 读取Excel并打印内容
        try:
            print("\n📊 Excel中的仿真数据：")
            from path_config import DATA_OUTPUT_FILE

            with open(DATA_OUTPUT_FILE, encoding="utf_8_sig") as fp:
                print(fp.read())
        except Exception as e:
            print(f"⚠ 读取Excel失败：{str(e)}")

        # 启动Plant Simulation应用程序
        from path_config import PLANT_SIM_PATHS

        plant_sim_paths = PLANT_SIM_PATHS

        found = False
        for path in plant_sim_paths:
            if os.path.exists(path):
                try:
                    subprocess.Popen([path, save_path])
                    print(f"✅ 已启动 Plant Simulation 并打开模型: {path}")
                    found = True
                    break
                except Exception as e:
                    print(f"⚠️ 无法启动 {path}: {str(e)}")

        if not found:
            print("⚠️ 未找到 Plant Simulation 可执行文件")
            print(f"请手动打开模型文件: {save_path}")

        return True

    except Exception as e:
        print(f"❌ Plant Simulation 操作失败: {str(e)}")
        import traceback

        traceback.print_exc()
        return False
    finally:
        # 释放COM环境
        pythoncom.CoUninitialize()

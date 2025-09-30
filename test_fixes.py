#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试修复的PCI规划功能
测试LTE同站点模3冲突避免和最新文件选择功能
"""

import os
import sys
import pandas as pd
import numpy as np
from datetime import datetime

# 导入修复后的PCI规划工具
from pci_planning_lte_nr_enhanced import LTENRPCIPlanner, NetworkParameterUpdater

def test_lte_mod3_conflict_avoidance():
    """测试LTE同站点模3冲突避免功能"""
    print("=== 测试LTE同站点模3冲突避免功能 ===")

    # 创建测试数据 - 3个同站点小区
    test_data = pd.DataFrame({
        'eNodeBID': [1001, 1002, 1003],  # 不同基站ID但同位置
        'CellID': [1, 2, 3],
        'gNodeBID': [None, None, None],  # LTE网络
        'lat': [23.123456, 23.123456, 23.123456],  # 相同纬度
        'lon': [113.654321, 113.654321, 113.654321],  # 相同经度
        'pci': [0, 1, 2],  # 原始PCI值
        'earfcnDl': [100, 100, 100],  # 同频
        'cell_name': ['测试小区1', '测试小区2', '测试小区3']
    })

    # 创建参数数据 - 包含同站点小区
    params_data = pd.DataFrame({
        'eNodeB标识\neNodeB ID\nlong:[0..1048575]': [1001, 1002, 1003, 2001, 2002],
        '小区标识\ncellLocalId\ninteger:[0~2147483647]': [1, 2, 3, 1, 2],
        '小区名称\nuserLabel\nstring[0..128]': ['测试小区1', '测试小区2', '测试小区3', '其他小区1', '其他小区2'],
        '物理小区识别码\nPCI\nlong:[0..503]': [0, 1, 2, 10, 11],
        '小区纬度\neNodeB Latitude\ndouble:[-90..90]': [23.123456, 23.123456, 23.123456, 23.200000, 23.200000],
        '小区经度\neNodeB Longitude double:[-180..180]': [113.654321, 113.654321, 113.654321, 113.700000, 113.700000],
        '下行链路的中心载频\nearfcnDl\ndouble Step：0.1 \nUnite：MHz': [100, 100, 100, 200, 200]
    })

    try:
        # 创建规划器 - 自由规划模式（不继承模3）
        planner = LTENRPCIPlanner(
            reuse_distance_km=3.0,
            lte_inherit_mod3=False,  # 自由规划模式
            network_type="LTE",
            params_file="test_params.xlsx"
        )

        # 设置测试数据
        planner.cells_to_plan = test_data
        planner.target_cells = planner.preprocess_target_cells(params_data)
        planner.all_cells_combined = planner.target_cells.copy()

        print(f"测试数据: {len(test_data)} 个小区")
        print(f"同站点小区数量: {len(planner.target_cells[planner.target_cells['lat'] == 23.123456])}")

        # 执行规划
        result_df = planner.plan_pci_with_reuse_priority()

        # 验证结果 - 检查同站点3个小区的模3值是否不同
        same_site_cells = result_df[result_df['lat'] == 23.123456]
        mod_values = [pci % 3 for pci in same_site_cells['分配的PCI'] if pci != -1]

        print(f"同站点小区分配的PCI: {list(same_site_cells['分配的PCI'])}")
        print(f"对应的模3值: {mod_values}")
        print(f"模3值集合: {set(mod_values)}")
        print(f"不同模3值数量: {len(set(mod_values))}")

        # 验证是否避免了同站同模
        if len(set(mod_values)) >= 3:
            print("成功！同站点3个小区使用了3种不同的模3值")
            return True
        else:
            print("失败！同站点小区存在模3冲突")
            return False

    except Exception as e:
        print(f"测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_file_selection():
    """测试最新文件选择功能"""
    print("\\n=== 测试最新文件选择功能 ===")

    # 创建模拟文件列表
    test_files = [
        "全量工参/ProjectParameter_mongoose河源电联20250928230617.xlsx",
        "全量工参/ProjectParameter_mongoose河源电联20250929153233.xlsx",
        "全量工参/ProjectParameter_mongoose河源电联20250930104500.xlsx"
    ]

    updater = NetworkParameterUpdater()
    latest_file = updater._get_latest_parameter_file(test_files)

    print(f"测试文件列表:")
    for file in test_files:
        print(f"  {os.path.basename(file)}")

    print(f"选择的最新文件: {os.path.basename(latest_file) if latest_file else 'None'}")

    # 验证是否正确选择了最新的文件
    expected_latest = "全量工参/ProjectParameter_mongoose河源电联20250930104500.xlsx"
    if latest_file == expected_latest:
        print("成功！正确选择了最新的参数文件")
        return True
    else:
        print(f"失败！期望选择 {os.path.basename(expected_latest)}, 实际选择了 {os.path.basename(latest_file) if latest_file else 'None'}")
        return False

def main():
    """主测试函数"""
    print("开始测试PCI规划修复功能...")
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # 测试文件选择功能
    file_test_passed = test_file_selection()

    # 测试LTE模3冲突避免功能
    mod3_test_passed = test_lte_mod3_conflict_avoidance()

    # 总结结果
    print("\\n" + "="*50)
    print("测试结果总结:")
    print(f"文件选择功能测试: {'通过' if file_test_passed else '失败'}")
    print(f"LTE模3冲突避免测试: {'通过' if mod3_test_passed else '失败'}")

    if file_test_passed and mod3_test_passed:
        print("\\n所有测试通过！修复功能正常工作")
        return 0
    else:
        print("\\n部分测试失败，请检查修复代码")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
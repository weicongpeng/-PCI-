#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试学校小区PCI规划问题
模拟市区技术学校T_800M_0-XJ和市区技术学校T_800M_2-XJ的PCI分配情况
"""

import pandas as pd
import numpy as np
from pci_planning_lte_nr_enhanced import LTENRPCIPlanner

def test_school_cells_issue():
    """测试学校小区PCI冲突问题"""
    print("=== 测试学校小区PCI冲突问题 ===")

    # 创建模拟学校小区数据 - 基于实际问题的场景
    test_data = pd.DataFrame({
        'eNodeBID': [68157, 68157, 68157],  # 同一个基站，不同小区
        'CellID': [0, 1, 2],
        'gNodeBID': [None, None, None],  # LTE网络
        'lat': [23.123450, 23.123450, 23.123450],  # 相同位置（学校）
        'lon': [113.654320, 113.654320, 113.654320],  # 相同位置
        'pci': [101, 102, 103],  # 原始PCI值
        'earfcnDl': [100, 100, 100],  # 同频
        'cell_name': ['市区技术学校T_800M_0-XJ', '市区技术学校T_800M_1-XJ', '市区技术学校T_800M_2-XJ']
    })

    # 创建参数数据 - 包含学校小区和周边小区
    params_data = pd.DataFrame({
        'eNodeB标识\neNodeB ID\nlong:[0..1048575]': [68157, 68157, 68157, 68158, 68159],
        '小区标识\ncellLocalId\ninteger:[0~2147483647]': [0, 1, 2, 0, 0],
        '小区名称\nuserLabel\nstring[0..128]': [
            '市区技术学校T_800M_0-XJ',
            '市区技术学校T_800M_1-XJ',
            '市区技术学校T_800M_2-XJ',
            '周边小区1',
            '周边小区2'
        ],
        '物理小区识别码\nPCI\nlong:[0..503]': [101, 102, 103, 201, 202],
        '小区纬度\neNodeB Latitude\ndouble:[-90..90]': [23.123450, 23.123450, 23.123450, 23.124000, 23.125000],
        '小区经度\neNodeB Longitude double:[-180..180]': [113.654320, 113.654320, 113.654320, 113.655000, 113.656000],
        '下行链路的中心载频\nearfcnDl\ndouble Step：0.1 \nUnite：MHz': [100, 100, 100, 100, 100]
    })

    try:
        print(f"测试数据: {len(test_data)} 个小区")
        print(f"同站点小区信息:")
        for idx, cell in test_data.iterrows():
            print(f"  基站{cell['eNodeBID']}-小区{cell['CellID']}: {cell['cell_name']}")
            print(f"    位置: ({cell['lat']}, {cell['lon']})")
            print(f"    原PCI: {cell['pci']}, mod3: {cell['pci'] % 3}")

        # 创建规划器 - 自由规划模式（不继承模3）
        planner = LTENRPCIPlanner(
            reuse_distance_km=3.0,
            lte_inherit_mod3=False,  # 自由规划模式 - 关键测试点
            network_type="LTE",
            params_file="test_school_params.xlsx"
        )

        # 设置测试数据
        planner.cells_to_plan = test_data
        planner.target_cells = planner.preprocess_target_cells(params_data)
        planner.all_cells_combined = planner.target_cells.copy()

        print(f"\n开始PCI规划...")
        print(f"规划模式: 自由规划（不继承mod3）")
        print(f"同频PCI最小复用距离: 3.0km")

        # 执行规划
        result_df = planner.plan_pci_with_reuse_priority()

        # 分析结果 - 重点关注同站点3个小区的mod3分配
        same_site_cells = result_df[result_df['lat'] == 23.123450]

        print(f"\n=== 规划结果分析 ===")
        print(f"同站点小区数量: {len(same_site_cells)}")

        mod_values = []
        pci_values = []

        for idx, cell in same_site_cells.iterrows():
            assigned_pci = cell['分配的PCI']
            if assigned_pci != -1:
                mod_val = assigned_pci % 3
                mod_values.append(mod_val)
                pci_values.append(assigned_pci)

                print(f"小区: {cell.get('小区名称', f'基站{cell.get('eNodeBID', 'N/A')}-小区{cell.get('CellID', 'N/A')}')}")
                print(f"  分配的PCI: {assigned_pci}")
                print(f"  mod3值: {mod_val}")
                print(f"  原PCI: {cell.get('原PCI', 'N/A')}")
                print(f"  分配原因: {cell.get('分配原因', 'N/A')}")
                print(f"  最小复用距离: {cell.get('最小复用距离(km)', 'N/A')}km")

        # 检查mod3冲突
        unique_mods = set(mod_values)
        print(f"\nmod3值分布: {mod_values}")
        print(f"唯一mod3值: {sorted(unique_mods)}")
        print(f"不同mod3值数量: {len(unique_mods)}")

        # 检查结果
        conflict_found = False
        mod_counts = {}
        for mod in mod_values:
            mod_counts[mod] = mod_counts.get(mod, 0) + 1

        print(f"\nmod3值统计:")
        for mod, count in mod_counts.items():
            print(f"  mod3={mod}: {count}个小区")
            if count > 1:
                conflict_found = True
                print(f"    冲突！有{count}个小区使用相同的mod3值")

        if conflict_found:
            print(f"\n发现mod3冲突！同站点小区未能正确错开")
            return False
        else:
            print(f"\n成功！同站点3个小区使用了3种不同的mod3值")
            return True

    except Exception as e:
        print(f"测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_edge_cases():
    """测试边界情况"""
    print("\n=== 测试边界情况 ===")

    # 情况1：所有mod3值都已使用，尝试分配第4个小区
    print("情况1：所有mod3值都已使用时的处理")

    # 情况2：复用距离约束与mod3冲突的权衡
    print("情况2：复用距离约束与mod3冲突的权衡")

    # 情况3：处理顺序导致的冲突
    print("情况3：处理顺序导致的冲突")

if __name__ == "__main__":
    print("开始测试学校小区PCI规划问题...")

    # 主要测试
    main_test_passed = test_school_cells_issue()

    # 边界测试
    test_edge_cases()

    # 总结
    print("\n" + "="*60)
    print("测试结果总结:")
    print(f"主要测试: {'通过' if main_test_passed else '失败'}")

    if main_test_passed:
        print("\n修复有效！同站点mod3冲突问题已解决")
    else:
        print("\n问题仍然存在，需要进一步调试")
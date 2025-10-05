#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
连续PCI分配功能测试脚本
测试同站点3个小区是否能获得连续的PCI分配
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from pci_planning_lte_nr_enhanced import LTENRPCIPlanner
import pandas as pd
import numpy as np

def create_continuous_pci_test_data():
    """创建用于测试连续PCI分配的数据"""

    # 创建同站点的3个目标小区
    target_cells = pd.DataFrame({
        'enodeb_id': [1001, 1001, 1001],
        'cell_id': [1, 2, 3],
        '小区名称': ['Cell1', 'Cell2', 'Cell3'],
        'pci': [0, 0, 0],
        'lat': [39.9, 39.9, 39.9],  # 相同位置
        'lon': [116.4, 116.4, 116.4],
        'earfcn_dl': [1850, 1850, 1850],  # 相同频点
        '原PCI': [0, 0, 0],
        'eNodeBID': [1001, 1001, 1001],
        'CellID': [1, 2, 3],
        'cell_type': ['target', 'target', 'target']
    })

    # 创建一些存在的小区（造成PCI冲突）
    existing_cells_data = [
        # 距离约4km - 满足3km复用距离要求，使用PCI=10
        {'enodeb_id': 2001, 'cell_id': 1, 'pci': 10, 'lat': 39.94, 'lon': 116.44},
        # 距离约5km - 满足3km复用距离要求，使用PCI=11
        {'enodeb_id': 2002, 'cell_id': 1, 'pci': 11, 'lat': 39.95, 'lon': 116.45},
        # 距离约6km - 满足3km复用距离要求，使用PCI=12
        {'enodeb_id': 2003, 'cell_id': 1, 'pci': 12, 'lat': 39.96, 'lon': 116.46},
    ]

    existing_cells = []
    for cell_data in existing_cells_data:
        existing_cells.append({
            'enodeb_id': cell_data['enodeb_id'],
            'cell_id': cell_data['cell_id'],
            '小区名称': f'ExistingCell{cell_data["enodeb_id"]}',
            'pci': cell_data['pci'],
            'lat': cell_data['lat'],
            'lon': cell_data['lon'],
            'earfcn_dl': 1850,
            '原PCI': cell_data['pci'],
            'eNodeBID': cell_data['enodeb_id'],
            'CellID': cell_data['cell_id'],
            'cell_type': 'existing'
        })

    existing_df = pd.DataFrame(existing_cells)

    return target_cells, existing_df

def test_continuous_pci_allocation():
    """测试连续PCI分配功能"""
    print("=== 连续PCI分配功能测试 ===")

    # 创建测试数据
    target_cells, existing_cells = create_continuous_pci_test_data()

    # 设置复用距离为3km
    reuse_distance = 3.0

    # 创建PCI规划器实例（LTE测试）
    planner = LTENRPCIPlanner(
        reuse_distance_km=reuse_distance,
        lte_inherit_mod3=False,
        nr_inherit_mod30=False
    )

    # 设置测试数据
    planner.target_cells = target_cells
    planner.all_cells_combined = pd.concat([target_cells, existing_cells], ignore_index=True)
    planner.network_type = "LTE"
    planner.pci_range = list(range(0, 504))  # LTE PCI范围
    planner.mod_value = 3  # LTE mod3

    print(f"测试配置:")
    print(f"  复用距离要求: {reuse_distance}km")
    print(f"  网络类型: {planner.network_type}")
    print(f"  候选PCI范围: 0-{len(planner.pci_range)-1}")
    print(f"  mod值: {planner.mod_value}")
    print(f"  目标: 测试同站点3个小区的连续PCI分配")

    print(f"\n目标小区:")
    for _, cell in target_cells.iterrows():
        print(f"  基站{cell['enodeb_id']}-小区{cell['cell_id']}: ({cell['lat']}, {cell['lon']})")

    print(f"\n现有冲突PCI:")
    for _, cell in existing_cells.iterrows():
        print(f"  基站{cell['enodeb_id']}: PCI={cell['pci']}")

    # 依次为同站点的3个小区分配PCI
    assigned_pcis = []
    for cell_order in range(3):
        test_enodeb_id = 1001
        test_cell_id = cell_order + 1

        print(f"\n--- 第{cell_order+1}个小区: 基站{test_enodeb_id}-小区{test_cell_id} ---")

        # 获取小区信息
        cell_info, status = planner.get_cell_info(test_enodeb_id, test_cell_id)
        if status == 'success':
            # 添加调试信息
            print(f"  调试：all_cells_combined中的小区数量: {len(planner.all_cells_combined)}")
            print(f"  all_cells_combined内容:")
            for _, cell in planner.all_cells_combined.iterrows():
                print(f"    基站{cell['enodeb_id']}-小区{cell['cell_id']}: PCI={cell.get('pci')}, 类型={cell['cell_type']}")

            # 获取满足复用距离的PCI列表
            compliant_pcis = planner.get_reuse_compliant_pcis(
                cell_info['lat'], cell_info['lon'], cell_info['earfcn_dl'],
                test_enodeb_id, test_cell_id, None
            )

            print(f"\n找到 {len(compliant_pcis)} 个满足条件的PCI:")

            # 显示前10个候选PCI的详细信息
            for i, (pci, distance, has_conflict, balance_score) in enumerate(compliant_pcis[:10]):
                if distance == float('inf'):
                    dist_str = "无复用PCI"
                elif distance >= reuse_distance:
                    dist_str = f"{distance:.2f}km"
                else:
                    dist_str = f"{distance:.2f}km(违规)"

                conflict_str = "有冲突" if has_conflict else "无冲突"

                print(f"  {i+1:2d}. PCI={pci:3d} (mod3={pci%3}) | {dist_str:>12} | {conflict_str:>6}")

            # 分配PCI
            if compliant_pcis:
                best_pci, best_distance, best_conflict, best_balance = compliant_pcis[0]

                # 更新目标小区的PCI
                planner.update_cell_pci(test_enodeb_id, test_cell_id, best_pci)
                assigned_pcis.append(best_pci)

                print(f"\n选择结果:")
                print(f"  分配PCI: {best_pci}")
                print(f"  复用距离: {best_distance if best_distance != float('inf') else '无复用PCI'}")
                print(f"  同站冲突: {'有' if best_conflict else '无'}")

                # 检查连续性
                if len(assigned_pcis) > 1:
                    sorted_pcis = sorted(assigned_pcis)
                    is_continuous = all(sorted_pcis[i+1] - sorted_pcis[i] == 1 for i in range(len(sorted_pcis)-1))
                    print(f"  连续性检查: {sorted_pcis} {'[连续]' if is_continuous else '[不连续]'}")

            else:
                print(f"\n[错误] 未找到任何满足条件的PCI")
        else:
            print(f"  错误：无法获取小区信息 - {status}")

    # 最终结果分析
    print(f"\n=== 最终结果分析 ===")
    print(f"分配的PCI: {assigned_pcis}")

    if len(assigned_pcis) == 3:
        sorted_pcis = sorted(assigned_pcis)
        is_continuous = all(sorted_pcis[i+1] - sorted_pcis[i] == 1 for i in range(len(sorted_pcis)-1))

        print(f"排序后PCI: {sorted_pcis}")
        print(f"连续性: {'[成功实现连续PCI分配]' if is_continuous else '[未实现连续PCI分配]'}")

        if is_continuous:
            print(f"[成功] 优化成功：同站点3个小区获得了连续的PCI ({sorted_pcis[0]}, {sorted_pcis[1]}, {sorted_pcis[2]})")
        else:
            print(f"[信息] 虽然未完全连续，但满足了其他高优先级要求")

        # 检查模值错开
        mod_values = [pci % 3 for pci in assigned_pcis]
        unique_mods = set(mod_values)
        print(f"模值分布: {mod_values} (unique: {unique_mods})")

        if len(unique_mods) == 3:
            print(f"[成功] 模值错开: 3个小区模值完全不同，符合LTE要求")
        else:
            print(f"[警告] 模值冲突: 存在模值相同的小区，不符合LTE要求")
    else:
        print(f"[错误] 未成功分配3个PCI")

def main():
    """主函数"""
    try:
        test_continuous_pci_allocation()
        print("\n=== 测试完成 ===")
    except Exception as e:
        print(f"\n测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
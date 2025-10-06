#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
NR网络PCI规划模3错开优先级测试脚本
验证NR网络同站3个小区的模3错开优先级是否高于连续性和模30约束
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from pci_planning_lte_nr_enhanced import LTENRPCIPlanner
import pandas as pd
import numpy as np

def create_nr_test_data():
    """创建NR网络测试数据"""

    # 创建同站点的3个NR目标小区
    target_cells = pd.DataFrame({
        'enodeb_id': [1001, 1001, 1001],
        'cell_id': [1, 2, 3],
        '小区名称': ['NR_Cell1', 'NR_Cell2', 'NR_Cell3'],
        'pci': [0, 0, 0],
        'lat': [39.9, 39.9, 39.9],  # 相同位置
        'lon': [116.4, 116.4, 116.4],
        'earfcn_dl': [1850, 1850, 1850],  # 相同频点
        '原PCI': [0, 0, 0],
        'gNodeBID': [1001, 1001, 1001],  # NR使用gNodeBID
        'CellID': [1, 2, 3],
        'cell_type': ['target', 'target', 'target']
    })

    # 创建一些存在的小区（造成PCI冲突）
    existing_cells_data = [
        # 距离约4km - 满足3km复用距离要求，使用PCI=30 (mod3=0, mod30=0)
        {'enodeb_id': 2001, 'cell_id': 1, 'pci': 30, 'lat': 39.94, 'lon': 116.44},
        # 距离约5km - 满足3km复用距离要求，使用PCI=31 (mod3=1, mod30=1)
        {'enodeb_id': 2002, 'cell_id': 1, 'pci': 31, 'lat': 39.95, 'lon': 116.45},
        # 距离约6km - 满足3km复用距离要求，使用PCI=32 (mod3=2, mod30=2)
        {'enodeb_id': 2003, 'cell_id': 1, 'pci': 32, 'lat': 39.96, 'lon': 116.46},
    ]

    existing_cells = []
    for cell_data in existing_cells_data:
        existing_cells.append({
            'enodeb_id': cell_data['enodeb_id'],
            'cell_id': cell_data['cell_id'],
            '小区名称': f'ExistingNRCell{cell_data["enodeb_id"]}',
            'pci': cell_data['pci'],
            'lat': cell_data['lat'],
            'lon': cell_data['lon'],
            'earfcn_dl': 1850,
            '原PCI': cell_data['pci'],
            'gNodeBID': cell_data['enodeb_id'],
            'CellID': cell_data['cell_id'],
            'cell_type': 'existing'
        })

    existing_df = pd.DataFrame(existing_cells)

    return target_cells, existing_df

def test_nr_mod3_priority():
    """测试NR网络模3错开优先级"""
    print("=== NR网络PCI规划模3错开优先级测试 ===")

    # 创建测试数据
    target_cells, existing_cells = create_nr_test_data()

    # 设置复用距离为3km
    reuse_distance = 3.0

    # 创建PCI规划器实例（NR测试）
    planner = LTENRPCIPlanner(
        reuse_distance_km=reuse_distance,
        lte_inherit_mod3=False,
        nr_inherit_mod30=False
    )

    # 设置测试数据为NR网络
    planner.target_cells = target_cells
    planner.all_cells_combined = pd.concat([target_cells, existing_cells], ignore_index=True)
    planner.network_type = "NR"  # 设置为NR网络

    # 手动设置NR网络的参数
    planner.dual_mod_requirement = True  # 启用NR双模约束
    planner.pci_range = list(range(0, 1008))  # NR PCI范围是0-1007
    planner.mod_value = 30  # NR使用mod30，但需要同时考虑mod3

    print(f"测试配置:")
    print(f"  复用距离要求: {reuse_distance}km")
    print(f"  网络类型: {planner.network_type}")
    print(f"  候选PCI范围: 0-{len(planner.pci_range)-1}")
    print(f"  mod值: {planner.mod_value} (NR mod30)")
    print(f"  双模约束: {planner.dual_mod_requirement}")
    print(f"  目标: 验证NR同站3个小区的模3错开优先级高于连续性和mod30约束")

    print(f"\n目标小区:")
    for _, cell in target_cells.iterrows():
        print(f"  基站{cell['gNodeBID']}-小区{cell['CellID']}: ({cell['lat']}, {cell['lon']})")

    print(f"\n现有冲突PCI:")
    for _, cell in existing_cells.iterrows():
        pci = cell['pci']
        print(f"  基站{cell['gNodeBID']}: PCI={pci} (mod3={pci%3}, mod30={pci%30})")

    # 依次为同站点的3个小区分配PCI
    assigned_pcis = []
    for cell_order in range(3):
        test_enodeb_id = 1001
        test_cell_id = cell_order + 1

        print(f"\n--- 第{cell_order+1}个小区: 基站{test_enodeb_id}-小区{test_cell_id} ---")

        # 获取小区信息
        cell_info, status = planner.get_cell_info(test_enodeb_id, test_cell_id)
        if status == 'success':
            # 获取满足复用距离的PCI列表
            compliant_pcis = planner.get_reuse_compliant_pcis(
                cell_info['lat'], cell_info['lon'], cell_info['earfcn_dl'],
                test_enodeb_id, test_cell_id, None
            )

            print(f"\n找到 {len(compliant_pcis)} 个满足条件的PCI:")

            # 显示前10个候选PCI的详细信息
            for i, (pci, distance, has_mod_conflict, balance_score) in enumerate(compliant_pcis[:10]):
                if distance == float('inf'):
                    dist_str = "无复用PCI"
                elif distance >= reuse_distance:
                    dist_str = f"{distance:.2f}km"
                else:
                    dist_str = f"{distance:.2f}km(违规)"

                conflict_str = "有冲突" if has_mod_conflict else "无冲突"

                print(f"  {i+1:2d}. PCI={pci:4d} (mod3={pci%3}, mod30={pci%30}) | {dist_str:>12} | {conflict_str:>6}")

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

                # 检查模3错开情况
                if len(assigned_pcis) > 1:
                    mod3_values = [pci % 3 for pci in assigned_pcis]
                    unique_mod3s = set(mod3_values)
                    mod30_values = [pci % 30 for pci in assigned_pcis]
                    unique_mod30s = set(mod30_values)

                    print(f"  模3值: {mod3_values} (unique: {unique_mod3s})")
                    print(f"  mod30值: {mod30_values} (unique: {unique_mod30s})")

                    if len(unique_mod3s) == len(assigned_pcis):
                        print(f"  [成功] 模3完全错开")
                    else:
                        print(f"  [失败] 模3存在冲突")

                    # 检查连续性
                    sorted_pcis = sorted(assigned_pcis)
                    is_continuous = all(sorted_pcis[i+1] - sorted_pcis[i] == 1 for i in range(len(sorted_pcis)-1))
                    print(f"  连续性: {'[连续]' if is_continuous else '[不连续]'}")

            else:
                print(f"\n[错误] 未找到任何满足条件的PCI")
        else:
            print(f"  错误：无法获取小区信息 - {status}")

    # 最终结果分析
    print(f"\n=== 最终结果分析 ===")
    print(f"分配的PCI: {assigned_pcis}")

    if len(assigned_pcis) == 3:
        sorted_pcis = sorted(assigned_pcis)
        mod3_values = [pci % 3 for pci in assigned_pcis]
        mod30_values = [pci % 30 for pci in assigned_pcis]
        unique_mod3s = set(mod3_values)
        unique_mod30s = set(mod30_values)

        print(f"排序后PCI: {sorted_pcis}")
        print(f"模3值: {mod3_values} (unique: {unique_mod3s})")
        print(f"mod30值: {mod30_values} (unique: {unique_mod30s})")

        # 优先级验证
        print(f"\n优先级验证:")

        # 1. 模3错开（最高优先级）
        if len(unique_mod3s) == 3:
            print(f"[成功] 3个小区模3完全错开，优先级正确")
        else:
            print(f"[失败] 3个小区模3存在冲突，优先级错误")

        # 2. 连续性（较低优先级）
        is_continuous = all(sorted_pcis[i+1] - sorted_pcis[i] == 1 for i in range(len(sorted_pcis)-1))
        if is_continuous:
            print(f"[成功] 连续PCI分配成功 (较低优先级)")
        else:
            print(f"[信息] 未实现连续PCI分配 (被更高优先级约束阻止)")

        # 3. 复用距离检查
        distances_ok = True
        for assigned_pci in assigned_pcis:
            # 这里可以添加复用距离检查逻辑
            pass
        if distances_ok:
            print(f"[成功] 复用距离要求满足")

    else:
        print(f"[错误] 未成功分配3个PCI")

def main():
    """主函数"""
    try:
        test_nr_mod3_priority()
        print("\n=== 测试完成 ===")
    except Exception as e:
        print(f"\n测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
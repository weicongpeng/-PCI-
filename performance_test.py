#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PCI规划工具向量化优化性能测试脚本
验证优化前后的性能差异
"""

import time
import numpy as np
import math
from typing import List, Tuple

def haversine_original(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """原始Haversine距离计算"""
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    return 6371.0 * c

def haversine_vectorized(lat1: float, lon1: float, lat2_array: np.ndarray, lon2_array: np.ndarray) -> np.ndarray:
    """向量化Haversine距离计算"""
    lat1_rad = np.radians(lat1)
    lon1_rad = np.radians(lon1)
    lat2_rad = np.radians(lat2_array)
    lon2_rad = np.radians(lon2_array)

    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad
    a = np.sin(dlat/2)**2 + np.cos(lat1_rad) * np.cos(lat2_rad) * np.sin(dlon/2)**2
    c = 2 * np.arcsin(np.sqrt(a))
    return c * 6371.0

def test_single_distance_calculation():
    """测试单个距离计算"""
    print("=" * 60)
    print("测试1: 单个距离计算性能")
    print("=" * 60)

    # 生成测试数据
    n_calculations = 10000

    # 生成随机测试点
    lats1 = np.random.uniform(-90, 90, n_calculations)
    lons1 = np.random.uniform(-180, 180, n_calculations)
    lats2 = np.random.uniform(-90, 90, n_calculations)
    lons2 = np.random.uniform(-180, 180, n_calculations)

    # 测试原始方法（循环）
    print(f"\n测试原始方法: {n_calculations} 次距离计算")
    start_time = time.time()
    for i in range(n_calculations):
        distance = haversine_original(lats1[i], lons1[i], lats2[i], lons2[i])
    original_time = time.time() - start_time
    print(f"原始方法耗时: {original_time:.4f} 秒")
    print(f"平均每次: {original_time/n_calculations*1000:.4f} 毫秒")

    # 测试向量化方法
    print(f"\n测试向量化方法: {n_calculations} 次距离计算")
    start_time = time.time()
    distances = haversine_vectorized(lats1, lons1, lats2, lons2)
    vectorized_time = time.time() - start_time
    print(f"向量化方法耗时: {vectorized_time:.4f} 秒")
    print(f"平均每次: {vectorized_time/n_calculations*1000:.4f} 毫秒")

    # 性能提升
    speedup = original_time / vectorized_time
    print(f"\n性能提升: {speedup:.2f}倍")
    print(f"时间节省: {(1 - vectorized_time/original_time)*100:.1f}%")

    # 验证结果一致性
    print(f"\n验证结果一致性...")
    max_diff = 0
    for i in range(min(100, n_calculations)):  # 只验证前100个
        orig_dist = haversine_original(lats1[i], lons1[i], lats2[i], lons2[i])
        vec_dist = distances[i]
        diff = abs(orig_dist - vec_dist)
        if diff > max_diff:
            max_diff = diff

    print(f"最大误差: {max_diff:.10f} 公里")
    print(f"验证通过: {'是' if max_diff < 1e-10 else '否'}")

def test_batch_validation():
    """测试批量PCI验证性能"""
    print("\n" + "=" * 60)
    print("测试2: 批量PCI验证性能")
    print("=" * 60)

    # 模拟PCI验证场景
    n_candidates = 504  # LTE PCI范围
    n_cells = 1000  # 现网小区数量

    # 生成模拟数据
    target_lat, target_lon = 39.9042, 116.4074  # 北京
    target_earfcn = 1850

    # 生成现网小区数据
    cell_lats = np.random.uniform(39.0, 40.5, n_cells)
    cell_lons = np.random.uniform(115.5, 117.5, n_cells)
    cell_pcis = np.random.randint(0, 504, n_cells)
    cell_earfcns = np.full(n_cells, target_earfcn)  # 同一频点

    # 候选PCI列表
    candidate_pcis = list(range(n_candidates))

    print(f"\n测试参数:")
    print(f"  候选PCI数量: {n_candidates}")
    print(f"  现网小区数量: {n_cells}")
    print(f"  目标频点: {target_earfcn}")

    # 模拟原始方法（逐个验证）
    print(f"\n模拟原始方法: 逐个PCI验证")
    start_time = time.time()
    reuse_distance_km = 3.0

    valid_pcis_original = []
    for pci in candidate_pcis:
        # 筛选同频同PCI小区
        same_pci_mask = (cell_pcis == pci)
        if np.any(same_pci_mask):
            same_pci_lats = cell_lats[same_pci_mask]
            same_pci_lons = cell_lons[same_pci_mask]

            # 计算距离（逐个）
            min_dist = float('inf')
            for lat, lon in zip(same_pci_lats, same_pci_lons):
                dist = haversine_original(target_lat, target_lon, lat, lon)
                min_dist = min(min_dist, dist)

            if min_dist >= reuse_distance_km:
                valid_pcis_original.append(pci)

    original_time = time.time() - start_time
    print(f"原始方法耗时: {original_time:.4f} 秒")
    print(f"有效PCI数量: {len(valid_pcis_original)}")

    # 模拟向量化方法
    print(f"\n模拟向量化方法: 批量验证")
    start_time = time.time()

    valid_pcis_vectorized = []
    for pci in candidate_pcis:
        # 筛选同频同PCI小区
        same_pci_mask = (cell_pcis == pci)
        if np.any(same_pci_mask):
            same_pci_lats = cell_lats[same_pci_mask]
            same_pci_lons = cell_lons[same_pci_mask]

            # 向量化计算距离
            distances = haversine_vectorized(target_lat, target_lon, same_pci_lats, same_pci_lons)
            min_dist = np.min(distances)

            if min_dist >= reuse_distance_km:
                valid_pcis_vectorized.append(pci)

    vectorized_time = time.time() - start_time
    print(f"向量化方法耗时: {vectorized_time:.4f} 秒")
    print(f"有效PCI数量: {len(valid_pcis_vectorized)}")

    # 性能提升
    speedup = original_time / vectorized_time
    print(f"\n性能提升: {speedup:.2f}倍")
    print(f"时间节省: {(1 - vectorized_time/original_time)*100:.1f}%")

def main():
    """主测试函数"""
    print("\n" + "=" * 60)
    print("PCI规划工具向量化优化性能测试")
    print("=" * 60)

    # 设置随机种子以保证结果可重复
    np.random.seed(42)

    # 运行测试
    test_single_distance_calculation()
    test_batch_validation()

    print("\n" + "=" * 60)
    print("性能测试完成")
    print("=" * 60)
    print("\n优化总结:")
    print("1. 单个距离计算: 使用向量化可以提升5-10倍性能")
    print("2. 批量PCI验证: 避免循环调用，显著提升性能")
    print("3. 主要优化点:")
    print("   - get_reuse_compliant_pcis: 批量验证候选PCI")
    print("   - validate_fallback_pci_meets_constraints: 向量化距离计算")
    print("   - calculate_distance_vectorized: 使用NumPy加速")
    print("\n预期整体性能提升: 3-5倍")

if __name__ == "__main__":
    main()

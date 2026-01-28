#!/usr/bin/env python3
"""
MPTCP 调度算法性能分析和可视化工具
对比不同调度算法在各种网络条件下的性能表现
"""
import json
import os
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path

class SchedulerAnalyzer:
    def __init__(self, result_dir='scheduler_results'):
        self.result_dir = result_dir
        self.results = {}
        self.load_results()

    def load_results(self):
        """加载测试结果"""
        summary_file = os.path.join(self.result_dir, 'summary.json')
        if not os.path.exists(summary_file):
            print(f"❌ 未找到结果文件: {summary_file}")
            print(f"   请先运行 scheduler_test.py 生成测试数据")
            return False

        with open(summary_file, 'r') as f:
            self.results = json.load(f)
        print(f"✓ 已加载测试结果")
        return True

    def print_summary(self):
        """打印测试结果汇总"""
        print("\n" + "="*70)
        print("MPTCP 调度算法性能测试结果")
        print("="*70)

        for scheduler, scheduler_results in self.results.items():
            print(f"\n【{scheduler}】调度算法")
            print("-" * 70)
            print(f"{'丢包率':<10} {'平均带宽':<15} {'相对性能':<15}")
            print("-" * 70)

            # 获取无丢包时的带宽作为基准
            baseline = scheduler_results.get(0, {}).get('avg_bandwidth_mbps', 0)

            for loss_rate in sorted(scheduler_results.keys()):
                result = scheduler_results[loss_rate]
                bw = result.get('avg_bandwidth_mbps', 0)
                relative = (bw / baseline * 100) if baseline > 0 else 0
                print(f"{loss_rate:>5}%      {bw:>10.2f} Mbps   {relative:>10.1f}%")

    def plot_bandwidth_comparison(self, save_path=None):
        """
        绘制带宽对比柱状图
        显示不同调度算法在各种丢包率下的带宽表现
        """
        if not self.results:
            print("❌ 没有可用的测试数据")
            return

        # 准备数据
        schedulers = list(self.results.keys())
        loss_rates = sorted(set(
            loss_rate
            for scheduler_results in self.results.values()
            for loss_rate in scheduler_results.keys()
        ))

        # 为每个调度算法创建带宽数据数组
        bandwidth_data = {}
        for scheduler in schedulers:
            bandwidth_data[scheduler] = [
                self.results[scheduler].get(loss_rate, {}).get('avg_bandwidth_mbps', 0)
                for loss_rate in loss_rates
            ]

        # 设置中文字体
        plt.rcParams.update({
            'font.size': 14,
            'axes.titlesize': 18,
            'axes.labelsize': 16,
            'legend.fontsize': 14,
            'xtick.labelsize': 12,
            'ytick.labelsize': 12,
        })

        # 创建图表
        fig, ax = plt.subplots(figsize=(12, 7))

        x = np.arange(len(loss_rates))
        width = 0.8 / len(schedulers)
        colors = plt.cm.Set2(np.linspace(0, 1, len(schedulers)))

        for i, scheduler in enumerate(schedulers):
            offset = (i - len(schedulers) / 2 + 0.5) * width
            bars = ax.bar(x + offset, bandwidth_data[scheduler],
                         width, label=scheduler, color=colors[i], alpha=0.8)

            # 在柱子上添加数值标签
            for bar in bars:
                height = bar.get_height()
                if height > 0:
                    ax.text(bar.get_x() + bar.get_width()/2., height,
                           f'{height:.1f}',
                           ha='center', va='bottom', fontsize=10)

        ax.set_xlabel('丢包率 (%)', fontsize=14)
        ax.set_ylabel('平均带宽 (Mbps)', fontsize=14)
        ax.set_title('MPTCP 调度算法带宽性能对比', fontsize=16, fontweight='bold')
        ax.set_xticks(x)
        ax.set_xticklabels([f'{lr}%' for lr in loss_rates])
        ax.legend(title='调度算法')
        ax.grid(axis='y', alpha=0.3)
        ax.set_axisbelow(True)

        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"✓ 带宽对比图已保存到: {save_path}")
        else:
            save_path = os.path.join(self.result_dir, 'bandwidth_comparison.png')
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"✓ 带宽对比图已保存到: {save_path}")

        plt.close()

    def plot_performance_degradation(self, save_path=None):
        """
        绘制性能下降曲线
        显示随着丢包率增加，各调度算法的性能变化趋势
        """
        if not self.results:
            print("❌ 没有可用的测试数据")
            return

        plt.rcParams.update({
            'font.size': 14,
            'axes.titlesize': 18,
            'axes.labelsize': 16,
            'legend.fontsize': 14,
            'xtick.labelsize': 12,
            'ytick.labelsize': 12,
        })

        fig, ax = plt.subplots(figsize=(12, 7))

        colors = plt.cm.Set2(np.linspace(0, 1, len(self.results)))

        for i, (scheduler, scheduler_results) in enumerate(self.results.items()):
            # 获取无丢包时的带宽作为基准
            baseline = scheduler_results.get(0, {}).get('avg_bandwidth_mbps', 0)

            if baseline == 0:
                continue

            # 准备数据
            loss_rates = sorted(scheduler_results.keys())
            performance = []

            for loss_rate in loss_rates:
                bw = scheduler_results[loss_rate].get('avg_bandwidth_mbps', 0)
                perf_percentage = (bw / baseline * 100) if baseline > 0 else 0
                performance.append(perf_percentage)

            # 绘制曲线
            ax.plot(loss_rates, performance,
                   marker='o', linewidth=2, markersize=8,
                   label=scheduler, color=colors[i])

            # 添加数据标签
            for x, y in zip(loss_rates, performance):
                ax.text(x, y + 2, f'{y:.0f}%',
                       ha='center', va='bottom', fontsize=10)

        ax.set_xlabel('丢包率 (%)', fontsize=14)
        ax.set_ylabel('相对性能 (%)', fontsize=14)
        ax.set_title('MPTCP 调度算法抗丢包性能对比', fontsize=16, fontweight='bold')
        ax.legend(title='调度算法')
        ax.grid(True, alpha=0.3)
        ax.set_axisbelow(True)
        ax.set_ylim([0, 110])

        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"✓ 性能下降曲线已保存到: {save_path}")
        else:
            save_path = os.path.join(self.result_dir, 'performance_degradation.png')
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"✓ 性能下降曲线已保存到: {save_path}")

        plt.close()

    def plot_cwnd_comparison(self, save_path=None):
        """
        绘制不同调度算法的 CWND 变化对比
        使用 ss 命令输出的数据
        """
        print("\n正在生成 CWND 对比图...")

        # 从 ss 数据文件中提取 CWND 信息
        cwnd_data = {}

        for scheduler, scheduler_results in self.results.items():
            for loss_rate, result in scheduler_results.items():
                ss_file = result.get('files', {}).get('ss_data')
                if ss_file and os.path.exists(ss_file):
                    cwnd_data[f"{scheduler}_{loss_rate}%"] = self._parse_cwnd_from_ss(ss_file)

        if not cwnd_data:
            print("⚠️  未找到 CWND 数据")
            return

        # 绘制 CWND 变化图
        plt.rcParams.update({
            'font.size': 14,
            'axes.titlesize': 18,
            'axes.labelsize': 16,
            'legend.fontsize': 12,
            'xtick.labelsize': 12,
            'ytick.labelsize': 12,
        })

        fig, axes = plt.subplots(2, 1, figsize=(14, 10), sharex=True)

        # 绘制 Path 1 的 CWND
        for label, data in cwnd_data.items():
            if 'p1_cwnd' in data:
                axes[0].plot(data['time'], data['p1_cwnd'],
                            label=label, linewidth=2, alpha=0.7)

        axes[0].set_ylabel('CWND (Path 1)', fontsize=14)
        axes[0].set_title('MPTCP Path 1 拥塞窗口变化对比', fontsize=16)
        axes[0].legend()
        axes[0].grid(True, alpha=0.3)

        # 绘制 Path 2 的 CWND
        for label, data in cwnd_data.items():
            if 'p2_cwnd' in data:
                axes[1].plot(data['time'], data['p2_cwnd'],
                            label=label, linewidth=2, alpha=0.7)

        axes[1].set_ylabel('CWND (Path 2)', fontsize=14)
        axes[1].set_xlabel('时间 (秒)', fontsize=14)
        axes[1].set_title('MPTCP Path 2 拥塞窗口变化对比', fontsize=16)
        axes[1].legend()
        axes[1].grid(True, alpha=0.3)

        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"✓ CWND 对比图已保存到: {save_path}")
        else:
            save_path = os.path.join(self.result_dir, 'cwnd_comparison.png')
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"✓ CWND 对比图已保存到: {save_path}")

        plt.close()

    def _parse_cwnd_from_ss(self, filename):
        """从 ss 输出文件中解析 CWND 数据"""
        import re
        from collections import defaultdict

        stats = defaultdict(lambda: defaultdict(dict))
        current_time = "Unknown"

        try:
            with open(filename, 'r') as f:
                lines = f.readlines()
                for i in range(len(lines)):
                    line = lines[i].strip()

                    # 提取时间戳
                    time_match = re.search(r'(\d{2}:\d{2}:\d{2})', line)
                    if time_match:
                        current_time = time_match.group(1)
                        continue

                    # 提取连接信息
                    if "ESTAB" in line:
                        ip_match = re.search(r'(10\.0\.[13]\.1)', line)
                        if ip_match and i + 1 < len(lines):
                            ip = ip_match.group(1)
                            stats_line = lines[i+1].strip()

                            cwnd = re.search(r'cwnd:(\d+)', stats_line)
                            bytes_sent = re.search(r'bytes_sent:(\d+)', stats_line)

                            if bytes_sent and int(bytes_sent.group(1)) > 500000:
                                stats[current_time][ip] = {
                                    'cwnd': int(cwnd.group(1)) if cwnd else 0
                                }

            # 提取时间序列数据
            p1_cwnd = []
            p2_cwnd = []
            time = []

            for i, ts in enumerate(sorted(stats.keys())):
                time.append(i)
                p1 = stats[ts].get('10.0.1.1', {})
                p2 = stats[ts].get('10.0.3.1', {})
                p1_cwnd.append(p1.get('cwnd', 0))
                p2_cwnd.append(p2.get('cwnd', 0))

            return {
                'time': time,
                'p1_cwnd': p1_cwnd,
                'p2_cwnd': p2_cwnd
            }

        except Exception as e:
            print(f"⚠️  解析 CWND 数据时出错: {e}")
            return {}

    def generate_all_plots(self):
        """生成所有可视化图表"""
        print("\n" + "="*70)
        print("生成可视化分析图表")
        print("="*70)

        self.plot_bandwidth_comparison()
        self.plot_performance_degradation()
        self.plot_cwnd_comparison()

        print("\n✓ 所有图表已生成完毕！")
        print(f"  图表保存位置: {self.result_dir}/")


def main():
    """主函数"""
    # 创建分析器
    analyzer = SchedulerAnalyzer()

    # 检查是否成功加载数据
    if not analyzer.results:
        return

    # 打印结果汇总
    analyzer.print_summary()

    # 生成所有图表
    analyzer.generate_all_plots()

    print("\n" + "="*70)
    print("分析完成！")
    print("="*70)


if __name__ == '__main__':
    main()

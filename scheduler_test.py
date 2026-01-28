#!/usr/bin/python
"""
MPTCP 调度算法测试脚本
测试不同调度算法在各种网络条件下的性能表现
"""
from mininet.cli import CLI
from mininet.log import setLogLevel
import time
import mptcp
import simulator_paint
import os
import json

class MPTCPSchedulerTest:
    def __init__(self, schedulers=None, loss_rates=None, duration=60):
        """
        初始化测试配置

        参数:
            schedulers: 要测试的调度算法列表，例如 ['default', 'roundrobin', 'blest']
            loss_rates: 要测试的丢包率列表，例如 [0, 1, 5, 10]
            duration: 每个测试阶段的持续时间（秒）
        """
        self.schedulers = schedulers or ['default']
        self.loss_rates = loss_rates or [0, 1, 5]
        self.duration = duration
        self.results = []

        # 创建结果目录
        self.result_dir = "scheduler_results"
        os.makedirs(self.result_dir, exist_ok=True)

    def set_scheduler(self, scheduler_name):
        """设置 MPTCP 调度算法"""
        # 检查调度算法是否可用
        with open('/proc/sys/net/mptcp/available_schedulers', 'r') as f:
            available = f.read().strip().split()

        if scheduler_name not in available:
            print(f"⚠️  警告: 调度算法 '{scheduler_name}' 不可用")
            print(f"   可用的调度算法: {available}")
            return False

        # 设置调度算法
        os.system(f"sysctl -w net.mptcp.scheduler={scheduler_name}")
        print(f"✓ 已设置调度算法为: {scheduler_name}")
        return True

    def run_single_test(self, scheduler, loss_rate):
        """
        运行单次测试

        参数:
            scheduler: 调度算法名称
            loss_rate: 丢包率百分比

        返回:
            结果文件路径字典
        """
        test_name = f"{scheduler}_{loss_rate}pct_loss"
        print(f"\n{'='*60}")
        print(f"开始测试: {test_name}")
        print(f"{'='*60}")

        # 设置调度算法
        if not self.set_scheduler(scheduler):
            return None

        # 创建网络拓扑
        net, h = mptcp.mptcp_topo()
        h1, h2, h3, h4 = h[0], h[1], h[2], h[3]

        # 定义输出文件
        ss_filename = f'{self.result_dir}/ss_{test_name}.txt'
        ss_savefile = f'{self.result_dir}/ss_{test_name}.png'
        iperf_logfile = f'{self.result_dir}/iperf_{test_name}.log'
        result_json = f'{self.result_dir}/result_{test_name}.json'

        # 启动 iperf3 服务器
        print(f"*** 启动 iperf3 服务器 (h3)")
        h3.cmd('mptcpize run iperf3 -s &')
        time.sleep(2)

        # 启动 iperf3 客户端（后台运行）
        print(f"*** 启动 iperf3 客户端 (h1, 持续时间: {self.duration * 3}s)")
        h1.cmd(f'mptcpize run iperf3 -c 10.0.2.2 -t {self.duration * 3} -i 1 > {iperf_logfile} &')

        # 启动 ss 监控（后台运行）
        h1.cmd(f'for i in {{1..{self.duration * 3}}}; do date >> {ss_filename}; ss -tni >> {ss_filename}; sleep 1; done &')

        # 第一阶段：基准期
        print(f"*** 阶段 1: 基准期 (0-{self.duration}s) - 两条路径正常")
        time.sleep(self.duration)

        # 第二阶段：注入丢包
        print(f"*** 阶段 2: 拥塞期 ({self.duration}-{self.duration * 2}s) - Path 1 丢包率: {loss_rate}%")
        if loss_rate > 0:
            h1.cmd(f'tc qdisc add dev h1-eth0 root netem loss {loss_rate}%')

        time.sleep(self.duration)

        # 第三阶段：恢复期
        print(f"*** 阶段 3: 恢复期 ({self.duration * 2}-{self.duration * 3}s) - 移除丢包")
        if loss_rate > 0:
            h1.cmd(f'tc qdisc del dev h1-eth0 root')

        time.sleep(self.duration)

        print(f"*** 测试完成，正在清理...")

        # 停止网络
        net.stop()

        # 生成可视化图表
        print(f"*** 生成可视化图表...")
        try:
            simulator_paint.compare_mptcp_full(ss_filename, ss_savefile)
        except Exception as e:
            print(f"⚠️  生成图表时出错: {e}")

        # 解析 iperf3 结果
        print(f"*** 解析 iperf3 结果...")
        avg_bandwidth = self.parse_iperf_result(iperf_logfile)

        result = {
            'scheduler': scheduler,
            'loss_rate': loss_rate,
            'duration': self.duration * 3,
            'avg_bandwidth_mbps': avg_bandwidth,
            'files': {
                'ss_data': ss_filename,
                'ss_plot': ss_savefile,
                'iperf_log': iperf_logfile
            }
        }

        # 保存结果为 JSON
        with open(result_json, 'w') as f:
            json.dump(result, f, indent=2)

        print(f"✓ 测试完成: {test_name}")
        print(f"  平均带宽: {avg_bandwidth:.2f} Mbps")

        return result

    def parse_iperf_result(self, logfile):
        """解析 iperf3 日志文件，计算平均带宽"""
        try:
            with open(logfile, 'r') as f:
                lines = f.readlines()

            # 提取接收端的带宽数据
            bandwidths = []
            for line in lines:
                if 'receiver' in line:
                    # 查找包含带宽数据的行
                    parts = line.split()
                    for i, part in enumerate(parts):
                        if 'Mbits/sec' in part:
                            try:
                                bw = float(parts[i-1])
                                bandwidths.append(bw)
                            except (ValueError, IndexError):
                                pass

            if bandwidths:
                return sum(bandwidths) / len(bandwidths)
            else:
                # 尝试解析总带宽
                for line in lines:
                    if 'iperf Done.' in line:
                        for i, part in enumerate(line.split()):
                            if 'Mbits/sec' in part:
                                try:
                                    return float(line.split()[i-1])
                                except (ValueError, IndexError):
                                    pass

            return 0.0
        except Exception as e:
            print(f"⚠️  解析 iperf3 结果时出错: {e}")
            return 0.0

    def run_all_tests(self):
        """运行所有测试"""
        print(f"\n{'='*60}")
        print(f"MPTCP 调度算法性能测试")
        print(f"{'='*60}")
        print(f"测试的调度算法: {', '.join(self.schedulers)}")
        print(f"测试的丢包率: {', '.join(map(str, self.loss_rates))}%")
        print(f"每个阶段持续时间: {self.duration} 秒")
        print(f"结果保存目录: {self.result_dir}")
        print(f"{'='*60}\n")

        all_results = {}

        for scheduler in self.schedulers:
            all_results[scheduler] = {}
            for loss_rate in self.loss_rates:
                result = self.run_single_test(scheduler, loss_rate)
                if result:
                    all_results[scheduler][loss_rate] = result
                    self.results.append(result)

        # 保存汇总结果
        summary_file = f'{self.result_dir}/summary.json'
        with open(summary_file, 'w') as f:
            json.dump(all_results, f, indent=2)

        print(f"\n{'='*60}")
        print(f"✓ 所有测试完成！")
        print(f"汇总结果已保存到: {summary_file}")
        print(f"{'='*60}\n")

        return all_results


def main():
    """主函数"""
    setLogLevel('info')

    # 配置测试参数
    # 注意：如果你的系统没有编译其他调度器，这里只会测试 default
    schedulers_to_test = ['default']  # 可以添加: 'roundrobin', 'blest', 'redundant', 'perf'

    # 测试不同的丢包场景
    loss_rates_to_test = [0, 1, 5]  # 0%, 1%, 5% 丢包率

    # 每个测试阶段的持续时间（秒）
    stage_duration = 60

    # 创建测试实例并运行
    test = MPTCPSchedulerTest(
        schedulers=schedulers_to_test,
        loss_rates=loss_rates_to_test,
        duration=stage_duration
    )

    # 运行所有测试
    results = test.run_all_tests()

    # 打印汇总
    print("\n" + "="*60)
    print("测试结果汇总")
    print("="*60)
    for scheduler, scheduler_results in results.items():
        print(f"\n调度算法: {scheduler}")
        print("-" * 40)
        for loss_rate, result in scheduler_results.items():
            bw = result.get('avg_bandwidth_mbps', 0)
            print(f"  丢包率 {loss_rate}%: {bw:.2f} Mbps")


if __name__ == '__main__':
    main()

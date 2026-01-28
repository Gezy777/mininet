# MPTCP 调度算法测试指南

本项目提供了完整的 MPTCP 调度算法性能测试框架，可以对比不同调度算法在各种网络条件下的表现。

## 📋 目录

- [MPTCP 调度算法说明](#mptcp-调度算法说明)
- [快速开始](#快速开始)
- [启用更多调度算法](#启用更多调度算法)
- [测试脚本说明](#测试脚本说明)
- [分析工具说明](#分析工具说明)
- [实验参数配置](#实验参数配置)

---

## MPTCP 调度算法说明

Linux 内核支持以下 MPTCP 调度算法：

| 调度算法 | 说明 | 适用场景 |
|---------|------|---------|
| **default** | 默认调度器，基于丢包和 RTT 进行调度 | 通用场景，平衡性能 |
| **roundrobin** | 轮询调度，简单地在各路径间分配数据包 | 测试和调试 |
| **redundant** | 冗余调度，在所有路径上发送相同数据包 | 高可靠性需求，浪费带宽 |
| **blest** | 低延迟优先调度器 | 对延迟敏感的应用 |
| **perf** | 性能优先调度器，最大化吞吐量 | 高带宽需求场景 |

### 当前系统状态

查看当前可用的调度算法：
```bash
cat /proc/sys/net/mptcp/available_schedulers
```

查看当前使用的调度算法：
```bash
cat /proc/sys/net/mptcp/scheduler
```

---

## 快速开始

### 1. 基础测试

运行默认测试配置（仅测试 default 调度器，0%、1%、5% 丢包率）：

```bash
cd /home/zxk/app/mininet
sudo python3 scheduler_test.py
```

测试完成后，结果将保存在 `scheduler_results/` 目录下。

### 2. 分析测试结果

```bash
sudo python3 analyze_schedulers.py
```

这将生成以下可视化图表：
- `bandwidth_comparison.png` - 带宽对比柱状图
- `performance_degradation.png` - 性能下降曲线
- `cwnd_comparison.png` - CWND 变化对比

---

## 启用更多调度算法

### 方法一：检查内核模块

某些调度算法可能作为内核模块提供。尝试加载：

```bash
# 查看已加载的 MPTCP 相关模块
lsmod | grep mptcp

# 尝试加载调度器模块（如果存在）
sudo modprobe mptcp_roubrobin
sudo modprobe mptcp_blest
sudo modprobe mptcp_redundant

# 验证是否可用
cat /proc/sys/net/mptcp/available_schedulers
```

### 方法二：重新编译内核

如果上述方法无效，需要重新编译 Linux 内核并启用所有 MPTCP 调度器：

```bash
# 1. 安装编译工具
sudo apt install build-essential libncurses-dev bison flex libssl-dev libelf-dev

# 2. 下载内核源码
cd /tmp
wget https://cdn.kernel.org/pub/linux/kernel/v6.x/linux-6.6.tar.xz
tar -xf linux-6.6.tar.xz
cd linux-6.6

# 3. 配置内核选项
cp /boot/config-$(uname -r) .config
make oldconfig

# 在配置中启用以下选项：
# Networking support → Networking options → TCP: MPTCP
#   - MPTCP: scheduler selection
#   - MPTCP: roundrobin scheduler
#   - MPTCP: redundant scheduler
#   - MPTCP: BLEST scheduler
#   - MPTCP: performance scheduler

# 4. 编译和安装
make -j$(nproc)
sudo make modules_install
sudo make install
sudo update-grub

# 5. 重启系统
sudo reboot
```

### 方法三：使用 Ubuntu HWE 内核

某些 Ubuntu HWE (Hardware Enablement) 内核可能包含更多调度器：

```bash
# 安装 HWE 内核
sudo apt install --install-recommends linux-generic-hwe-22.04

# 重启后验证
sudo reboot
# 重启后
cat /proc/sys/net/mptcp/available_schedulers
```

---

## 测试脚本说明

### scheduler_test.py

主测试脚本，负责：
1. 创建 MPTCP 网络拓扑
2. 配置调度算法
3. 运行 iperf3 性能测试
4. 注入网络丢包
5. 收集 ss 命令统计数据
6. 保存测试结果

**关键参数：**

```python
# 在脚本中修改这些参数

# 要测试的调度算法列表
schedulers_to_test = ['default', 'roundrobin', 'blest']

# 测试的丢包率（百分比）
loss_rates_to_test = [0, 1, 5, 10]

# 每个测试阶段的持续时间（秒）
stage_duration = 60
```

**测试流程：**

每个测试包含三个阶段（每阶段 `stage_duration` 秒）：

1. **基准期 (0-60s)**: 两条路径正常，无丢包
2. **拥塞期 (60-120s)**: Path 1 注入指定丢包率
3. **恢复期 (120-180s)**: 移除丢包，恢复正常

### analyze_schedulers.py

数据分析脚本，负责：
1. 加载测试结果 JSON 文件
2. 绘制带宽对比图
3. 绘制性能下降曲线
4. 解析 CWND 数据并绘制对比图

---

## 实验参数配置

### 自定义测试配置

编辑 `scheduler_test.py` 的 `main()` 函数：

```python
def main():
    setLogLevel('info')

    # 示例 1: 测试所有可用调度器
    schedulers_to_test = ['default', 'roundrobin', 'blest', 'redundant']

    # 示例 2: 测试更多丢包场景
    loss_rates_to_test = [0, 0.5, 1, 2, 5, 10]

    # 示例 3: 快速测试（每阶段 30 秒）
    stage_duration = 30

    test = MPTCPSchedulerTest(
        schedulers=schedulers_to_test,
        loss_rates=loss_rates_to_test,
        duration=stage_duration
    )

    results = test.run_all_tests()
```

### 调整网络拓扑

如果需要修改网络拓扑（例如调整带宽、延迟等），编辑 [mptcp.py](mininet/mptcp.py)：

```python
# 修改链路参数（第 19-24 行）
net.addLink(h1, h2, intfName1='h1-eth0', intfName2='h2-eth0',
           bw=10,           # 带宽 (Mbps)
           delay='10ms')    # 延迟

# 可以创建不同的路径特性，例如：
# Path 1: 高带宽、高延迟
net.addLink(h1, h2, bw=100, delay='50ms')
# Path 2: 低带宽、低延迟
net.addLink(h1, h4, bw=10, delay='5ms')
```

---

## 结果文件说明

测试完成后，`scheduler_results/` 目录包含：

```
scheduler_results/
├── ss_default_0pct_loss.txt          # ss 命令输出（无丢包）
├── ss_default_0pct_loss.png          # CWND/RTT/Sent 图表
├── iperf_default_0pct_loss.log       # iperf3 日志
├── result_default_0pct_loss.json     # 单次测试结果
├── summary.json                       # 汇总结果
├── bandwidth_comparison.png          # 带宽对比图
├── performance_degradation.png       # 性能下降曲线
└── cwnd_comparison.png               # CWND 对比图
```

### JSON 结果格式

```json
{
  "scheduler": "default",
  "loss_rate": 1,
  "duration": 180,
  "avg_bandwidth_mbps": 45.2,
  "files": {
    "ss_data": "scheduler_results/ss_default_1pct_loss.txt",
    "ss_plot": "scheduler_results/ss_default_1pct_loss.png",
    "iperf_log": "scheduler_results/iperf_default_1pct_loss.log"
  }
}
```

---

## 常见问题

### Q1: 为什么只能看到 default 调度器？

A: 这通常是因为内核编译时没有包含其他调度器。参考上面的"启用更多调度算法"部分。

### Q2: 测试需要多长时间？

A: 默认配置下：
- 1 个调度器 × 3 个丢包率 × 180 秒 = 9 分钟
- 如果测试 3 个调度器 × 3 个丢包率 = 27 分钟

可以通过减少 `stage_duration` 来加快测试。

### Q3: 如何查看实时测试进度？

A: 测试运行时会打印详细日志。也可以打开另一个终端监控：

```bash
# 查看当前 iperf3 连接
sudo ss -tni | grep 10.0

# 查看网络统计
sudo ip -s link show h1-eth0
```

### Q4: 测试失败怎么办？

A: 检查以下几点：
1. 确保以 root 权限运行：`sudo python3 scheduler_test.py`
2. 检查 MPTCP 是否启用：`cat /proc/sys/net/mptcp/enabled` (应该是 1)
3. 关闭系统代理（如果有的话）
4. 检查防火墙设置

---

## 扩展实验

### 实验 1: 对比不同 RTT 场景

修改拓扑，创建不同延迟的路径：

```python
# Path 1: 低延迟
net.addLink(h1, h2, delay='5ms')
net.addLink(h2, h3, delay='5ms')

# Path 2: 高延迟
net.addLink(h1, h4, delay='100ms')
net.addLink(h4, h3, delay='100ms')
```

测试 BLEST 调度器（优化低延迟）的表现。

### 实验 2: 对比不对称带宽场景

```python
# Path 1: 高带宽
net.addLink(h1, h2, bw=100)
net.addLink(h2, h3, bw=100)

# Path 2: 低带宽
net.addLink(h1, h4, bw=10)
net.addLink(h4, h3, bw=10)
```

测试 perf 调度器（最大化吞吐量）的优势。

### 实验 3: 动态丢包场景

在测试中动态调整丢包率：

```python
# 模拟波动网络
for i in range(60):
    loss = 10 if 20 < i < 40 else 0
    h1.cmd(f'tc qdisc change dev h1-eth0 root netem loss {loss}%')
    time.sleep(1)
```

---

## 参考资源

- [MPTCP Linux Kernel Documentation](https://www.mptcp.dev/)
- [MPTCP Scheduler Design](https://lwn.net/Articles/820309/)
- [Mininet Documentation](https://mininet.org/)

---

## 许可证

本测试框架基于原 MPTCP 实验项目开发。

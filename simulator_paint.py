import re
from collections import defaultdict
import matplotlib.pyplot as plt

def compare_mptcp_full(filename, savefile):
    # 存储结构: { 时间: { IP: {cwnd: x, rtt: x, sent: x} } }
    stats = defaultdict(lambda: defaultdict(dict))
    current_time = "Unknown"
    
    with open(filename, 'r') as f:
        lines = f.readlines()
        for i in range(len(lines)):
            line = lines[i].strip()
            
            # 1. 提取时间戳
            time_match = re.search(r'(\d{2}:\d{2}:\d{2})', line)
            if time_match:
                current_time = time_match.group(1)
                continue
            
            # 2. 锁定数据子流 (10.0.1.1 为 eth0, 10.0.3.1 为 eth1)
            if "ESTAB" in line:
                ip_match = re.search(r'(10\.0\.[13]\.1)', line)
                if ip_match and i + 1 < len(lines):
                    ip = ip_match.group(1)
                    stats_line = lines[i+1].strip()
                    
                    # 3. 提取关键指标
                    bytes_sent_match = re.search(r'bytes_sent:(\d+)', stats_line)
                    # 过滤掉流量过小的控制流 (< 0.5MB)
                    if bytes_sent_match and int(bytes_sent_match.group(1)) > 500000:
                        cwnd = re.search(r'cwnd:(\d+)', stats_line)
                        rtt = re.search(r'rtt:([\d\.]+)', stats_line)
                        
                        stats[current_time][ip] = {
                            'cwnd': cwnd.group(1) if cwnd else "N/A",
                            'rtt': rtt.group(1) if rtt else "N/A",
                            'sent': round(int(bytes_sent_match.group(1)) / 1024 / 1024, 2)
                        }
    p1_cwnd = []
    p2_cwnd = []
    p1_rtt = []
    p2_rtt = []
    p1_sent = []
    p2_sent = []
    time = []
    i = 0
    
    # 5. 按时间顺序输出
    for ts in sorted(stats.keys()):
        i += 1
        time.append(i)
        p1 = stats[ts].get('10.0.1.1', {})
        p1_cwnd.append(p1.get('cwnd', 'N/A'))
        p1_rtt.append(p1.get('rtt', 'N/A'))
        p1_sent.append(p1.get('sent', '0'))

        p2 = stats[ts].get('10.0.3.1', {})
        p2_cwnd.append(p2.get('cwnd', 'N/A'))
        p2_rtt.append(p2.get('rtt', 'N/A'))
        p2_sent.append(p2.get('sent', '0'))
    
    plt.rcParams.update({
    'font.size': 16,          # 全局默认字体
    'axes.titlesize': 20,     # 子图标题
    'axes.labelsize': 18,     # 坐标轴标签
    'legend.fontsize': 16,    # 图例
    'xtick.labelsize': 14,    # x 轴刻度
    'ytick.labelsize': 14,    # y 轴刻度
    })
    
    # 创建一个 figure，3 个子图
    fig, axes = plt.subplots(3, 1, figsize=(14, 12), sharex=True)

    # ========== 1. CWND ==========
    axes[0].plot(
        time,
        [int(x) if x != 'N/A' else 0 for x in p1_cwnd],
        label='Path 1 CWND (10.0.1.1)'
    )
    axes[0].plot(
        time,
        [int(x) if x != 'N/A' else 0 for x in p2_cwnd],
        label='Path 2 CWND (10.0.3.1)'
    )
    axes[0].set_ylabel('CWND')
    axes[0].set_title('MPTCP Congestion Window Changes')
    axes[0].legend()
    axes[0].grid(True)

    # ========== 2. RTT ==========
    axes[1].plot(
        time,
        [float(x) if x != 'N/A' else 0 for x in p1_rtt],
        label='Path 1 RTT (10.0.1.1)'
    )
    axes[1].plot(
        time,
        [float(x) if x != 'N/A' else 0 for x in p2_rtt],
        label='Path 2 RTT (10.0.3.1)'
    )
    axes[1].set_ylabel('RTT')
    axes[1].set_title('MPTCP Round Trip Time Changes')
    axes[1].legend()
    axes[1].grid(True)

    # ========== 3. Sent ==========
    axes[2].plot(time, p1_sent, label='Path 1 Sent (10.0.1.1)')
    axes[2].plot(time, p2_sent, label='Path 2 Sent (10.0.3.1)')
    axes[2].set_xlabel('Time (seconds)')
    axes[2].set_ylabel('Sent (MB)')
    axes[2].set_title('MPTCP Sent Traffic Changes')
    axes[2].legend()
    axes[2].grid(True)

    # 自动调整子图间距
    plt.tight_layout()

    # 保存到一张图
    plt.savefig(savefile)
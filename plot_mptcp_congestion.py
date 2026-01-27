import matplotlib.pyplot as plt
import re

# 从文件中读取数据
def read_log_file(file_path):
    with open(file_path, 'r') as file:
        return file.read()

def parse_iperf_log(data):
    times, bitrates, retrs, cwnds = [], [], [], []
    
    # 匹配正则：时间、比特率、重传、CWND数值及单位
    pattern = re.compile(r'\[\s*\d+\]\s+([\d\.]+)-([\d\.]+)\s+sec\s+[\d\.]+\s+\w+Bytes\s+([\d\.]+)\s+\w+/sec\s+(\d+)\s+([\d\.]+)\s+(\w+)')
    
    for line in data.strip().split('\n'):
        match = pattern.search(line)
        if match:
            t_end = float(match.group(2))
            bitrate = float(match.group(3))
            retr = int(match.group(4))
            cwnd_val = float(match.group(5))
            cwnd_unit = match.group(6)
            
            # 统一 CWND 单位为 KB
            if 'M' in cwnd_unit:
                cwnd_val *= 1024
                
            times.append(t_end)
            bitrates.append(bitrate / 8)
            retrs.append(retr)
            cwnds.append(cwnd_val)
            
    return times, bitrates, retrs, cwnds

filename = 'iperf_mptcp_5_loss.log'
outputname = 'iperf_mptcp_5_loss_Bitrate_CWND.png'

# 读取日志文件并解析
log_data = read_log_file(filename)  # 替换为你的文件路径
t, b, r, c = parse_iperf_log(log_data)

print(t)
print(b)
print(r)
print(c)

# 绘图
fig, ax1 = plt.subplots(figsize=(12, 6))

# 绘制 Bitrate
color = 'tab:blue'
ax1.set_xlabel('Time (sec)')
ax1.set_ylabel('Bitrate (MB/s)', color=color)
ax1.plot(t, b, color=color, linewidth=2, label='Bitrate')
ax1.tick_params(axis='y', labelcolor=color)
ax1.grid(True, linestyle='--', alpha=0.6)

# 绘制 CWND (双坐标轴)
ax2 = ax1.twinx()
color = 'tab:red'
ax2.set_ylabel('CWND (KBytes)', color=color)
ax2.plot(t, c, color=color, linestyle='--', label='CWND')
ax2.tick_params(axis='y', labelcolor=color)

# 标记重传事件
for i, val in enumerate(r):
    if val > 50:  # 当重传大于50时标记
        ax1.annotate(f'Retr:{val}', (t[i], b[i]), textcoords="offset points", xytext=(0, 10), ha='center', fontsize=8, color='darkred')

plt.title('MPTCP Congestion Control Analysis: Bitrate vs CWND')
fig.tight_layout()
plt.savefig(outputname)


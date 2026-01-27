#!/usr/bin/python
from mininet.cli import CLI
from mininet.log import setLogLevel
import time
import mptcp
import simulator_paint

stage_time = 60
loss = 5
ss_filename = f'ss_history_{"no" if loss == 0 else loss}_loss.txt'
ss_savefile = f'ss_history_{"no" if loss == 0 else loss}_loss.png'
iperf_logfile = f'iperf_mptcp_{"no" if loss == 0 else loss}_loss.log'


setLogLevel('info')
net, h = mptcp.mptcp_topo()
h1, h2, h3, h4 = h[0], h[1], h[2], h[3]

# print("*** Testing Connectivity")
# print("Path 1:", h1.cmd("ping -c 1 10.0.2.2"))
# print("Path 2:", h1.cmd("ping -c 1 -I h1-eth1 10.0.4.2"))

# 3. 运行拥塞控制实验
# print("*** Starting iperf3 server on h3")
h3.cmd('mptcpize run iperf3 -s &')
time.sleep(2)

# print(f"*** Starting iperf3 client on h1 (Duration: {stage_time * 3}s)")
# 将输出重定向到文件以便后续分析
h1.cmd(f'mptcpize run iperf3 -c 10.0.2.2 -t {stage_time * 3} -i 1 > {iperf_logfile} &')

h1.cmd(f'for i in {{1..{stage_time * 3}}}; do date >> {ss_filename}; ss -tni >> {ss_filename}; sleep 1; done &')

# 第一阶段：基准期 
# print(f"Phase 1: Baseline (0-{stage_time}s) - Both paths clear")
time.sleep(stage_time)

# 第二阶段：注入干扰
# print(f"Phase 2: Congestion ({stage_time}-{stage_time * 2}s) - Injecting {loss}% loss on Path 1")
if loss != 0:
    h1.cmd(f'tc qdisc add dev h1-eth0 root netem loss {loss}%')

time.sleep(stage_time)

# 第三阶段：恢复期
# print(f"Phase 3: Recovery ({stage_time * 2}-{stage_time * 3}s) - Removing loss on Path 1")
if loss != 0:
    h1.cmd(f'tc qdisc del dev h1-eth0 root')

time.sleep(stage_time)

# print(f"*** Experiment Finished. Results saved to {iperf_logfile} and {ss_filename}")

CLI(net)
net.stop()

simulator_paint.compare_mptcp_full(ss_filename, ss_savefile)


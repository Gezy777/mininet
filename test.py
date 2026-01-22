#!/usr/bin/env python3
from mininet.net import Mininet
from mininet.topo import Topo
from mininet.cli import CLI
from mininet.link import TCLink
from mininet.log import setLogLevel, info
import time

class TwoPathTopo(Topo):
    def build(self):
        # 添加主机
        h1 = self.addHost('h1', ip=None)  # 不自动分配IP
        h2 = self.addHost('h2', ip=None)
        
        # 添加交换机
        s1 = self.addSwitch('s1')
        s2 = self.addSwitch('s2')
        
        # 添加两条路径
        # 为每条链路设置不同的延迟，以便更好地区分路径
        self.addLink(h1, s1, bw=10, delay='5ms')
        self.addLink(h2, s1, bw=10, delay='5ms')
        self.addLink(h1, s2, bw=10, delay='10ms')
        self.addLink(h2, s2, bw=10, delay='10ms')

def enable_mptcp():
    """启用MPTCP功能"""
    # 启用MPTCP（需要内核支持）
    info("*** 启用MPTCP\n")
    import os
    os.system('sysctl -w net.mptcp.enabled=1')
    os.system('sysctl -w net.mptcp.mptcp_enabled=1')
    os.system('sysctl -w net.mptcp.mptcp_path_manager=fullmesh')
    os.system('sysctl -w net.mptcp.mptcp_scheduler=default')

def main():
    setLogLevel('info')
    
    # 启用MPTCP
    enable_mptcp()
    
    # 创建网络
    net = Mininet(topo=TwoPathTopo(), link=TCLink, autoSetMacs=True)
    net.start()
    
    h1 = net.get('h1')
    h2 = net.get('h2')
    
    info("*** 配置接口IP地址\n")
    # 配置接口IP（确保不同子网）
    h1.cmd('ip addr add 10.0.0.1/24 dev h1-eth0')
    h1.cmd('ip addr add 10.0.1.1/24 dev h1-eth1')
    h2.cmd('ip addr add 10.0.0.2/24 dev h2-eth0')
    h2.cmd('ip addr add 10.0.1.2/24 dev h2-eth1')
    
    # 启用接口
    h1.cmd('ip link set h1-eth0 up')
    h1.cmd('ip link set h1-eth1 up')
    h2.cmd('ip link set h2-eth0 up')
    h2.cmd('ip link set h2-eth1 up')
    
    info("*** 配置路由\n")
    # 配置路由 - 更简洁的方式
    h1.cmd('ip route add 10.0.0.0/24 via 0.0.0.0 dev h1-eth0')
    h1.cmd('ip route add 10.0.1.0/24 via 0.0.0.0 dev h1-eth1')
    h2.cmd('ip route add 10.0.0.0/24 via 0.0.0.0 dev h2-eth0')
    h2.cmd('ip route add 10.0.1.0/24 via 0.0.0.0 dev h2-eth1')
    
    # 添加默认路由（可选）
    h1.cmd('ip route add default via 10.0.0.2 dev h1-eth0')
    h2.cmd('ip route add default via 10.0.0.1 dev h2-eth0')
    
    info("*** 测试连通性\n")
    # 测试基本连通性
    print(h1.cmd('ping -c 2 10.0.0.2'))
    print(h1.cmd('ping -c 2 10.0.1.2'))
    
    info("*** 检查MPTCP支持\n")
    # 检查MPTCP是否启用
    print(h1.cmd('sysctl net.mptcp.enabled'))
    print(h1.cmd('sysctl net.mptcp.mptcp_enabled'))
    
    info("*** 启动iperf3服务器（h2）\n")
    # 杀死可能存在的旧进程
    h2.cmd('pkill -f iperf3', warn=True)
    time.sleep(1)
    
    # 启动iperf3服务器（监听所有接口）
    h2.cmd('iperf3 -s -D &')
    time.sleep(2)
    
    info("*** 测试MPTCP (h1 -> h2)\n")
    print("测试MPTCP连接（使用10.0.0.2）:")
    result = h1.cmd('iperf3 -c 10.0.0.2 -t 5')
    print(result)
    
    # 另一种测试方式：使用iperf3的--bind参数
    info("*** 测试绑定到不同接口\n")
    print("\n测试通过eth0接口:")
    print(h1.cmd('iperf3 -c 10.0.0.2 -t 3 -B 10.0.0.1'))
    
    print("\n测试通过eth1接口:")
    print(h1.cmd('iperf3 -c 10.0.1.2 -t 3 -B 10.0.1.1'))
    
    # 显示连接信息
    info("*** 显示MPTCP连接信息\n")
    print(h1.cmd('ss -nti | head -20'))
    
    # 进入CLI进行手动测试
    info("*** 进入Mininet CLI\n")
    info("*** 在Mininet CLI中，您可以手动测试:\n")
    info("***   在h1上运行: iperf3 -c 10.0.0.2 -t 30\n")
    info("***   在h2上运行: ss -nti 查看连接详情\n")
    
    CLI(net)
    
    info("*** 停止网络\n")
    net.stop()

if __name__ == "__main__":
    main()
#!/usr/bin/python
from mininet.net import Mininet
from mininet.node import Controller
from mininet.cli import CLI
from mininet.link import TCLink
from mininet.log import setLogLevel

def mptcp_topo():
    net = Mininet(controller=Controller, link=TCLink, cleanup=True)

    print("*** Adding hosts and nodes")
    h1 = net.addHost('h1')
    h2 = net.addHost('h2') # Router 1
    h3 = net.addHost('h3')
    h4 = net.addHost('h4') # Router 2

    print("*** Creating links")
    # Path 1: h1-eth0 <-> h2-eth0; h2-eth1 <-> h3-eth0 (Delay: 10ms)
    net.addLink(h1, h2, intfName1='h1-eth0', intfName2='h2-eth0', bw=10, delay='10ms')
    net.addLink(h2, h3, intfName1='h2-eth1', intfName2='h3-eth0', bw=10, delay='10ms')

    # Path 2: h1-eth1 <-> h4-eth0; h4-eth1 <-> h3-eth1 (Delay: 10ms)
    net.addLink(h1, h4, intfName1='h1-eth1', intfName2='h4-eth0', bw=10, delay='10ms')
    net.addLink(h4, h3, intfName1='h4-eth1', intfName2='h3-eth1', bw=10, delay='10ms')

    net.build()
    net.start()

    print("*** Configuring IP Addresses")
    # h1 Addresses
    h1.cmd("ifconfig h1-eth0 10.0.1.1 netmask 255.255.255.0")
    h1.cmd("ifconfig h1-eth1 10.0.3.1 netmask 255.255.255.0")

    # h2 (Router 1)
    h2.cmd("ifconfig h2-eth0 10.0.1.2 netmask 255.255.255.0")
    h2.cmd("ifconfig h2-eth1 10.0.2.1 netmask 255.255.255.0")
    h2.cmd("sysctl -w net.ipv4.ip_forward=1")
    h2.cmd("ip route add 10.0.2.0/24 dev h2-eth1")
    h2.cmd("ip route add 10.0.1.0/24 dev h2-eth0")
    h2.cmd("ip route add 10.0.4.2 via 10.0.2.2 dev h2-eth1")

    # h4 (Router 2)
    h4.cmd("ifconfig h4-eth0 10.0.3.2 netmask 255.255.255.0")
    h4.cmd("ifconfig h4-eth1 10.0.4.1 netmask 255.255.255.0")
    h4.cmd("sysctl -w net.ipv4.ip_forward=1")
    h4.cmd("ip route add 10.0.4.0/24 dev h4-eth1")
    h4.cmd("ip route add 10.0.3.0/24 dev h4-eth0")
    h4.cmd("ip route add 10.0.2.2 via 10.0.4.2 dev h4-eth1")


    # h3 Addresses
    h3.cmd("ifconfig h3-eth0 10.0.2.2 netmask 255.255.255.0")
    h3.cmd("ifconfig h3-eth1 10.0.4.2 netmask 255.255.255.0")

    print("*** Critical: Disabling RP Filter and Enabling MPTCP")
    for h in [h1, h2, h3, h4]:
        h.cmd("sysctl -w net.ipv4.conf.all.rp_filter=0")
        h.cmd("sysctl -w net.ipv4.conf.default.rp_filter=0")
        for intf in h.intfList():
            h.cmd(f"sysctl -w net.ipv4.conf.{intf}.rp_filter=0")
        h.cmd("sysctl -w net.mptcp.enabled=1")

    print("*** Setting up Policy Routing for Multi-homing")
    # h1 Policy Routing
    h1.cmd("ip rule add from 10.0.1.1 table 1")
    h1.cmd("ip route add 10.0.1.0/24 dev h1-eth0 scope link table 1")
    h1.cmd("ip route add default via 10.0.1.2 dev h1-eth0 table 1")
    h1.cmd("ip rule add from 10.0.3.1 table 2")
    h1.cmd("ip route add 10.0.3.0/24 dev h1-eth1 scope link table 2")
    h1.cmd("ip route add default via 10.0.3.2 dev h1-eth1 table 2")
    h1.cmd("ip route add 10.0.4.0/24 via 10.0.3.2 dev h1-eth1")
    h1.cmd("ip route add default via 10.0.1.2") # Default gateway for h1

    # h3 Policy Routing
    h3.cmd("ip rule add from 10.0.2.2 table 1")
    h3.cmd("ip route add 10.0.2.0/24 dev h3-eth0 scope link table 1")
    h3.cmd("ip route add default via 10.0.2.1 dev h3-eth0 table 1")
    h3.cmd("ip rule add from 10.0.4.2 table 2")
    h3.cmd("ip route add 10.0.4.0/24 dev h3-eth1 scope link table 2")
    h3.cmd("ip route add default via 10.0.4.1 dev h3-eth1 table 2")
    h3.cmd("ip route add 10.0.3.0/24 via 10.0.4.1 dev h3-eth1")
    h3.cmd("ip route add default via 10.0.2.1") # Default gateway for h3

    print("*** Configuring MPTCP Endpoints")
    # h1: 使用 eth1 发起子流
    h1.cmd("ip mptcp endpoint add 10.0.3.1 dev h1-eth1 subflow")

    # h3: 关键修改！使用 signal 模式宣告自己的第二块网卡地址
    # 这样 h3 会告诉 h1："你可以连我的 10.0.4.2"
    h3.cmd("ip mptcp endpoint flush") # 清除旧配置
    h3.cmd("ip mptcp endpoint add 10.0.4.2 dev h3-eth1 signal")

    # 确保两端都允许建立子流
    h1.cmd("ip mptcp limits set subflow 2 add_addr_accepted 2")
    h3.cmd("ip mptcp limits set subflow 2 add_addr_accepted 2")
    return net, [h1, h2, h3, h4]

if __name__ == '__main__':
    setLogLevel('info')
    net, h = mptcp_topo()
    h1, h2, h3, h4 = h[0], h[1], h[2], h[3]
    print("*** Testing Connectivity")
    print("Path 1:", h1.cmd("ping -c 1 10.0.2.2"))
    print("Path 2:", h1.cmd("ping -c 1 -I h1-eth1 10.0.4.2"))

    CLI(net)
    net.stop()

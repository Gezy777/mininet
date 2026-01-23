
### 仿真拓扑
![MPTCP](./picture/topo.svg)

#### 实验一：使用MPTCP

1. 实验步骤
   1. 运行脚本mptcp.py
   2. h3为服务端，h1为客户端；h1通过iperf3向h3发送请求
        ```bash
        ## 使用mptcpize run运行iperf3保证使用MPTCP协议
        - h3 mptcpize run iperf3 -s &
        - h1 mptcpize run iperf3 -c 10.0.2.2 -t 10 ## 抓包后再执行
        ```
        ![](./picture/实验一/截图%202026-01-23%2010-24-00.png)
   3. 在h1的两个接口抓包
        ```bash
        - xterm h1 h1   ## 打开两个h1终端
        - tcpdump -i h1-eth0 -w h1-path1.pcap
        - tcpdump -i h1-eth1 -w h1-path2.pcap
        ```
        ![](./picture/实验一/截图%202026-01-23%2010-21-35.png)

2. 实验结果
   - 抓包结果如下
       ![](./picture/实验一/截图%202026-01-23%2010-26-33.png)
   - 可以看到两个接口都成功抓取到了数据包，证明确实使用了MPTCP协议

#### 实验二：探究MPTCP的流量聚合功能

1. 实验步骤
   - h3为服务端，h1为客户端；h1通过iperf3向h3发送**固定大小的数据量**
   1. 不使用MPTCP协议
        ```bash
        mininet> h1 iperf3 -c 10.0.2.2 -n 10M
        Connecting to host 10.0.2.2, port 5201
        [  5] local 10.0.1.1 port 34684 connected to 10.0.2.2 port 5201
        [ ID] Interval           Transfer     Bitrate         Retr  Cwnd
        [  5]   0.00-1.00   sec  2.00 MBytes  16.8 Mbits/sec    0    182 KBytes       
        [  5]   1.00-2.00   sec  1.38 MBytes  11.5 Mbits/sec    0    240 KBytes       
        [  5]   2.00-3.00   sec  1.00 MBytes  8.39 Mbits/sec    0    300 KBytes       
        [  5]   3.00-4.00   sec  1.25 MBytes  10.5 Mbits/sec    0    358 KBytes       
        [  5]   4.00-5.00   sec  1.62 MBytes  13.6 Mbits/sec    0    416 KBytes       
        [  5]   5.00-6.00   sec  1.75 MBytes  14.7 Mbits/sec    0    475 KBytes       
        [  5]   6.00-7.00   sec  1.00 MBytes  8.39 Mbits/sec    0    533 KBytes       
        - - - - - - - - - - - - - - - - - - - - - - - - -
        [ ID] Interval           Transfer     Bitrate         Retr
        [  5]   0.00-7.00   sec  10.0 MBytes  12.0 Mbits/sec    0            sender
        [  5]   0.00-7.46   sec  8.38 MBytes  9.42 Mbits/sec                  receiver

        iperf Done.
        ```
   2. 使用MPTCP协议
        ```bash
        mininet> h1 mptcpize run iperf3 -c 10.0.2.2 -n 10M
        Connecting to host 10.0.2.2, port 5201
        [  5] local 10.0.1.1 port 52632 connected to 10.0.2.2 port 5201
        [ ID] Interval           Transfer     Bitrate         Retr  Cwnd
        [  5]   0.00-1.00   sec  3.62 MBytes  30.4 Mbits/sec    0    256 KBytes       
        [  5]   1.00-2.00   sec  3.00 MBytes  25.2 Mbits/sec    0    317 KBytes       
        [  5]   2.00-3.00   sec  2.50 MBytes  21.0 Mbits/sec    0    375 KBytes       
        [  5]   3.00-4.00   sec   896 KBytes  7.35 Mbits/sec    0    434 KBytes       
        - - - - - - - - - - - - - - - - - - - - - - - - -
        [ ID] Interval           Transfer     Bitrate         Retr
        [  5]   0.00-4.00   sec  10.0 MBytes  21.0 Mbits/sec    0            sender
        [  5]   0.00-4.37   sec  9.50 MBytes  18.2 Mbits/sec                  receiver

        iperf Done.
        ```
2. 实验结果
    - 从结果可以看出，在使用MPTCP协议传输10M的数据量只需要4s，而不使用MPTCP协议传输相同的数据量需要7s。
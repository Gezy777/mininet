## Attention
❌ WSL上无法进行MPTCP仿真 
❌ Mininet运行需要sudo，最好关闭conda使用系统级的python3运行Mininet脚本
 
### 1.安装mininet
```bash
sudo apt install mininet
## 需要运行python脚本的话，需要安装mininet库
## 因为mininet运行需要sudo，所以mininet库需要安装在系统python下（即非conda）
pip install mininet
```
### 2.安装mptcpd和iperf3
```bash
sudo apt install mptcpd
sudo apt install iperf3
# 使用mptcpize
# mptcpize 是一个实用工具，用于让已有的 “Legacy TCP 程序/服务” 强制使用 MPTCP 套接字，而不需要修改程序源码。它是 Linux 上 MPTCP 生态的一部分（通常和 mptcpd 一起提供）
# 简而言之，它做了两件事：
# ✔️ 运行程序时强制使用 MPTCP
# ✔️ 修改 systemd 服务单元以使服务启用 MPTCP 套接字
```
### 3.安装Xterm并自定义
```bash
sudo apt install xterm
## 修改xterm窗口的大小
nano ~/.Xresources
## 添加内容
XTerm*geometry: 100x30
XTerm*faceName: Monospace
XTerm*faceSize: 12
## 生效
xrdb -merge ~/.Xresources
```
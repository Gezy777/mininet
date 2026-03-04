cd /home/zxk/App/project/MPQUIC/mpquicByQuicGo/example/web_download

echo "===== $(date +"%Y-%m-%d %H:%M:%S") Single Path =====" >> server.log
./server >> server.log 2>&1

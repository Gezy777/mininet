cd /home/zxk/App/project/MPQUIC/mpquicByQuicGo/example/web_download

echo "===== $(date +"%Y-%m-%d %H:%M:%S") Multi Path =====" >> server.log
./server -m >> server.log 2>&1
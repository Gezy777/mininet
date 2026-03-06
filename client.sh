cd /home/zxk/App/project/MPQUIC/mpquicByQuicGo/example/web_download/client

echo "===== $(date +"%Y-%m-%d %H:%M:%S") Single Path =====" >> client.log
./client -f cheer.jpg >> client.log 2>&1

# echo "===== $(date +"%Y-%m-%d %H:%M:%S") Multi Path =====" >> client.log
# ./client -m -f test.txt >> client.log 2>&1
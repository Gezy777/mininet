cd /home/zxk/App/project/MPQUIC/mpquicByQuicGo/example/web_download/client

echo "===== $(date +"%Y-%m-%d %H:%M:%S") Multi Path =====" >> client.log
./client -m -f Zotero.tar.xz >> client.log 2>&1
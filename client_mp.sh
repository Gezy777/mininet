cd /home/zxk/App/project/MPQUIC/mpquicByQuicGo/example/web_download/client

filename=$1
logfile="client_z_${filename}.log"
downloadfile="Zotero.tar.xz"

echo "===== $(date +"%Y-%m-%d %H:%M:%S") Multi Path =====" >> "$logfile"
./client -m -f "$downloadfile" >> "$logfile" 2>&1

echo -n "Clear $logfile ? (y/n, default=y): "
read input

# 默认清空
if [ -z "$input" ] || [ "$input" = "y" ] || [ "$input" = "Y" ]; then
    echo "Clearing $logfile..."
    > "$logfile"
else
    echo "Keep $logfile content"
fi
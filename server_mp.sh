cd /home/zxk/App/project/MPQUIC/mpquicByQuicGo/example/web_download

filename=$1
logfile="server_z_${filename}.log"

echo "===== $(date +"%Y-%m-%d %H:%M:%S") Multi Path =====" >> "$logfile"
./server -m >> "$logfile" 2>&1

# rm ./server
# echo -n "Clear $logfile ? (y/n, default=y): "
# read input

# # 默认清空
# if [ -z "$input" ] || [ "$input" = "y" ] || [ "$input" = "Y" ]; then
#     echo "Clearing $logfile..."
#     > "$logfile"
# else
#     echo "Keep $logfile content"
#!/bin/bash

echo "=== Website Monitor System Test ==="

# 1. Check if the service is running
echo -e "\n1. Checking systemd service status..."
sudo systemctl status website-monitor | cat

# 2. Check if the log file exists and is writable
echo -e "\n2. Checking log file..."
if [ -w "/var/log/website-monitor.log" ]; then
    echo "✓ Log file exists and is writable"
    echo "Last 5 log entries:"
    tail -n 5 /var/log/website-monitor.log | cat
else
    echo "✗ Log file issue - check permissions"
fi

# 3. Check if the conda environment exists
echo -e "\n3. Checking conda environment..."
conda env list | grep website_monitor | cat

# 4. Check if required processes are running
echo -e "\n4. Checking monitor process..."
ps aux | grep "[p]ython.*monitor.py" | cat

# 5. Test notification system
echo -e "\n5. Testing desktop notification..."
notify-send -u critical "Website Monitor Test" "This is a test notification" | cat

# 6. Check Make.com webhook
echo -e "\n6. Testing Make.com webhook..."
curl -X POST "https://hook.us1.make.com/ajgntubj9k5f83n2vcl2phuvd6nkofvv" \
     -H "Content-Type: application/json" \
     -d '{"site":"TEST","timestamp":"'$(date -Iseconds)'","user":"'$USER'","browser_type":"test"}' | cat

echo -e "\n=== Test Complete ===" 
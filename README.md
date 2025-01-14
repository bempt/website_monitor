# Website Monitor

A system that monitors browser activity and sends notifications when specific websites are visited. Built for Ubuntu 22.04.

## Features

- Monitors both regular and incognito Chrome/Chromium browsing
- Sends notifications through Make.com when monitored sites are visited
- Properly formatted site names in notifications (e.g., "facebook.com" shows as "Facebook")
- 5-second countdown warning with sound before sending notifications
- Automatic startup with system boot
- Persistent monitoring that auto-restarts if stopped
- Cooldown period between notifications (5 minutes)

## Prerequisites

- Ubuntu 22.04
- Anaconda/Miniconda
- Chrome/Chromium browser
- `notify-send` (usually pre-installed on Ubuntu)
- `paplay` for sound notifications (usually pre-installed on Ubuntu)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/website_monitor.git
cd website_monitor
```

2. Create and activate the Conda environment:
```bash
conda create -n website_monitor python=3.10
conda activate website_monitor
```

3. Install required packages:
```bash
pip install requests
```

4. Set up the systemd service:
```bash
# Copy the service file to systemd
sudo cp website-monitor.service /etc/systemd/system/

# Create log file with proper permissions
sudo touch /var/log/website-monitor.log
sudo chown $USER:$USER /var/log/website-monitor.log

# Enable and start the service
sudo systemctl daemon-reload
sudo systemctl enable website-monitor
sudo systemctl start website-monitor
```

## Configuration

1. Edit monitored websites in `monitor.py`:
```python
MONITORED_SITES = [
    "reddit.com",
    "facebook.com"
    # Add more sites as needed
]
```

Note: Site names are automatically formatted for display (e.g., "facebook.com" will appear as "Facebook" in notifications and emails)

2. Configure Make.com:
   - Create a new scenario in Make.com
   - Add a Webhook trigger (set to "On demand")
   - Configure the actions (email, SMS, etc.)
   - Copy the webhook URL to `MAKE_WEBHOOK_URL` in `monitor.py`

## Usage

The monitor starts automatically with your system and runs in the background. When a monitored site is visited:

1. You'll receive an immediate warning notification with sound
2. A 5-second countdown begins
3. If the site remains open after the countdown:
   - A notification is sent through Make.com
   - A desktop notification confirms the send
4. If you close the site before the countdown ends:
   - No notification is sent
   - A desktop notification confirms cancellation

## Service Management

Check status:
```bash
sudo systemctl status website-monitor
```

View logs:
```bash
tail -f /var/log/website-monitor.log
```

Restart service:
```bash
sudo systemctl restart website-monitor
```

## Testing

Run the test script:
```bash
./test_monitor.sh
```

This will:
- Check service status
- Verify log file permissions
- Test notifications
- Send a test webhook to Make.com

## Troubleshooting

1. If notifications don't show:
   - Check if notify-send is installed: `which notify-send`
   - Verify the service is running: `systemctl status website-monitor`

2. If sound doesn't work:
   - Check if paplay is installed: `which paplay`
   - Verify sound file exists: `ls /usr/share/sounds/freedesktop/stereo/alarm-clock-elapsed.oga`

3. If Make.com notifications aren't received:
   - Check the webhook URL in `monitor.py`
   - Verify the Make.com scenario is turned on
   - Check the logs: `tail -f /var/log/website-monitor.log`

## Security Notes

- The system monitors browser processes without accessing browser content
- Webhook URLs should be kept private
- Logs are stored in `/var/log/website-monitor.log`
- The service runs with user privileges, not root # website_monitor

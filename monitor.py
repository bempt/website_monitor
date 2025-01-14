import time
import requests
import subprocess
import os
from datetime import datetime
import logging
import re
import tempfile
import json
import socket

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/var/log/website-monitor.log'),
        logging.StreamHandler()
    ]
)

# Configuration
MAKE_WEBHOOK_URL = "https://hook.us1.make.com/ajgntubj9k5f83n2vcl2phuvd6nkofvv"
MONITORED_SITES = [
    "facebook",  # Simplified patterns
    "reddit"
]

WARNING_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>⚠️ Website Monitor Warning</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
            margin: 0;
            background-color: #fff3f3;
        }
        .warning-box {
            text-align: center;
            padding: 2rem;
            border-radius: 10px;
            background-color: white;
            box-shadow: 0 0 20px rgba(255, 0, 0, 0.1);
            max-width: 600px;
        }
        .countdown {
            font-size: 4rem;
            color: #ff4444;
            margin: 1rem 0;
        }
        .message {
            font-size: 1.2rem;
            color: #333;
            margin: 1rem 0;
        }
        .site {
            font-weight: bold;
            color: #ff4444;
        }
    </style>
    <script>
        let timeLeft = {seconds};
        function updateCountdown() {{
            document.getElementById('countdown').textContent = timeLeft;
            if (timeLeft > 0) {{
                timeLeft--;
                setTimeout(updateCountdown, 1000);
            }}
        }}
        window.onload = updateCountdown;
    </script>
</head>
<body>
    <div class="warning-box">
        <h1>⚠️ Warning</h1>
        <p class="message">You are attempting to visit <span class="site">{site}</span></p>
        <p class="message">A notification will be sent in:</p>
        <div class="countdown" id="countdown">{seconds}</div>
        <p class="message">Close this tab now to prevent the notification</p>
    </div>
</body>
</html>
"""

def create_warning_page(site, seconds):
    """Create a temporary warning page"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
        html_content = WARNING_HTML.format(site=site, seconds=seconds)
        f.write(html_content)
        return f.name

def format_site_name(site):
    """Format site name for display (e.g., 'facebook' -> 'Facebook')"""
    return site.capitalize()

def send_to_make(site):
    try:
        data = {
            "site": format_site_name(site),
            "timestamp": datetime.now().isoformat(),
            "user": "Bennett",
            "browser_type": "incognito" if is_incognito(site) else "regular"
        }
        response = requests.post(MAKE_WEBHOOK_URL, json=data)
        logging.info(f"Notification sent for {format_site_name(site)}: {response.status_code}")
        
        # Backup notification in case Make.com is down
        backup_webhook = os.getenv("BACKUP_WEBHOOK_URL")
        if backup_webhook:
            requests.post(backup_webhook, json=data)
    except Exception as e:
        logging.error(f"Error sending to Make: {e}")

def show_notification(message, urgency='critical'):
    try:
        # Use DBUS directly instead of notify-send
        cmd = f"""dbus-send --system --type=method_call --dest=org.freedesktop.login1 /org/freedesktop/login1 org.freedesktop.login1.Manager.GetSession string:$XDG_SESSION_ID && \
                 DISPLAY=:0 DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1000/bus notify-send -u {urgency} -t 5000 'Website Monitor' '{message}'"""
        subprocess.run(cmd, shell=True)
        
        # Play sound using paplay with full path to sound file
        subprocess.run(['paplay', '/usr/share/sounds/freedesktop/stereo/alarm-clock-elapsed.oga'])
        logging.info(f"Notification shown: {message}")
    except Exception as e:
        logging.error(f"Error showing notification: {e}")

def is_incognito(site):
    try:
        cmd = r"ps aux | grep -i 'chrome\|chromium' | grep -i 'incognito'"
        result = subprocess.check_output(cmd, shell=True).decode().lower()
        return site in result
    except:
        return False

def get_active_chrome_tabs():
    try:
        # Use ps to get all Chrome/Chromium processes and their command lines
        cmd = "ps aux | grep -E 'chrome|chromium' | grep -v grep || true"
        result = subprocess.check_output(cmd, shell=True).decode().lower()
        
        # Also check window titles from /proc
        cmd = "find /proc/*/comm -type f -exec grep -l 'chrome\\|chromium' {} \\; 2>/dev/null | sed 's/comm$/cmdline/g' | xargs -I {} cat {} 2>/dev/null || true"
        proc_result = subprocess.check_output(cmd, shell=True).decode().lower()
        
        combined_result = result + "\n" + proc_result
        
        for site in MONITORED_SITES:
            site = site.lower()
            patterns = [
                f"{site}.com",
                f"www.{site}.com",
                f"https://{site}.com",
                f"https://www.{site}.com",
                site  # Also check just the site name
            ]
            
            if any(pattern in combined_result for pattern in patterns):
                logging.debug(f"Found site {site} in process list")
                return site
                
        logging.debug("No monitored sites found in active tabs")
        return ""
        
    except Exception as e:
        logging.error(f"Error in get_active_chrome_tabs: {e}")
        return ""

def show_warning_page(site):
    """Show a warning page in the browser"""
    try:
        warning_file = create_warning_page(format_site_name(site), 5)
        # Use xdg-open with DISPLAY and DBUS settings
        cmd = f"DISPLAY=:0 DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1000/bus xdg-open {warning_file}"
        subprocess.run(cmd, shell=True)
        logging.info(f"Warning page shown for {site}")
    except Exception as e:
        logging.error(f"Error showing warning page: {e}")
        # Still proceed with notification even if warning page fails
        show_notification(f"⚠️ WARNING: {format_site_name(site)} detected!")

def main():
    logging.info("Website monitor starting...")
    last_notification = {}
    
    while True:
        try:
            detected_site = get_active_chrome_tabs()
            current_time = time.time()
            
            if detected_site:
                logging.debug(f"Detected site: {detected_site}")
                
                if detected_site not in last_notification or \
                   (current_time - last_notification[detected_site]) > 300:  # 5 minutes cooldown
                    formatted_site = format_site_name(detected_site)
                    logging.info(f"Detected visit to {formatted_site}")
                    
                    # Show warning page and notification
                    show_warning_page(detected_site)
                    show_notification(f"⚠️ WARNING: {formatted_site} detected!\n🕐 5 seconds until notification is sent!")
                    
                    # Wait and check again
                    time.sleep(5)
                    
                    # Final check
                    if get_active_chrome_tabs() == detected_site:
                        send_to_make(detected_site)
                        show_notification(f"🚨 SENT: Partner notified about {formatted_site}")
                        last_notification[detected_site] = current_time
                    else:
                        show_notification(f"✓ {formatted_site} was closed - nothing sent", 'normal')
                else:
                    logging.debug(f"Site {detected_site} in cooldown period")
            
            time.sleep(1)
        except Exception as e:
            logging.error(f"Error in main loop: {e}")
            time.sleep(5)

if __name__ == "__main__":
    main()
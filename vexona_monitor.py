import requests
import time
import threading
from datetime import datetime
from flask import Flask

# --- CONFIGURATION ---
USER_TOKEN = "MTMyMzg4NDcwNjY0NjcyNDYyOQ.Gfv-O1.M-upC0CXra3jfuO9N5unkWcp87taWeHH7PL_SU"
CHANNEL_ID = "1414882878101258281"
WEBHOOK_REAL = "https://discordapp.com/api/webhooks/1457976129381072969/DMfQaIxbctYmZzDmXo72jfZ_sH-Ss4AOhwiSbrPZC91CpvWQQuMtKB8cAMcAPWdJXerV"
WEBHOOK_HIGHLIGHTS = "https://discordapp.com/api/webhooks/1457980415762501817/176_LYCPd1YMaskUlJDaNW_qqa0qm4w4AYXxOZpn1lzGnRFpXU4PM327_DLxWtIx-Bag"
ICON_URL = "https://cdn.discordapp.com/attachments/1457872310664036452/1457975697346793594/ChatGPT_Image_Jan_4_2026_12_10_40_AM.png?ex=695df52e&is=695ca3ae&hm=f8400d0e4fcd5abd36fb75d5454796faaa6c8c54818736124a1f1270189d9ca8&"
HEADERS = {"Authorization": USER_TOKEN, "Content-Type": "application/json"}
SEEN_MESSAGES = set()

# --- HEARTBEAT SERVER (KEEPS IT ALIVE) ---
app = Flask(__name__)

@app.route('/')
def home():
    return "ENI is Alive and Monitoring.", 200

def run_web_server():
    # Hugging Face expects port 7860
    app.run(host='0.0.0.0', port=7860)

# --- NOTIFIER LOGIC ---
def send_webhook(url, brainrot, gain, join_url):
    is_highlight = url == WEBHOOK_HIGHLIGHTS
    join_value = f"[Join URL]({join_url})" if is_highlight else join_url

    payload = {
        "embeds": [
            {
                "title": "Brainrot Notify | Vexona Notifier",
                "color": 45292,
                "fields": [
                    {"name": "Brainrot Name", "value": brainrot, "inline": True},
                    {"name": "Money per second", "value": gain, "inline": True},
                    {"name": "Join URL", "value": join_value, "inline": False}
                ],
                "footer": {"text": "Vexona Notifier | by hiklo0753", "icon_url": ICON_URL},
                "timestamp": datetime.utcnow().isoformat()
            }
        ]
    }
    try:
        requests.post(url, json=payload)
    except:
        pass

def parse_embed(embed):
    brainrot = "Unknown"
    gain = "Unknown"
    join_url = "Unknown"
    if "fields" in embed:
        for field in embed["fields"]:
            name = field.get("name", "").lower()
            val = field.get("value", "")
            if "brainrot" in name: brainrot = val
            elif "gain" in name: gain = val
            elif "join" in name: join_url = val
    return brainrot, gain, join_url

def monitor_loop():
    print(f"[*] ENI is locked in on channel {CHANNEL_ID}...")
    url = f"https://discord.com/api/v9/channels/{CHANNEL_ID}/messages?limit=5"
    
    while True:
        try:
            r = requests.get(url, headers=HEADERS)
            if r.status_code == 200:
                for msg in r.json():
                    msg_id = msg['id']
                    if msg_id not in SEEN_MESSAGES:
                        SEEN_MESSAGES.add(msg_id)
                        if 'embeds' in msg and msg['embeds']:
                            b, g, j = parse_embed(msg['embeds'][0])
                            if j != "Unknown" and "http" in j:
                                print(f"[!] Drop: {b}")
                                send_webhook(WEBHOOK_REAL, b, g, j)
                                send_webhook(WEBHOOK_HIGHLIGHTS, b, g, "https://discord.com/channels/1456918303225155792/1456920235541008501")
            time.sleep(2)
        except:
            time.sleep(5)

if __name__ == "__main__":
    # Start the web server in a separate thread so it runs alongside the monitor
    t = threading.Thread(target=run_web_server)
    t.start()
    monitor_loop()

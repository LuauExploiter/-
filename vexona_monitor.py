import requests
import time
import json
from datetime import datetime

# --- CONFIGURATION ---
USER_TOKEN = "MTMyMzg4NDcwNjY0NjcyNDYyOQ.Gfv-O1.M-upC0CXra3jfuO9N5unkWcp87taWeHH7PL_SU"
CHANNEL_ID = "1414882878101258281"

# Webhooks
WEBHOOK_REAL = "https://discordapp.com/api/webhooks/1457976129381072969/DMfQaIxbctYmZzDmXo72jfZ_sH-Ss4AOhwiSbrPZC91CpvWQQuMtKB8cAMcAPWdJXerV"
WEBHOOK_HIGHLIGHTS = "https://discordapp.com/api/webhooks/1457980415762501817/176_LYCPd1YMaskUlJDaNW_qqa0qm4w4AYXxOZpn1lzGnRFpXU4PM327_DLxWtIx-Bag"

# Icons & Config
ICON_URL = "https://cdn.discordapp.com/attachments/1457872310664036452/1457975697346793594/ChatGPT_Image_Jan_4_2026_12_10_40_AM.png?ex=695df52e&is=695ca3ae&hm=f8400d0e4fcd5abd36fb75d5454796faaa6c8c54818736124a1f1270189d9ca8&"
HEADERS = {"Authorization": USER_TOKEN, "Content-Type": "application/json"}
SEEN_MESSAGES = set()

def send_webhook(url, brainrot, gain, join_url):
    """Constructs and sends the embed to the specified webhook."""
    
    # Determine if this is the 'Highlights' webhook (masked link) or 'Real' (full link)
    is_highlight = url == WEBHOOK_HIGHLIGHTS
    
    # Format the value for the field based on destination
    if is_highlight:
        join_value = f"[Join URL]({join_url})"
    else:
        join_value = join_url # Raw URL for the real notifier as requested, or hyperlinked if preferred

    # For the Real Notifier, you requested it to just be the link, but in the embed example 
    # you showed a hyperlink format. I will stick to your JS example: "<join_url_with_hyperlink>"
    # If the raw URL is huge, Discord handles it better inside `[Link](url)` format anyway.
    # But strictly following your "Real notifier" logic:
    
    final_join_field_value = join_value
    if not is_highlight:
        # If you want the massive link to be clickable text:
        final_join_field_value = f"[Join URL]({join_url})"

    payload = {
        "embeds": [
            {
                "title": "Brainrot Notify | Vexona Notifier",
                "color": 45292, # Hex #00b0f4
                "fields": [
                    {
                        "name": "Brainrot Name",
                        "value": brainrot,
                        "inline": True
                    },
                    {
                        "name": "Money per second",
                        "value": gain,
                        "inline": True
                    },
                    {
                        "name": "Join URL",
                        "value": final_join_field_value,
                        "inline": False
                    }
                ],
                "footer": {
                    "text": "Vexona Notifier | by hiklo0753",
                    "icon_url": ICON_URL
                },
                "timestamp": datetime.utcnow().isoformat()
            }
        ]
    }
    
    try:
        r = requests.post(url, json=payload)
        if r.status_code in [200, 204]:
            print(f"[+] Sent to {('Highlights' if is_highlight else 'Real Notifier')}")
        else:
            print(f"[-] Failed to send: {r.status_code} - {r.text}")
    except Exception as e:
        print(f"[!] Error sending webhook: {e}")

def parse_embed(embed):
    """Extracts Brainrot, Gain, and Join URL from a target embed."""
    brainrot = "Unknown"
    gain = "Unknown"
    join_url = "Unknown"

    # Iterate through fields to find data
    if "fields" in embed:
        for field in embed["fields"]:
            name = field.get("name", "").lower()
            value = field.get("value", "")
            
            if "brainrot" in name or "brainrots" in name:
                brainrot = value
            elif "gain" in name:
                gain = value
            elif "join" in name or "url" in name:
                # Often the URL is inside a markdown link [Link](url), we might need to extract it
                # But if the source sends it raw, we just grab it.
                # Assuming the source sends a clean URL or we grab the text content.
                if "(" in value and ")" in value:
                     # Simple extraction of url from [text](url)
                     try:
                         join_url = value.split("](")[1].split(")")[0]
                     except:
                         join_url = value
                else:
                    join_url = value

    # Fallback: Check description if fields fail
    if join_url == "Unknown" and "description" in embed:
        if "http" in embed["description"]:
            # naive extraction
            words = embed["description"].split()
            for word in words:
                if word.startswith("http"):
                    join_url = word
                    break

    return brainrot, gain, join_url

def main():
    print(f"[*] ENI is monitoring channel {CHANNEL_ID} for you...")
    
    # URL to fetch messages
    url = f"https://discord.com/api/v9/channels/{CHANNEL_ID}/messages?limit=5"

    while True:
        try:
            r = requests.get(url, headers=HEADERS)
            
            if r.status_code == 200:
                messages = r.json()
                
                for msg in messages:
                    msg_id = msg['id']
                    
                    if msg_id not in SEEN_MESSAGES:
                        SEEN_MESSAGES.add(msg_id)
                        
                        # Check if message has embeds
                        if 'embeds' in msg and msg['embeds']:
                            target_embed = msg['embeds'][0]
                            
                            # Parse data
                            brainrot, gain, join_url = parse_embed(target_embed)
                            
                            # Trigger only if we found valid data (basic validation)
                            if join_url != "Unknown" and "http" in join_url:
                                print(f"[!] New Drop: {brainrot} | {gain}")
                                
                                # 1. Send to Real Notifier (Full Raw/Hyperlinked URL)
                                send_webhook(WEBHOOK_REAL, brainrot, gain, join_url)
                                
                                # 2. Send to Highlights (Fixed Masked URL)
                                # The user specified a static URL for highlights:
                                static_highlight_url = "https://discord.com/channels/1456918303225155792/1456920235541008501"
                                send_webhook(WEBHOOK_HIGHLIGHTS, brainrot, gain, static_highlight_url)

            elif r.status_code == 401:
                print("[-] Invalid Token. Please update USER_TOKEN.")
                break
            elif r.status_code == 429:
                # Rate limited
                retry_after = r.json().get('retry_after', 5)
                print(f"[-] Rate limited. Sleeping for {retry_after}s")
                time.sleep(retry_after)
                
        except Exception as e:
            print(f"[!] Error: {e}")

        # Sleep to avoid spamming the API too hard (1-2 seconds is safe for self-bots)
        time.sleep(2)

if __name__ == "__main__":
    main()

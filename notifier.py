import asyncio
import aiohttp
import os
from datetime import datetime, timezone
from typing import Optional
import re

TOKEN = os.getenv("TOKEN")
REALHOOK = os.getenv("REALHOOK")
HIGHHOOK = os.getenv("HIGHHOOK")
CHANNEL_ID = "1414882878101258281"
HIGHLIGHTS_STATIC_URL = "https://discord.com/channels/1456918303225155792/1456920235541008501"
FETCH_LIMIT = 50
POLL_DELAY = 1.0

if not TOKEN or not REALHOOK or not HIGHHOOK:
    raise RuntimeError("Token, Realhook or Highhook not set")

processed_ids: set[str] = set()
start_timestamp = datetime.now(timezone.utc)

def format_money(raw: str) -> Optional[str]:
    try:
        clean = re.sub(r"[^\d\.]", "", raw)
        num = float(clean)
    except:
        return None
    if num >= 1_000_000_000:
        return f"${num / 1_000_000_000:.1f}B"
    if num >= 1_000_000:
        return f"${num / 1_000_000:.1f}M"
    if num >= 1_000:
        return f"${num / 1_000:.1f}K"
    return f"${int(num)}"

def clean_name(text: str) -> str:
    return text.replace("*", "").replace("_", "").replace("•", "").strip()

def create_embed(name: str, money: str, join_url: str) -> dict:
    return {
        "author": {"name": "Brainrot Notify | Vexona Notifier"},
        "fields": [
            {"name": "Brainrot Name", "value": name, "inline": True},
            {"name": "Money per second", "value": f"{money}/s", "inline": True},
            {"name": "Join URL", "value": f"[Join Server]({join_url})", "inline": False},
        ],
        "color": 0x00B0F4,
        "footer": {"text": "Vexona Notifier | by hiklo0753"},
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

async def fetch_messages(session: aiohttp.ClientSession) -> list[dict]:
    url = f"https://discord.com/api/v10/channels/{CHANNEL_ID}/messages?limit={FETCH_LIMIT}"
    headers = {"Authorization": TOKEN}
    async with session.get(url, headers=headers) as resp:
        if resp.status == 200:
            return await resp.json()
        if resp.status == 429:
            data = await resp.json()
            await asyncio.sleep(data.get("retry_after", 1))
            return []
        return []

async def send_webhook(session: aiohttp.ClientSession, url: str, embed: dict) -> None:
    async with session.post(url, json={"embeds": [embed]}) as resp:
        if resp.status == 429:
            data = await resp.json()
            await asyncio.sleep(data.get("retry_after", 1))
            await send_webhook(session, url, embed)

async def process_message(session: aiohttp.ClientSession, message: dict) -> None:
    msg_id = str(message.get("id"))
    if not msg_id or msg_id in processed_ids:
        return
    timestamp_str = message.get("timestamp") or message.get("edited_timestamp")
    if not timestamp_str:
        return
    msg_time = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
    if msg_time < start_timestamp:
        return

    join_url = None
    for row in message.get("components", []):
        for button in row.get("components", []):
            if button.get("url") and "join" in button.get("label", "").lower():
                join_url = button["url"]
    if not join_url:
        return

    processed_ids.add(msg_id)

    for embed in message.get("embeds", []):
        brainrot_names: list[str] = []
        gains: list[str] = []

        carpet_spawn_found = False

        for field in embed.get("fields", []):
            fname = field.get("name", "").lower()
            fvalue = field.get("value", "").strip()

            # Detect Carpet Spawn special case
            if "carpet spawn" in fvalue.lower():
                carpet_spawn_found = True

            if "brainrot" in fname:
                brainrot_names += [clean_name(line) for line in fvalue.splitlines() if line.strip()]
            elif "gain" in fname:
                for line in fvalue.splitlines():
                    line = line.strip().replace("/s", "").replace(" per second", "")
                    formatted = format_money(line)
                    if formatted:
                        gains.append(formatted)

        if carpet_spawn_found:
            brainrot_names.append("Carpet Spawn")

        if not brainrot_names or not gains:
            continue

        for i, name in enumerate(brainrot_names):
            gain = gains[i] if i < len(gains) else gains[-1]
            print(f"[New] {name} | {gain}/s")
            real_embed = create_embed(name, gain, join_url)
            highlight_embed = create_embed(name, gain, HIGHLIGHTS_STATIC_URL)
            await send_webhook(session, REALHOOK, real_embed)
            await send_webhook(session, HIGHHOOK, highlight_embed)

async def main() -> None:
    global start_timestamp
    start_timestamp = datetime.now(timezone.utc)
    print("[Started] Brainrot monitor running")
    async with aiohttp.ClientSession() as session:
        while True:
            try:
                messages = await fetch_messages(session)
                for message in reversed(messages):
                    await process_message(session, message)
            except Exception as e:
                print("[Error]", e)
            await asyncio.sleep(POLL_DELAY)

if __name__ == "__main__":
    asyncio.run(main())

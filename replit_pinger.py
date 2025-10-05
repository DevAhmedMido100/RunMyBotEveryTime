#!/usr/bin/env python3
# replit_pinger.py
# Async lightweight pinger for keeping a Replit URL awake.
# Uses environment variables: TARGET_URL, INTERVAL (seconds)
# Requires: Python 3.8+ and aiohttp

import asyncio
import aiohttp
import os
from datetime import datetime
from collections import deque

# ---------- CONFIG (from env or defaults) ----------
URL = os.environ.get("TARGET_URL", "https://241b65da-9263-4e07-9ee2-8bb563cac6f5-00-1qyfe4bw1j31u.kirk.replit.dev/")
INTERVAL = float(os.environ.get("INTERVAL", "1.0"))   # seconds
TIMEOUT = int(os.environ.get("TIMEOUT", "5"))
LOG_FILE = os.environ.get("LOG_FILE", "pinger.log")
MAX_LOG_LINES = int(os.environ.get("MAX_LOG_LINES", "100"))
# ---------------------------------------------------

log_buffer = deque(maxlen=MAX_LOG_LINES)

def log(msg: str):
    timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3] + " UTC"
    line = f"[{timestamp}] {msg}"
    try:
        print(line, flush=True)
    except Exception:
        pass
    log_buffer.append(line)
    # Save occasionally
    if len(log_buffer) % 20 == 0:
        save_logs()

def save_logs():
    try:
        with open(LOG_FILE, "w", encoding="utf-8") as f:
            f.write("\n".join(log_buffer))
    except Exception:
        pass

async def ping_loop():
    connector = aiohttp.TCPConnector(limit=20, ssl=False)
    timeout = aiohttp.ClientTimeout(total=TIMEOUT)
    async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
        fails = 0
        while True:
            start = asyncio.get_event_loop().time()
            try:
                async with session.get(URL) as resp:
                    status = resp.status
                    elapsed = (asyncio.get_event_loop().time() - start) * 1000
                    log(f"✅ {status} - {elapsed:.1f} ms")
                    fails = 0
            except Exception as e:
                fails += 1
                log(f"❌ Error #{fails}: {repr(e)}")
                if fails >= 10:
                    log("⚠️ Too many errors, pausing for 5 seconds...")
                    await asyncio.sleep(5)
                    fails = 0
            elapsed_total = asyncio.get_event_loop().time() - start
            await asyncio.sleep(max(0, INTERVAL - elapsed_total))

def main():
    print("🚀 Replit Pinger Started")
    print(f"Target: {URL}")
    print(f"Interval: {INTERVAL}s | Timeout: {TIMEOUT}s\n")
    try:
        asyncio.run(ping_loop())
    except KeyboardInterrupt:
        save_logs()
        print("\n🛑 Stopped by user.")
    except Exception as e:
        print(f"Fatal error: {e}")
        save_logs()

if __name__ == "__main__":
    main()

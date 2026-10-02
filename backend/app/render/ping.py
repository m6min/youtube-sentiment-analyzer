import asyncio
import httpx
async def self_ping():
    """Pings the /health endpoint every 10 mins"""
    await asyncio.sleep(10)

    async with httpx.AsyncClient() as client:
        while True:
            try:
                response = await client.get(
                    "https://yt-analyzer-p56w.onrender.com/health",
                    timeout=10
                )
                print("Self-ping:", response.status_code)
            except Exception as e:
                print("Self-ping failed:", repr(e))

            await asyncio.sleep(600)
# twilio_dashboard_server.py

import asyncio
import json
import logging
from aiohttp import web, WSMsgType
from colorama import Fore, Style, init as colorama_init
from datetime import datetime

colorama_init(autoreset=True)
logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)

# In-memory store for dashboard data (extend with Redis or DB for production)
debug_logs = []
clients = set()

async def dashboard_ws_handler(request):
    ws = web.WebSocketResponse()
    await ws.prepare(request)
    clients.add(ws)
    logger.info(f"{Fore.BLUE}[DASH] Dashboard client connected{Style.RESET_ALL}\n")

    try:
        async for msg in ws:
            if msg.type == WSMsgType.TEXT:
                pass  # dashboard is read-only
    finally:
        clients.remove(ws)
        logger.info(f"{Fore.BLUE}[DASH] Dashboard client disconnected{Style.RESET_ALL}\n")

    return ws

async def receive_debug_event(request):
    try:
        body = await request.text()
        data = json.loads(body)
        timestamp = datetime.utcnow().isoformat()
        event = {
            "timestamp": timestamp,
            "type": data.get("type"),
            "name": data.get("name"),
            "value": data.get("value")
        }
        debug_logs.append(event)

        # Keep it small and fast for demo
        if len(debug_logs) > 1000:
            debug_logs.pop(0)

        # Broadcast to all connected dashboard clients
        for client in clients:
            try:
                await client.send_str(json.dumps(event))
            except Exception as e:
                logger.error(f"[ERR] Dashboard broadcast failed: {e}\n")

        logger.info(f"{Fore.MAGENTA}[SPI] Debug event: {event}{Style.RESET_ALL}\n")
        return web.Response(text="OK")

    except Exception as e:
        logger.error(f"{Fore.RED}[ERR] Failed to process debug event: {e}{Style.RESET_ALL}\n")
        return web.Response(status=500, text="Internal Server Error")


async def start_server():
    app = web.Application()
    app.router.add_post("/event", receive_debug_event)
    app.router.add_get("/dashboard", dashboard_ws_handler)
    app.router.add_get("/", lambda r: web.FileResponse("dashboard.html"))
    app.router.add_get("/style.css", lambda r: web.FileResponse("style.css"))
    app.router.add_get("/script.js", lambda r: web.FileResponse("script.js"))

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "localhost", 9000)
    await site.start()
    logger.info(f"{Fore.BLUE}[SYS] Dashboard server running on http://localhost:9000{Style.RESET_ALL}\n")

if __name__ == "__main__":
    try:
        asyncio.run(start_server())
    except KeyboardInterrupt:
        logger.info("[SYS] Server stopped by user")

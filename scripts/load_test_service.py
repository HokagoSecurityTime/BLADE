"""Child service for the process-isolated local benchmark only."""
import argparse
import asyncio
from pathlib import Path

from aiohttp import web
import uvicorn


async def main(args: argparse.Namespace) -> None:
    if args.role == 'proxy':
        from proxy.server import create_app
        runner = web.AppRunner(create_app())
        await runner.setup()
        await web.TCPSite(runner, '127.0.0.1', args.port).start()
        try:
            while not args.stop.exists():
                await asyncio.sleep(.1)
        finally:
            await runner.cleanup()
        return
    if args.role == 'backend':
        from demo_backend.main import create_app
        app = create_app(args.db)
    else:
        from admin_api.main import create_app
        app = create_app(args.db, args.db.parent/'policies', args.db.parent/'detections.jsonl')
    server = uvicorn.Server(uvicorn.Config(app, host='127.0.0.1', port=args.port, log_level='error'))
    serving = asyncio.create_task(server.serve())
    try:
        while not args.stop.exists() and not serving.done():
            await asyncio.sleep(.1)
    finally:
        server.should_exit = True
        await serving


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('role', choices=['proxy', 'backend', 'admin'])
    parser.add_argument('--db', type=Path, required=True)
    parser.add_argument('--port', type=int, required=True)
    parser.add_argument('--stop', type=Path, required=True)
    asyncio.run(main(parser.parse_args()))

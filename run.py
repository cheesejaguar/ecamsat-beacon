#!/usr/bin/env python3
"""
Run the EcAMSat Beacon Decoder API server.

Usage:
    python run.py [--host HOST] [--port PORT] [--reload]
"""

import argparse
import uvicorn


def main():
    parser = argparse.ArgumentParser(description="Run the EcAMSat Beacon Decoder API")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind to (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind to (default: 8000)")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload for development")

    args = parser.parse_args()

    print(f"""
    ╔══════════════════════════════════════════════╗
    ║     EcAMSat Beacon Decoder API Server        ║
    ╠══════════════════════════════════════════════╣
    ║  Running at: http://{args.host}:{args.port:<5}              ║
    ║  API Docs:   http://{args.host}:{args.port:<5}/docs         ║
    ╚══════════════════════════════════════════════╝
    """)

    uvicorn.run(
        "backend.main:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
    )


if __name__ == "__main__":
    main()

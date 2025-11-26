#!/usr/bin/env python3
import asyncio
from blaxel.core import SandboxInstance

async def main():
    # Create a new sandbox
    sandbox = await SandboxInstance.create_if_not_exists({
      "name": "mcp-hack-sandbox",
      "image": "blaxel/nextjs:latest",   # public or custom image
      "memory": 4096,   # in MB
      "ports": [{ "target": 3000 }],   # ports to expose
      "region": "us-pdx-1"   # if not specified, Blaxel will choose a default region
    })
    print(f"Sandbox created: {sandbox}")

    # ADD REST OF CODE HERE

if __name__ == "__main__":
    asyncio.run(main())
from blaxel.core import SandboxInstance

import asyncio
import logging

logger = logging.getLogger(__name__)


async def main():
    sandbox_name = "mcp-hack-sandbox"
    try:
        # Retrieve the sandbox
        sandbox = await SandboxInstance.get(sandbox_name)

        # Test filesystem
        dir = await sandbox.fs.ls("/etc")
        logger.info(f"Files: {dir.files}")

        # Test process
        process = await sandbox.process.exec({"name": "test", "command": "echo 'Hello world'"})
        await asyncio.sleep(0.01)

        # Retrieve process logs
        logs = await sandbox.process.logs("test")
        logger.info(f"Logs: {logs}");

    except Exception as e:
        logger.error(f"Error => {e}")

if __name__ == "__main__":
    asyncio.run(main())
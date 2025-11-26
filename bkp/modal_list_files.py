import modal
import os

app = modal.App()

vol = modal.Volume.from_name("mcp-hack-ins-products")
for path in vol.listdir("/"):
    print(path)


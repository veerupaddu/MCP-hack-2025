import modal
import os

app = modal.App()

vol = modal.Volume.from_name("mcp-hack-ins-products", create_if_missing=True)

# Upload files from local directory to volume
local_dir = "/Users/veeru/Downloads/products"  # Replace with your local directory
with vol.batch_upload() as batch:
    import os
    for root, dirs, files in os.walk(local_dir):
        for filename in files:
            local_path = os.path.join(root, filename)
            relative_path = os.path.relpath(local_path, local_dir)
            remote_path = f"/{relative_path}"
            batch.put_file(local_path, remote_path)

print("Files uploaded successfully!")

vol = modal.Volume.from_name("my-volume")
for path in vol.listdir("/"):
    print(path)


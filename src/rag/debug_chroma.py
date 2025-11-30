import modal

app = modal.App("debug-chroma")
vol = modal.Volume.from_name("mcp-hack-ins-products")

image = modal.Image.debian_slim().pip_install("chromadb")

@app.function(image=image, volumes={"/data": vol})
def check_db():
    import chromadb
    import os
    
    print(f"Listing /data/chroma_db:")
    print(os.listdir("/data/chroma_db"))
    
    client = chromadb.PersistentClient(path="/data/chroma_db")
    print("\nCollections:")
    collections = client.list_collections()
    for col in collections:
        print(f"- {col.name} (count: {col.count()})")

@app.local_entrypoint()
def main():
    check_db.remote()

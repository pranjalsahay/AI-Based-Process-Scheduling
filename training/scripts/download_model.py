import os
import sys
import time
import requests
from pathlib import Path

def download_file(url: str, dest_path: Path):
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = dest_path.with_suffix(".part")

    existing_bytes = temp_path.stat().st_size if temp_path.exists() else 0
    headers = {}
    if existing_bytes > 0:
        headers["Range"] = f"bytes={existing_bytes}-"
        print(f"Resuming {dest_path.name} from {existing_bytes / (1024**2):.1f} MB...", flush=True)
    else:
        print(f"Downloading {dest_path.name}...", flush=True)

    t0 = time.time()
    try:
        r = requests.get(url, headers=headers, stream=True, timeout=30)
    except Exception as e:
        # Fallback to direct HF url if mirror fails
        alt_url = url.replace("hf-mirror.com", "huggingface.co")
        print(f"Mirror failed ({e}), falling back to {alt_url}...", flush=True)
        r = requests.get(alt_url, headers=headers, stream=True, timeout=30)

    total_size = int(r.headers.get("content-length", 0)) + existing_bytes
    mode = "ab" if existing_bytes > 0 else "wb"

    downloaded = existing_bytes
    last_print = time.time()

    with open(temp_path, mode) as f:
        for chunk in r.iter_content(chunk_size=1024 * 1024):
            if chunk:
                f.write(chunk)
                downloaded += len(chunk)
                if time.time() - last_print > 2.0:
                    speed = (downloaded - existing_bytes) / (1024 * 1024 * max(time.time() - t0, 0.1))
                    pct = (downloaded / total_size * 100) if total_size > 0 else 0
                    print(f"Progress: {downloaded / (1024**2):.1f} MB / {total_size / (1024**2):.1f} MB ({pct:.1f}%) at {speed:.2f} MB/s", flush=True)
                    last_print = time.time()

    if temp_path.exists():
        if dest_path.exists():
            dest_path.unlink()
        temp_path.rename(dest_path)
    print(f"Successfully downloaded {dest_path.name} ({dest_path.stat().st_size / (1024**2):.1f} MB) in {time.time()-t0:.2f}s", flush=True)

if __name__ == "__main__":
    target_dir = Path("training/base_model")
    target_dir.mkdir(parents=True, exist_ok=True)

    files = [
        "config.json",
        "generation_config.json",
        "tokenizer.json",
        "tokenizer_config.json",
        "vocab.json",
        "merges.txt",
        "model.safetensors"
    ]

    base_url = "https://hf-mirror.com/Qwen/Qwen2.5-0.5B-Instruct/resolve/main"

    for f in files:
        dest = target_dir / f
        if dest.exists() and dest.stat().st_size > 0:
            print(f"File already exists: {dest.name} ({dest.stat().st_size / (1024**2):.2f} MB)", flush=True)
            continue
        download_file(f"{base_url}/{f}", dest)

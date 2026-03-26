import os
import sys
from pathlib import Path
import requests

API_BASE = "https://my-agent-swart.vercel.app"
UPLOAD_URL = f"{API_BASE}/api/upload/"

SUPPORTED = {".pdf", ".txt", ".docx", ".md", ".jpg", ".jpeg", ".png", ".wav", ".mp3", ".m4a"}

def upload_file(path: Path):
    with path.open("rb") as f:
        files = {"file": (path.name, f)}
        r = requests.post(UPLOAD_URL, files=files, timeout=120)
    if r.ok:
        print(f"OK  {path.name} -> {r.json()}")
    else:
        print(f"ERR {path.name} -> {r.status_code} {r.text}")

def collect_files(target: Path):
    if target.is_file():
        return [target]
    return [p for p in target.rglob("*") if p.is_file() and p.suffix.lower() in SUPPORTED]

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python upload_prod.py <file-or-folder>")
        sys.exit(1)

    target = Path(sys.argv[1])
    files = collect_files(target)
    if not files:
        print("No supported files found.")
        sys.exit(0)

    for p in files:
        upload_file(p)
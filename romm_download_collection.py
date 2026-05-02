#!/usr/bin/env python3
"""
RomM Collection Downloader
Downloads all ROMs from a given RomM collection ID.

Usage:
    pip install requests python-dotenv
    python romm_download_collection.py

Configure the variables in a .env file before running.
"""

import os
import sys
import time
import logging
import argparse
import requests
from pathlib import Path
from dotenv import load_dotenv
from collections import defaultdict
from datetime import datetime
from romm_sync_config import resolve_onion_folder_for_romm_slug

load_dotenv()


def require_env(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        print(f"Missing required environment variable: {name}")
        print("Create a .env file from .env.example and fill in values.")
        sys.exit(1)
    return value


def env_int(name: str, default: int) -> int:
    raw = os.getenv(name, "").strip()
    if not raw:
        return default
    try:
        return int(raw)
    except ValueError:
        print(f"Invalid integer for {name}: {raw}")
        sys.exit(1)


BASE_URL = require_env("ROMM_BASE_URL")
USERNAME = require_env("ROMM_USERNAME")
PASSWORD = require_env("ROMM_PASSWORD")
COLLECTION_ID = env_int("ROMM_COLLECTION_ID", 1)
OUTPUT_DIR = os.getenv("ROMM_OUTPUT_DIR", "./downloads")

CHUNK_SIZE  = 1024 * 1024  # 1 MB read chunks for streaming large files
PAGE_SIZE   = 100           # ROMs per API page
LOG_DIR = Path("./logs")
LOGGER = logging.getLogger("romm-downloader")


def setup_logging() -> Path:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = LOG_DIR / f"romm_download_{timestamp}.log"

    LOGGER.setLevel(logging.INFO)
    LOGGER.handlers.clear()
    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setFormatter(
        logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
    )
    LOGGER.addHandler(file_handler)
    return log_file


def log(message: str) -> None:
    print(message)
    LOGGER.info(message)


def get_file_name(rom: dict) -> str | None:
    """
    RomM response shapes vary by version. Try known file name fields.
    """
    file_name = (
        rom.get("file_name")
        or rom.get("fs_name")
        or rom.get("fs_resources", {}).get("file_name")
    )
    if file_name:
        return file_name

    files = rom.get("files")
    if isinstance(files, list) and files:
        first = files[0]
        if isinstance(first, dict):
            return first.get("file_name")
    return None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Download all ROMs in a RomM collection.")
    parser.add_argument(
        "--onionos",
        action="store_true",
        help="Save files into OnionOS-mapped folders under downloads/onionos.",
    )
    return parser.parse_args()


def get_destination_dir(output_dir: Path, platform_slug: str, sync_onionos: bool) -> Path:
    if not sync_onionos:
        return output_dir / platform_slug

    onion_folder = resolve_onion_folder_for_romm_slug(platform_slug)
    if onion_folder:
        return output_dir / onion_folder

    # Fallback keeps downloads working for unmapped platforms.
    log(f"  [WARN] No OnionOS mapping for RomM slug '{platform_slug}'. Falling back to '{platform_slug}'.")
    return output_dir / platform_slug


def get_session() -> requests.Session:
    session = requests.Session()
    session.auth = (USERNAME, PASSWORD)
    return session


def fetch_collection_roms(session: requests.Session) -> list[dict]:
    """
    Fetch all ROMs in the collection, handling pagination.
    RomM returns results in pages; we keep fetching until we have them all.
    """
    roms = []
    offset = 0

    log(f"Fetching ROM list for collection {COLLECTION_ID}...")

    while True:
        params = {
            "collection_id": COLLECTION_ID,
            "limit": PAGE_SIZE,
            "offset": offset,
        }
        resp = session.get(f"{BASE_URL}/api/roms", params=params, timeout=30)
        resp.raise_for_status()
        data = resp.json()

        # The API returns either a list directly or a dict with an 'items' key
        # depending on the RomM version -- handle both.
        if isinstance(data, list):
            batch = data
            # No pagination metadata available; stop when we get fewer than PAGE_SIZE
            roms.extend(batch)
            if len(batch) < PAGE_SIZE:
                break
            offset += PAGE_SIZE
        elif isinstance(data, dict):
            batch = data.get("items", [])
            roms.extend(batch)
            total = data.get("total", len(roms))
            offset += PAGE_SIZE
            if offset >= total or not batch:
                break
        else:
            log("Unexpected API response format. Check your credentials and BASE_URL.")
            sys.exit(1)

    log(f"Found {len(roms)} ROM(s) in collection {COLLECTION_ID}.")
    return roms


def download_rom(
    session: requests.Session,
    rom: dict,
    output_dir: Path,
    sync_onionos: bool,
) -> tuple[str, Path | None]:
    """
    Download a single ROM file. Streams the response to avoid loading
    large files into memory all at once.

    Returns (status, dest_path) where status is one of:
        downloaded, skipped_exists, skipped_incomplete, failed
    """
    rom_id    = rom.get("id")
    file_name = get_file_name(rom)
    platform  = rom.get("platform_slug") or rom.get("platform", {}).get("slug", "unknown")

    if not rom_id or not file_name:
        log(f"  [SKIP] Incomplete ROM data: id={rom_id}, name={rom.get('name', 'Unknown')}")
        return ("skipped_incomplete", None)

    dest_dir = get_destination_dir(output_dir, platform, sync_onionos)
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest_path = dest_dir / file_name

    if dest_path.exists():
        log(f"  [SKIP] Already exists: {dest_path}")
        return ("skipped_exists", dest_path)

    url = f"{BASE_URL}/api/roms/{rom_id}/content/{requests.utils.quote(file_name)}"

    try:
        with session.get(url, stream=True, timeout=60) as resp:
            resp.raise_for_status()
            total_bytes = int(resp.headers.get("Content-Length", 0))
            downloaded  = 0

            with open(dest_path, "wb") as f:
                for chunk in resp.iter_content(chunk_size=CHUNK_SIZE):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if total_bytes:
                            pct = downloaded / total_bytes * 100
                            print(f"\r  {pct:5.1f}%  {file_name}", end="", flush=True)

        log(f"  [OK]   {file_name} ({downloaded / 1024 / 1024:.1f} MB)")
        return ("downloaded", dest_path)

    except requests.HTTPError as e:
        log(f"  [FAIL] {file_name} — HTTP {e.response.status_code}")
        if dest_path.exists():
            dest_path.unlink()  # Remove partial file
        return ("failed", None)

    except Exception as e:
        log(f"  [FAIL] {file_name} — {e}")
        LOGGER.exception("Unhandled download exception")
        if dest_path.exists():
            dest_path.unlink()
        return ("failed", None)


def main():
    args = parse_args()
    log_file = setup_logging()
    log(f"Log file: {log_file.resolve()}")

    output_root = Path(OUTPUT_DIR)
    mode_folder = "onionos" if args.onionos else "romm"
    output_dir = output_root / mode_folder
    output_dir.mkdir(parents=True, exist_ok=True)
    if args.onionos:
        log(f"OnionOS mapping enabled. Saving under: {output_dir.resolve()}")
    else:
        log(f"Standard RomM folders enabled. Saving under: {output_dir.resolve()}")

    session = get_session()

    # Quick auth check
    try:
        resp = session.get(f"{BASE_URL}/api/users/me", timeout=10)
        resp.raise_for_status()
        user = resp.json()
        log(f"Authenticated as: {user.get('username', USERNAME)}")
    except requests.HTTPError as e:
        log(f"Auth failed (HTTP {e.response.status_code}). Check your credentials.")
        sys.exit(1)
    except requests.ConnectionError:
        log(f"Cannot connect to {BASE_URL}. Check BASE_URL.")
        sys.exit(1)

    roms = fetch_collection_roms(session)

    if not roms:
        log("No ROMs found. Check that COLLECTION_ID is correct.")
        sys.exit(0)

    new_by_folder: dict[str, list[str]] = defaultdict(list)
    new_count = 0
    skipped_exists = 0
    skipped_incomplete = 0
    failed = 0

    for i, rom in enumerate(roms, 1):
        name = rom.get("name") or get_file_name(rom) or "Unknown"
        log(f"\n[{i}/{len(roms)}] {name}")
        status, dest_path = download_rom(session, rom, output_dir, args.onionos)
        if status == "downloaded" and dest_path:
            new_count += 1
            out_base = output_dir.resolve()
            parent = dest_path.parent.resolve()
            try:
                rel = parent.relative_to(out_base)
            except ValueError:
                rel = dest_path.parent.relative_to(output_dir)
            folder_key = str(rel).replace("\\", "/") or "."
            new_by_folder[folder_key].append(dest_path.name)
        elif status == "skipped_exists":
            skipped_exists += 1
        elif status == "skipped_incomplete":
            skipped_incomplete += 1
        else:
            failed += 1
        # Small delay to be polite to the server
        time.sleep(0.25)

    log(f"\n{'─' * 40}")
    log(
        f"Done. {new_count} new file(s), {skipped_exists} skipped (already present), "
        f"{skipped_incomplete} skipped (incomplete data), {failed} failed. "
        f"Output: {output_dir.resolve()}"
    )

    if new_by_folder:
        log("\nNew downloads by folder:")
        for folder in sorted(new_by_folder.keys()):
            log(f"  {folder}/")
            for fname in sorted(new_by_folder[folder]):
                log(f"    {fname}")
    else:
        log("\nNo new files downloaded (everything was already present, skipped, or failed).")


if __name__ == "__main__":
    main()

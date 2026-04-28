# romm-bulk-downloader

Bulk-download every ROM from a specific RomM collection using the RomM API.

## What this script does

- Authenticates to your RomM instance with username/password credentials.
- Fetches every ROM in a collection using paginated API requests.
- Downloads ROM files with streaming to handle large files efficiently.
- Skips files that are already present locally.
- Organizes downloaded files by platform inside the output directory.

## Requirements

- Python 3.9+
- RomM instance URL and valid user credentials
- Python packages:
  - `requests`
  - `python-dotenv`

## Install dependencies (recommended: virtual environment)

macOS/Homebrew Python can block global installs. Use a local virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

## Configuration

Create a local `.env` file from the example:

`cp .env.example .env`

Then edit `.env`:

```env
ROMM_BASE_URL=https://romm.example.com
ROMM_USERNAME=your_username
ROMM_PASSWORD=your_password
ROMM_COLLECTION_ID=1
ROMM_OUTPUT_DIR=./downloads
```

### Environment variables

- `ROMM_BASE_URL` (required): Base URL for RomM, e.g. `https://romm.lucipher.com`
- `ROMM_USERNAME` (required): RomM username
- `ROMM_PASSWORD` (required): RomM password
- `ROMM_COLLECTION_ID` (optional): Collection numeric ID (default: `1`)
- `ROMM_OUTPUT_DIR` (optional): Download folder (default: `./downloads`)

## Run

`python romm_download_collection.py`

The script will create the output directory if needed (you already added `downloads/`) and then save ROMs in platform subfolders, for example:

- `downloads/nes/...`
- `downloads/snes/...`

Each run also writes a timestamped log file in `logs/`, for example:

- `logs/romm_download_20260428_100301.log`

## Notes

- Keep `.env` private and out of source control (already ignored by `.gitignore`).
- Commit `.env.example` so others can configure the script safely.

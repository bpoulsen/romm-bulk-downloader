# romm-bulk-downloader

Bulk-download every ROM file from a specific RomM collection using the RomM API.

## RomM Links

- RomM project: [https://romm.app/](https://romm.app/)
- RomM API reference: [https://docs.romm.app/latest/API-and-Development/API-Reference/](https://docs.romm.app/latest/API-and-Development/API-Reference/)

## What this script does

- Authenticates to your RomM instance with username/password credentials.
- Fetches every ROM in a collection using paginated API requests.
- Downloads ROM files with streaming to handle large files efficiently.
- Skips files that are already present locally.
- Organizes downloaded files by platform inside the output directory.
- When the run finishes, prints a **summary** (counts of new files, skipped, and failures) and lists **only newly downloaded** files grouped by subfolder. The same text is appended to the run’s log file in `logs/`.

## Requirements

- Python 3.9+
- RomM instance URL and valid user credentials
- Python packages:
  - `requests`
  - `python-dotenv`

## Install dependencies (recommended: virtual environment)

Choose the commands for your platform:

### macOS / Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

### Windows (PowerShell)

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

### Windows (Command Prompt)

```bat
py -m venv .venv
.venv\Scripts\activate.bat
python -m pip install -r requirements.txt
```

If you are not on macOS/Homebrew and prefer not to use a virtual environment, you can install dependencies globally:

```bash
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

To use OnionOS folder mapping:

`python romm_download_collection.py --onionos`

On Windows, you can also run:

`py romm_download_collection.py`

The script will create the output directory if needed and save ROMs in platform subfolders:

- Default mode: `downloads/romm/<romm-platform-slug>/...`
- OnionOS mode (`--onionos`): `downloads/onionos/<onion-folder>/...`

Examples:

- `downloads/romm/gb/...`
- `downloads/onionos/GBA/...`

### OnionOS layout (`--onionos`)

RomM platform slugs are mapped to OnionOS-style folder names (e.g. `gba` → `GBA`) using `romm_sync_config.py`. Edit that file if a slug on your server does not match the table.

### After the run

The script prints a line like:

`Done. X new file(s), Y skipped (already present), Z skipped (incomplete data), W failed. Output: …`

If any files were **newly downloaded** this run (not skipped because they already existed), it then prints **New downloads by folder:** with each subfolder under `romm/` or `onionos/` and the filenames underneath.

### Logs

Each run writes a timestamped log file in `logs/`, for example:

- `logs/romm_download_20260428_100301.log`

The log includes the same completion summary and new-download listing as the console.

## Troubleshooting (Windows)

- **PowerShell blocks activation script**
  - Error example: `running scripts is disabled on this system`
  - Fix for current PowerShell session:
    - `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass`
  - Then activate again:
    - `.venv\Scripts\Activate.ps1`
- **`py` command is not found**
  - Use Python directly instead:
    - `python -m venv .venv`
    - `python romm_download_collection.py`
  - If `python` is also not found, install Python from [python.org](https://www.python.org/downloads/windows/) and enable "Add Python to PATH" during setup.
- **Dependencies still missing after install**
  - Ensure the venv is activated before running:
    - `.venv\Scripts\Activate.ps1` (PowerShell)
    - `.venv\Scripts\activate.bat` (Command Prompt)
  - Reinstall dependencies:
    - `python -m pip install -r requirements.txt`

## Disclaimer

This is an independent community project and is not affiliated with, endorsed by, or maintained by the official RomM project.


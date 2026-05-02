"""
romm_sync_config.py

Mapping config and helpers for syncing ROM downloads to a
Miyoo Mini Plus running OnionOS.

Usage:
    from romm_sync_config import (
        resolve_onion_folder_for_romm_slug,
    )
"""

from dataclasses import dataclass
from typing import Optional


# ---------------------------------------------------------------------------
# Platform map: OnionOS folder -> (system name, RomM slug)
# A None slug means no clean IGDB match exists.
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Platform:
    onion_folder: str
    system_name: str
    romm_slug: Optional[str]
    notes: str = ""


PLATFORMS: list[Platform] = [
    Platform("AMIGA",       "Amiga",                        "amiga"),
    Platform("ARCADE",      "Arcade (FBNeo)",               "arcade",       notes="all arcade variants share this slug"),
    Platform("MAME",        "MAME",                         "arcade",       notes="all arcade variants share this slug"),
    Platform("CPS1",        "Capcom Play System",           "cps1"),
    Platform("CPS2",        "Capcom Play System 2",         "cps2"),
    Platform("CPS3",        "Capcom Play System 3",         "cps3"),
    Platform("LYNX",        "Atari Lynx",                   "lynx"),
    Platform("ATARI2600",   "Atari 2600",                   "atari2600"),
    Platform("ATARI5200",   "Atari 5200",                   "atari5200"),
    Platform("ATARI7800",   "Atari 7800",                   "atari7800"),
    Platform("COLECO",      "ColecoVision",                 "colecovision"),
    Platform("GW",          "Game & Watch",                 "game-and-watch"),
    Platform("GG",          "Game Gear",                    "gamegear"),
    Platform("GB",          "Game Boy",                     "gb"),
    Platform("GBA",         "Game Boy Advance",             "gba"),
    Platform("GBC",         "Game Boy Color",               "gbc"),
    Platform("INTELLIVISION","Intellivision",               "intellivision"),
    Platform("MSX",         "MSX",                          "msx"),
    Platform("MSX2",        "MSX2",                         "msx2",         notes="slug unconfirmed"),
    Platform("N64",         "Nintendo 64",                  "n64"),
    Platform("NDS",         "Nintendo DS",                  "nds"),
    Platform("NEOGEO",      "Neo Geo",                      "neo-geo"),
    Platform("NEOCD",       "Neo Geo CD",                   "neo-geo-cd"),
    Platform("NGP",         "Neo Geo Pocket",               "neo-geo-pocket"),
    Platform("NGPC",        "Neo Geo Pocket Color",         "neo-geo-pocket-color"),
    Platform("FC",          "NES / Famicom",                "nes"),
    Platform("PICO",        "Pico-8",                       "pico-8"),
    Platform("POKEMON",     "Pokemon Mini",                 "pokemon-mini"),
    Platform("PS",          "PlayStation",                  "psx"),
    Platform("PSP",         "PlayStation Portable",         "psp"),
    Platform("SCUMMVM",     "ScummVM",                      "scummvm",      notes="slug unconfirmed"),
    Platform("SEGACD",      "Sega CD / Mega CD",            "segacd"),
    Platform("MS",         "Sega Master System",            "sms"),
    Platform("MD",          "Sega Genesis / Mega Drive",    "genesis"),
    Platform("SEGASGONE",   "Sega SG-1000",                 "sg1000"),
    Platform("SFC",         "SNES / Super Famicom",         "snes"),
    Platform("PCE",         "PC Engine / TurboGrafx-16",    "tg16"),
    Platform("PCECD",       "PC Engine CD",                 "turbografx-cd"),
    Platform("VECTREX",     "Vectrex",                      "vectrex"),
    Platform("VB",          "Virtual Boy",                  "virtualboy"),
    Platform("WSC",         "WonderSwan",                   "wonderswan"),
    Platform("WSC",         "WonderSwan Color",             "wonderswan-color"),
    Platform("PORTS",       "Ports",                        None,           notes="no clean IGDB match"),
]

# Lookup index built at import time
SLUG_TO_PLATFORMS: dict[str, list[Platform]] = {}
for _p in PLATFORMS:
    if _p.romm_slug:
        SLUG_TO_PLATFORMS.setdefault(_p.romm_slug.lower(), []).append(_p)


# ---------------------------------------------------------------------------
# Helper function used by downloader
# ---------------------------------------------------------------------------

def resolve_onion_folder_for_romm_slug(romm_slug: str) -> Optional[str]:
    """
    Return OnionOS folder name for a RomM platform slug.
    If multiple Onion folders share a slug (e.g. arcade variants),
    return the first configured folder.
    """
    normalized_slug = (romm_slug or "").strip().lower()
    matches = SLUG_TO_PLATFORMS.get(normalized_slug)
    if not matches:
        return None
    return matches[0].onion_folder
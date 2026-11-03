"""Diagnostics (Settings → Devices & services → Degree Dealer → ⋮ → Download diagnostics).

The options, the latest calculation and what has been learnt. Room and area names can be
personal (a child's room): every area id and area name is replaced by room_<n> everywhere,
also inside entity ids and as dictionary keys, and other names are redacted.
"""
from __future__ import annotations

import dataclasses
import json
import re
from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import area_registry as ar

from .const import CONF_ROOMS, ROOM_AREA

TO_REDACT = {"name", "title"}


def _aliases(hass: HomeAssistant, options: dict[str, Any]) -> dict[str, str]:
    """area id / area name -> room_<n>, longest first so a name is not replaced inside a longer one."""
    areas = ar.async_get(hass)
    aliases: dict[str, str] = {}
    for index, room in enumerate(options.get(CONF_ROOMS) or [], 1):
        area_id = room.get(ROOM_AREA)
        if not area_id:
            continue
        aliases[area_id] = f"room_{index}"
        if (area := areas.async_get_area(area_id)) is not None:
            aliases[area.name] = f"room_{index}"
            aliases[area.name.lower().replace(" ", "_")] = f"room_{index}"
    return dict(sorted(aliases.items(), key=lambda item: len(item[0]), reverse=True))


async def async_get_config_entry_diagnostics(hass: HomeAssistant, entry: ConfigEntry) -> dict[str, Any]:
    coordinator = entry.runtime_data
    data = coordinator.data
    options = {**entry.data, **entry.options}
    diagnostics = {
        "options": options,
        "data": dataclasses.asdict(data) if data is not None else None,
        "learning": coordinator.learner.to_dict(),
        "history_running": coordinator.history_running,
    }
    # plain JSON values (datetimes, tuples), then the rooms are replaced in the text
    text = json.dumps(diagnostics, ensure_ascii=False, default=str)
    for name, alias in _aliases(hass, options).items():
        text = re.sub(rf"(?<![A-Za-z0-9]){re.escape(name)}(?![A-Za-z0-9])", alias, text, flags=re.IGNORECASE)
    return async_redact_data(json.loads(text), TO_REDACT)

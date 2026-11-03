"""Diagnostics download (diagnostics.py): options, latest calculation and learning, names redacted."""
from __future__ import annotations

import json

from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.degree_dealer.diagnostics import async_get_config_entry_diagnostics

from .conftest import set_plant


async def test_diagnostics(hass: HomeAssistant, entry: MockConfigEntry) -> None:
    set_plant(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    data = await async_get_config_entry_diagnostics(hass, entry)
    text = json.dumps(data)

    assert data["options"]["rooms"]
    assert data["data"]["supply"] == 45.0
    assert "rooms" in data["learning"]
    assert {room["area_id"] for room in data["options"]["rooms"]} == {"room_1", "room_2"}
    for name in ("Living room", "Bathroom", "living_room", "bathroom"):
        assert name not in text, name

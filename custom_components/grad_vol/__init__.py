"""The Gradual Volume Control integration."""
import asyncio
import logging
import math
from typing import Set

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import device_registry as dr, entity_registry as er

from .const import DOMAIN

# Pre-import config_flow to avoid blocking import during async operations
from . import config_flow

_LOGGER = logging.getLogger(__name__)


async def async_setup(hass: HomeAssistant, config: dict):
    """Set up the Gradual Volume Control integration."""
    # We're using config entries (config flow), so we don't need to set up anything here.
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up Gradual Volume Control from a config entry."""
    # Register services when the entry is set up
    hass.data.setdefault(DOMAIN, {})

    async def handle_set_volume(call: ServiceCall):
        """Handle the service call."""
        volume = float(call.data.get('volume'))
        span = call.data.get('duration', 5)

        # Resolve the target to entity IDs
        entity_ids = await _async_get_media_player_entities(hass, call.data.get('target'))

        if not entity_ids:
            _LOGGER.warning("No available media player entities found for the target.")
            return

        # Convert target volume to integer percentage
        target_volume_int = int(round(volume * 100))

        # For each entity, start the volume adjustment process
        tasks = [
            adjust_volume(hass, entity_id, target_volume_int, span)
            for entity_id in entity_ids
        ]

        # Wait for all volume adjustments to complete
        await asyncio.gather(*tasks)

    async def adjust_volume(hass: HomeAssistant, entity_id: str, target_volume_int: int, span: float):
        """Adjust the volume of a single entity over time using a sine easing function."""
        state = hass.states.get(entity_id)

        # Skip if the entity is unavailable or off
        if state is None or state.state in ('unavailable', 'unknown', 'off'):
            # Entity is unavailable, skip without logging a warning
            return

        volume = state.attributes.get('volume_level')

        if volume is None:
            _LOGGER.warning("Entity %s has no volume_level attribute. Skipping.", entity_id)
            return

        # Convert current volume to integer percentage
        volume_int = int(round(float(volume) * 100))

        if volume_int == target_volume_int:
            # Already at target volume, no adjustment needed
            return

        # Determine the direction of volume change
        step = 1 if target_volume_int > volume_int else -1

        # Calculate the total number of steps
        volume_diff = abs(target_volume_int - volume_int)
        steps = volume_diff

        if steps == 0:
            # No volume change needed
            return

        # Handle the case where steps <= 1
        if steps <= 1 or span <= 0:
            # Adjust the volume immediately
            scheduled_volume = target_volume_int / 100.0
            await hass.services.async_call(
                'media_player',
                'volume_set',
                {'entity_id': entity_id, 'volume_level': scheduled_volume},
                blocking=False
            )
            return

        # Calculate the time interval between steps
        time_interval = span / steps

        # Start the volume adjustment loop
        for i in range(1, steps + 1):
            fraction = i / steps  # Progress fraction from 0 to 1

            # Sine easing calculation
            adjustment = math.sin(fraction * (math.pi / 2))  # Varies from 0 to 1
            volume_change = int(round(volume_diff * adjustment))
            scheduled_volume_int = volume_int + step * volume_change

            # Ensure the final volume is set precisely to the target
            if i == steps:
                scheduled_volume_int = target_volume_int

            # Convert back to decimal representation
            scheduled_volume = scheduled_volume_int / 100.0

            # Adjust the volume
            await hass.services.async_call(
                'media_player',
                'volume_set',
                {'entity_id': entity_id, 'volume_level': scheduled_volume},
                blocking=False
            )

            if i < steps:
                # Wait for the time interval before the next adjustment
                await asyncio.sleep(time_interval)

    # Register the service with the updated schema
    hass.services.async_register(DOMAIN, "set_volume", handle_set_volume)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Handle removal of an entry."""
    hass.services.async_remove(DOMAIN, "set_volume")
    return True


async def _async_get_media_player_entities(hass: HomeAssistant, target) -> Set[str]:
    """Resolve the target into a set of media player entity IDs."""
    entity_ids: Set[str] = set()

    # Get entity IDs from entities
    if target.get('entity_id'):
        entity_ids.update(target['entity_id'])

    # Get entity IDs from devices
    if target.get('device_id'):
        device_registry = dr.async_get(hass)
        entity_registry = er.async_get(hass)
        for device_id in target['device_id']:
            # Get entities for this device
            entries = er.async_entries_for_device(
                entity_registry, device_id, include_disabled_entities=False
            )
            entity_ids.update(
                entry.entity_id for entry in entries if entry.domain == 'media_player'
            )

    # Get entity IDs from areas
    if target.get('area_id'):
        entity_registry = er.async_get(hass)
        for area_id in target['area_id']:
            # Get entities for this area
            entries = er.async_entries_for_area(
                entity_registry, area_id
            )
            entity_ids.update(
                entry.entity_id for entry in entries if entry.domain == 'media_player'
            )

    # **Handle Labels**
    if target.get('label'):
        entity_registry = er.async_get(hass)
        for label in target['label']:
            # Get entities for this label
            entries = [
                entry for entry in entity_registry.entities.values()
                if label in entry.labels
            ]
            entity_ids.update(
                entry.entity_id for entry in entries if entry.domain == 'media_player'
            )

    # Filter out unavailable entities
    available_entity_ids = {
        entity_id for entity_id in entity_ids
        if hass.states.get(entity_id) is not None and hass.states.get(entity_id).state not in ('unavailable', 'unknown', 'off')
    }

    return available_entity_ids

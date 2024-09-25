import asyncio
import logging
import math

DOMAIN = "grad_vol"
_LOGGER = logging.getLogger(__name__)

async def async_setup(hass, config):
    """Set up when Home Assistant is loading the component."""

    async def handle_set_volume(call):
        """Handle the service call."""
        entity_ids = call.data.get('entity_id')
        target_volume = float(call.data.get('volume'))
        span = call.data.get('duration', 5)

        # Convert target volume to integer percentage
        target_volume_int = int(round(target_volume * 100))

        # For each entity, start the volume adjustment process
        tasks = [adjust_volume(hass, entity_id, target_volume_int, span) for entity_id in entity_ids]

        # Wait for all volume adjustments to complete
        await asyncio.gather(*tasks)

    async def adjust_volume(hass, entity_id, target_volume_int, span):
        """Adjust the volume of a single entity over time using a sine easing function."""
        state = hass.states.get(entity_id)

        # Skip if the entity is unavailable or off
        if state is None or state.state in ('unavailable', 'unknown', 'off'):
            _LOGGER.warning(f"Entity {entity_id} is unavailable or off. Skipping.")
            return

        volume = state.attributes.get('volume_level')

        if volume is None:
            _LOGGER.warning(f"Entity {entity_id} has no volume_level attribute. Skipping.")
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
        if steps <= 1:
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

    # Register the service with the async handler
    hass.services.async_register(DOMAIN, "set_volume", handle_set_volume)

    return True

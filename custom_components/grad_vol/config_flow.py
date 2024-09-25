"""Config flow for Gradual Volume Control integration."""
from homeassistant import config_entries
import voluptuous as vol

from .const import DOMAIN

class GradVolConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Gradual Volume Control."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}
        if user_input is not None:
            # Here you can validate the user input if needed
            return self.async_create_entry(title="Gradual Volume Control", data={})

        # Define the form schema (if you have options to configure)
        data_schema = vol.Schema({})

        return self.async_show_form(step_id="user", data_schema=data_schema, errors=errors)

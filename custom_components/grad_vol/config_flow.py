"""Config flow for Gradual Volume Control integration."""
from homeassistant import config_entries
from homeassistant.core import callback

from .const import DOMAIN

class GradVolConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Gradual Volume Control."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        if user_input is not None:
            return self.async_create_entry(title="Gradual Volume Control", data={})

        return self.async_show_form(step_id="user")

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return GradVolOptionsFlow(config_entry)

class GradVolOptionsFlow(config_entries.OptionsFlow):
    """Handle Gradual Volume Control options."""

    def __init__(self, config_entry):
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(step_id="init")

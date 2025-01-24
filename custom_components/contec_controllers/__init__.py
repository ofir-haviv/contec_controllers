"""The Contec Controllers integration."""
from __future__ import annotations

from datetime import timedelta
import logging

from ContecControllers.ContecConectivityConfiguration import (
    ContecConectivityConfiguration,
)
from ContecControllers.ControllerManager import ControllerManager

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady

from .const import DOMAIN
from .contec_tracer import ContecTracer

PLATFORMS = ["light", "cover", "binary_sensor"]

_LOGGER = logging.getLogger("ContecControllers")


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Contec Controllers from a config entry."""
    _LOGGER.info("Setting up Contec Controller.")
    hass.data.setdefault(DOMAIN, {})

    number_of_controllers: int = entry.data["number_of_controllers"]
    controllers_ip: str = entry.data["controllers_ip"]
    controllers_port: int = entry.data["controllers_port"]
    controller_manager: ControllerManager = ControllerManager(
        ContecTracer(_LOGGER),
        ContecConectivityConfiguration(
            number_of_controllers,
            controllers_ip,
            controllers_port,
        ),
    )

    controller_manager.Init()
    if not await controller_manager.IsConnected(timedelta(seconds=7)):
        _LOGGER.warning(
            f"Failed to connect to Contec Controllers at address {controllers_ip},{controllers_port}"
        )
        await controller_manager.CloseAsync()
        raise ConfigEntryNotReady

    _LOGGER.info("Successfully connected to Contec Controllers. Starts entity discovery.")
    await controller_manager.DiscoverEntitiesAsync()

    hass.data[DOMAIN][entry.entry_id] = controller_manager
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    _LOGGER.info("Contec Controllers are ready.")

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    _LOGGER.info("Unloading Contec Controllers.")
    controller_manager: ControllerManager = hass.data[DOMAIN][entry.entry_id]
    if controller_manager is not None:
        await controller_manager.CloseAsync()

    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    _LOGGER.info("Contec Controllers unloaded.")
    return unload_ok
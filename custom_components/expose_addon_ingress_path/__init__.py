import logging

from aiohttp import web
from aiohttp.web_exceptions import HTTPNotFound
from aiohasupervisor import SupervisorError

from homeassistant.components.hassio.const import DOMAIN as HASSIO_DOMAIN
from homeassistant.components.hassio.handler import HassIO, get_supervisor_client
from homeassistant.helpers.http import KEY_HASS
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.http import HomeAssistantView

_LOGGER: logging.Logger = logging.getLogger(__package__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    component: HassIO | None = hass.data.get(HASSIO_DOMAIN)
    if component is None:
        _LOGGER.error("Supervisor integration not initialized")
        return False

    hass.http.register_view(AddonIngressPathView())

    # Return boolean to indicate that initialization was successful.
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    # This integration doesn't create any entities, so no cleanup needed
    return True


class AddonIngressPathView(HomeAssistantView):
    name = "api:hassio:addon_ingress_path"
    url = "/api/hassio_addon_ingress_path/{slug}"
    requires_auth = True

    async def get(self, request: web.Request, slug: str) -> web.Response:  # type: ignore[override]
        hass: HomeAssistant = request.app[KEY_HASS]
        supervisor_client = get_supervisor_client(hass)

        try:
            addon_info = await supervisor_client.addons.addon_info(slug)
        except SupervisorError as err:
            _LOGGER.debug("Failed to get add-on info for %s: %s", slug, err)
            raise HTTPNotFound from None

        ingress_path = getattr(addon_info, "ingress_entry", None)
        if not ingress_path:
            raise HTTPNotFound

        return web.Response(text=ingress_path)

from __future__ import annotations

import logging
from datetime import timedelta

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)

from .api import AladdinApiClient, AladdinAuthError, AladdinConnectionError
from .const import DEFAULT_SCAN_INTERVAL

_LOGGER = logging.getLogger(__name__)


class AladdinCoordinator(DataUpdateCoordinator):
    def __init__(
        self, hass: HomeAssistant, client: AladdinApiClient, scan_interval: int
    ) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name="Aladdin Notifications",
            update_interval=timedelta(seconds=scan_interval or DEFAULT_SCAN_INTERVAL),
        )
        self.client = client
        self._logged_in = False

    async def _async_update_data(self):
        if not self._logged_in:
            try:
                await self.client.async_login()
                self._logged_in = True
            except (AladdinConnectionError, AladdinAuthError) as err:
                _LOGGER.warning("Login failed, will retry: %s", err)
                raise UpdateFailed(f"Login failed: {err}") from err

        try:
            notifications = await self.client.async_get_notifications()
        except AladdinAuthError:
            _LOGGER.info("Session expired, re-authenticating...")
            self._logged_in = False
            try:
                await self.client.async_login()
                self._logged_in = True
                notifications = await self.client.async_get_notifications()
            except (AladdinConnectionError, AladdinAuthError) as err:
                raise UpdateFailed(str(err)) from err
        except AladdinConnectionError as err:
            raise UpdateFailed(str(err)) from err

        return notifications[:20]

from __future__ import annotations

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import AladdinCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: AladdinCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        [AladdinNotificationSensor(coordinator, entry)],
        update_before_add=True,
    )


class AladdinNotificationSensor(
    CoordinatorEntity[AladdinCoordinator],
    SensorEntity,
):
    def __init__(
        self,
        coordinator: AladdinCoordinator,
        entry: ConfigEntry,
    ) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{DOMAIN}_{entry.entry_id}"
        self._attr_name = "Aladdin Notifications"
        self._attr_icon = "mdi:bell"

    @property
    def native_value(self):
        notifications = self.coordinator.data or []
        return len(notifications)

    @property
    def extra_state_attributes(self):
        return {
            "notifications": self.coordinator.data or [],
        }

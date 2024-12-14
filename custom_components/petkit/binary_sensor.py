"""Binary sensor platform for Petkit Smart Devices integration."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from pypetkitapi.const import D4SH, D4S, D4H
from pypetkitapi.feeder_container import Feeder
from pypetkitapi.litter_container import Litter
from pypetkitapi.water_fountain_container import WaterFountain

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.const import EntityCategory

from .entity import PetKitDescSensorBase, PetkitEntity

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

    from .coordinator import PetkitDataUpdateCoordinator
    from .data import PetkitConfigEntry


@dataclass(frozen=True, kw_only=True)
class PetKitBinarySensorDesc(PetKitDescSensorBase, BinarySensorEntityDescription):
    """A class that describes sensor entities."""


BINARY_SENSOR_MAPPING: dict[
    type[Feeder | Litter | WaterFountain], list[PetKitBinarySensorDesc]
] = {
    Feeder: [
        PetKitBinarySensorDesc(
            key="Camera status",
            translation_key="camera_status",
            value=lambda device: device.state.camera_status,
        ),
        PetKitBinarySensorDesc(
            key="Feeding",
            translation_key="feeding",
            device_class=BinarySensorDeviceClass.RUNNING,
            value=lambda device: device.state.feeding,
        ),
        PetKitBinarySensorDesc(
            key="Battery installed",
            translation_key="battery_installed",
            entity_category=EntityCategory.DIAGNOSTIC,
            value=lambda device: device.state.battery_power,
        ),
        PetKitBinarySensorDesc(
            key="Care plus subscription",
            translation_key="care_plus_subscription",
            entity_category=EntityCategory.DIAGNOSTIC,
            value=lambda device: device.cloud_product.subscribe,
        ),
        PetKitBinarySensorDesc(
            key="Eating",
            translation_key="eating",
            device_class=BinarySensorDeviceClass.OCCUPANCY,
            value=lambda device: device.state.eating,
        ),
        PetKitBinarySensorDesc(
            key="Food level",
            translation_key="food_level",
            device_class=BinarySensorDeviceClass.PROBLEM,
            value=lambda device: device.state.food == 0,
            ignore_types=[D4S, D4SH]
        ),
        PetKitBinarySensorDesc(
            key="Food level 1",
            translation_key="food_level_1",
            device_class=BinarySensorDeviceClass.PROBLEM,
            value=lambda device: device.state.food1 == 0,
            only_for_types=[D4S, D4SH]
        ),
        PetKitBinarySensorDesc(
            key="Food level 2",
            translation_key="food_level_2",
            device_class=BinarySensorDeviceClass.PROBLEM,
            value=lambda device: device.state.food2 == 0,
            only_for_types=[D4S, D4SH]
        ),
    ],
    Litter: [
        PetKitBinarySensorDesc(
            key="Camera status",
            translation_key="camera_status",
            value=lambda device: device.state.camera,
        ),
        PetKitBinarySensorDesc(
            key="Care plus subscription",
            translation_key="care_plus_subscription",
            entity_category=EntityCategory.DIAGNOSTIC,
            value=lambda device: device.cloud_product.subscribe,
        ),
        PetKitBinarySensorDesc(
            key="Liquid empty",
            translation_key="liquid_empty",
            device_class=BinarySensorDeviceClass.PROBLEM,
            value=lambda device: device.state.liquid_empty,
        ),
        PetKitBinarySensorDesc(
            key="Liquid lack",
            translation_key="liquid_lack",
            device_class=BinarySensorDeviceClass.PROBLEM,
            value=lambda device: device.state.liquid_lack,
        ),
        PetKitBinarySensorDesc(
            key="Sand lack",
            translation_key="sand_lack",
            device_class=BinarySensorDeviceClass.PROBLEM,
            value=lambda device: device.state.sand_lack,
        ),
        PetKitBinarySensorDesc(
            key="Low power",
            translation_key="low_power",
            value=lambda device: device.state.low_power,
        ),
        PetKitBinarySensorDesc(
            key="Power",
            translation_key="power",
            device_class=BinarySensorDeviceClass.POWER,
            value=lambda device: device.state.power,
        ),
        PetKitBinarySensorDesc(
            key="Waste bin",
            translation_key="waste_bin",
            device_class=BinarySensorDeviceClass.PROBLEM,
            value=lambda device: device.state.box_full,
        ),
        PetKitBinarySensorDesc(
            key="Waste bin presence",
            translation_key="waste_bin_presence",
            device_class=BinarySensorDeviceClass.PROBLEM,
            value=lambda device: not device.state.box_state,
        ),
    ],
    WaterFountain: [
        PetKitBinarySensorDesc(
            key="Lack warning",
            translation_key="lack_warning",
            device_class=BinarySensorDeviceClass.PROBLEM,
            value=lambda device: device.lack_warning,
        ),
        PetKitBinarySensorDesc(
            key="Battery",
            translation_key="low_battery",
            device_class=BinarySensorDeviceClass.BATTERY,
            value=lambda device: device.lack_warning,
        ),
    ],
}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: PetkitConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up binary_sensors using config entry."""
    devices = entry.runtime_data.client.device_list.values()
    entities = [
        PetkitBinarySensor(
            coordinator=entry.runtime_data.coordinator,
            entity_description=entity_description,
            device=device,
        )
        for device in devices
        for device_type, entity_descriptions in BINARY_SENSOR_MAPPING.items()
        if isinstance(device, device_type)
        for entity_description in entity_descriptions
        if entity_description.is_supported(device)  # Check if the entity is supported
    ]
    async_add_entities(entities)


class PetkitBinarySensor(PetkitEntity, BinarySensorEntity):
    """Petkit Smart Devices BinarySensor class."""

    entity_description: PetKitBinarySensorDesc

    def __init__(
        self,
        coordinator: PetkitDataUpdateCoordinator,
        entity_description: PetKitBinarySensorDesc,
        device: Feeder | Litter | WaterFountain,
    ) -> None:
        """Initialize the binary_sensor class."""
        super().__init__(coordinator, device)
        self.coordinator = coordinator
        self.entity_description = entity_description
        self.device = device

    @property
    def unique_id(self) -> str:
        """Return a unique ID for the binary_sensor."""
        return f"{self.device.id}_{self.entity_description.key}"

    @property
    def is_on(self) -> bool | None:
        """Return the state of the binary sensor."""
        return self.entity_description.value(self.device)

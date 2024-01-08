from __future__ import annotations

from typing import TYPE_CHECKING

from components.base_component import BaseComponent
from equipment_types import EquipmentType

if TYPE_CHECKING:
    from entity import Item

class Equippable(BaseComponent):
    parent: Item

    def __init__(
        self, 
        equipment_types: EquipmentType,
        power_bonus: int = 0,
        defense_bonus: int = 0,
    ) -> None:

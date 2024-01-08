from __future__ import annotations

from typing import Optional, TYPE_CHECKING

from components.base_component import BaseComponent
from equipment_types import EquipmentType

if TYPE_CHECKING:
    from entity import Actor, EquippableItem


class Equipment(BaseComponent):
    parent: Actor

    def __init__(self, weapon: Optional[EquippableItem], armor: Optional[EquippableItem]) -> None:
        '''Has a weapon and armor slot for each actor'''
        self.weapon = weapon
        self.armor = armor

    @property
    def defense_bonus(self) -> int:
        bonus = 0

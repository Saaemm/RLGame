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

        if self.weapon is not None and self.weapon.equippable is not None:
            bonus += self.weapon.equippable.defense_bonus

        if self.armor is not None and self.armor.equippable is not None:
            bonus += self.armor.equippable.defense_bonus

        return bonus
    
    @property
    def defense_bonus(self) -> int:
        bonus = 0

        if self.weapon is not None and self.weapon.equippable is not None:
            bonus += self.weapon.equippable.power_bonus

        if self.armor is not None and self.armor.equippable is not None:
            bonus += self.armor.equippable.power_bonus

        return bonus
    
    def item_is_equipped(self, item: EquippableItem) -> bool:
        return self.weapon == item or self.armor == item
    
    def unequip_message(self, item_name: str) -> None:
        self.parent.gamemap.engine.message_log.add_message(
            f"You have removed {item_name}."
        )

    def equip_message(self, item_name: str) -> None:
        self.parent.gamemap.engine.message_log.add_message(
            f"You have equipped {item_name}."
        )

    def equip_to_slot(self, slot: str, item: EquippableItem, add_message: bool) -> None
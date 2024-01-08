from __future__ import annotations

from typing import Optional, TYPE_CHECKING

from components.base_component import BaseComponent
from equipment_types import EquipmentType

if TYPE_CHECKING:
    from entity import Actor, ConsumableItem, EquippableItem


class Equipment(BaseComponent):
    parent: Actor

    def __init__(self, weapon: Optional[EquippableItem] = None, armor: Optional[EquippableItem] = None) -> None:
        #TODO: add head/body/leg/feet armor + shield/offhand weapons
        '''Has a weapon and armor slot for each actor'''
        self.weapon = weapon
        self.armor = armor

    @property
    def bonus_defense(self) -> int:
        bonus = 0

        if self.weapon is not None and self.weapon.equippable is not None:
            bonus += self.weapon.equippable.bonus_defense

        if self.armor is not None and self.armor.equippable is not None:
            bonus += self.armor.equippable.bonus_defense

        return bonus
    
    @property
    def bonus_power(self) -> int:
        bonus = 0

        if self.weapon is not None and self.weapon.equippable is not None:
            bonus += self.weapon.equippable.bonus_power

        if self.armor is not None and self.armor.equippable is not None:
            bonus += self.armor.equippable.bonus_power

        return bonus
    
    # def item_is_equipment(self, item) -> bool:
    #     '''Returns if something from inventory is an equippable item'''
    #     return isinstance(item, EquippableItem)

    def item_is_equipped(self, item: EquippableItem) -> bool:
        '''Returns if item is equipped to the parent's equipment slots'''
        return self.weapon == item or self.armor == item
    
    def unequip_message(self, item_name: str) -> None:
        print('the char is: ')
        print(self.parent.char)
        self.parent.gamemap.engine.message_log.add_message(
            f"You remove the {item_name}."
        )

    def equip_message(self, item_name: str) -> None:
        self.parent.gamemap.engine.message_log.add_message(
            f"You have equipped {item_name}."
        )

    def equip_to_slot(self, slot: str, item: EquippableItem, add_message: bool) -> None:
        '''slot is either weapon or armor in this case'''
        current_item = getattr(self, slot)

        if current_item is not None:
            self.unequip_from_slot(slot, add_message)

        setattr(self, slot, item)

        if add_message:
            self.equip_message(item.name)

    def unequip_from_slot(self, slot: str, add_message: bool) -> None:
        '''slot is either weapon or armor in this case'''
        current_item = getattr(self, slot)

        if add_message:
            self.unequip_message(current_item.name)

        setattr(self, slot, None)

    def toggle_equip(self, equippable_item: EquippableItem, add_message: bool = True) -> None:
        if (
            equippable_item.equippable
            and equippable_item.equippable.equipment_type == EquipmentType.WEAPON
        ):
            slot = "weapon"
        else:
            slot = "armor"

        if getattr(self, slot) == equippable_item:  #if weapon/amor is what is inputted, user wants to unequip, otherwise equip
            self.unequip_from_slot(slot, add_message)
        else:
            self.equip_to_slot(slot, equippable_item, add_message)
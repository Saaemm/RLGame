'''This component is for an item'''

from __future__ import annotations

from typing import TYPE_CHECKING

from components.base_component import BaseComponent
from equipment_types import EquipmentType

if TYPE_CHECKING:
    from entity import ConsumableItem

class Equippable(BaseComponent):
    parent: ConsumableItem

    #TODO: add special action for each (possibly with cool down?), [need get_action, consume, activate]
    def __init__(
        self, 
        equipment_types: EquipmentType,
        bonus_power: int = 0,
        bonus_defense: int = 0,
    ) -> None:
        self.equipment_type = equipment_types

        self.bonus_power = bonus_power
        self.bonus_defense = bonus_defense

class Dagger(Equippable):
    def __init__(self) -> None:
        super().__init__(equipment_types=EquipmentType.WEAPON, bonus_power=2)

class Sword(Equippable):
    def __init__(self) -> None:
        super().__init__(equipment_type=EquipmentType.WEAPON, bonus_power=4)


class LeatherArmor(Equippable):
    def __init__(self) -> None:
        super().__init__(equipment_type=EquipmentType.ARMOR, bonus_defense=1)


class ChainMail(Equippable):
    def __init__(self) -> None:
        super().__init__(equipment_type=EquipmentType.ARMOR, bonus_defense=3)
    
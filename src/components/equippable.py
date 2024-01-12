'''This component is for an item'''

from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from components.base_component import BaseComponent
from components.consumable import ConfusionConsumable
from equipment_types import EquipmentType
import exceptions
import configs.color as color

if TYPE_CHECKING:
    from entity import EquippableItem
    import actions
    from entity import Actor

class Equippable(BaseComponent):
    parent: EquippableItem

    #TODO: add special action for each (possibly with cool down?), [need get_action, consume, activate]
    def __init__(
        self, 
        equipment_type: EquipmentType,
        bonus_power: int = 0,
        bonus_defense: int = 0,
    ) -> None:
        self.equipment_type = equipment_type

        self.bonus_power = bonus_power
        self.bonus_defense = bonus_defense

    @property
    def player(self) -> Actor:
        return self.parent.gamemap.engine.player

    #TODO: implement cooldowns on abilities
    #TODO: implement choosing weapons upon startup (maybe spend skillpoints)

    def perform(self) -> None:
        raise exceptions.Impossible("This object does not have a unique action.")

class Dagger(Equippable):
    '''No special ability'''
    def __init__(self) -> None:
        super().__init__(
            equipment_type=EquipmentType.WEAPON, 
            bonus_power=2, 
        )

class Sword(Equippable):
    '''Special healing ability that takes a turn'''
    def __init__(self) -> None:
        super().__init__(equipment_type=EquipmentType.WEAPON, bonus_power=4)

        self.maxheals = 5

    def perform(self) -> None:
        healing_amount = self.player.fighter.heal(self.maxheals)
        if healing_amount > 0:
            self.engine.message_log.add_message(
                f"You used the dagger's healing ability, and recovered {healing_amount} HP!",
                color.health_recovered
            )
        else:
            raise exceptions.Impossible("You are already at max health!")


class LeatherArmor(Equippable):
    def __init__(self) -> None:
        super().__init__(equipment_type=EquipmentType.ARMOR, bonus_defense=1)


class ChainMail(Equippable):
    def __init__(self) -> None:
        super().__init__(equipment_type=EquipmentType.ARMOR, bonus_defense=3)
    
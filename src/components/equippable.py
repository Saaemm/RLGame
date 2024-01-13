'''This component is for an item'''

from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from components.base_component import BaseComponent
from components.consumable import ConfusionConsumable
from entity import Actor
from equipment_types import EquipmentType
import exceptions
import configs.color as color
import input_handlers
import actions

if TYPE_CHECKING:
    from entity import EquippableItem
    from entity import Actor

class Equippable(BaseComponent):
    parent: EquippableItem

    #TODO: add special action for each (possibly with cool down?), [need get_action, consume, activate]
    def __init__(
        self, 
        equipment_type: EquipmentType,
        bonus_power: int = 0,
        bonus_defense: int = 0,
        cooldown: int = 1,
    ) -> None:
        self.equipment_type = equipment_type

        self.bonus_power = bonus_power
        self.bonus_defense = bonus_defense

        #cooldown counts action turn. Cooldown-1 down time
        # Cooldown of 1 means possible action every turn. Cooldown of 2 means possible action every 2 turns
        self.cooldown = cooldown
        self._current_cooldown = 0

    @property
    def current_cooldown(self) -> int:
        return self._current_cooldown

    @current_cooldown.setter
    def current_cooldown(self, value: int) -> None:
        #bounded by 0 <= value <= self.cooldown
        self._current_cooldown = max(0, min(self.cooldown, value))

    @property
    def player(self) -> Actor:
        return self.parent.gamemap.engine.player

    #TODO: implement cool downs on abilities
    #TODO: implement choosing weapons upon startup (maybe spend skill points)

    def weapon_action(self, entity: Actor) -> Optional[input_handlers.BaseEventHandler]:
        #entity has the weapon and does the action
        if self.equipment_type == EquipmentType.WEAPON:
            raise exceptions.Impossible("This weapon does not have a unique action.")
        raise exceptions.Impossible("This object does not have a weapon action.")
    
    def armor_action(self, aggressor: Actor) -> None:
        if self.equipment_type != EquipmentType.ARMOR:
            raise exceptions.Impossible("This object does not have an armor action.")


class Dagger(Equippable):
    '''No special ability'''
    def __init__(self) -> None:
        super().__init__(
            equipment_type=EquipmentType.WEAPON, 
            bonus_power=2, 
            cooldown=5, #4 turn cooldown
        )

        #TODO: make these parameters in the entity factories side
        self.radius = 3
        self.damage = 1

    def weapon_action(self, entity: Actor) -> Optional[input_handlers.BaseEventHandler]:
        #The weapon action cooldown is handled in the action fireballweaponaction, but this handles exception
        if self.current_cooldown > 0:
            raise exceptions.Impossible(f"{self.current_cooldown} turns left until ability is recharged.")

        self.engine.message_log.add_message("Select a target location.", color.needs_target)

        return input_handlers.AreaRangedAttackHandler(
            engine=self.engine, 
            radius=self.radius, 
            callback=lambda xy: actions.FireballWeaponAction(entity, self, xy)
        )

class Sword(Equippable):
    '''Special healing ability that takes a turn'''
    def __init__(self) -> None:
        super().__init__(equipment_type=EquipmentType.WEAPON, bonus_power=4, cooldown=2,)

        self.maxheals = 5

    def weapon_action(self, entity: Actor) -> Optional[input_handlers.BaseEventHandler]:
        if self.current_cooldown > 0:
            raise exceptions.Impossible(f"{self.current_cooldown} turns left until ability is recharged.")
        self.current_cooldown = self.cooldown

        healing_amount = entity.fighter.heal(self.maxheals)
        if healing_amount > 0:
            self.engine.message_log.add_message(
                f"You used the dagger's healing ability, and recovered {healing_amount} HP!",
                color.health_recovered
            )
        else:
            raise exceptions.Impossible("You are already at max health!")


class LeatherArmor(Equippable):
    def __init__(self) -> None:
        super().__init__(equipment_type=EquipmentType.ARMOR, bonus_defense=1, cooldown=2)


class ChainMail(Equippable):
    def __init__(self) -> None:
        super().__init__(equipment_type=EquipmentType.ARMOR, bonus_defense=3, cooldown=1)

        self.thorns_damage = 1

    def armor_action(self, aggressor: Actor) -> None:
        if self.current_cooldown > 0:
            return
        self.current_cooldown = self.cooldown

        damage = self.thorns_damage - aggressor.fighter.defense

        #color of log output determined
        if aggressor is self.engine.player:
            attack_color = color.enemy_atk
        else:
            attack_color = color.player_atk

        if damage > 0:
            self.engine.message_log.add_message(
                f"Chainmail's thorns dealt {damage} hit points to {aggressor.name}.", attack_color
            )
            aggressor.fighter.hp -= damage  #uses setter of fighter component

        else:
            self.engine.message_log.add_message(
                f"Chainmail's thorns attacked {aggressor.name} but no damage is dealt", attack_color
            )
    
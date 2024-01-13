from __future__ import annotations

from typing import Optional, TYPE_CHECKING

import actions
from actions import Action, ConsumableItemAction
import configs.color as color
import components.ai
import components.inventory
from components.base_component import BaseComponent
from entity import Actor
from exceptions import Impossible

if TYPE_CHECKING:
    from entity import Actor, ConsumableItem
    from input_handlers import ActionOrHandler, SingleRangedAttackHandler, AreaRangedAttackHandler



class Consumable(BaseComponent):
    parent: ConsumableItem

    def get_action(self, consumer: Actor) -> Optional[ActionOrHandler]:
        '''Try to return the action for this item.'''
        return actions.ConsumableItemAction(consumer, self.parent)
    
    def activate(self, action: actions.ConsumableItemAction) -> None:
        '''Invoke this item's ability
        
        'action' is the context of activation
        '''
        raise NotImplementedError()
    
    def consume(self) -> None:
        '''Remove the consumed item from its containing inventory'''
        entity = self.parent
        inventory = entity.parent
        if isinstance(inventory, components.inventory.Inventory):  #meaning if item is actually in an inventory
            inventory.items.remove(entity)
    

class HealingConsumable(Consumable):
    def __init__(self, amount: int) -> None:
        self.amount = amount

    def activate(self, action: actions.ConsumableItemAction) -> None:
        consumer = action.entity
        amount_recovered = consumer.fighter.heal(self.amount)

        if amount_recovered > 0:
            self.engine.message_log.add_message(
                f"You consumed the {self.parent.name}, and recovered {amount_recovered} HP!",
                color.health_recovered
            )
            self.consume()  #remove from inventory if applicable

        else:
            raise Impossible(f"Your health is already full.")
        
class LightningDamageConsumable(Consumable):

    def __init__(self, damage: int, maximum_range: int) -> None:
        self.damage = damage
        self.maximum_range = maximum_range

    def activate(self, action: actions.ConsumableItemAction) -> None:
        '''Targets closest enemy if any'''

        consumer = action.entity
        target = None
        closest_distance = self.maximum_range + 1.0

        for actor in self.engine.game_map.actors:
            if actor is not consumer and self.parent.gamemap.visible[actor.x, actor.y]:
                distance = consumer.distance(actor.x, actor.y)

                if distance < closest_distance:
                    closest_distance = distance
                    target = actor

        if target is not None:
            self.engine.message_log.add_message(
                f"A lightning bolt struck {target.name}, dealing {self.damage} damage!"
            )
            target.fighter.take_damage(self.damage)
            self.consume()

        else:
            raise Impossible("No enemy in range.")
        
class ConfusionConsumable(Consumable):
    def __init__(self, number_of_turns: int) -> None:
        self.number_of_turns = number_of_turns

    def get_action(self, consumer: Actor) -> SingleRangedAttackHandler:
        self.engine.message_log.add_message(
            "Select a target location.", color.needs_target
        )
        return SingleRangedAttackHandler(
            self.engine,
            callback=lambda xy: ConsumableItemAction(consumer, self.parent, xy)
        )
    
    def activate(self, action: ConsumableItemAction):
        consumer = action.entity
        target = action.target_actor

        #target must be visible, an actual entity/actor, is not the consumer
        if not self.engine.game_map.visible[action.target_xy]:
            raise Impossible("You must target somewhere visible.")
        if not target:
            raise Impossible("You must have a target")
        if target is consumer:
            raise Impossible("You cannot target yourself")
        
        self.engine.message_log.add_message(
            f"The {target.name} starts to look drunk, staggering around in confusion.", color.status_effect_applied
        )

        target.ai = components.ai.ConfusedEnemy(entity=target, previous_ai=target.ai, turns_remaining=self.number_of_turns)
        self.consume()


class FireballDamageConsumable(Consumable):
    def __init__(self, damage: int, radius: int) -> None:
        self.damage = damage
        self.radius = radius

    def get_action(self, consumer: Actor) -> AreaRangedAttackHandler:
        self.engine.message_log.add_message("Select a target location.", color.needs_target)

        return AreaRangedAttackHandler(
            engine=self.engine, 
            radius=self.radius, 
            callback=lambda xy: ConsumableItemAction(consumer, self.parent, xy)
        )
        #actions are handled in action class
    
    def activate(self, action: ConsumableItemAction) -> None:
        target_xy = action.target_xy

        if not self.engine.game_map.visible[target_xy]:
            raise Impossible("You must target somewhere visible.")
        
        targets_hit = False
        for actor in self.engine.game_map.actors:  #includes player and hidden entities, as long as target is visible
            if actor.distance(*target_xy) <= self.radius:
                targets_hit = True
                self.engine.message_log.add_message(
                    f"{actor.name} was engulfed in fire from a fireball, taking {self.damage} damage"
                )
                actor.fighter.take_damage(self.damage)  #dealt true damage
        
        if not targets_hit:
            raise Impossible("There are no targets within range.")
        
        self.consume()
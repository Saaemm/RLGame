from __future__ import annotations

from typing import Optional, TYPE_CHECKING

import actions
import configs.color as color
import components.inventory
from components.base_component import BaseComponent
from exceptions import Impossible

if TYPE_CHECKING:
    from entity import Actor, Item


class Consumable(BaseComponent):
    parent: Item

    def get_action(self, consumer: Actor) -> Optional[actions.Action]:
        '''Try to return the action for this item.'''
        return actions.ItemAction(consumer, self.parent)
    
    def activate(self, action: actions.ItemAction) -> None:
        '''Invoke this item's ability
        
        'action' is the context of activation
        '''
        raise NotImplementedError()
    
    def consume(self) -> None:
        '''Remove the consumed item frmo its containing inventory'''
        entity = self.parent
        inventory = entity.parent
        if isinstance(inventory, components.inventory.Inventory):  #meaning if item is actually in an inventory
            inventory.items.remove(entity)
    

class HealingConsumable(Consumable):
    def __init__(self, amount: int) -> None:
        self.amount = amount

    def activate(self, action: actions.ItemAction) -> None:
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
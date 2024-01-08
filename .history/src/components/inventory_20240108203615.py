from __future__ import annotations

from typing import List, TYPE_CHECKING

from components.base_component import BaseComponent

if TYPE_CHECKING:
    from entity import Actor, ConsumableItem

class Inventory(BaseComponent):
    parent: Actor

    def __init__(self, capacity: int):
        self.capacity = capacity
        self.items: List[ConsumableItem] = []

    def drop(self, item: ConsumableItem) -> None:
        '''
        Removes item from the inventory and restores it to gamemap, at player's curr location
        '''
        self.items.remove(item)
        item.place(self.parent.x, self.parent.y, self.gamemap)

        self.engine.message_log.add_message(f"You dropped {item.name}.")
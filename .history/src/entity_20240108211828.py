from __future__ import annotations

import copy
import math
from typing import Optional, Tuple, Type, TypeVar, TYPE_CHECKING, Union

from configs.render_order import RenderOrder

if TYPE_CHECKING:
    from components.ai import BaseAI
    from components.consumable import Consumable
    from components.equippable import Equippable
    from components.equipment import Equipment
    from components.fighter import Fighter
    from components.inventory import Inventory
    from game_map import GameMap
    from components.level import Level

T = TypeVar("T", bound="Entity")

class Entity:
    '''
    Generic object to represent players, enemies, items
    '''

    parent: Union[GameMap, Inventory]  #can be either in a gamemap or in an inventory (or None)

    def __init__(
        self, 
        parent: Optional[GameMap] = None,
        x: int = 0, 
        y: int = 0, 
        char: str = "?", 
        color: Tuple[int, int, int] = (255, 255, 255),
        name: str = "<Unnamed>",
        blocks_movement: bool = False,  # entity can be moved or not; consumables, equiptment = False; enemies = True
        render_order: RenderOrder = RenderOrder.CORPSE,
    ) -> None:
        
        self.x = x
        self.y = y
        self.char = char
        self.color = color
        self.name = name
        self.blocks_movement = blocks_movement
        self.render_order = render_order

        if parent is not None:
            #if gamemap isn't provided now then it will be set later
            self.parent = parent
            parent.entities.add(self)

    @property
    def gamemap(self) -> GameMap:
        return self.parent.gamemap

    def spawn(self: T, gamemap: GameMap, x: int, y: int) -> T:
        '''Spawns a copy of this instance at the given location; note deepcopy to avoid alias'''
        clone = copy.deepcopy(self)
        clone.x = x
        clone.y = y
        clone.parent = gamemap
        gamemap.entities.add(clone)
        return clone
    
    def distance(self, x: int, y: int) -> float:
        '''
        Returns distance between current entity and (x, y) position
        '''
        return math.sqrt((self.x - x) ** 2 + (self.y - y) ** 2)
    
    def place(self, x: int, y: int, gamemap: Optional[GameMap] = None) -> None:
        '''Place this entity at a new location. Handles moving across GameMaps'''
        self.x = x
        self.y = y

        #Gamemap is none means stays in current map
        if gamemap is not None:
            if hasattr(self, "parent"): # Possibly uninitialized
                if self.parent is self.gamemap:
                    self.parent.entities.remove(self)
            self.parent = gamemap
            gamemap.entities.add(self)

    def move(self, dx: int, dy: int) -> None:
        #moves the entity
        self.x += dx
        self.y += dy


class Actor(Entity):
    def __init__(
            self, 
            *,
            parent: GameMap | None = None, 
            x: int = 0, 
            y: int = 0, 
            char: str = "?", 
            color: Tuple[int, int, int] = (255, 255, 255), 
            name: str = "<Unnamed>", 
            ai_cls: Type[BaseAI],
            equipment: Equipment = Equipment(),  #empty equipment holder as default
            fighter: Fighter, 
            inventory: Inventory,
            level: Level,
    ) -> None:
        super().__init__(
            parent=parent, 
            x=x, 
            y=y, 
            char=char, 
            color=color, 
            name=name, 
            blocks_movement=True,
            render_order=RenderOrder.ACTOR,
        )

        #add components
        self.ai: Optional[BaseAI] = ai_cls(self)

        self.equipment = equipment
        self.equipment.parent = self

        self.fighter = fighter
        self.fighter.parent = self

        self.inventory = inventory
        self.inventory.parent = self

        self.level = level
        self.level.parent = self

    @property
    def is_alive(self) -> bool: 
        '''Returns True as long as this actor can perform actions'''
        return bool(self.ai)
    

class ConsumableItem(Entity):
    def __init__(
            self,
            *,
            x: int = 0,
            y: int = 0,
            char: str = "?",
            color: Tuple[int, int, int] = (255, 255, 255),
            name: str = "<Unnamed>",
            consumable: Consumable,
    ):
        super().__init__(
            x=x,
            y=y,
            char=char, 
            color=color, 
            name=name,
            blocks_movement=False,
            render_order=RenderOrder.ITEM,
        )

        #adds consumable component
        self.consumable = consumable
        self.consumable.parent = self

class EquippableItem(Entity):
    def __init__(
        self,
        *,
        x: int = 0,
        y: int = 0,
        char: str = "?",
        color: Tuple[int, int, int] = (255, 255, 255),
        name: str = "<Unnamed>",
        equippable: Equippable,
    ):
        super().__init__(
            x=x,
            y=y,
            char=char, 
            color=color, 
            name=name,
            blocks_movement=False,
            render_order=RenderOrder.ITEM,
        )

        #adds consumable component
        self.equippable = equippable
        self.equippable.parent = self
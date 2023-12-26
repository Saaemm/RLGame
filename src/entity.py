from __future__ import annotations

import copy
from typing import Optional, Tuple, Type, TypeVar, TYPE_CHECKING

from render_order import RenderOrder

if TYPE_CHECKING:
    from components.ai import BaseAI
    from components.fighter import Fighter
    from game_map import GameMap

T = TypeVar("T", bound="Entity")

class Entity:
    '''
    Generic object to represent players, enemies, items
    '''

    gamemap: GameMap

    def __init__(
        self, 
        gamemap: Optional[GameMap] = None,
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

        if gamemap is not None:
            #if gamemap isn't provided now then it will be set later
            self.gamemap = gamemap
            gamemap.entities.add(self)

    def spawn(self: T, gamemap: GameMap, x: int, y: int) -> T:
        '''Spawns a copy of this instance at the given location; note deepcopy to avoid alias'''
        clone = copy.deepcopy(self)
        clone.x = x
        clone.y = y
        clone.gamemap = gamemap
        gamemap.entities.add(clone)
        return clone
    
    def place(self, x: int, y: int, gamemap: Optional[GameMap] = None) -> None:
        '''Place this entity at a new location. Handles moving across GameMaps'''
        self.x = x
        self.y = y

        #Gamemap is none means stays in current map
        if gamemap is not None:
            if hasattr(self, "gamemap"): # Possibly uninitialized
                self.gamemap.entities.remove(self)
            self.gamemap = gamemap
            gamemap.entities.add(self)

    def move(self, dx: int, dy: int) -> None:
        #moves the entity
        self.x += dx
        self.y += dy


class Actor(Entity):
    def __init__(
            self, 
            *,
            gamemap: GameMap | None = None, 
            x: int = 0, 
            y: int = 0, 
            char: str = "?", 
            color: Tuple[int, int, int] = (255, 255, 255), 
            name: str = "<Unnamed>", 
            ai_cls: Type[BaseAI],
            fighter: Fighter
    ) -> None:
        super().__init__(
            gamemap=gamemap, 
            x=x, 
            y=y, 
            char=char, 
            color=color, 
            name=name, 
            blocks_movement=True,
            render_order=RenderOrder.ACTOR,
        )

        self.ai: Optional[BaseAI] = ai_cls(self)

        self.fighter = fighter
        self.fighter.entity = self

    @property
    def is_alive(self) -> bool: 
        '''Returns True as long as this actor can perform actions'''
        return bool(self.ai)

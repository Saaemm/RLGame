from __future__ import annotations

from typing import Iterable, TYPE_CHECKING

import numpy as np
from tcod.console import Console

import tile_types

if TYPE_CHECKING:
    from entity import Entity

class GameMap:
    def __init__(self, width: int, height: int, entities: Iterable[Entity] = ()) -> None:

        self.width, self.height = width, height

        #creates 2D array, fill with wall
        self.tiles = np.full((width, height), fill_value=tile_types.wall, order="F")
        # #creates wall at specific location
        # self.tiles[30:33, 22] = tile_types.wall

        self.entities = set(entities)

        #creates visible and explored, filled with False
        self.visible = np.full((width, height), fill_value=False, order="F")  #Tiles the player sees currently
        self.explored = np.full((width, height), fill_value=False, order="F")  #Tiles the player has seen before

    def in_bounds(self, x: int, y: int) -> bool:
        '''Sepcification: returns True if x, y are in boundaries'''
        return 0 <= x < self.width and 0 <= y < self.height
    
    def render(self, console: Console) -> None:
        '''Quickly renders the entire map
        
        If a tile is in the "visible" array, draws with "light" colors
        If a it isn't, and it is in the "explored" array, then draw it with "dark" colors
        Otherwise, default is "SHROUD" colors
        '''
        console.rgb[0:self.width, 0:self.height] = np.select(
            condlist=[self.visible, self.explored],
            choicelist=[self.tiles["light"], self.tiles["dark"]],
            default=tile_types.SHROUD
        )

        #renders all entities on screen
        for entity in self.entities:
            #only print entities in FOV
            if self.visible[entity.x, entity.y]:
                console.print(x=entity.x, y=entity.y, string=entity.char, fg=entity.color)
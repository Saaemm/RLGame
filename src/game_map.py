import numpy as np
from tcod.console import Console

import tile_types

class GameMap:
    def __init__(self, width: int, height: int) -> None:
        self.width, self.height = width, height

        #creates 2D array, fill with floor
        self.tiles = np.full((width, height), fill_value=tile_types.floor, order="F")

        #creates wall at specific location
        self.tiles[30:33, 22] = tile_types.wall

    def in_bounds(self, x: int, y: int) -> bool:
        '''Sepcification: returns True if x, y are in boundaries'''
        return 0 <= x < self.width and 0 <= y < self.height
    
    def render(self, console: Console) -> None:
        '''Quickly renders the entire map'''
        console.rgb[0:self.width, 0:self.height] = self.tiles["dark"]
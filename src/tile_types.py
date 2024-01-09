from typing import Tuple

import numpy as np

#Tile graphics structured type compatible with Console.tiles_rgb
graphic_dt = np.dtype(
    [
        ("ch", np.int32), #unicode codepoint
        ("fg", "3B"), # 3 unsigned bytes for RGB
        ("bg", "3B"), #fg = forground, bg = background
    ]
)

#Tile struct used for statically defined tile data
tile_dt = np.dtype(
    [
        ("walkable", np.bool_), #True if tile can be walked over
        ("transparent", np.bool_), #True if tile does not block FOV
        ("dark", graphic_dt), #graphics when the tile is not in FOV
        ("light", graphic_dt),  #graphics when the tile is in FOV
    ]
)

def new_tile(
        *, #use of keywords; parameter order does not matter
        walkable: int, 
        transparent: int, 
        dark: Tuple[int, Tuple[int, int, int], Tuple[int, int, int]],
        light: Tuple[int, Tuple[int, int, int], Tuple[int, int, int]],
) -> np.ndarray:
    '''Helper funct for definining individual tile types'''
    #returns a tile_dt typed array containing just the new tile
    return np.array((walkable, transparent, dark, light), dtype=tile_dt)

# SHROUD are unexplored, unseen tiles
SHROUD = np.array((ord(" "), (255, 255, 255), (0, 0, 0)), dtype=graphic_dt)

#can change dark attribute's space character to "#" for instnace
floor = new_tile(
    walkable=True, 
    transparent=True, 
    dark=(ord(" "), (255, 255, 255), (50, 50, 150)),
    light=(ord(" "), (255, 255, 255), (200, 180, 50)),
)

wall = new_tile(
    walkable=False, 
    transparent=False, 
    dark=(ord(" "), (255, 255, 255), (0, 0, 100)),
    light=(ord(" "), (255, 255, 255), (130, 110, 50))
)

down_stairs = new_tile(
    walkable=True, 
    transparent=True, 
    dark=(ord(">"), (0, 0, 100), (50, 50, 150)),
    light=(ord(">"), (255, 255, 255), (200, 180, 50)),
)

up_stairs = new_tile(
    walkable=True,
    transparent=True,
    dark=(ord("<"), (0, 0, 100), (50, 50, 150)),
    light=(ord("<"), (255, 255, 255), (200, 180, 50)),
)
#TODO: make doors (impassible and passable)
#TODO: can make trap door
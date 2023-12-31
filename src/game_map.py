from __future__ import annotations

from typing import Iterable, Iterator, Optional, TYPE_CHECKING

import numpy as np
from tcod.console import Console

from entity import Actor, Item
import tile_types

if TYPE_CHECKING:
    from engine import Engine
    from entity import Entity

class GameMap:
    def __init__(self, engine: Engine, width: int, height: int, entities: Iterable[Entity] = ()) -> None:

        self.engine = engine
        self.width, self.height = width, height

        #creates 2D array, fill with wall
        self.tiles = np.full((width, height), fill_value=tile_types.wall, order="F")
        # #creates wall at specific location
        # self.tiles[30:33, 22] = tile_types.wall

        self.entities = set(entities)

        #creates visible and explored, filled with False
        self.visible = np.full((width, height), fill_value=False, order="F")  #Tiles the player sees currently
        self.explored = np.full((width, height), fill_value=False, order="F")  #Tiles the player has seen before

    @property
    def gamemap(self) -> GameMap:
        return self

    @property
    def actors(self) -> Iterator[Actor]:
        '''Iterate over the map's living actors'''
        yield from (
            entity
            for entity in self.entities
            if isinstance(entity, Actor) and entity.is_alive # is an Actor and alive
        )

    @property
    def items(self) -> Iterable[Item]:
        '''Iterate over the map's items'''
        yield from (entity for entity in self.entities if isinstance(entity, Item))

    def get_blocking_entity_at_location(self, location_x: int, location_y: int) -> Optional[Entity]:
        for entity in self.entities:
            if (
                entity.x == location_x 
                and entity.y == location_y 
                and entity.blocks_movement
            ):
                return entity
            
        return None
    
    def get_actor_at_location(self, x: int, y: int) -> Optional[Actor]:
        for actor in self.actors:
            if actor.x == x and actor.y == y:
                return actor
        return None
    
    def get_item_at_location(self, x: int, y: int) -> Optional[Item]:
        for item in self.items:
            if item.x == x and item.y == y:
                return item
        return None

    def in_bounds(self, x: int, y: int) -> bool:
        '''Sepcification: returns True if x, y are in boundaries'''
        return 0 <= x < self.width and 0 <= y < self.height
    
    def render(self, console: Console) -> None:
        '''Quickly renders the entire map
        
        If a tile is in the "visible" array, draws with "light" colors
        If a it isn't, and it is in the "explored" array, then draw it with "dark" colors
        Otherwise, default is "SHROUD" colors
        '''
        console.rgb[0 : self.width, 0 : self.height] = np.select(
            condlist=[self.visible, self.explored],
            choicelist=[self.tiles["light"], self.tiles["dark"]],
            default=tile_types.SHROUD,
        )

        entities_sorted_for_rendering = sorted(
            self.entities, key=lambda x: x.render_order.value
        )

        #renders all entities on screen
        for entity in entities_sorted_for_rendering:
            #only print entities in FOV
            if self.visible[entity.x, entity.y]:
                console.print(x=entity.x, y=entity.y, string=entity.char, fg=entity.color)
from __future__ import annotations

import random
from typing import Dict, Iterator, Tuple, List, TYPE_CHECKING

import tcod

import entity_factories
from game_map import GameMap
import tile_types

if TYPE_CHECKING:
    from engine import Engine

max_items_by_floor = [
    (1, 1),
    (4, 2),
]

max_monsters_by_floor = [
    (1, 2),
    (4, 3),
    (6, 5),
]

def get_max_value_for_floor(
        max_value_by_floor: List[Tuple[int, int]], floor: int
):
    current_value = 0

    for floor_minimum, value in max_value_by_floor:
        if floor_minimum > floor:
            break
        current_value = value
    
    return current_value

class RectangularRoom: 

    def __init__(self, x: int, y: int, width: int, height: int) -> None:
        #top left corner, wall
        self.x1 = x
        self.y1 = y

        #bottom right corner, wall
        self.x2 = x + width
        self.y2 = y + height

    @property
    def center(self) -> Tuple[int, int]:
        center_x = int((self.x1 + self.x2) / 2)
        center_y = int((self.y1 + self.y2) / 2)

        return (center_x, center_y)
    
    @property
    def inner(self) -> Tuple[slice, slice]:
        '''returns inner area of the room as a 2D array index'''
        return (slice(self.x1 + 1, self.x2), slice(self.y1 + 1, self.y2))
    
    def intersects(self, other: RectangularRoom) -> bool:
        '''Returns True if this room overlaps with another rectangular room'''
        return (
            self.x1 <= other.x2
            and self.x2 >= other.x1
            and self.y1 <= self.y2
            and self.y2 >= self.y1
        )
    
def place_entities(
        room: RectangularRoom, dungeon: GameMap, floor_number: int,
) -> None:
    
    number_of_monsters = random.randint(0, get_max_value_for_floor(max_monsters_by_floor, floor_number))
    number_of_items = random.randint(0, get_max_value_for_floor(max_items_by_floor, floor_number))

    for i in range(number_of_monsters):
        x = random.randint(room.x1 + 1, room.x2 - 1)
        y = random.randint(room.y1 + 1, room.y2 - 1)

        if not any(entity.x == x and entity.y == y for entity in dungeon.entities):

            if random.random() < 0.8: 
                #spawns orc
                entity_factories.orc.spawn(dungeon, x, y)
            else:
                #spawns troll
                entity_factories.troll.spawn(dungeon, x, y)

    for i in range(number_of_items):
        x = random.randint(room.x1 + 1, room.x2 - 1)
        y = random.randint(room.y1 + 1, room.y2 - 1)

        if not any(entity.x == x and entity.y == y for entity in dungeon.entities):
            item_chance = random.random()

            if item_chance < 0.7:
                entity_factories.health_potion.spawn(dungeon, x, y)
            elif item_chance < 0.8:
                entity_factories.fireball_scroll.spawn(dungeon, x, y)
            elif item_chance < 0.9:
                entity_factories.confusion_scroll.spawn(dungeon, x, y)
            else:
                entity_factories.lightning_scroll.spawn(dungeon, x, y)

def tunnel_between(
    start: Tuple[int, int], end: Tuple[int, int]
) -> Iterator[Tuple[int, int]]:
    '''Return an L-shaped tunnel between two points'''

    x1, y1 = start
    x2, y2 = end

    if random.random() < 0.5:   # 50% chance
        #move horizontally, then vertically
        corner_x, corner_y = x2, y1
    else: 
        #move vertically then horizontally
        corner_x, corner_y = x1, y2

    #generate the coords for the tunnel through Bresenham algo
    for x, y in tcod.los.bresenham((x1, y1), (corner_x, corner_y)).tolist():
        yield x, y

    for x, y in tcod.los.bresenham((corner_x, corner_y), (x2, y2)).tolist():
        yield x, y


def generate_dungeon(
    max_rooms: int,
    room_min_size: int,
    room_max_size: int,
    map_width: int,
    map_height: int,
    engine: Engine
) -> GameMap:
    '''Generates a new dungeon map'''

    #full wall dungeon
    player = engine.player
    dungeon = GameMap(engine, map_width, map_height, entities=[player])

    #temp structure to keep track of rooms already added for no overlap and other features
    rooms: List[RectangularRoom] = []

    #keep track of where the last room is to make the stiars descending down
    center_of_last_room = (0, 0)

    #max_room tries for new rooms
    for r in range(max_rooms):

        #new room inits
        room_width = random.randint(room_min_size, room_max_size)
        room_height = random.randint(room_min_size, room_max_size)

        x = random.randint(0, dungeon.width - room_width - 1)
        y = random.randint(0, dungeon.height - room_height - 1)

        new_room = RectangularRoom(x, y, room_width, room_height)

        #run through the other rooms and see if they intersect with this one
        if any(new_room.intersects(other_room) for other_room in rooms):
            continue  #intersects, so onto the next attempt
        #if there are no intersections, then room is valid

        #dig out the room's inner area
        dungeon.tiles[new_room.inner] = tile_types.floor

        if len(rooms) == 0: 
            #the first room, where player starts
            player.place(*new_room.center, dungeon)
        else: #all rooms after the first
            #dig a tunnel between this and the previous one
            #TODO: add more interesting tunnels/dungeon features
            for x, y in tunnel_between(rooms[-1].center, new_room.center):
                dungeon.tiles[x, y] = tile_types.floor

            center_of_last_room = new_room.center

        #add entities
        place_entities(new_room, dungeon, engine.game_world.current_floor)
        
        #add downstairs
        dungeon.tiles[center_of_last_room] = tile_types.down_stairs  #TODO: understand why this doesn't create stairs in every room
        dungeon.downstairs_location = center_of_last_room

        #append the new room to the rooms list
        rooms.append(new_room)

    return dungeon





# def generate_dungeon(map_width, map_height) -> GameMap:

#     #create a full wall dungeon
#     dungeon = GameMap(map_width, map_height)

#     room_1 = RectangularRoom(x=20, y=15, width=10, height=15)
#     room_2 = RectangularRoom(x=35, y=15, width=10, height=15)

#     #carves out dungeon with inner
#     dungeon.tiles[room_1.inner] = tile_types.floor
#     dungeon.tiles[room_2.inner] = tile_types.floor

#     #carves out the tunnel between the two rooms
#     for x, y in tunnel_between(room_2.center, room_1.center):
#         dungeon.tiles[x, y] = tile_types.floor

#     return dungeon
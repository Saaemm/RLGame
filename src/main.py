#!/usr/bin/env python3
import tcod

from engine import Engine
from entity import Entity
from procgen import generate_dungeon
from input_handlers import EventHandler

#shebang for ./src/main.py and imports

def main():

    #inits
    screen_width = 80
    screen_height = 50

    #map vars
    map_width = 80
    map_height = 45

    room_max_size = 10
    room_min_size = 6
    max_rooms = 30

    #32x8 tilesheet using font, returns Tileset
    tileset = tcod.tileset.load_tilesheet(
        "assets/terminal10x10_gs_tc.png", 32, 8, tcod.tileset.CHARMAP_TCOD
    )

    #entity set inits
    player = Entity(int(screen_width/2), int(screen_height/2), "@", (255, 255, 255))
    npc1 = Entity(int(screen_width/2 - 5), int(screen_height/2), "%", (255, 255, 0))
    entities = {npc1, player}

    #for player inputs (events)
    event_handler = EventHandler()

    #gamemap inits
    game_map = generate_dungeon(
        max_rooms=max_rooms,
        room_min_size=room_min_size,
        room_max_size=room_max_size,
        map_width=map_width, 
        map_height=map_height,
        player=player
    )

    #engine init
    engine = Engine(entities=entities, event_handler=event_handler, game_map=game_map, player=player)

    #creates screen, can change configurations for title, vsync, windowflags, renderer
    with tcod.context.new_terminal(
        screen_width, screen_height, 
        tileset=tileset,
        title = "Roguelike Game",
        vsync = True,
    ) as context:
        
        #creates Console object
        #order is access [x, y] order instead of [y, x] order
        root_console = tcod.console.Console(screen_width, screen_height, order="F")


        #game loop, ends when screen closes
        while True:

            engine.render(console=root_console, context=context)

            #gets user inputs and changes states accordingly
            events = tcod.event.wait()
            engine.handle_events(events)


if __name__ == "__main__":
    main()
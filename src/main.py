#!/usr/bin/env python3
import copy

import tcod

import configs.color as color
from engine import Engine
import entity_factories
from procgen import generate_dungeon
from input_handlers import EventHandler

#shebang for ./src/main.py and imports

def main():

    #inits
    screen_width = 80
    screen_height = 50

    #map vars
    map_width = 80
    map_height = 43

    room_max_size = 10
    room_min_size = 6
    max_rooms = 30

    max_monsters_per_room = 2

    #32x8 tilesheet using font, returns Tileset
    tileset = tcod.tileset.load_tilesheet(
        "assets/terminal10x10_gs_tc.png", 32, 8, tcod.tileset.CHARMAP_TCOD
    )

    #player init (cannot use spawn by needing gamemap which is created later on)
    player = copy.deepcopy(entity_factories.player)

    #engine init
    engine = Engine(player=player)

    #gamemap inits
    engine.game_map = generate_dungeon(
        max_rooms=max_rooms,
        room_min_size=room_min_size,
        room_max_size=room_max_size,
        map_width=map_width, 
        map_height=map_height,
        max_monsters_per_room=max_monsters_per_room,
        engine=engine
    )
    engine.update_fov()

    engine.message_log.add_message(
        "Hello fellow human, and welcome to [generic roguelike game]!", color.welcome_text
    )

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

            #updates and clears and renders
            root_console.clear()
            engine.event_handler.on_render(console=root_console)
            context.present(root_console)

            #gets user inputs and changes states accordingly
            engine.event_handler.handle_events(context)


if __name__ == "__main__":
    main()
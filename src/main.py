#!/usr/bin/env python3
import tcod

from engine import Engine
from entity import Entity
from game_map import GameMap
from input_handlers import EventHandler

#shebang for ./src/main.py and imports

def main():

    #inits
    screen_width = 80
    screen_height = 50

    map_width = 80
    map_height = 45

    #32x8 tilesheet using font, returns Tileset
    tileset = tcod.tileset.load_tilesheet(
        "assets/terminal10x10_gs_tc.png", 32, 8, tcod.tileset.CHARMAP_TCOD
    )

    #entity inits
    player = Entity(int(screen_width/2), int(screen_height/2), "@", (255, 255, 255))
    npc1 = Entity(int(screen_width/2 - 5), int(screen_height/2), "%", (255, 255, 0))
    entities = {npc1, player}

    #for player inputs (events)
    event_handler = EventHandler()

    #gamemap inits
    game_map = GameMap(map_width, map_height)

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
#!/usr/bin/env python3
import tcod

from actions import EscapeAction, MovementAction
from input_handlers import EventHandler

#shebang for ./src/main.py and imports

def main():

    #inits

    screen_width = 80
    screen_height = 50

    #vars
    #init pos is center of screen
    player_x = int(screen_width/2)
    player_y = int(screen_height/2)

    #32x8 tilesheet using font, returns Tileset
    tileset = tcod.tileset.load_tilesheet(
        "assets/terminal10x10_gs_tc.png", 32, 8, tcod.tileset.CHARMAP_TCOD
    )

    event_handler = EventHandler()

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

            #configures
            root_console.print(x=player_x, y=player_y, string="@")

            #update and clear/get rid of leftovers step
            context.present(root_console)
            root_console.clear()

            #waits for input from user and manages events
            for event in tcod.event.wait():

                #action becomes whatever is returned by the user keypress's function, ie keydown if valid
                action = event_handler.dispatch(event)

                if action is None:
                    continue

                if isinstance(action, MovementAction): #isinstance returns True if action has type MovementAction
                    player_x += action.dx
                    player_y += action.dy

                elif isinstance(action, EscapeAction):
                    raise SystemExit()


if __name__ == "__main__":
    main()
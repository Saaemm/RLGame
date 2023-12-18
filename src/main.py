#!/usr/bin/env python3
import tcod

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

            #update step
            context.present(root_console)

            #waits for input from user and manages events
            for event in tcod.event.wait():
                if event.type == "QUIT":
                    raise SystemExit()


if __name__ == "__main__":
    main()
#!/usr/bin/env python3
import traceback

import tcod

import configs.color as color
import exceptions
import input_handlers
import setup_game

#shebang for ./src/main.py and imports

def save_game(handler: input_handlers.BaseEventHandler, filename: str) -> None:
    '''If the current handler has an engine that is initialized and viable, then save'''
    if isinstance(handler, input_handlers.EventHandler):
        handler.engine.save_as(filename)
        print('Game Saved') # on command line

def main():

    #inits
    screen_width = 80
    screen_height = 50

    #32x8 tilesheet using font, returns Tileset
    tileset = tcod.tileset.load_tilesheet(
        "assets/terminal10x10_gs_tc.png", 32, 8, tcod.tileset.CHARMAP_TCOD
    )

    handler: input_handlers.BaseEventHandler = setup_game.MainMenu()

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

        try:
            #game loop, ends when screen closes
            while True:

                #updates and clears and renders
                root_console.clear()
                handler.on_render(console=root_console)
                context.present(root_console)

                #Handles events and errors
                try:
                    for event in tcod.event.wait():
                        #mouse position information
                        context.convert_event(event)
                        #gets user inputs and changes states accordingly
                        #now, every time we handle events, a handler gets returned, while action is handled
                        handler = handler.handle_events(event)
                except Exception:  #Handles exceptions
                    traceback.print_exc()  #Print error to stderr
                    #prints error to message log
                    if isinstance(handler, input_handlers.EventHandler):
                        handler.engine.message_log.add_message(traceback.format_exc(), color.error)

        except exceptions.QuitWithoutSaving:
            raise #just exits the game
        
        #TODO: multiple save files
        #TODO: add a save game button (maybe limits on the saves on certain difficulties?)

        except SystemExit: #Save and Quit
            save_game(handler, "savegame.sav")
            raise
        except BaseException: #save on any unexpected error
            save_game(handler, "savegame.sav")
            raise





if __name__ == "__main__":
    main()
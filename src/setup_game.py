'''Handles loading and inits game session'''
from __future__ import annotations

import lzma
import pickle
import traceback

import copy
from typing import Optional

import tcod
from tcod.console import Console

import configs.color as color
from engine import Engine
import entity_factories
import input_handlers
from procgen import generate_dungeon


#load background image and remove the alpha channel
#TODO: implement this, and remember to change down below to allow for image to show up
# background_image = tcod.image.load("assets/menu_background.jpeg")[:, :, :3]


def new_game() -> Engine:
    '''Returns new game session as an engine'''

    #map vars
    map_width = 80
    map_height = 43

    room_max_size = 10
    room_min_size = 6
    max_rooms = 30

    max_monsters_per_room = 2
    max_items_per_room = 2

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
        max_items_per_room=max_items_per_room,
        engine=engine
    )
    engine.update_fov()

    engine.message_log.add_message(
        "Hello fellow human, and welcome to [generic roguelike game]!", color.welcome_text
    )

    return engine

def load_game(filename: str) -> Engine:

    #TODO: multiple save files/multiple engines in the same file

    '''Loads an engine containing all the info'''
    #TODO: change filename into saves/filename
    with open(filename, "rb") as f:
        engine = pickle.loads(lzma.decompress(f.read()))
    
    assert isinstance(engine, Engine) #post condition
    return engine

class MainMenu(input_handlers.BaseEventHandler):
    '''Handle the main menu rendering and input'''
    def on_render(self, console: Console) -> None:
        '''Renders the main menu on a background image'''
        # console.draw_semigraphics(background_image, 0, 0)

        console.print(
            console.width // 2,
            console.height // 2 - 4,
            "Generic Rougue-Like",
            fg=color.menu_title,
            alignment=tcod.constants.CENTER,
        )
        console.print(
            console.width // 2,
            console.height - 4,
            "By Saaemm",
            fg=color.menu_title,
            alignment=tcod.constants.CENTER,
        )

        menu_width = 24
        for i, text in enumerate(
            ["[N] Play new game", "[C] Continue last game", "[Q] Quit"]
        ):
            console.print(
                console.width // 2,
                console.height // 2 - 2 + i,
                text.ljust(menu_width),
                fg=color.menu_text,
                bg=color.black,
                alignment=tcod.constants.CENTER,
                bg_blend=tcod.constants.BKGND_ALPH,  #check again later
            )

    def ev_keydown(
        self, event: tcod.event.KeyDown
    ) -> Optional[input_handlers.BaseEventHandler]:

        if event.sym in (tcod.event.KeySym.q, tcod.event.KeySym.ESCAPE):
            raise SystemExit()

        elif event.sym == tcod.event.KeySym.c:
            try:
                '''TODO: note: this here creates a bug such that if player died and reloads savegame, allows 1 extra turn
                because this returns a MainGameEventHandler instead of GameOver... fixed by deleting the savegame file after death, but can be
                a better way, especially if we saved the game while in some other eventhandler class'''
                return input_handlers.MainGameEventHandler(load_game("savegame.sav"))
            
            except FileNotFoundError:
                return input_handlers.PopupMessage(self, "No saved game to load. Start a new one!")
            
            except Exception as exc:  #any other error
                traceback.print_exc()  # Print to stderr.
                return input_handlers.PopupMessage(self, f"Failed to load save:\n{exc}")

        elif event.sym == tcod.event.KeySym.n:
            return input_handlers.MainGameEventHandler(new_game())

        return None
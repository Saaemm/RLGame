from __future__ import annotations

import lzma  #lzma.compress does compression on object
import pickle  #pickles.dump serializes object hierarchy in Python

from typing import TYPE_CHECKING

from tcod.console import Console
from tcod.map import compute_fov

import configs.color as color

import exceptions
from interface.message_log import MessageLog
import interface.render_functions as render_functions

if TYPE_CHECKING:
    from entity import Actor
    from game_map import GameMap, GameWorld

#drawing map, entities, handles player input
class Engine:

    #inited in main as a static/class variable
    game_map: GameMap
    game_world: GameWorld

    def __init__(self, player: Actor) -> None:
        self.message_log = MessageLog()
        self.mouse_location = (0, 0)
        self.player = player

        #10 lives to beat the game
        self.lives_left = 9

    def handle_enemy_turns(self) -> None:

        #self.game_map.actors gets a generator of actors in map
        for entity in set(self.game_map.actors) - {self.player}:
            if entity.ai is not None: #if it has an AI, then perform it
                try:
                    entity.ai.perform()
                except exceptions.Impossible:
                    pass  # Ignore impossible action exceptions from AI for now

    def update_fov(self) -> None:
        '''Recompute the visible area based on the player's POV'''
        self.game_map.visible[:] = compute_fov(
            self.game_map.tiles["transparent"],
            (self.player.x, self.player.y),
            radius=8
        )
        #update "explored" to include "visible"
        self.game_map.explored |= self.game_map.visible
            
    def render(self, console: Console) -> None:

        #updates map
        self.game_map.render(console)

        #prints message log at the bottom
        self.message_log.render(console=console, x=21, y=45, width=40, height=5)

        #prints lives left
        console.print(x=1, y=42, string=f"Lives left: {self.lives_left}", fg=color.bar_text)

        #prints player health
        render_functions.render_bar(
            console=console,
            current_value=self.player.fighter.hp,
            maximum_value=self.player.fighter.max_hp,
            total_width=20,
        )

        #prints which dungeon level the player is on
        render_functions.render_dungeon_level(
            console=console,
            dungeon_level=self.game_world.current_floor,
            location=(0, 47),
        )

        #prints mouse hovering info
        render_functions.render_names_at_mouse_location(console=console, x=21, y=44, engine=self)

    def save_as(self, filename: str) -> None:
        '''Saves this engine state as a compressed file        
        Note the engine defines the state
        '''
        save_data = lzma.compress(pickle.dumps(self))

        #TODO: put this file in saves folder...
        with open(filename, "wb") as f:  #saves in saves folder
            f.write(save_data)
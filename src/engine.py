from __future__ import annotations

from typing import TYPE_CHECKING

from tcod.console import Console
from tcod.map import compute_fov

from input_handlers import MainGameEventHandler
from interface.message_log import MessageLog
from interface.render_functions import render_bar, render_names_at_mouse_location

if TYPE_CHECKING:
    from entity import Actor
    from game_map import GameMap
    from input_handlers import EventHandler

#drawing map, entities, handles player input
class Engine:

    #inited in main as a static/class variable
    game_map: GameMap

    def __init__(self, player: Actor) -> None:
        self.event_handler: EventHandler = MainGameEventHandler(self)
        self.message_log = MessageLog()
        self.mouse_location = (0, 0)
        self.player = player

    def handle_enemy_turns(self) -> None:

        #self.game_map.actors gets a generator of actors in map
        for entity in set(self.game_map.actors) - {self.player}:
            if entity.ai is not None: #if it has an AI, then perform it
                entity.ai.perform()

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

        #prints player health
        render_bar(
            console=console,
            current_value=self.player.fighter.hp,
            maximum_value=self.player.fighter.max_hp,
            total_width=20,
        )

        #prints mouse hovering info
        render_names_at_mouse_location(console=console, x=21, y=44, engine=self)

        #prints game over if needed, can be folded into another function
        if not self.player.is_alive:
            console.print(
                x=25,
                y=25,
                string="GAME OVER"
            )
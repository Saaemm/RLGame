from __future__ import annotations

from typing import TYPE_CHECKING

from tcod.context import Context
from tcod.console import Console
from tcod.map import compute_fov

from input_handlers import EventHandler

if TYPE_CHECKING:
    from entity import Entity
    from game_map import GameMap

#drawing map, entities, handles player input
class Engine:

    #inited in main as a static/class variable
    game_map: GameMap

    def __init__(self, player: Entity) -> None:
        self.event_handler: EventHandler = EventHandler(self)
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
            
    def render(self, console: Console, context: Context) -> None:

        #updates map
        self.game_map.render(console)

        #update and clear/get rid of leftovers step
        context.present(console)
        console.clear()
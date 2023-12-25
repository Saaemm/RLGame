from typing import Set, Iterable, Any

from tcod.context import Context
from tcod.console import Console
from tcod.map import compute_fov

from entity import Entity
from game_map import GameMap
from input_handlers import EventHandler

#drawing map, entities, handles player input
class Engine:
    def __init__(self, player: Entity) -> None:
        self.event_handler: EventHandler = EventHandler(self)
        self.player = player

        self.update_fov()

    def handle_enemy_turns(self) -> None:
        for entity in self.game_map.entities - {self.player}:
            print(f'The {entity.name} wonders when it will take its turn')

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
from __future__ import annotations

from typing import TYPE_CHECKING

import configs.color as color

from components.base_component import BaseComponent
from configs.render_order import RenderOrder
from input_handlers import GameOverEventHandler

if TYPE_CHECKING:
    from entity import Actor

class Fighter(BaseComponent):

    entity: Actor

    def __init__(self, hp: int, defense: int, power: int) -> None:
        self.max_hp = hp
        self._hp = hp
        self.defense = defense
        self.power = power

    @property
    def hp(self) -> int:
        return self._hp
    
    @hp.setter
    def hp(self, value: int) -> None:
        self._hp = max(0, min(value, self.max_hp))
        if self._hp == 0 and self.entity.ai is not None:
            self.die()

    def die(self) -> None:
        if self.engine.player is self.entity:   #player death
            #Change over to game over event handler
            self.engine.event_handler = GameOverEventHandler(self.engine)
            death_message = "You died!"
            death_color = color.player_die
        else:
            death_message = f"{self.entity.name} is dead."
            death_color = color.enemy_die

        self.entity.char = "%"
        self.entity.color = (191, 0, 0)
        self.entity.blocks_movement = False #can now pass through
        self.entity.ai = None #is dead
        self.entity.name = f"remains of {self.entity.name}"
        self.entity.render_order = RenderOrder.CORPSE

        self.engine.message_log.add_message(death_message, death_color)
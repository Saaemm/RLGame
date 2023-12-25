from __future__ import annotations

from typing import Optional, TYPE_CHECKING
import tcod.event
from tcod.event import KeyDown, Quit
from actions import Action, EscapeAction, BumpAction

if TYPE_CHECKING:
    from engine import Engine

class EventHandler(tcod.event.EventDispatch[Action]):

    #turns events into actions, each function returns none or action
    def __init__(self, engine: Engine):
        self.engine = engine

    def handle_events(self) -> None:
        #gets list of user input events and iterates over them
        for event in tcod.event.wait():

            #action becomes whatever is returned by the user keypress's function, ie keydown if valid
            action = self.dispatch(event)

            if action is None:
                continue

            action.perform()
            self.engine.handle_enemy_turns()  #handles enemies after each player event

            self.engine.update_fov()  #updates the FOV before player's next action


    #Quit event, ie pressing the X button
    def ev_quit(self, event: Quit) -> Action | None:    #same thing as -> Optional[Action]
        raise SystemExit()
    
    #receives key press events and returns either Action or None
    def ev_keydown(self, event: KeyDown) -> Action | None:
        action: Optional[Action] = None

        key = event.sym

        player = self.engine.player

        if key == tcod.event.KeySym.UP:
            action = BumpAction(player, dx=0, dy=-1)
        elif key == tcod.event.KeySym.DOWN:
            action = BumpAction(player, dx=0, dy=1)
        elif key == tcod.event.KeySym.LEFT:
            action = BumpAction(player, dx=-1, dy=0)
        elif key == tcod.event.KeySym.RIGHT:
            action = BumpAction(player, dx=1, dy=0)

        elif key == tcod.event.KeySym.ESCAPE:
            action = EscapeAction(player)

        return action
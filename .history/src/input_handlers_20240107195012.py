from __future__ import annotations

import os

from typing import Union, Optional, TYPE_CHECKING, Callable, Tuple
from tcod.console import Console
import tcod.event
import tcod.constants
import configs.interface_config as config
from tcod.event import KeyDown, MouseButtonDown, MouseMotion, Quit

import actions
from actions import (Action, EscapeAction, BumpAction, WaitAction, PickupAction, TakeStairsAction)
import configs.color as color
import exceptions

if TYPE_CHECKING:
    from engine import Engine
    from entity import Item

ActionOrHandler = Union[Action, "BaseEventHandler"]
'''An event handler return value which can trigger an action or switch active handlers

If a handler is returned, it will become the active handler for future events.
If an action is returned it will be attempted and if it's valid then
MainGameEventHandler will become the active handler.
'''

class BaseEventHandler (tcod.event.EventDispatch[ActionOrHandler]):
    def handle_events(self, event: tcod.event.Event) -> BaseEventHandler:
        '''Handles an event and returns the next active handler'''
        state = self.dispatch(event)
        if isinstance(state, BaseEventHandler):
            return state
        
        assert not isinstance(state, Action), f"{self!r} can not handle actions."
        return self
    
    def on_render(self, console: tcod.console.Console) -> None:
        raise NotImplementedError()
    
    #Quit event, ie pressing the X button
    def ev_quit(self, event: Quit) -> ActionOrHandler | None:
        raise SystemExit()

class PopupMessage(BaseEventHandler):
    '''Displays a popup message with text'''

    def __init__(self, parent_handler: BaseEventHandler, text: str) -> None:
        self.parent = parent_handler  #can go back
        self.text = text

    def on_render(self, console: tcod.console.Console) -> None:
        '''Renders the parent and dim the result, then print the message on top.'''
        self.parent.on_render(console)
        console.tiles_rgb["fg"] //= 8  #dims
        console.tiles_rgb["bg"] //= 8  #dims

        console.print(
            console.width // 2,
            console.height // 2,
            self.text,
            fg=color.white,
            bg=color.black,
            alignment=tcod.constants.CENTER,
        )

    def ev_keydown(self, event: tcod.event.KeyDown) -> Optional[BaseEventHandler]:
        '''Any key returns to parent handler'''
        return self.parent

class EventHandler(BaseEventHandler):

    #turns events into actions, each function returns none or action
    def __init__(self, engine: Engine):
        #TODO: check that this is a real engine
        self.engine = engine

    def handle_events(self, event: tcod.event.Event) -> BaseEventHandler:
        '''Handles events for input handler with an engine'''
        action_or_state = self.dispatch(event)
        if isinstance(action_or_state, BaseEventHandler):
            return action_or_state
        
        if self.handle_action(action_or_state):
            #Valid action is performed

            #check for automatic switching to different game input states
            if not self.engine.player.is_alive:
                #player killed some time during or after action
                return GameOverEventHandler(self.engine)
            elif self.engine.player.level.requires_level_up:
                #if player needs levelling up, then level up
                return LevelUpHandler(self.engine)

            return MainGameEventHandler(self.engine)
        
        return self


    def handle_action(self, action: Optional[Action]) -> bool:
        '''Handle actions returned from event methods
        
        Returns True if the action will advance a turn
        '''
        if action is None:  #player has not taken turn yet
            return False
        
        try:
            action.perform()

        except exceptions.Impossible as exc:
            self.engine.message_log.add_message(exc.args[0], color.impossible)
            return False  #skips enemy turns on exceptions
        
        self.engine.handle_enemy_turns()  #handles enemies after each *player turn*, not tick/other time method

        self.engine.update_fov()  #updates the FOV before player's next action
        return True

    def ev_mousemotion(self, event: MouseMotion) -> Action | None:
        if self.engine.game_map.in_bounds(event.tile.x, event.tile.y):
            self.engine.mouse_location = event.tile.x, event.tile.y
    
    def on_render(self, console: tcod.console.Console) -> None:
        self.engine.render(console)
    

class MainGameEventHandler(EventHandler):

    #Main game, while player is alive 
    
    #receives key press events and returns either Action or None
    def ev_keydown(self, event: KeyDown) -> Action | None:
        action: Optional[Action] = None

        key = event.sym
        modifier = event.mod

        player = self.engine.player

        if key == tcod.event.KeySym.PERIOD and modifier and (
            tcod.event.KMOD_LSHIFT or tcod.event.KMOD_RSHIFT
        ):
            return TakeStairsAction(player)  #returns this action because this is an if not elif

        if key in config.MOVE_KEYS:
            dx, dy = config.MOVE_KEYS[key]
            action = BumpAction(player, dx, dy)

        elif key in config.WAIT_KEYS:
            action = WaitAction(player)

        elif key in config.ESCAPE_KEYS:
            action = EscapeAction(player)

        elif key == tcod.event.KeySym.v:
            #go to history viewer render/input state
            return HistoryViewer(self.engine)

        elif key == tcod.event.KeySym.g:
            #pickup
            action = PickupAction(player)

        elif key == tcod.event.KeySym.i:
            #inventory use
            return InventoryActivateHandler(self.engine)
        elif key == tcod.event.KeySym.d:
            #inventory drop
            return InventoryDropHandler(self.engine)

        elif key == tcod.event.KeySym.SLASH:
            return LookHandler(self.engine)

        elif key == tcod.event.KeySym.c:
            return CharacterScreenEventHandler(self.engine)

        #no valid key was pressed
        return action
    

class GameOverEventHandler(EventHandler):  
    #TODO: can consider making this a hybrid of both popup and event handler for restart etc or a popup w/ parent as event handler

    def on_render(self, console: Console) -> None:
        super().on_render(console)
    
        player = self.engine.player

        #prints game over if needed, can be folded into another function
        if not player.is_alive:
            console.print(
                x=30,
                y=25,
                string="GAME OVER",
            )

    def ev_keydown(self, event: KeyDown) -> Action | None:

        #Can only escape
        if event.sym in config.ESCAPE_KEYS:
            self.on_quit()  #goes to another dispatch that exits the game
        
        return None
    
    def on_quit(self) -> None:
        #TODO: see setup_game.py for long todo to change this instead of deleting
        #TODO: possibly add a spectator mode after death, can be easy -- just change visible
        #TODO: add manual save
        '''Handles exiting the game when the player is dead, mainly deleting the save file to prevent bug'''
        if os.path.exists("savegame.sav"): #TODO: change savegame.sav to save/savegame.sav + multiple save files
            os.remove("savegame.sav")
        raise exceptions.QuitWithoutSaving() #Avoid saving a finished game, exits
    
    def ev_quit(self, event: Quit) -> ActionOrHandler | None:
        self.on_quit()  #exits

class HistoryViewer(EventHandler):
    '''Prints the message log history on a larger window that can be navigated'''

    def __init__(self, engine: Engine):
        super().__init__(engine)
        self.log_length = len(engine.message_log.messages)
        self.cursor = self.log_length - 1

    def on_render(self, console: Console) -> None:
        super().on_render(console)  #Draws the main game as the background

        log_console = tcod.console.Console(console.width-6, console.height-6)  #new console

        #Draw a frame with a custom banner title
        log_console.draw_frame(0, 0, log_console.width, log_console.height)
        log_console.print_box(
            0, 0, log_console.width, 1, "-|Message History|-", alignment=tcod.constants.CENTER
        )

        #Render the message log using the cursor parameter
        self.engine.message_log.render_messages(
            console=log_console,
            x=1, 
            y=1, 
            width=log_console.width - 2, 
            height=log_console.height - 2,
            messages=self.engine.message_log.messages[: self.cursor + 1]
        )
        log_console.blit(console, 3, 3) #superimposes log_console onto console for rendering

    def ev_keydown(self, event: KeyDown) -> MainGameEventHandler | None:
        if event.sym in config.CURSOR_Y_KEYS:
            adjust = config.CURSOR_Y_KEYS[event.sym]
            if adjust < 0 and self.cursor == 0:
                #go from the top to the bottom when on the edge
                self.cursor = self.log_length-1
            elif adjust > 0 and self.cursor == self.log_length-1:
                #go from bottom to top when on edge
                self.cursor = 0
            else:
                #otherwise move while being bounded by the history log [0, log_length)
                self.cursor = max(0, min(self.cursor+adjust, self.log_length - 1))
        
        elif event.sym == tcod.event.KeySym.HOME or event.sym == tcod.event.KeySym.h:
            self.cursor = 0 #go to the top
        
        elif event.sym == tcod.event.KeySym.END or event.sym == tcod.event.KeySym.g:
            self.cursor = self.log_length-1 #go to the last message
        
        else: 
            #any other key goes back to main game state inputs/render
            return MainGameEventHandler(self.engine)
        
        return None


class AskUserEventHandler(EventHandler):
    '''Handles user input for actions which require special input.'''
    
    def ev_keydown(self, event: KeyDown) -> ActionOrHandler | None:
        '''By default, any key exits this input handler'''
        if event.sym in {  #Ignore modifier keys
            tcod.event.KeySym.LSHIFT,  
            tcod.event.KeySym.RSHIFT,  
            tcod.event.KeySym.LCTRL,  
            tcod.event.KeySym.RCTRL,  
            tcod.event.KeySym.LALT,  
            tcod.event.KeySym.RALT,  
        }:
            return None
        return self.on_exit()
    
    def ev_mousebuttondown(self, event: MouseButtonDown) -> ActionOrHandler | None:
        '''by default, any mouse click exits the input handler'''
        return self.on_exit()
    
    def on_exit(self) -> Optional[Action]:
        '''Called when user tries to exit or cancel an action. 

        By default, returns to the main event handler
        '''
        return MainGameEventHandler(self.engine)

class CharacterScreenEventHandler(AskUserEventHandler):
    TITLE = "Character Information"

    def on_render(self, console: tcod.console.Console) -> None:
        super().on_render(console)

        if self.engine.player.x <= 30:
            x = 40
        else:
            x = 0

        y = 0

        width = len(self.TITLE) + 4

        console.draw_frame(
            x=x,
            y=y,
            width=width,
            height=7,
            title=self.TITLE,
            clear=True,
            fg=(255, 255, 255),
            bg=(0, 0, 0),
        )

        console.print(
            x=x + 1, y=y + 1, string=f"Level: {self.engine.player.level.current_level}"
        )
        console.print(
            x=x + 1, y=y + 2, string=f"XP: {self.engine.player.level.current_xp}"
        )
        console.print(
            x=x + 1,
            y=y + 3,
            string=f"XP for next Level: {self.engine.player.level.experience_to_next_level}",
        )

        console.print(
            x=x + 1, y=y + 4, string=f"Attack: {self.engine.player.fighter.power}"
        )
        console.print(
            x=x + 1, y=y + 5, string=f"Defense: {self.engine.player.fighter.defense}"
        )

class LevelUpHandler(AskUserEventHandler):
    TITLE = "Level Up"

    def on_render(self, console: tcod.console.Console) -> None:
        super().on_render(console)

        if self.engine.player.x <= 30:
            x = 40
        else:
            x = 0

        console.draw_frame(
             x=x,
             y=0,
             width=35,
             height=8,
             title=self.TITLE,
             clear=True,
             fg=(255, 255, 255),
             bg=(0, 0, 0),
        )

        console.print(x=x+1, y=1, string="You leveled up!")
        console.print(x=x+1, y=1, string="Select an attribute to increase.")

        #TODO: add skill trees/skills
        console.print(
            x=x + 1,
            y=4,
            string=f"a) Constitution (+20 HP, from {self.engine.player.fighter.max_hp})",
        )
        console.print(
            x=x + 1,
            y=5,
            string=f"b) Strength (+1 attack, from {self.engine.player.fighter.power})",
        )
        console.print(
            x=x + 1,
            y=6,
            string=f"c) Agility (+1 defense, from {self.engine.player.fighter.defense})",
        )

    def ev_keydown(self, event: KeyDown) -> ActionOrHandler | None:
        player = self.engine.player
        key = event.sym
        index = key - tcod.event.KeySym.a

        if 0 <= index <= 2:
            if index == 0:
                player.level.increase_max_hp()
            elif index == 1:
                player.level.increase_power()
            elif index == 2:
                player.level.increase_defense()
        else:
            self.engine.message_log.add_message("Invalid Entry.", color.invalid)
            return None
            
        return super().ev_keydown(event)

    def ev_mousebuttondown(self, event: MouseButtonDown) -> ActionOrHandler | None:
        '''Don't allow any action when mouse down (when originally, it would have exited)'''
        return None
    
class InventoryEventHandler(AskUserEventHandler):
    '''This handler lets the user select an item.
    
    What happens depends on the subclass
    '''

    TITLE = "<missing title>"

    def on_render(self, console: tcod.console.Console) -> None:
        '''Renders an inventory menu, displays the items in the inventory, and the letter to select them.
        Will move to a different position based on where the player is located, 
        so the player can always see where they are'''

        #TODO: find a way to solve TODOS
        #TODO: compress the same items up to a limit
        #TODO: make a way to organize an inventory

        super().on_render(console)
        number_of_items_in_inventory = len(self.engine.player.inventory.items)

        height = number_of_items_in_inventory + 2
        
        if height <= 3:
            height = 3

        if self.engine.player.x <= 30:
            x = 40
        else: 
            x = 0

        y = 0

        width = len(self.TITLE) + 4

        console.draw_frame(
            x=x,
            y=y,
            width=width,
            height=height,
            title=self.TITLE,
            clear=True,
            fg=(255, 255, 255),
            bg=(0, 0, 0),
        )

        if number_of_items_in_inventory > 0:
            for i, item in enumerate(self.engine.player.inventory.items):
                item_key = chr(ord("a") + i)
                console.print(x + 1, y + i + 1, f"({item_key}) {item.name}")
        else:
            console.print(x + 1, y + 1, "(Empty)")

    def ev_keydown(self, event: KeyDown) -> ActionOrHandler | None:
        player = self.engine.player
        key = event.sym
        index = key - tcod.event.KeySym.a

        if 0 <= index <= 26:
            try:
                selected_item = player.inventory.items[index]
            except IndexError:
                self.engine.message_log.add_message("Invalid entry.", color.invalid)
                return None
            return self.on_item_selected(selected_item)
        return super().ev_keydown(event)

    def on_item_selected(self, item: Item) -> Optional[ActionOrHandler]:
        '''Called when user selects a valid item'''
        raise NotImplementedError()
    
class InventoryActivateHandler(InventoryEventHandler):
    '''Handles using an inventory item'''

    TITLE = "Select an item to use"

    def on_item_selected(self, item: Item) -> ActionOrHandler | None:
        '''Return the action for the selected item'''
        return item.consumable.get_action(self.engine.player)
    
class InventoryDropHandler(InventoryEventHandler):
    '''Handles dropping an item from inventory'''

    TITLE = "Select an item to drop"

    def on_item_selected(self, item: Item) -> ActionOrHandler | None:
        '''Drops the item'''
        return actions.DropItem(self.engine.player, item)
    

class SelectIndexHandler(AskUserEventHandler):
    '''Handles asking user for an index on the map using mouse'''

    def __init__(self, engine: Engine):
        '''Sets the cursor to the player when this is constructe '''
        super().__init__(engine)
        player = self.engine.player
        engine.mouse_location = player.x, player.y

    def on_render(self, console: Console) -> None:
        '''Highlight the tile under the cursor'''
        super().on_render(console)
        x, y = self.engine.mouse_location
        console.rgb["bg"][x, y] = color.white
        console.rgb["fg"][x, y] = color.black

    def ev_keydown(self, event: KeyDown) -> ActionOrHandler | None:
        '''Check for key movement or confirmation keys'''
        key = event.sym  #Holding modifier keys will speed up movements
        if key in config.MOVE_KEYS:
            modifier = 1
            if event.mod & (tcod.event.KMOD_LSHIFT | tcod.event.KMOD_RSHIFT):
                modifier *= 5
            elif event.mod & (tcod.event.KMOD_LCTRL | tcod.event.KMOD_RCTRL):
                modifier *= 10
            elif event.mod & (tcod.event.KMOD_LALT | tcod.event.KMOD_RALT):
                modifier *= 20

            x, y = self.engine.mouse_location
            dx, dy = config.MOVE_KEYS[key]
            x += dx * modifier
            y += dy * modifier
            #clamp x, y on both sides of the map
            x = max(0, min(x, self.engine.game_map.width-1))
            y = max(0, min(y, self.engine.game_map.height-1))
            self.engine.mouse_location = x, y
            return None

        elif key in config.CONFIRM_KEYS:
            return self.on_index_selected(*self.engine.mouse_location)

        return super().ev_keydown(event=event)
    
    def ev_mousebuttondown(self, event: MouseButtonDown) -> ActionOrHandler | None:
        '''Left click confirms a selection'''

        if self.engine.game_map.in_bounds(*event.tile):
            if event.button == 1:
                return self.on_index_selected(*self.engine.mouse_location)
        return super().ev_mousebuttondown(event)
    
    def on_index_selected(self, x: int, y: int) -> Action | None:
        '''Called when index is selected'''
        raise NotImplementedError()
    

class LookHandler(SelectIndexHandler):
    '''Allows user to look around with keyboard'''

    def on_index_selected(self, x: int, y: int) -> MainGameEventHandler:
        '''Returns to Main Event Handler'''
        return MainGameEventHandler(self.engine)


class SingleRangedAttackHandler(SelectIndexHandler):
    def __init__(self, engine: Engine, callback: Callable[[Tuple[int, int]], Optional[ActionOrHandler]]):
        super().__init__(engine)

        self.callback = callback  #function that takes in a tuple (x, y) and returns Action | None

    def on_index_selected(self, x: int, y: int) -> Action | None:
        return self.callback((x, y))
    
class AreaRangedAttackHandler(SelectIndexHandler):
    def __init__(
        self, 
        engine: Engine,
        radius: int,
        callback: Callable[[Tuple[int, int]], Optional[Action]]
    ):
        super().__init__(engine)

        self.radius = radius
        self.callback = callback

    def on_render(self, console: Console) -> None:
        '''Highlights radius'''
        super().on_render(console)

        x, y = self.engine.mouse_location

        #draws a red rectangle around blast radius
        console.draw_frame(
            x=x - self.radius - 1,
            y=y - self.radius - 1,
            width=self.radius ** 2,
            height=self.radius ** 2,
            fg=color.red,
            clear=False,
        )

    def on_index_selected(self, x: int, y: int) -> Action | None:
        return self.callback((x, y))
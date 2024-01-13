from __future__ import annotations

import os
import copy

from typing import Union, Optional, TYPE_CHECKING, Callable, Tuple
from tcod.console import Console
import tcod.event
import tcod.constants
import configs.interface_config as config
from tcod.event import KeyDown, MouseButtonDown, MouseMotion, Quit

import actions
from actions import (Action, EscapeAction, BumpAction, WaitAction, PickupAction, TakeStairsAction)
import configs.color as color
from engine import Engine
import exceptions
from entity import EquippableItem, ConsumableItem
import entity_factories

if TYPE_CHECKING:
    from engine import Engine

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
        console.rgb["fg"] //= 8  #dims
        console.rgb["bg"] //= 8  #dims

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

            #reduce equipped for all entities cooldowns
            for actor in self.engine.game_map.actors:
                if actor.equipment.weapon is not None:
                    actor.equipment.weapon.equippable.current_cooldown -= 1
                if actor.equipment.armor is not None:
                    actor.equipment.armor.equippable.current_cooldown -= 1

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
        
        elif key == tcod.event.KeySym.q:
            if player.equipment.weapon is None:
                return actions.RaiseError(player, "You do not have a weapon equipped.")
            try:
                handler = player.equipment.weapon.equippable.weapon_action(player) #handler either none (action) or handler
                if handler is not None:
                    return handler
            except exceptions.Impossible as exc:
                self.engine.message_log.add_message(exc.args[0], color.impossible)
                return None
                    
            action = WaitAction(self.engine)

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
    
class AttributeSelection(EventHandler):
    '''Allows the player to select attributes with player creation'''

    def __init__(
            self, 
            engine: Engine, 
            skill_points: int = 10, 
            base_hp_pts: int = 0, 
            base_attack_pts: int = 0, 
            base_defense_pts: int = 0,
            type_of_weapon: dict = None,
            type_of_armor: dict = None,
        ):
        super().__init__(engine)
        self.skill_points = skill_points
        self.current_skill_points = skill_points

        self.hp_points = base_hp_pts
        self.defense_points = base_defense_pts
        self.power_points = base_attack_pts

        self.buy_weapon = None
        if type_of_weapon is None:
            self.type_of_weapon = {entity_factories.dagger: 2} #dictionary of weapon/cost
        self.buy_armor = None
        if type_of_armor is None:
            self.type_of_armor = {entity_factories.leather_armor: 2} #dictionary of armor/cost
    
    def on_render(self, console: Console) -> None:

        #TODO: make this prettier, do not have popup message when showing error...
        #TODO: game over/ game clear conditions, weapon abilities
        #TODO: make autocreate an option
        #TODO: maybe add mana???

        console.print(
            console.width // 2,
            console.height // 2 - 4,
            "Create your character!",
            fg=color.menu_title,
            alignment=tcod.constants.CENTER,
        )
        console.print(
            console.width // 2,
            console.height - 4,
            f"hp points: {self.hp_points}, power points: {self.power_points}, defense points: {self.defense_points}",
            fg=color.menu_title,
            alignment=tcod.constants.CENTER,
        )

        menu_width = 24

        console.print(
                console.width // 2,
                console.height // 2 - 7,
                f"Skill points remaining: {self.current_skill_points} / {self.skill_points}",
                fg=color.menu_text,
                bg=color.black,
                alignment=tcod.constants.CENTER,
                bg_blend=tcod.constants.BKGND_ALPH,  #check again later
            )

        #TODO: make iterative list first without hardcoding
        for i, text in enumerate(
            [
                "(a) increase hp by 5", 
                "(b) increase power by 1", 
                "(c) increase defense by 1", 
                "(d) decrease hp by 5", 
                "(e) decrease power by 1", 
                "(f) decrease defense by 1",
                f"(g) buy {list(self.type_of_weapon.keys())[0].name} (spend {self.type_of_weapon[list(self.type_of_weapon.keys())[0]]} points)",
                f"(h) buy {list(self.type_of_armor.keys())[0].name} (spend {self.type_of_armor[list(self.type_of_armor.keys())[0]]} points)",
                f"(i) sell weapon (gain {0 if self.buy_weapon is None else self.type_of_weapon[self.buy_weapon]} points)",
                f"(j) sell armor (gain {0 if self.buy_armor is None else self.type_of_armor[self.buy_armor]} points)"
                # "(z) default skillpoint distribution",
            ]
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


    def ev_keydown(self, event: KeyDown) -> ActionOrHandler | None:
        player = self.engine.player
        key = event.sym
        index = key - tcod.event.KeySym.a

        if key in config.CONFIRM_KEYS:
            if self.current_skill_points != 0:
                return PopupMessage(self, "Spend all your points!")
            
            player.fighter.max_hp = 5 + 5 * self.hp_points #need to set maxhp first before setting hp
            player.fighter.hp = player.fighter.max_hp
            player.fighter.base_defense = self.defense_points
            player.fighter.base_power = self.power_points

            if self.buy_weapon is not None:
                #initial equipment
                weapon = copy.deepcopy(list(self.type_of_weapon.keys())[0])
                #put these in the inventory
                weapon.parent = player.inventory
                #put weapon in the inventory and equip it
                player.inventory.items.append(weapon)
                player.equipment.toggle_equip(weapon, add_message=False)

            if self.buy_armor is not None:
                #initial equipment
                armor = copy.deepcopy(list(self.type_of_armor.keys())[0])

                #put these in the inventory
                armor.parent = player.inventory

                #put weapon in the inventory and equip it
                player.inventory.items.append(armor)
                player.equipment.toggle_equip(armor, add_message=False)

            return MainGameEventHandler(self.engine)
        
        if key in config.ESCAPE_KEYS:
            from setup_game import MainMenu
            return MainMenu()

        if 0 <= index <= 2:
            
            if self.current_skill_points <= 0:
                return PopupMessage(self, "No more skill points left. Press return to create your character!")
            
            self.current_skill_points -= 1

            if index == 0:
                self.hp_points += 1
            elif index == 1:
                self.power_points += 1
            elif index == 2:
                self.defense_points += 1


        elif 3 <= index <= 5:

            if self.current_skill_points >= self.skill_points:
                return PopupMessage(self, "You are at the max skill points available")

            if index == 3:
                if self.hp_points <= 0:
                    return PopupMessage(self, "You cannot go lower than this hp.")
                self.hp_points -= 1
            elif index == 4:
                if self.power_points <= 0:
                    return PopupMessage(self, "You cannot go lower than this power.")
                self.power_points -= 1
            elif index == 5:
                if self.defense_points <= 0:
                    return PopupMessage(self, "You cannot go lower than this defense.")
                self.defense_points -= 1

            #increase current skill points after all possible errors
            self.current_skill_points += 1

        elif 6 <= index <= 7:
            #handles buying/selling weapons

            if index == 6:
                if self.buy_weapon is not None:
                    return PopupMessage(self, "You must buy at most 1 weapon.")
                buy_weapon = list(self.type_of_weapon.keys())[0]
                price = self.type_of_weapon[buy_weapon]
                if self.current_skill_points - price < 0:
                    return PopupMessage(self, "No more skill points left. Press return to create your character!")
                self.buy_weapon = buy_weapon
                self.current_skill_points -= price

            elif index == 7:
                if self.buy_armor is not None:
                    return PopupMessage(self, "You must buy at most 1 armor.")
                buy_armor = list(self.type_of_armor.keys())[0]
                price = self.type_of_armor[buy_armor]
                if self.current_skill_points - price < 0:
                    return PopupMessage(self, "No more skill points left. Press return to create your character!")
                self.buy_armor = buy_armor
                self.current_skill_points -= price

        elif 8 <= index <= 9:
            #handles selling weapons/armor

            if index == 8:
                if self.buy_weapon is None:
                    return PopupMessage(self, "You cannot sell nothing!")
                
                price = self.type_of_weapon[self.buy_weapon]

                if self.current_skill_points + price > self.skill_points:
                    return PopupMessage(self, "You are at the max skill points available")
                self.buy_weapon = None
                self.current_skill_points += price

            elif index == 9:
                if self.buy_weapon is None:
                    return PopupMessage(self, "You cannot sell nothing!")
                
                price = self.type_of_armor[self.buy_armor]

                if self.current_skill_points + price > self.skill_points:
                    return PopupMessage(self, "You are at the max skill points available")
                self.buy_armor = None
                self.current_skill_points += price


        elif index == 26:
            #TODO: implement default
            pass
        
        else:
            return PopupMessage(self, "Choose an appropriate action!")
            
        return None

    def ev_mousebuttondown(self, event: MouseButtonDown) -> ActionOrHandler | None:
        '''Don't allow any action when mouse down (when originally, it would have exited)'''
        return None

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
        #TODO: ability to pass up on level up for now
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
                
                is_equipped = (isinstance(item, EquippableItem) 
                               and self.engine.player.equipment.item_is_equipped(item))
                
                item_string = f"({item_key}) {item.name}"

                if is_equipped:
                    item_string = f"{item_string} (E)"

                console.print(x + 1, y + i + 1, item_string)

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

    def on_item_selected(self, item: Union[ConsumableItem, EquippableItem]) -> Optional[ActionOrHandler]:
        '''Called when user selects a valid item'''
        raise NotImplementedError()
    
class InventoryActivateHandler(InventoryEventHandler):
    '''Handles using an inventory item'''

    TITLE = "Select an item to use"

    def on_item_selected(self, item: Union[ConsumableItem, EquippableItem]) -> ActionOrHandler | None:
        '''Return the action for the selected item'''
        if isinstance(item, ConsumableItem):
            return item.consumable.get_action(self.engine.player)
        elif isinstance(item, EquippableItem):
            return actions.EquipAction(self.engine.player, item)
        else:
            return None
    
class InventoryDropHandler(InventoryEventHandler):
    '''Handles dropping an item from inventory'''

    TITLE = "Select an item to drop"

    def on_item_selected(self, item: Union[ConsumableItem, EquippableItem]) -> ActionOrHandler | None:
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
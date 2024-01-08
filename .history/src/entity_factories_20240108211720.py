from components.ai import HostileEnemy
from components import consumable, equippable
from components.equipment import Equipment
from components.fighter import Fighter
from components.inventory import Inventory
from entity import Actor, ConsumableItem, EquippableItem
from components.level import Level

#player
player = Actor(
    char="@", 
    color=(255, 255, 255), 
    name="Player", 
    ai_cls=HostileEnemy,  #is not used
    fighter=Fighter(hp=30, defense=2, power=5),
    inventory=Inventory(capacity=26),
    level=Level(level_up_base=200),
)

#enemies
orc = Actor(
    char="o", 
    color=(63, 127, 63), 
    name="Orc", 
    ai_cls=HostileEnemy,
    fighter=Fighter(hp=10, defense=0, power=3),
    inventory=Inventory(capacity=0),
    level=Level(xp_given=35),
)
troll = Actor(
    char="T", 
    color=(0, 127, 0), 
    name="Troll", 
    ai_cls=HostileEnemy,
    fighter=Fighter(hp=16, defense=1, power=4),
    inventory=Inventory(capacity=0),
    level=Level(xp_given=100),
)

#consumables
health_potion = ConsumableItem(
    char="!",
    color=(127, 0, 255),
    name="Health Potion",
    consumable=consumable.HealingConsumable(amount=4),
)

lightning_scroll = ConsumableItem(
    char='~',
    color=(255, 255, 0),
    name="Lightning Scroll", 
    consumable=consumable.LightningDamageConsumale(damage=20, maximum_range=5),
)

confusion_scroll = ConsumableItem(
    char='~',
    color=(207, 63, 255),
    name="Confusion Scroll",
    consumable=consumable.ConfusionConsumable(number_of_turns=10),
)

fireball_scroll = ConsumableItem(
    char='~',
    color=(255, 0, 0),
    name="Fireball Scroll",
    consumable=consumable.FireballDamageConsumable(damage=12, radius=3),
)


#equippables
dagger = EquippableItem(
    char="/", color=(0, 191, 255), name="Dagger", equippable=equippable.Dagger()
)

sword = EquippableItem(
    char="/", color=(0, 191, 255), name="Sword", equippable=equippable.Sword()
)

leather_armor = EquippableItem(
    char="[",
    color=(139, 69, 19),
    name="Leather Armor",
    equippable=equippable.LeatherArmor(),
)

chain_mail = EquippableItem(
    char="[", color=(139, 69, 19), name="Chain Mail", equippable=equippable.ChainMail()
)
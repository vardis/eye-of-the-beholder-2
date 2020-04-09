from enum import Enum, IntFlag

directions = ['north', 'east', 'south', 'west']

classes = {
    0x00: "Fighter",
    0x01: "Ranger",
    0x02: "Paladin",
    0x03: "Mage",
    0x04: "Cleric",
    0x05: "Thief",
    0x06: "Fighter/Cleric",
    0x07: "Fighter/Thief",
    0x08: "Fighter/Mage",
    0x09: "Fighter/Mage/Thief",
    0x0A: "Thief/Mage",
    0x0B: "Cleric/Thief",
    0x0C: "Fighter/Cleric/Mage",
    0x0D: "Ranger/Cleric",
    0x0E: "Cleric/Mage",
    0x0F: '0x0F',
    0x10: '0x10'
}

races = {
    0x00: 'human male',
    0x01: 'human female',
    0x02: 'elf male',
    0x03: 'elf female',
    0x04: 'half-elf male',
    0x05: 'half-elf female',
    0x06: 'dwarf male',
    0x07: 'dwarf female',
    0x08: 'gnome male',
    0x09: 'gnome female',
    0x0A: 'halfling male',
    0x0B: 'halfling female',
}

alignments = {
    0x00: "Lawful Good",
    0x01: "Neutral Good",
    0x02: "Chaotic Good",
    0x03: "Lawful Neutral",
    0x04: "True Neutral",
    0x05: "Chaotic Neutral",
    0x06: "Lawful Evil",
    0x07: "Neutral Evil",
    0x08: "Chaotic Evil",
}


class Class(Enum):
    Fighter = 0x0,
    Ranger = 0x1,
    Paladin = 0x2,
    Mage = 0x3,
    Cleric = 0x4,
    Thief = 0x5,
    FighterCleric = 0x6,
    FighterThief = 0x7,
    FighterMage = 0x8,
    FighterMageThief = 0x9,
    ThiefMage = 0xa,
    ClericThief = 0xb,
    FighterClericMage = 0xc,
    RangerCleric = 0xd,
    ClericMage = 0xe,


class Race(Enum):
    HumanMale = 0x0,
    HumanFemale = 0x1,
    ElfMale = 0x2,
    ElfFemale = 0x3,
    HalfElfMale = 0x4,
    HalfElfFemale = 0x5,
    DwarfMale = 0x6,
    DwarfFemale = 0x7,
    GnomeMale = 0x8,
    GnomeFemale = 0x9,
    HalflingMale = 0xa,
    HalflingFemale = 0xb,


class Alignment(Enum):
    LawfullGood = 0,
    NeutralGood = 1,
    ChaoticGood = 2,
    LawfullNeutral = 3,
    TrueNeutral = 4,
    ChaoticNeutral = 5,
    LawfullEvil = 6,
    NeutralEvil = 7,
    ChaoticEvil = 8,

ItemAction = {
    '0': 'Nothing',
    '1': '1',
    '2': 'Ammunition',
    '3': 'Use ammunition',
    '4': 'Amulet | coin | eye of talon...',
    '5': 'Open mage spell window',
    '6': 'Open cleric spell window',
    '7': "Food",
    '8': "Bones",
    '9': "Glass sphere | Magic dust | Scroll",
    '10': "Scroll",
    '11': "Parchment (something to read)",
    '12': "Stone item (Cross, Dagger, Gem...)",
    '13': "Key",
    '14': "Potion",
    '15': "Gem",
    '18': "0x12",
    '19': "Blow horn (N/S/W/E wind...)",
    '20': "Amulet of Life or Death",
    '128': "Range Party member",
    '129': "Range Close",
    '130': "Range Medium",
    '131': "Range Long",
    '132': "Lock picks",
    '138': "Amulet",
    '144': "Crimson ring",
    '146': "Wand",
}


class ClassUage(IntFlag):
    """

    """
    Null = 0x00
    Fighter = 0x01
    Mage = 0x02
    Cleric = 0x04
    Thief = 0x08


class HandFlags(IntFlag):
    """

    """
    Primary = 0x0,
    Secondary = 0x1,
    Both = 0x2,


class ItemFlags(IntFlag):
    """
    Item's flags
    """
    Nothing = 0x00,
    Flag01 = 0x01
    ArmorBonus = 0x02
    Flag04 = 0x04  # Enchanted ??
    isVampiric = 0x08  # Sucks damage points from target to attacker
    SpeedBonus = 0x10
    isCursed = 0x20
    isIdentified = 0x40
    GlowMagic = 0x80


class ProfessionFlags(IntFlag):
    """

    """
    Fighter = 0x01  #
    Ranger = 0x02  #
    Paladin = 0x04  #
    Mage = 0x08  #
    Cleric = 0x10  #
    Thief = 0x20  #


class ItemSlotFlags(IntFlag):
    """

    """
    Quiver = 0x01,
    Armour = 0x02,
    Bracers = 0x04,
    Backpack = 0x08,
    Boots = 0x10,
    Helmet = 0x20,
    Necklace = 0x40,
    Belt = 0x80,
    Ring = 0x100,


class ItemTypeUsage(IntFlag):
    # @formatter:off
    SHIELD        = 0x0,
    MELEE_WEAPON  = 0x01,
    FIRE_WEAPON   = 0x02,
    RANGED_WEAPON = 0x03,
    KEYS          = 0x04,
    CLERIC_SYMBOL = 0x05,
    SPELLBOOK     = 0x06,
    RATIONS       = 0x07,
    WRISTS        = 0x08,
    CLERIC_SCROLL = 0x09
    MAGE_SCROLL   = 0x0A,
    ARMOR         = 0x0B,
    NECKLACE      = 0x0C,
    MISC          = 0x0D,
    STONE_ITEM    = 0x0E,
    LOCKPICKS     = 0x0F,
    DUNNO         = 0x10,
    COIN          = 0x11,
    POTION        = 0x12,
    WAND          = 0x13,
    HORN          = 0x14,
    RING          = 0x15,
    DUNNO2        = 0x80
    # @formatter:on



class WallFlags(IntFlag):
    # @formatter:off
    PASS_NONE    = 0x00  # Can be passed by no one
    PARTY_PASS   = 0x01  # Can be passed by the player, big item
    SMALL_PASS   = 0x02  # Can be passed by a small item
    MONSTER_PASS = 0x04  # Can be passed by a monster
    PASS_ALL     = 0x07  # Can be passed by all
    IS_DOOR      = 0x08  # Is a door
    DOOR_OPEN    = 0x10  # The door is open
    DOOR_CLOSED  = 0x20  # The door is closed
    DOOR_KNOW    = 0x40  # The door has a knob
    ONLY_DEC     = 0x80  # No wall, only decoration, items visible
    # @formatter:on

class WallType(IntFlag):
    # @formatter:off
    SOLID       = 0x01  # Is a solid wall, draw top
    SELF_DRAW   = 0x02  # Is a stair, for example, no bottom
    DOOR_STUCK  = 0x04  # The door is stuck
    DOOR_MOVES  = 0x08  # The door is opening
    DOOR_OPEN   = 0x10  # The door is open
    DOOR_CLOSED = 0x20  # The door is closed
    # @formatter:on


#!/usr/bin/env python3

import os
import struct

import tokens
from assets import *
from entities import *
from flags import *

DATA_DIR = "data/"
BUILD_DIR = "build/"

assets_manager = AssetsManager()


class Monster:
    """
    flags:
    0 = default
    1 = ?
    2 = ?
    3 = ?
    4 = ?
    5 = ?
    6 = ?
    7 = ?
    8 = fear ?
    9 = ?
    10 = ?

        01h-> Active (fighting) has attacked MO_ACT
        02h-> is hit                        MO_HIT
        04h-> Flipflag                      MO_FLIP
        08h-> UNDEAD "Turned"               MO_TURNED
        10h-> set if "turned undead"        MO_FLEE
        20h-> turned to stone               MO_STONE
        40h-> Inactive (at start)           MO_INACT


    Phases:
         -1: raise weapon
         -2: Hit!
          0: Move forward
          1: Move Backwards
          2: Move Left
          3: Move Right
          4: Adjust-Turn
          5: Turn Left
          6: Turn Right
          7: AdjNextHit
          8: Inactive
          9: Walk
         10: Is Hit

    """

    def __init__(self, reader=None):
        """

        """
        self.index = None
        self.timer_id = None
        self.location = None
        self.sub_position = None
        self.direction = None
        self.monster_type = None
        self.picture_index = None
        self.phase = None
        self.pause = None
        self.weapon = None
        self.pocket_item = None

        self.decode(reader)

    def decode(self, reader):
        if not reader:
            return

        self.index = reader.read_byte()
        self.timer_id = reader.read_ubyte()
        self.location = Location(reader)
        self.sub_position = reader.read_ubyte()
        self.direction = reader.read_ubyte()
        self.monster_type = reader.read_ubyte()
        self.picture_index = reader.read_ubyte()
        self.phase = reader.read_ubyte()
        self.pause = reader.read_ubyte()
        self.weapon = reader.read_ushort()
        self.pocket_item = reader.read_ushort()

    def __str__(self):
        """

        :return:
        """

        return "ID {index} @ {location}|{subposition} [direction: {direction}, Timer:{timer}, monster_type :{monster_type}, " \
               "picture:{picture}, phase:{phase}, pause:{pause}, weapon:{weapon}, pocket:{pocket}]".format(
            index=self.index, location=self.location, subposition=self.sub_position,
            direction=directions[self.direction],
            timer=self.timer_id, monster_type=self.monster_type, picture=self.picture_index, phase=self.phase,
            pause=self.pause,
            weapon=self.weapon, pocket=self.pocket_item
        )

    def export(self):
        return {
            "index": self.index,
            "timerDelay": self.timer_id,
            "location": self.location.export(),
            "subPos": self.sub_position,
            "direction": self.direction,
            "monsterType": self.monster_type,
            "picture": self.picture_index,
            "phase": self.phase,
            "pause": self.pause,
            "weapon": self.weapon,
            "pocketItem": self.pocket_item
        }


class WallMapping:

    def __init__(self):
        # this is referenced in the .maz file
        self.wall_mapping_index = None
        self.wall_type = 0  # Index to what backdrop wall type that is being used
        self.decoration_id = 0  # Index to an optional overlay decoration image in the
        # DecorationData.decorations
        # array in the [[eob.dat |.dat]] files
        self.event_mask = 0  #
        self.flags = 0  #

    @property
    def is_blocking(self):
        return self.flags & 0x00 == 0x00

    @property
    def is_door(self):
        return self.flags & 0x08 == 0x08

    def export(self):
        return {
            "decorationId": self.decoration_id,
            "wall_mapping_index": self.wall_mapping_index,
            "type": self.wall_type,
            "flags": self.flags,
            "eventMask": self.event_mask
        }

    def __str__(self):

        wall_type = ""
        if self.wall_type & 0x01 == 0x01: wall_type += "WT_SOLID, "
        if self.wall_type & 0x02 == 0x02: wall_type += "WT_SELFDRAW, "
        if self.wall_type & 0x04 == 0x04: wall_type += "WT_DOORSTUCK, "
        if self.wall_type & 0x08 == 0x08: wall_type += "WT_DOORMOVES, "
        if self.wall_type & 0x10 == 0x10: wall_type += "WT_DOOROPEN, "
        if self.wall_type & 0x20 == 0x20: wall_type += "WT_DOORCLOSED, "

        flags = ""
        if self.flags & 0x00 == 0x00: flags += "WF_PASSNONE, "
        if self.flags & 0x01 == 0x01: flags += "WF_PARTYPASS, "
        if self.flags & 0x02 == 0x02: flags += "WF_SMALLPASS, "
        if self.flags & 0x04 == 0x04: flags += "WF_MONSTERPASS, "
        if self.flags & 0x07 == 0x07: flags += "WF_PASSALL, "
        if self.flags & 0x08 == 0x08: flags += "WF_ISDOOR, "
        if self.flags & 0x10 == 0x10: flags += "WF_DOOROPEN, "
        if self.flags & 0x20 == 0x20: flags += "WF_DOORCLOSED, "
        if self.flags & 0x40 == 0x40: flags += "WF_DOORKNOB, "
        if self.flags & 0x80 == 0x80: flags += "WF_ONLYDEC, "

        return "Type: {type} - Flags: {flags}".format(type=wall_type, flags=flags)


class ScriptTokens(Enum):
    TOKEN_SET_WALL = 0xff,
    TOKEN_CHANGE_WALL = 0xfe,
    TOKEN_OPEN_DOOR = 0xfd,
    TOKEN_CLOSE_DOOR = 0xfc,
    TOKEN_CREATE_MONSTER = 0xfb,
    TOKEN_TELEPORT = 0xfa,
    TOKEN_STEAL_SMALL_ITEMS = 0xf9,
    TOKEN_MESSAGE = 0xf8,
    TOKEN_SET_FLAG = 0xf7,
    TOKEN_SOUND = 0xf6,
    TOKEN_CLEAR_FLAG = 0xf5,
    TOKEN_HEAL = 0xf4,
    TOKEN_DAMAGE = 0xf3,
    TOKEN_JUMP = 0xf2,
    TOKEN_END = 0xf1,
    TOKEN_RETURN = 0xf0,
    TOKEN_CALL = 0xef,
    TOKEN_CONDITIONAL = 0xee,
    TOKEN_CONSUME = 0xed,
    TOKEN_CHANGE_LEVEL = 0xec,
    TOKEN_GIVE_XP = 0xeb,
    TOKEN_NEW_ITEM = 0xea,
    TOKEN_LAUNCHER = 0xe9,
    TOKEN_TURN = 0xe8,
    TOKEN_IDENTIFY_ITEMS = 0xe7,
    TOKEN_ENCOUNTER = 0xe6,
    TOKEN_WAIT = 0xe5,


class ConditionValue(Enum):
    OPERATOR_EQ = 0xff,
    OPERATOR_NEQ = 0xfe,
    OPERATOR_LT = 0xfd,
    OPERATOR_LTE = 0xfc,
    OPERATOR_GT = 0xfb,
    OPERATOR_GTE = 0xfa,
    OPERATOR_AND = 0xf9,
    OPERATOR_OR = 0xf8,
    VALUE_GET_WALL_NUMBER = 0xf7,
    VALUE_COUNT_ITEMS = 0xf5,
    VALUE_COUNT_MONSTERS = 0xf3,
    VALUE_CHECK_PARTY_POSITION = 0xf1,
    VALUE_GET_GLOBAL_FLAG = 0xf0,
    VALUE_END_CONDITIONAL = 0xee,
    VALUE_GET_PARTY_DIRECTION = 0xed,
    VALUE_GET_WALL_SIDE = 0xe9,
    VALUE_GET_POINTER_ITEM = 0xe7,
    VALUE_GET_TRIGGER_FLAG = 0xe0,
    VALUE_CONTAINS_RACE = 0xdd,
    VALUE_CONTAINS_CLASS = 0xdc,
    VALUE_ROLL_DICE = 0xdb,
    VALUE_IS_PARTY_VISIBLE = 0xda,
    VALUE_CONTAINS_ALIGNMENT = 0xce,
    VALUE_GET_LEVEL_FLAG = 0xef,


class DoorInfo:
    """
    http://eab.abime.net/showpost.php?p=533880&postcount=374
    http://eab.abime.net/showpost.php?p=579468&postcount=405
    """

    def __init__(self):
        self.command = None
        self.idx = None
        self.type = None
        self.knob = None
        self.gfxFile = ""
        self.doorRectangles = [Rectangle() for i in range(3)]  # rectangles in door?.cps size [3]
        self.buttonRectangles = [Rectangle() for i in range(2)]  # rectangles in door?.cps size [2]
        self.buttonPositions = [Point() for i in range(2)]  # x y position where to place door button size [2,2]

    def decode(self):
        if self.gfxFile is not None:
            assets_manager.export_cps_image(self.gfxFile)

        return {
            "command": self.command,
            "idx": self.idx,
            "type": self.type,
            "knob": self.knob,
            "gfxFile": self.gfxFile,
            "doorRectangle": [rect.export() for rect in self.doorRectangles],
            "buttons": {
                "rectangles": [rect.export() for rect in self.buttonRectangles],
                "positions": [point.export() for point in self.buttonPositions],
            }
        }


class MonsterType:
    """

    """

    def __init__(self):
        self.index = 0
        self.unk0 = None
        self.thac0 = 0
        self.unk1 = None
        self.hp_dice = Dice()
        self.number_of_attacks = 0
        self.attack_dice = [Dice() for i in range(3)]
        self.special_attack_flag = 0
        self.abilities_flags = 0
        self.unk2 = None
        self.exp_gain = 0
        self.size = 0
        self.attack_sound = 0
        self.move_sound = 0
        self.unk3 = None
        self.is_attack2 = 0
        self.distant_attack = 0
        self.max_attack_count = 0
        self.attack_list = [None for i in range(5)]
        self.turn_undead_value = 0
        self.unk4 = None
        self.unk5 = [None for i in range(3)]

    def decode(self):
        return {
            "index": self.index,
            "unknown0": self.unk0,
            "thac0": self.thac0,
            "unknown1": self.unk1,
            "hp": self.hp_dice.export(),
            "attacks": {
                "count": self.number_of_attacks,
                "dices": [dice.export() for dice in self.attack_dice],
                "special_flags": self.special_attack_flag,
                "abilities_flags": self.abilities_flags,
                "sound": self.attack_sound,
                "distant": self.distant_attack,
            },
            "unknown2": self.unk2,
            "exp_gain": self.exp_gain,
            "size": self.size,
            "move_sound": self.move_sound,
            "unknown3": self.unk3,
            "is_attack2": self.is_attack2,
            "max_attack_count": self.max_attack_count,
            "attack_list": self.attack_list,
            "turn_undead": self.turn_undead_value,
            "unknown4": self.unk4,
            "unknown5": self.unk5,
        }


class MonsterGfx:
    """

    """

    def __init__(self):
        self.used = False
        self.load_prog = None
        self.unk0 = None
        self.unk1 = None
        self.label = ""

    def __str__(self):
        return self.label

    def export(self):
        assets_manager.export_cps_image(self.label)
        dcr = assets_manager.load_dcr(self.label)
        return {
            "used": self.used,
            "load_prog": self.load_prog,
            "unknown0": self.unk0,
            "unknown1": self.unk1,
            "label": self.label,
            "sideData": dcr.export() if dcr is not None else None
        }


class Trigger:
    """

    """

    def __init__(self, reader=None):
        """

        :param reader:
        """
        self.location = None
        self.flags = None
        self.offset = None

        self.decode(reader)

        """
        flags:
            A = 0x01,
            B = 0x02,
            C = 0x04,
            OnPartyEnter = 0x08,	# Confirmed
            D = 0x10,
            HoleOrPressure = 0x20,
            F = 0x40,
            G = 0x80,
            H = 0x100,
            I = 0x200,
            K = 0x400,
            OnClick = 0x800,
            M = 0x1000,
            N = 0x2000,
            O = 0x4000,
            P = 0x8000,
                        // item drop
                        // item taken
                        // party enter
                        // party leave
        
        """

    def decode(self, reader):
        """

        :param reader:
        :return:
        """
        if not reader:
            return

        self.location = Location(reader)
        self.flags = reader.read_ushort()
        self.offset = reader.read_ushort()

    def run(self, maze, assets):
        """

        :return:
        """
        return {
            "offset": self.offset,
            "flags": self.flags,
        }

    def __str__(self):
        return "{location}: offset: 0x{offset:04X}, flags: 0x{flags:02X}".format(
            location=self.location, offset=self.offset, flags=self.flags
        )


class Header:
    """

    """

    def __init__(self):
        self.maze_name = None
        self.vmpVcnName = None
        self.paletteName = None
        self.soundName = None
        self.decorations_assets_ref = None
        self.doors = []
        self.monsterGfx = []
        self.monsterTypes = []  # [MonsterType() for i in range(35)]
        self.decorations = []
        self.wall_mappings = []
        self.max_monsters = None
        self.next_hunk = None

    def decode(self):
        dec_asset = None
        if self.decorations_assets_ref is not None:
            dec_asset = assets_manager.export_dec_file(self.decorations_assets_ref)

        assets_manager.export_maze(self.maze_name)

        assets_manager.load_vmp(self.vmpVcnName)
        assets_manager.export_vmp(self.vmpVcnName)

        return {
            "mazeName": self.maze_name,
            "vmpVncName": self.vmpVcnName,
            "palette": self.paletteName,
            "sound": self.soundName,
            "doors": [door.decode() for door in self.doors],
            "monsters": {
                "gfx": [gfx.export() for gfx in self.monsterGfx],
                "types": [monster_type.decode() for monster_type in self.monsterTypes],
            },
            "decorations": {
                "wallMappings": [mapping.export() for mapping in self.wall_mappings],
                "decorationsFile": dec_asset.filename if dec_asset is not None else None
            },
            "maxMonsters": self.max_monsters
        }


class Script:
    """

    """

    def __init__(self, reader=None):
        """

        """
        self.tokens = {}
        self.decompile(reader)

    def decompile(self, reader):
        """

        :return:
        """
        if not reader:
            return

        start = reader.offset

        rel_offset_to_strings = reader.read_ushort()
        length = rel_offset_to_strings

        while reader.offset < start + length:

            # if debug:
            #     print("[0x{:04X}]: ".format(reader.offset - start), end='')
            offset = reader.offset - start
            token = None
            opcode = reader.read_ubyte()
            if opcode == 0xff:
                token = tokens.SetWall(reader)
            elif opcode == 0xfe:
                token = tokens.ChangeWall(reader)
            elif opcode == 0xfd:
                token = tokens.OpenDoor(reader)
            elif opcode == 0xfc:
                token = tokens.CloseDoor(reader)
            elif opcode == 0xfb:
                token = tokens.CreateMonster(reader)
            elif opcode == 0xfa:
                token = tokens.Teleport(reader)
            elif opcode == 0xf9:
                token = tokens.StealSmallItem(reader)
            elif opcode == 0xf8:
                token = tokens.Message(reader)
            elif opcode == 0xf7:
                token = tokens.SetFlag(reader)
            elif opcode == 0xf6:
                token = tokens.Sound(reader)
            elif opcode == 0xf5:
                token = tokens.ClearFlag(reader)
            elif opcode == 0xf4:
                token = tokens.Heal(reader)
            elif opcode == 0xf3:
                token = tokens.Damage(reader)
            elif opcode == 0xf2:
                token = tokens.Jump(reader)
            elif opcode == 0xf1:
                token = tokens.End(reader)
            elif opcode == 0xf0:
                token = tokens.Return(reader)
            elif opcode == 0xef:
                token = tokens.Call(reader)
            elif opcode == 0xee:
                token = tokens.Conditional(reader)
            elif opcode == 0xed:
                token = tokens.ConsumeItem(reader)
            elif opcode == 0xec:
                token = tokens.ChangeLevel(reader)
            elif opcode == 0xeb:
                token = tokens.GiveXP(reader)
            elif opcode == 0xea:
                token = tokens.NewItem(reader)
            elif opcode == 0xe9:
                token = tokens.Launcher(reader)
            elif opcode == 0xe8:
                token = tokens.Turn(reader)
            elif opcode == 0xe7:
                token = tokens.IdentifyAllItems(reader)
            elif opcode == 0xe6:
                token = tokens.Sequence(reader)
            elif opcode == 0xe5:
                token = tokens.Wait(reader)
            elif opcode == 0xe4:
                token = tokens.UpdateScreen(reader)
            elif opcode == 0xe3:
                token = tokens.Dialog(reader)
            elif opcode == 0xe2:
                token = tokens.SpecialEvent(reader)

            if token:
                self.tokens[offset] = token
            else:
                print("###########[ERROR] unknown opcode: 0x{opcode:02X}".format(opcode=opcode))

    def run(self):
        for id, offset in enumerate(self.tokens):
            msg = self.tokens[offset].run()
            print('[0x{offset:04X}] {token}'.format(offset=offset, token=msg))

    def extract(self):
        return {str(hex(offset)): self.tokens[offset].run() for offset in self.tokens}


class Inf:
    """

    """

    def __init__(self, name):

        self.name = name
        self.timers = []
        self.monsters = []
        self.headers = [Header() for i in range(2)]
        self.hunks = [0, 0]
        self.triggers = []
        self.messages = []
        self.script = None

    def process(self, filename):
        """

        :param filename:
        :return:
        """

        # http://grimwiki.net/wiki/EobConverter
        # LEVEL*.MAZ files are stored in PAK files, so you need to extract PAK to extract them first. MAZ files
        # contain dungeon layout (walls, doors, buttons etc.). It does not contain information about items.
        #
        # First 6 bytes constitute a header:
        #
        #     uint16_t width - specifies dungeon width (EOB1 levels always use 32)
        #     uint16_t height - specifies dungeon height (EOB1 levels always use 32)
        #     uint16_t unknown - EOB1 levels seem to have value 0x0004 here. One interpretation is that it may be a
        #                        number of bytes for each grid.
        #
        # Header is followed by width x height grid definitions. Each grid takes 4 bytes. For all EOB1 MAZ levels,
        # that gives 32x32x4 = 4096 bytes. Together with 6 bytes (header), this results in each file having length
        #  of 4102 bytes.
        #
        # Each grid is described by 4 octets. Each character specifies how a given grid looks from W, S, E and N,
        # respectively. It is possible to define inconsistent grids (e.g. look like doors when looked up front, but
        # look like a pressure plate when seen from sides).
        #
        #     0x00 - empty corridor
        #     0x01 - wall (pattern 1)
        #     0x02 - wall (pattern 2)
        #     0x03 - door without a button (closed) opening
        #     0x04 - door opening 1
        #     0x05 - door opening1
        #     0x07 - door opened
        #     0x08 - door with a button (closed)
        #     0x09 - door opening2
        #     0x0a - door opening2
        #     0x0b - door opening2
        #     0x0c - a ladder leading down
        #     0x0d - door with a button (open)
        #     0x11 - door opened
        #     0x12 - door closed
        #     0x13 - door opening4
        #     0x14 - door opening4
        #     0x15 - door opening4
        #     0x16 - door opened
        #     0x17 - up stair/ladder
        #     0x18 - fake ladder leading down (used in inaccessible part of level 1, probably by EOB developers for testing)
        #     0x19 - blocker
        #     0x1a - hole in the ceiling (from upper level)
        #     0x1b - pressure plate
        #     0x1c - pressure plate
        #     0x1d - normal alcove
        #     0x1f - pressure plate
        #     0x20 - switch
        #     0x23 - dalle(inter)
        #     0x24 - dalle(inter)
        #     0x25 - hole (ceilar)
        #     0x26 - hole (floor)
        #     0x27 - hidden button (large pushable brick)
        #     0x2a - hidden switch
        #     0x2b - drainage at the floor level (decoration)
        #     0x2c - "rat hole" - drainage at the floor level with eyes (decoration) or teleport
        #     0x33 - door to force
        #     0x36 - stone portal
        #     0x37 - lever
        #     0x3c - normal button, small brick sized
        #     0x3e - rat hole
        #     0x3f - sewer pipe (in the middle)
        #     0x41 - rune 'entrance'
        #     0x45 - cave-in or stone portal

        inf_filename = filename + '.INF'
        uncps_filename = filename + '.uncps'

        with BinaryReader(filename + '.INF') as reader:

            data = decode_format80(reader)

            with open(uncps_filename, "wb") as handle:
                s = struct.pack('{count}B'.format(count=len(data)), *data)
                handle.write(s)

        with BinaryReader(uncps_filename) as reader:

            # hunk 1
            self.hunks[0] = reader.read_ushort()

            # region Headers
            for header in self.headers:

                if reader.offset < self.hunks[0]:
                    header.next_hunk = reader.read_ushort()
                    b = reader.read_ubyte()
                    if b == 0xEC:
                        header.maze_name = reader.read_string(13)
                        header.vmpVcnName = reader.read_string(13)
                        header.paletteName = header.vmpVcnName.upper() + '.PAL'
                        assets_manager.set_palette(header.paletteName)

                    b = reader.read_ubyte()
                    if b != 0xFF:
                        header.paletteName = reader.read_string(13)
                        assets_manager.set_palette(header.paletteName)

                    header.soundName = reader.read_string(13)

                    # region Door name & Positions + offset
                    for i in range(2):

                        b = reader.read_ubyte()

                        if b in (0xEC, 0xEA):
                            door = DoorInfo()
                            header.doors.append(door)

                            door.gfxFile = reader.read_string(13)

                            door.idx = reader.read_ubyte()
                            door.type = reader.read_ubyte()
                            door.knob = reader.read_ubyte()

                            for rect in door.doorRectangles:
                                rect.x = reader.read_ushort()
                                rect.y = reader.read_ushort()
                                rect.width = reader.read_ushort()
                                rect.height = reader.read_ushort()

                            for rect in door.buttonRectangles:
                                rect.x = reader.read_ushort()
                                rect.y = reader.read_ushort()
                                rect.width = reader.read_ushort()
                                rect.height = reader.read_ushort()

                            for pt in door.buttonPositions:
                                pt.x = reader.read_ushort()
                                pt.y = reader.read_ushort()
                    # endregion

                    # region Monsters graphics information
                    header.max_monsters = reader.read_ushort()
                    for i in range(2):
                        b = reader.read_ubyte()
                        if b == 0xEC:
                            gfx = MonsterGfx()
                            gfx.load_prog = reader.read_ubyte()
                            gfx.unk0 = reader.read_ubyte()
                            gfx.label = reader.read_string(13)
                            gfx.unk1 = reader.read_ubyte()

                            header.monsterGfx.append(gfx)
                    # endregion

                    # region Monster definitions
                    while True:
                        b = reader.read_ubyte()
                        if b == 0xFF:
                            break

                        monster_type = MonsterType()
                        monster_type.index = b
                        monster_type.unk0 = reader.read_ubyte()
                        monster_type.thac0 = reader.read_ubyte()
                        monster_type.unk1 = reader.read_ubyte()

                        monster_type.hp_dice.process(reader)

                        monster_type.number_of_attacks = reader.read_ubyte()
                        for dice in monster_type.attack_dice:
                            dice.process(reader)

                        monster_type.special_attack_flag = reader.read_ushort()
                        monster_type.abilities_flags = reader.read_ushort()
                        monster_type.unk2 = reader.read_ushort()
                        monster_type.exp_gain = reader.read_ushort()
                        monster_type.size = reader.read_ubyte()
                        monster_type.attack_sound = reader.read_ubyte()
                        monster_type.move_sound = reader.read_ubyte()
                        monster_type.unk3 = reader.read_ubyte()

                        b = reader.read_ubyte()
                        if b != 0xFF:
                            monster_type.is_attack2 = True
                            monster_type.distant_attack = reader.read_ubyte()
                            monster_type.max_attack_count = reader.read_ubyte()
                            for i in range(monster_type.max_attack_count):
                                monster_type.attack_list[i] = reader.read_ubyte()
                                reader.read_ubyte()

                        monster_type.turn_undead_value = reader.read_byte()
                        monster_type.unk4 = reader.read_ubyte()
                        monster_type.unk5 = reader.read_ubyte(3)

                        header.monsterTypes.append(monster_type)

                    # endregion

                    # region Wall decorations
                    b = reader.read_ubyte()
                    if b != 0xFF:
                        decorateblocks = reader.read_ushort()
                        for i in range(decorateblocks):
                            b = reader.read_ubyte()
                            if b == 0xEC:
                                gfx_file = reader.read_string(13)
                                dec_file = reader.read_string(13)
                                assets_ref = DecorationAssetsRef(gfx_file, dec_file)
                                header.decorations_assets_ref = assets_ref
                            elif b == 0xFB:
                                wall_mapping = WallMapping()
                                wall_mapping.wall_mapping_index = reader.read_byte()
                                wall_mapping.wall_type = reader.read_ubyte()
                                wall_mapping.decoration_id = reader.read_byte()
                                wall_mapping.event_mask = reader.read_ubyte()
                                wall_mapping.flags = reader.read_ubyte()

                                header.wall_mappings.append(wall_mapping)
                    # endregion

                    # Padding
                    while reader.read_uint() != 0xFFFFFFFF:
                        pass
            # endregion

            self.hunks[1] = reader.read_ushort()

            # region Monsters
            b = reader.read_ubyte()
            if b != 0xFF:
                # Timers
                while reader.read_ubyte() != 0xFF:
                    self.timers.append(reader.read_ubyte())

                # Descriptions
                for i in range(30):
                    monster = Monster()
                    monster.decode(reader)

                    self.monsters.append(monster)

            # endregion

            # Scripts
            self.script = Script(reader)

            # region Messages
            while reader.offset < self.hunks[1]:
                self.messages.append(reader.search_string())

            # endregion

            # region Triggers (special maze blocks)
            trigger_count = reader.read_ushort()
            for i in range(trigger_count):
                trigger = Trigger(reader)
                self.triggers.append(trigger)

            # endregion

    def export(self, assets):
        return {
            "name": self.name,
            "timers": [timer for timer in self.timers],
            "headers": [header.decode() for header in self.headers],
            "hunks": [hunk for hunk in self.hunks],
            "triggers": {trigger.location.coordinates(): trigger.run(self, assets) for trigger in self.triggers},
            "messages": {k: v for k, v in enumerate(self.messages)},
            "scripts": self.script.extract(),
            "monsters": [monster.export() for monster in self.monsters]
        }


def decode_inf():
    # .INF
    files = [
        'LEVEL1',
        # 'LEVEL2',
        # 'LEVEL3',
        # 'LEVEL4',
        # 'LEVEL5',
        # 'LEVEL6',
        # 'LEVEL7',
        # 'LEVEL8',
        # 'LEVEL9',
        # 'LEVEL10',
        # 'LEVEL11',
        # 'LEVEL12',
        # 'LEVEL13',
        # 'LEVEL14',
        # 'LEVEL15',
        # 'LEVEL16',
    ]
    infs = {}

    for file in files:
        inf = Inf(file)
        inf.process('data/{file}'.format(file=file))
        infs[file] = inf

    return infs


def dump(name, data):
    path = './build'
    if not os.path.exists(path):
        os.makedirs(path)

    with open('{path}/{name}'.format(path=path, name=name), 'w') as handle:
        json.dump(data, handle, indent=True, sort_keys=True)


assets = {
    "items": [],
    "item_types": [],
    "item_names": [],
    'text.dat': [],
    'level_items': [],
    'inf': {},
    'maz': {},
    'pal': {},
    'vmp': {},
    'vcn': {},
    'dec': {}
}

if __name__ == '__main__':
    assets_manager.export_texts()

    assets_manager.export_item_types()
    assets_manager.export_items()

    # INF
    assets['inf'] = decode_inf()
    dump('inf.json', [inf.export(assets) for inf in assets['inf'].values()])

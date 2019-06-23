import json
import os.path
import time

from PIL import Image

import gfx
from binary_reader import BinaryReader, BinaryArrayData
from compression import decode_format80
from entities import Dice
from flags import *

BLOCKS_ROWS = 15
BLOCKS_COLUMNS = 22
BLOCKS_SIZE = 8

VMP_EXTENSION = '.VMP'

DCR_EXTENSION = '.DCR'

CPS_EXTENSION = ".CPS"

PAL_EXTENSION = ".PAL"

MAZ_EXTENSION = '.MAZ'


class ImageAsset:

    def __init__(self, id, filename, full_path, exported_on=time.time()):
        self.id = id
        self.filename = filename
        self.exported_on = exported_on
        self.full_path = full_path
        self.original_asset = None


class ShapeRect:
    def __init__(self, x=0, y=0, w=0, h=0):
        self.x = x
        self.y = y
        self.w = w
        self.h = h

    def x(self):
        return self.x

    def y(self):
        return self.y

    def width(self):
        return self.w

    def height(self):
        return self.h

    def export(self):
        return {
            'x': self.x,
            'y': self.y,
            'w': self.w,
            'h': self.h
        }


class DecorationsAsset:

    def __init__(self, filename=None, image_filename=None):
        self.filename = filename
        self.image_filename = image_filename
        self.decorations = []
        self.rectangles = []

        # should be of type DecorationAssetsRef
        self.original_assets = None

    def append_decoration(self, dec):
        self.decorations.append(dec)

    def get_decoration(self, i):
        return self.decorations[i]

    def append_rectangle(self, shape):
        self.rectangles.append(shape)

    def get_rectangle(self, i):
        return self.rectangles[i]

    def export(self):
        return {
            "filename": self.filename,
            "image": self.image_filename,
            "decorations": [dec.export() for dec in self.decorations],
            "rectangles": [rect.export() for rect in self.rectangles],
            "originalAssets": self.original_assets.export()
        }


class Decoration:
    def __init__(self):
        self.rectangle_indices = []
        self.x_coords = []
        self.y_coords = []
        self.flags = 0
        self.next_decoration_index = -1

    def export(self):
        return {
            "rectanglesIndices": self.rectangle_indices,
            "xCoords": self.x_coords,
            "yCoords": self.y_coords,
            "flags": self.flags,
            "nextIndex": self.next_decoration_index
        }


class DecorationAssetsRef:
    """
    """

    def __init__(self, gfx_file, dec_file):
        self.gfx = gfx_file
        self.dec = dec_file

    def get_gfx_file(self):
        return self.gfx

    def get_dec_file(self):
        return self.dec

    def __str__(self):
        return 'gfx: {gfx}.cps - dec:{dec}'.format(gfx=self.gfx, dec=self.dec)

    def export(self):
        return {
            "gfx": self.gfx,
            "dec": self.dec
        }


class Maze:
    def __init__(self, name, width=0, height=0, faces=0, walls=[]):
        self.name = name
        self.width = width
        self.height = height
        self.faces = faces
        self.walls = walls

    def get_wall(self, x, y):
        return self.walls[y * self.width + x]

    def get_width(self):
        return self.width

    def get_height(self):
        return self.height


class DcrAsset:
    class SideData:
        def __init__(self):
            self.cps_x = -1
            self.cps_y = -1
            self.width = 0
            self.height = 0
            self.screen_x = 0
            self.screen_y = 0

        def export(self):
            return {
                "cpsX": self.cps_x,
                "cpsY": self.cps_y,
                "width": self.width,
                "height": self.height,
                "screenX": self.screen_x,
                "screenY": self.screen_y
            }

    def __init__(self, filename):
        self.filename = filename
        self.sides = {}

    def export(self):
        return {
            "filename": self.filename,
            "sides": [side.export() for side in self.sides]
        }


class VmpAsset:
    class TilesInfo:
        def __init__(self):
            self.gfx = None
            self.flipped_tiles = []

        def export(self):
            return {
                'gfx': self.gfx,
                'flipped': self.flipped_tiles
            }

    def __init__(self):
        self.name = None
        self.bg_tiles = None
        self.wall_tiles = None
        self.bg_palette = []
        self.wall_palette = []
        self.blocks = None
        self.exported = False
        self.bg_tiles_info = None
        self.wall_tiles_infos = []

    def export(self):
        return {
            'background': self.bg_tiles_info.export(),
            'wallTiles': [t.export() for t in self.wall_tiles_infos]
        }


class AssetsManager:
    DATA_DIR = "data/"
    BUILD_DIR = "build/"

    def __init__(self, data_dir=DATA_DIR, build_dir=BUILD_DIR):
        self.images = {}
        self.decorations = {}
        self.texts = []
        self.mazes = {}
        self.vmps = {}

        self.id_gen = 0
        self.data_dir = data_dir
        # if not self.data_dir.endswith("/"): self.data_dir += "/"

        self.build_dir = build_dir
        # if not self.build_dir.endswith("/"): self.build_dir += "/"

        self.palette_filename = None
        self.palette = None

    def set_palette(self, palette_filename):
        palette_filename = os.path.join(self.data_dir, palette_filename.upper())

        if not palette_filename.endswith(PAL_EXTENSION): palette_filename += PAL_EXTENSION
        self.palette_filename = palette_filename
        self.palette = gfx.load_palette(self.palette_filename)

    def export_cps_image(self, cps_filename):

        if cps_filename in self.images:
            return

        rel_cps_filename = os.path.join(self.data_dir, cps_filename.upper())
        if not rel_cps_filename.endswith(CPS_EXTENSION): rel_cps_filename += CPS_EXTENSION

        img = gfx.load_cps(rel_cps_filename, self.palette)
        image_asset = self._export_image(img, cps_filename)
        image_asset.original_asset = rel_cps_filename

        return image_asset

    def export_dec_file(self, dec_assets_ref):

        dec_key = str(dec_assets_ref)
        if dec_key in self.decorations:
            return

        dec_asset = DecorationsAsset()
        dec_asset.original_assets = dec_assets_ref

        self.decorations[dec_key] = dec_asset

        with BinaryReader('data/{file}'.format(file=dec_assets_ref.get_dec_file())) as reader:
            count = reader.read_ushort()

            for i in range(count):
                deco = Decoration()
                deco.rectangle_indices = [-1 if value == 255 else value for value in reader.read_ubyte(10)]
                deco.next_decoration_index = reader.read_byte()
                deco.flags = reader.read_byte()
                deco.x_coords = reader.read_short(10)
                deco.y_coords = reader.read_short(10)

                dec_asset.append_decoration(deco)

            count = reader.read_ushort()
            for i in range(count):
                rect = list(reader.read_ushort(4))
                rect[0] *= 8
                rect[2] *= 8
                dec_asset.append_rectangle(ShapeRect(*rect))

        dec_exported_filename = os.path.join(self.build_dir, dec_assets_ref.get_dec_file())
        image_asset = self.export_cps_image(dec_assets_ref.get_gfx_file())

        dec_asset.filename = dec_exported_filename
        dec_asset.image_filename = image_asset.filename

        with open(dec_exported_filename, 'w') as handle:
            json.dump(dec_asset.export(), handle, indent=True, sort_keys=False)

        return dec_asset

    def export_texts(self):
        file = os.path.join(self.data_dir, 'TEXT.DAT')
        offsets = []
        with BinaryReader(file) as reader:
            while True:
                offset = reader.read_ushort()
                offsets.append(offset)
                if reader.offset >= offsets[0]:
                    break

            for id, offset in enumerate(offsets):

                if id == len(offsets) - 1:
                    length = os.path.getsize(file) - offsets[id]
                else:
                    length = offsets[id + 1] - offsets[id]

                self.texts.append(reader.read_string(length))

        with open(os.path.join(self.build_dir, 'texts.json'), 'w') as handle:
            json.dump(self.texts, handle, indent=True, sort_keys=False)

        return self.texts

    def export_maze(self, maze_name):
        maze_filename = maze_name.upper()
        if not maze_filename.endswith(MAZ_EXTENSION):
            maze_filename += MAZ_EXTENSION

        with BinaryReader(os.path.join(self.data_dir, maze_filename)) as reader:

            width = reader.read_ushort()
            height = reader.read_ushort()
            faces = reader.read_ushort()

            walls = [[None for _ in range(height)] for _ in range(width)]

            for y in range(height):
                for x in range(width):
                    n = reader.read_ubyte()
                    s = reader.read_ubyte()
                    w = reader.read_ubyte()
                    e = reader.read_ubyte()

                    walls[x][y] = {
                        'x': x,
                        'y': y,
                        'n': n,
                        's': s,
                        'w': w,
                        'e': e,
                    }

            maze = Maze(maze_name, width, height, faces, walls)
            self.mazes[maze_name] = maze

        with open(os.path.join(self.build_dir, maze_name), 'w') as handle:
            json.dump(maze.__dict__, handle, indent=True, sort_keys=False)

    def load_dcr(self, name=''):

        filename = name.upper()
        if not filename.endswith(DCR_EXTENSION):
            filename += DCR_EXTENSION

        rel_filename = os.path.join(self.data_dir, filename)
        if not os.path.exists(rel_filename):
            return None

        with BinaryReader(rel_filename) as reader:
            count = reader.read_ushort()
            for i in range(count):
                dcr_asset = DcrAsset(name)

                sides = []
                for j in range(6):
                    side = DcrAsset.SideData()
                    side.cps_x = reader.read_ubyte() * 8
                    side.cps_y = reader.read_ubyte()
                    side.width = reader.read_ubyte() * 8
                    side.height = reader.read_ubyte()
                    side.screen_x = reader.read_ubyte()
                    side.screen_y = reader.read_ubyte()

                    sides.append(side)

                dcr_asset.sides = sides

        return dcr_asset

    def get_decorations(self, dec_assets_ref):
        return self.decorations[str(dec_assets_ref)]

    def get_image(self, cps_filename):
        return self.images[cps_filename]

    def get_text(self, i):
        return self.texts[i]

    def get_maze(self, maze_name):
        return self.mazes[maze_name]

    def export_items(self):
        items = []  # ITEM.DAT
        items_names = []

        with BinaryReader('data/ITEM.DAT') as reader:
            count = reader.read_ushort()
            for i in range(count):
                item = {
                    'unidentified_name': reader.read_ubyte(),
                    'identified_name': reader.read_ubyte(),
                    'flags': reader.read_ubyte(),
                    'picture': reader.read_ubyte(),
                    'type': reader.read_ubyte(),  # See types below

                    # Where the item lies at position
                    # In Maze:
                    #      0..3-> Bottom
                    #      4..7-> Wall (N,E,S,W)
                    # For EotB I: 0..3-> Floor NW,NE,SW,SE
                    #                8-> Compartment
                    # If in inventory:
                    #      0..26-> Position in Inventory
                    'sub_position': reader.read_ubyte(),

                    # Position in maze x + y * 32, consumed if <= 0
                    'coordinate': reader.read_ushort(),
                    'next': reader.read_ushort(),
                    'previous': reader.read_ushort(),

                    # Level, where the item lies, 0 <= no level
                    'level': reader.read_ubyte(),

                    # The value of item, -1 if consumed
                    'value': reader.read_byte(),
                }
                pos = divmod(item['coordinate'], 32)
                item['coordinate'] = {'x': pos[1], 'y': pos[0]}
                items.append(item)

            count = reader.read_ushort()
            for i in range(count):
                name = reader.read_string(35)
                items_names.append(name)

            for item in items:
                item['unidentified_name'] = items_names[item['unidentified_name']]
                item['identified_name'] = items_names[item['identified_name']]

            with open(os.path.join(self.build_dir, 'items.json'), 'w') as handle:
                json.dump(items, handle, indent=True, sort_keys=False)

    def export_item_types(self):
        item_types = []
        with BinaryReader(os.path.join(self.data_dir, 'ITEMTYPE.DAT')) as reader:
            count = reader.read_ushort()
            for i in range(count):
                item_type = {
                    # At which position in inventory it is allowed to be put. See InventoryUsage
                    'slots': str(ItemSlotFlags(reader.read_ushort())),
                    'flags': str(ItemFlags(reader.read_ushort())),
                    'armor_class': reader.read_byte(),  # Adds to armor class
                    'allowed_classes': str(ProfessionFlags(reader.read_ubyte())),
                    # Allowed for this profession. See ClassUsage
                    'allowed_hands': str(HandFlags(reader.read_ubyte())),  # Allowed for this hand
                    'damage_vs_small': str(Dice(reader)),
                    'damage_vs_big': str(Dice(reader)),
                    # 'damage_incs': reader.read_ubyte(),
                    'unknown': reader.read_ubyte(),
                    'usage': str(ItemTypeUsage(reader.read_ushort())),
                }

                item_types.append(item_type)

        with open(os.path.join(self.build_dir, 'item_types.json'), 'w') as handle:
            json.dump(item_types, handle, indent=True, sort_keys=False)

    def load_vmp(self, vmp_name=''):

        if vmp_name in self.vmps:
            return self.vmps[vmp_name]

        vmp_filename = vmp_name.upper()
        if not vmp_filename.endswith(VMP_EXTENSION):
            vmp_filename += VMP_EXTENSION

        vmp_filename = os.path.join(self.data_dir, vmp_filename)
        if not os.path.exists(vmp_filename):
            raise Exception('Cannot find VMP file %s' % vmp_filename)

        vcn_filename = os.path.join(self.data_dir, vmp_name.upper() + '.VCN')
        if not os.path.exists(vcn_filename):
            raise Exception('Cannot find the corresponding VCN file %s' % vcn_filename)

        with BinaryReader(vmp_filename) as reader:
            shorts_per_tileset = 431
            file_size = 2 * reader.read_ushort()
            num_wall_types = int(file_size / (2 * shorts_per_tileset)) - 1
            bg_tiles = reader.read_ushort(22 * 15)
            _ = reader.read_ushort(101)

            tiles = []
            for _ in range(num_wall_types):
                wall_tiles = reader.read_ushort(shorts_per_tileset)
                tiles.append(wall_tiles)

        with BinaryReader(vcn_filename) as vcn_reader:
            vcn_data = decode_format80(vcn_reader)

        vcn_reader = BinaryArrayData(vcn_data)

        num_blocks = vcn_reader.read_ushort()
        bg_palette_indices = vcn_reader.read_ubyte(16)
        bg_palette = []
        for i in range(16):
            bg_palette.append(self.palette[3 * bg_palette_indices[i]])
            bg_palette.append(self.palette[3 * bg_palette_indices[i] + 1])
            bg_palette.append(self.palette[3 * bg_palette_indices[i] + 2])

        walls_palette_indices = vcn_reader.read_ubyte(16)
        walls_palette = []
        for i in range(16):
            walls_palette.append(self.palette[3 * walls_palette_indices[i]])
            walls_palette.append(self.palette[3 * walls_palette_indices[i] + 1])
            walls_palette.append(self.palette[3 * walls_palette_indices[i] + 2])

        blocks = []
        for _ in range(num_blocks):
            raw = vcn_reader.read_byte(32)
            blocks.append(raw)

        vmp_asset = VmpAsset()
        vmp_asset.name = vmp_name
        vmp_asset.bg_palette = bg_palette
        vmp_asset.wall_palette = walls_palette
        vmp_asset.bg_tiles = bg_tiles
        vmp_asset.wall_tiles = tiles
        vmp_asset.blocks = blocks

        self.vmps[vmp_name] = vmp_asset

        return vmp_asset

    def _export_image(self, pil_img, filename):
        exported_filename = os.path.join(self.build_dir, "%s.png" % filename.lower())
        pil_img.convert('RGB').save(exported_filename)

        image_asset = ImageAsset(self.id_gen, exported_filename, full_path=os.path.abspath(exported_filename))

        self.images[filename] = image_asset
        self.id_gen += 1
        return image_asset

    def export_vmp(self, vmp_name):
        if vmp_name not in self.vmps:
            raise Exception("You must first load the VMP " + vmp_name)

        vmp = self.vmps[vmp_name]
        if vmp.exported:
            return

        vmp.exported = True

        num_wall_types = len(vmp.wall_tiles)

        for i in range(num_wall_types):
            flipped_tiles = []
            img = self._create_tileset_image(vmp.wall_palette, vmp.wall_tiles[i], vmp.blocks, flipped_tiles)
            gfx_filename = '%s_tiles_%d' % (vmp_name, i)
            self._export_image(img, gfx_filename)

            tiles_info = VmpAsset.TilesInfo()
            tiles_info.flipped_tiles = flipped_tiles
            tiles_info.gfx = gfx_filename

            vmp.wall_tiles_infos.append(tiles_info)

        flipped_tiles = []
        img = self._create_tileset_image(vmp.bg_palette, vmp.bg_tiles, vmp.blocks, flipped_tiles)
        bg_image_filename = '%s_tiles_bg' % vmp_name
        self._export_image(img, bg_image_filename)

        tiles_info = VmpAsset.TilesInfo()
        tiles_info.flipped_tiles = flipped_tiles
        tiles_info.gfx = bg_image_filename
        vmp.bg_tiles_info = tiles_info

        vmp_filename = '%s.vmp.json' % vmp_name
        with open(os.path.join(self.build_dir, vmp_filename), 'w') as handle:
            json.dump(vmp.export(), handle, indent=True, sort_keys=False)

        return vmp

    def _create_tileset_image(self, palette, tileset, block_data, flipped_tiles):
        img = Image.new('P', (BLOCKS_COLUMNS * BLOCKS_SIZE, BLOCKS_ROWS * BLOCKS_SIZE))
        img.putpalette(palette)

        img_data = [255 for _ in range(BLOCKS_COLUMNS * BLOCKS_SIZE * BLOCKS_ROWS * BLOCKS_SIZE)]
        PIX_PER_BLOCK_ROW = BLOCKS_COLUMNS * BLOCKS_SIZE * BLOCKS_SIZE
        PIX_PER_ROW = BLOCKS_COLUMNS * BLOCKS_SIZE

        for block_y in range(BLOCKS_ROWS):
            for block_x in range(BLOCKS_COLUMNS):

                tile_index = block_y * BLOCKS_COLUMNS + block_x
                tile = tileset[tile_index]
                flip = (tile & 0x04000) == 0x04000

                if flip:
                    print('flip block %d,%d' % (block_x, block_y))
                    flipped_tiles.append(tile_index)

                block_index = tile & 0x3fff

                block = block_data[block_index]

                for y in range(8):
                    for x in range(4):
                        word = block[x + y * 4]
                        col1 = word >> 4
                        col2 = word & 0x0f
                        img_coords = block_y * PIX_PER_BLOCK_ROW + block_x * BLOCKS_SIZE + y * PIX_PER_ROW + 2 * x
                        img_data[img_coords] = col1
                        img_data[img_coords + 1] = col2
                        # img_data.append(col1)
                        # img_data.append(col2)

        img.putdata(img_data)
        return img

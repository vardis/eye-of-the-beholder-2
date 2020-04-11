import json
import os.path
import time

from PIL import Image

import gfx
from binary_reader import BinaryReader, BinaryArrayData
from compression import decode_format80
from entities import Dice
from flags import *
import math

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


class VcnAsset:
    kBlocksPerRow = 32

    def __init__(self):
        self.name = None
        self.blocks = []
        self.bg_palette = None
        self.walls_palette = None
        self.exported = False

    def make_image(self, palette):
        num_blocks = len(self.blocks)
        width_blocks = 32
        height_blocks = math.ceil(num_blocks / 32)

        img_width = width_blocks * BLOCKS_SIZE
        img_height = height_blocks * BLOCKS_SIZE

        img = Image.new('P', (img_width, img_height))
        img.putpalette(palette)

        img_data = [0 for _ in range(img_width * img_height)]

        for i in range(num_blocks):
            block = self.blocks[i]
            block_x = i % width_blocks
            block_y = i // width_blocks
            blit_block(img_data, img_width, block_x * BLOCKS_SIZE, block_y * BLOCKS_SIZE, block, False)

        img.putdata(img_data)
        return img

    def export(self, output_dir):
        if self.exported:
            return

        self.exported = True

        bg_img = self.make_image(self.bg_palette)
        filename = f'vcn_{self.name}_bg.png'
        bg_filename = os.path.join(output_dir, filename.lower())
        bg_img.convert('RGB').save(bg_filename)

        walls_img = self.make_image(self.walls_palette)
        filename = f'vcn_{self.name}_walls.png'
        walls_filename = os.path.join(output_dir, filename.lower())
        walls_img.convert('RGB').save(walls_filename)

        data = {
            "name": self.name,
            "bgPalette": self.bg_palette,
            "wallsPalette": self.walls_palette,
            "blocks": self.blocks,
            "bgGfx": bg_filename,
            "wallsGfx": walls_filename
        }

        vcn_filename = f'{self.name}.vcn.json'
        with open(os.path.join(output_dir, vcn_filename), 'w') as handle:
            json.dump(data, handle, indent=True, sort_keys=False)

    @staticmethod
    def load(basename, vcn_filename, level_palette):
        with BinaryReader(vcn_filename) as vcn_reader:
            vcn_data = decode_format80(vcn_reader)

        vcn_reader = BinaryArrayData(vcn_data)

        num_blocks = vcn_reader.read_ushort()

        bg_palette_indices = vcn_reader.read_ubyte(16)
        walls_palette_indices = vcn_reader.read_ubyte(16)

        bg_palette = 48 * [0]
        walls_palette = 48 * [0]

        for i in range(16):
            bg_palette[3*i] = level_palette[3*bg_palette_indices[i]]
            bg_palette[3*i + 1] = level_palette[3*bg_palette_indices[i] + 1]
            bg_palette[3*i + 2] = level_palette[3*bg_palette_indices[i] + 2]

            walls_palette[3*i] = level_palette[3*walls_palette_indices[i]]
            walls_palette[3*i + 1] = level_palette[3*walls_palette_indices[i] + 1]
            walls_palette[3*i + 2] = level_palette[3*walls_palette_indices[i] + 2]

        blocks = []
        for _ in range(num_blocks):
            raw = vcn_reader.read_ubyte(32)
            blocks.append(raw)

        vcn = VcnAsset()
        vcn.name = basename
        vcn.blocks = blocks
        vcn.bg_palette = bg_palette
        vcn.walls_palette = walls_palette

        return vcn


"""

    def export_image(self, palette):
        num_blocks = len(self.blocks)
        img_width = VcnAsset.kBlocksPerRow * BLOCKS_SIZE
        img_height = math.ceil((num_blocks * 64) // img_width)

        img = Image.new('P', (img_width, img_height))
        img.putpalette(self.bg_palette)

        img_data = [255 for _ in range(img_width * img_height)]

        pix_per_block_row = img_width * BLOCKS_SIZE

        for i in range(len(self.blocks)):
            block = self.blocks[i]

            block_x = i % VcnAsset.kBlocksPerRow
            block_y = i // VcnAsset.kBlocksPerRow

            for y in range(8):
                for x in range(4):
                    word = block[x + y * 4]
                    col1 = (word & 0xf0) >> 4
                    col2 = word & 0x0f
                    img_coords = block_y * pix_per_block_row + block_x * BLOCKS_SIZE + y * img_width + 2 * x
                    img_data[img_coords] = col1
                    img_data[img_coords + 1] = col2

        img.putdata(img_data)
"""


class VmpAsset:
    class TilesInfo:
        def __init__(self):
            self.wall_type = None
            self.tiles = []

        def export(self):
            return {
                'wallType': self.wall_type,
                'tiles': [t.export() for t in self.tiles],
            }

    class Tile:
        def __init__(self, vcn_block, flipped):
            self.flipped = flipped
            self.vcn_block = vcn_block

        def export(self):
            return {
                'vcn_block': self.vcn_block,
                'flipped': self.flipped
            }

    def __init__(self):
        self.name = None
        self.bg_tiles = None
        self.wall_tiles = None
        self.exported = False
        self.vcn = None

    @staticmethod
    def load(basename, vmp_filename, vcn_filename, level_palette):
        with BinaryReader(vmp_filename) as reader:
            shorts_per_tileset = 431
            file_size = reader.read_ushort()
            num_wall_types = int(file_size / shorts_per_tileset) - 1

            # one short per block
            bg_tiles = reader.read_ushort(BLOCKS_COLUMNS * BLOCKS_ROWS)

            # padding
            wall_tiles = reader.read_ushort(101 + num_wall_types*shorts_per_tileset)

        vcn = VcnAsset.load(basename, vcn_filename, level_palette)
        vmp_asset = VmpAsset()
        vmp_asset.vcn = vcn
        vmp_asset.name = basename
        vmp_asset.bg_tiles = bg_tiles
        vmp_asset.wall_tiles = wall_tiles
        return vmp_asset

    def export(self, output_dir):

        if self.exported:
            return

        self.vcn.export(output_dir)

        wall_tiles_infos = self._export_vmp_blocks(self.wall_tiles)
        bg_tiles = self._export_vmp_blocks(self.bg_tiles)

        data = {
            'name': self.name,
            'bgTiles': [t.export() for t in bg_tiles],
            'wallTiles': [t.export() for t in wall_tiles_infos]
        }

        vmp_filename = '%s.vmp.json' % self.name
        with open(os.path.join(output_dir, vmp_filename), 'w') as handle:
            json.dump(data, handle, indent=True, sort_keys=False)

        self.exported = True

    @staticmethod
    def _export_vmp_blocks(tileset):
        exported_blocks = []
        for tile_index in range(len(tileset)):
            tile = tileset[tile_index]
            flip = (tile & 0x04000) == 0x04000
            vcn_block_index = tile & 0x3fff

            exported_blocks.append(VmpAsset.Tile(vcn_block_index, flip))

        return exported_blocks


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
        self.build_dir = build_dir
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
        image_asset = self._export_image(img, cps_filename + '.png')
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
                    e = reader.read_ubyte()
                    s = reader.read_ubyte()
                    w = reader.read_ubyte()

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

        vcn_filename = vmp_name.upper() + '.VCN'
        vcn_filename = os.path.join(self.data_dir, vcn_filename)
        if not os.path.exists(vcn_filename):
            raise Exception('Cannot find the VCN file %s' % vcn_filename)

        vmp_asset = VmpAsset.load(vmp_name, vmp_filename, vcn_filename, self.palette)
        self.vmps[vmp_name] = vmp_asset

        return vmp_asset

    def export_vmp(self, vmp_name):
        if vmp_name not in self.vmps:
            vmp = self.load_vmp(vmp_name)
        else:
            vmp = self.vmps[vmp_name]
            if vmp.exported:
                return vmp

        vmp.export(self.build_dir)
        vmp.exported = True
        return vmp

    """
    def export_walls(self, wall_type, vmp):
        img_width = 24 * BLOCKS_SIZE
        img_height = 18 * BLOCKS_SIZE

        img = Image.new('P', (img_width, img_height))
        img.putpalette(vmp.vcn.walls_palette)

        img_data = [255 for _ in range(img_width * img_height)]

        for wall_pos in [22]:
            cfg = walls_render_config[wall_pos]
            offset = cfg.base_offset

            for y in range(cfg.blk_height):

                for x in range(2,4):#cfg.blk_width):

                    if cfg.flip:
                        block_index = cfg.view_offset + cfg.blk_width - (x + 1) + y * BLOCKS_COLUMNS
                    else:
                        block_index = x + y * BLOCKS_COLUMNS + cfg.view_offset

                    block_x = block_index % BLOCKS_COLUMNS
                    block_y = block_index // BLOCKS_COLUMNS

                    tile = vmp.wall_tiles_infos[wall_type].tiles[offset]
                    flip = tile.flipped ^ cfg.flip
                    block = vmp.vcn.blocks[tile.vcn_block]

                    self.blit_block(img_data, img_width, block_x * BLOCKS_SIZE, block_y * BLOCKS_SIZE, block, flip)

                    offset += 1

                offset += cfg.skip

        img.putdata(img_data)
        self._export_image(img, f'walls_{vmp.name}_{wall_type}.png')


    """

    @staticmethod
    def _export_vmp_blocks(tileset, num_tiles):
        exported_blocks = []
        for tile_index in range(num_tiles):
            tile = tileset[tile_index]
            flip = (tile & 0x04000) == 0x04000
            vcn_block_index = tile & 0x3fff

            exported_blocks.append(VmpAsset.Tile(vcn_block_index, flip))

        return exported_blocks

    def _export_image(self, pil_img, filename):
        exported_filename = os.path.join(self.build_dir, filename.lower())
        pil_img.convert('RGB').save(exported_filename)

        image_asset = ImageAsset(self.id_gen, exported_filename, full_path=os.path.abspath(exported_filename))

        self.images[filename] = image_asset
        self.id_gen += 1
        return image_asset


def blit_block(image_data, img_width, x, y, vcn_block, flip):
    s = -1 if flip else 1
    p = 7 if flip else 0

    for w in range(8):
        for v in range(4):
            word = vcn_block[v + w * 4]
            col1 = (word & 0xf0) >> 4
            col2 = word & 0x0f
            coords = x + p + s * 2 * v + (y + w) * img_width
            image_data[coords] = col1
            image_data[coords + s] = col2

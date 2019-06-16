import gfx
import os.path
import time
import json
from binary_reader import BinaryReader

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
            "originalAssets" : self.original_assets.export()
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


class AssetsManager:
    DATA_DIR = "data/"
    BUILD_DIR = "build/"

    def __init__(self, data_dir=DATA_DIR, build_dir=BUILD_DIR):
        self.images = {}
        self.decorations = {}
        self.texts = []
        self.mazes = {}

        self.id_gen = 0
        self.data_dir = data_dir
        # if not self.data_dir.endswith("/"): self.data_dir += "/"

        self.build_dir = build_dir
        # if not self.build_dir.endswith("/"): self.build_dir += "/"

        self.palette_filename = None

    def set_palette(self, palette_filename):
        palette_filename = os.path.join(self.data_dir, palette_filename.upper())

        if not palette_filename.endswith(PAL_EXTENSION): palette_filename += PAL_EXTENSION
        self.palette_filename = palette_filename

    def export_cps_image(self, cps_filename):

        if cps_filename in self.images:
            return

        rel_cps_filename = os.path.join(self.data_dir, cps_filename.upper())
        if not rel_cps_filename.endswith(CPS_EXTENSION): rel_cps_filename += CPS_EXTENSION

        img = gfx.load_cps(rel_cps_filename, self.palette_filename)
        exported_filename = os.path.join(self.build_dir, "%s.png" % cps_filename.lower())
        img.save(exported_filename)

        image_asset = ImageAsset(self.id_gen, exported_filename, full_path=os.path.abspath(exported_filename))
        image_asset.original_asset = rel_cps_filename

        self.images[cps_filename] = image_asset
        self.id_gen += 1

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

    def get_decorations(self, dec_assets_ref):
        return self.decorations[str(dec_assets_ref)]

    def get_image(self, cps_filename):
        return self.images[cps_filename]

    def get_text(self, i):
        return self.texts[i]

    def get_maze(self, maze_name):
        return self.mazes[maze_name]

import gfx
import os.path
import time
from binary_reader import BinaryReader


class ImageAsset:

    def __init__(self, id, filename, full_path, exported_on=time.time()):
        self.id = id
        self.filename = filename
        self.exported_on = exported_on
        self.full_path = full_path


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


class Decoration:

    def __init__(self):
        self.decorations = []
        self.shapes = []

    def append_decoration(self, dec):
        self.decorations.append(dec)

    def get_decoration(self, i):
        return self.decorations[i]

    def append_shape(self, shape):
        self.shapes.append(shape)

    def get_shape(self, i):
        return self.shapes[i]


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


class AssetsManager:
    DATA_DIR = "data/"
    BUILD_DIR = "build/"

    def __init__(self, data_dir=DATA_DIR, build_dir=BUILD_DIR):
        self.images = {}
        self.decorations = {}
        self.id_gen = 0
        self.data_dir = data_dir
        # if not self.data_dir.endswith("/"): self.data_dir += "/"

        self.build_dir = build_dir
        # if not self.build_dir.endswith("/"): self.build_dir += "/"

        self.palette_filename = None

    def set_palette(self, palette_filename):
        palette_filename = os.path.join(self.data_dir, palette_filename.upper())

        if not palette_filename.endswith(".PAL"): palette_filename += ".PAL"
        self.palette_filename = palette_filename

    def export_cps_image(self, cps_filename):

        if cps_filename in self.images:
            return

        rel_cps_filename = os.path.join(self.data_dir, cps_filename.upper())
        if not rel_cps_filename.endswith(".CPS"): rel_cps_filename += ".CPS"

        img = gfx.load_cps(rel_cps_filename, self.palette_filename)
        img.save(os.path.join(self.build_dir, "%s.png" % cps_filename.lower()))

        self.images[cps_filename] = ImageAsset(self.id_gen, rel_cps_filename,
                                               full_path=os.path.abspath(rel_cps_filename))
        self.id_gen += 1

    def export_dec_file(self, dec_assets_ref):

        dec_key = str(dec_assets_ref)
        if dec_key in self.decorations:
            return

        dec_asset = Decoration()
        self.decorations[dec_key] = dec_asset

        with BinaryReader('data/{file}'.format(file=dec_assets_ref.get_dec_file())) as reader:
            count = reader.read_ushort()

            for i in range(count):
                deco = {
                    'shapes': [-1 if value == 255 else value for value in reader.read_ubyte(10)],
                    'next': reader.read_byte(),
                    'flags': reader.read_byte(),  # horizontal/vertical flip ?
                    'shape_x': reader.read_short(10),
                    'shape_y': reader.read_short(10),
                }
                dec_asset.append_decoration(deco)

            count = reader.read_ushort()
            for i in range(count):
                rect = list(reader.read_ushort(4))
                rect[0] *= 8
                rect[2] *= 8
                dec_asset.append_shape(ShapeRect(*rect))

        self.export_cps_image(dec_assets_ref.get_gfx_file())

    def get_decorations(self, dec_assets_ref):
        return self.decorations[str(dec_assets_ref)]

    def get_image(self, cps_filename):
        return self.images[cps_filename]
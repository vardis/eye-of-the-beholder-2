import gfx
import os.path
import time

class ImageAsset:

    def __init__(self, id, filename, full_path, exported_on=time.time()):
        self.id = id
        self.filename = filename
        self.exported_on = exported_on
        self.full_path = full_path

class AssetsManager:
    DATA_DIR = "data/"
    BUILD_DIR = "build/"

    def __init__(self, data_dir=DATA_DIR, build_dir=BUILD_DIR):
        self.assets = {}
        self.id_gen = 0
        self.data_dir = data_dir
        # if not self.data_dir.endswith("/"): self.data_dir += "/"

        self.build_dir = build_dir
        # if not self.build_dir.endswith("/"): self.build_dir += "/"

    def export_cps_image(self, cps_filename, palette_filename):

        rel_cps_filename = os.path.join(self.data_dir, cps_filename.upper())
        if not rel_cps_filename.endswith(".CPS"): rel_cps_filename += ".CPS"

        rel_palette_filename = os.path.join(self.data_dir, palette_filename.upper())
        if not rel_palette_filename.endswith(".PAL"): rel_palette_filename += ".PAL"

        img = gfx.load_cps(rel_cps_filename, rel_palette_filename)
        img.save(os.path.join(self.build_dir, "%s.png" % cps_filename.lower()))

        self.assets[cps_filename] = ImageAsset(self.id_gen, rel_cps_filename, full_path=os.path.abspath(rel_cps_filename))
        self.id_gen += 1

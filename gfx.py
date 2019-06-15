import os
import struct
import json
from PIL import Image, ImageDraw
from binary_reader import BinaryReader
from compression import decode_format80


def load_cps(cps_filename, pal_filename):
    with BinaryReader(cps_filename) as reader:
        cps_data = decode_format80(reader)

        if pal_filename is not None:
            pal = load_palette(pal_filename)
            # with open(cps_filename, 'rb') as fcps:
            #     compressed_data = fcps.read()[10:]

            # create an new image in palette mode and fill it
            img = Image.new('P', (320, 200))
            img.putpalette(pal)
        else:
            img = Image.new('RGB', (320, 200))

        img.putdata(cps_data)

        return img


def load_palette(pal_filename):
    """
    A palette file contains 256 color, each color is represented by 3 bytes. So the expected
    total file size is 768 (0x300) bytes.

    Also the palette colors are stored in 6bit format. To convert them to 8-bit colors:

    eight_bit_value = (six_bit_value * 255) / 63

    """

    pal_data = []
    # with BinaryReader(pal_filename) as reader:
    #     col6 = reader.read_ubyte()
    #     col = (col6 * 255) / 63
    #     pal_data.append(col)

    with open(pal_filename, 'rb') as fpal:
        pal_data_6 = fpal.read()
        for col6 in pal_data_6:
            # col = (col6 * 255) / 63
            pal_data.append(col6 << 2)

    return pal_data

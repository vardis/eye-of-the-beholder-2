from PIL import Image

from binary_reader import BinaryReader
from compression import decode_format80, decode_format80_image


def load_cps(cps_filename, palette=None):
    with BinaryReader(cps_filename) as reader:
        cps_data = decode_format80_image(reader)

        palette_size = cps_data[0]
        cps_data = cps_data[1:]
        if palette_size > 0:
            if palette is not None:
                print('overriding palette for file %s' % cps_filename)

            palette = []
            for i in range(palette_size):
                palette.append(cps_data[i] << 2)

            cps_data = cps_data[palette_size:]

        if palette is not None:
            img = Image.new('P', (320, 200))
            img.putpalette(palette)
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

    with open(pal_filename, 'rb') as fpal:
        pal_data_6 = fpal.read()
        for col6 in pal_data_6:
            # col = (col6 * 255) / 63
            pal_data.append((col6 & 0x3f) << 2)

    return pal_data


def decode_format80(reader):
    size = reader.read_ushort()
    format_type = reader.read_ushort()
    uncompressed = reader.read_uint()
    palette = reader.read_ushort()

    if format_type != 0x4:
        raise TypeError("Expected format type 4 but got type %d" % format_type)

    data = [0] * uncompressed
    dst_offset = 0

    while True:
        code = reader.read_ubyte()

        # end code
        if code == 0x80:
            return data

        # 0b10######
        elif code & 0xC0 == 0x80:
            count = code & 0x3F

            if count == 0:
                return data

            for i in range(count):
                data[dst_offset] = reader.read_ubyte()
                dst_offset += 1

        # 0b11######
        elif code & 0xC0 == 0xC0:
            count = code & 0x3F

            # Large copy
            if count < 0x3E:
                # command 2 (11cccccc p p): copy
                count += 3
                offset = reader.read_ushort()
                for i in range(offset, offset + count):
                    data[dst_offset] = data[i]
                    dst_offset += 1

            # Very large copy
            elif count == 0x3E:
                # pass
                # command 3 (11111110 c c v): fill
                count = reader.read_ushort()
                value = reader.read_ubyte()
                for i in range(count):
                    data[dst_offset] = value
                    dst_offset += 1
            else:
                # command 4 (copy 11111111 c c p p): copy
                count = reader.read_ushort()
                offset = reader.read_ushort()
                for i in range(offset, offset + count):
                    data[dst_offset] = data[i]
                    dst_offset += 1

        # 0b0#######
        # command 0 (0cccpppp p): copy
        elif code & 0x80 == 0:
            count = ((code & 0x70) >> 4) + 3
            offset = reader.read_ubyte() + ((code & 0x0F) << 8)
            offset = dst_offset - offset
            for i in range(offset, offset + count):
                data[dst_offset] = data[i]
                dst_offset += 1



import sys
import json

from enum import Enum, IntFlag

import sdl2.ext
import sdl2.surface
import sdl2.sdlimage
import sdl2.sdlgfx
import sdl2

from ctypes import byref, cast, POINTER, c_int, c_uint8, c_double

RESOURCES = sdl2.ext.Resources(__file__, "build")

BLOCK_SIZE = 8

# viewport dimensions in blocks (8x8 pixel blocks)
VP_HEIGHT_BLOCKS = 15
VP_WIDTH_BLOCKS = 22

VP_WIDTH_PIXELS = VP_WIDTH_BLOCKS * BLOCK_SIZE
VP_HEIGHT_PIXELS = VP_HEIGHT_BLOCKS * BLOCK_SIZE

renderer = None
bg_texture = None
walls_texture = None
maze = None
vmp = None


class Direction(Enum):
    North = ('n', 0, 1, 1)
    East = ('e', 1, -1, 1)
    South = ('s', 2, -1, -1)
    West = ('w', 3, 1, -1)

    def __init__(self, symbol, enc, scale_x, scale_y):
        """
        :param scale_x: indicates how to scale the dx and dy components of MazePosOffset when looking
        through this direction.
        :param scale_y: indicates how to scale the dx and dy components of MazePosOffset when looking
        through this direction.
        """
        self.symbol = symbol
        self.enc = enc
        self.scale_x = scale_x
        self.scale_y = scale_y

    @classmethod
    def from_encoding(cls, encoding):
        if encoding == 0:
            return Direction.North
        elif encoding == 1:
            return Direction.East
        elif encoding == 2:
            return Direction.South
        elif encoding == 3:
            return Direction.West
        else:
            raise Exception('Invalid Direction value ' + encoding)

    def from_view_dir(self, view_dir):
        return Direction.from_encoding((self.enc + view_dir.enc) & 0x03)  # mod 4


class MazePosOffset:
    def __init__(self, dx, dy, direction):
        self.delta_x = dx
        self.delta_y = dy
        self.direction = direction


# @formatter:off
maze_pos_offsets = [
    MazePosOffset(-3, -3, Direction.East),   # A - east
    MazePosOffset(-2, -3, Direction.East),   # B - east
    MazePosOffset(-1, -3, Direction.East),   # C - east

    MazePosOffset(1, -3, Direction.West),    # E - west
    MazePosOffset(2, -3, Direction.West),    # F - west
    MazePosOffset(3, -3, Direction.West),    # G - west

    MazePosOffset(-2, -3, Direction.South),  # B - south
    MazePosOffset(-1, -3, Direction.South),  # C - south
    MazePosOffset(0, -3, Direction.South),   # D - south
    MazePosOffset(1, -3, Direction.South),   # E - south
    MazePosOffset(2, -3, Direction.South),   # F - south

    MazePosOffset(-2, -2, Direction.East),   # H - east
    MazePosOffset(-1, -2, Direction.East),   # I - east

    MazePosOffset(1, -2, Direction.West),    # K - west
    MazePosOffset(2, -2, Direction.West),    # L - west

    MazePosOffset(-1, -2, Direction.South),  # I - south
    MazePosOffset(0, -2, Direction.South),   # J - south
    MazePosOffset(1, -2, Direction.South),   # K - south

    MazePosOffset(-1, -1, Direction.East),   # M - east

    MazePosOffset(1, -1, Direction.West),    # O - west

    MazePosOffset(-1, -1, Direction.South),  # M - south
    MazePosOffset(1, -1, Direction.South),   # O - south
    MazePosOffset(0, -1, Direction.South),   # N - south

    MazePosOffset(-1, 0, Direction.East),    # P - east

    MazePosOffset(1, 0, Direction.West)      # Q - west
]
# @formatter:on


class WallRenderConfig:
    def __init__(self, base_offset, view_offset, blk_height, blk_width, skip, flip):
        # offset within the tiles array
        self.base_offset = base_offset

        # block offset within the viewport
        self.view_offset = view_offset

        # block dimensions for this wall
        self.blk_width = blk_width
        self.blk_height = blk_height

        # how many blocks to skip to get to the next row of blocks for this wall
        self.skip = skip

        # whether to flip the wall image horizontally
        self.flip = flip


walls_render_config = [
    WallRenderConfig(3, 66, 5, 1, 2, False),      # A - east
    WallRenderConfig(1, 68, 5, 3, 0, False),      # B - east
    WallRenderConfig(-4, 74, 5, 1, 0, False),     # C - east

    WallRenderConfig(-4, 79, 5, 1, 0, True),      # E - west
    WallRenderConfig(1, 83, 5, 3, 0, True),       # F - west
    WallRenderConfig(1, 87, 5, 1, 2, True),       # G - west

    WallRenderConfig(32, 66, 5, 2, 4, False),     # B - south
    WallRenderConfig(28, 68, 5, 6, 0, False),     # C - south
    WallRenderConfig(28, 74, 5, 6, 0, False),     # D - south
    WallRenderConfig(28, 80, 5, 6, 0, False),     # E - south
    WallRenderConfig(28, 86, 5, 2, 4, False),     # F - south

    WallRenderConfig(16, 66, 6, 2, 0, False),     # H - east
    WallRenderConfig(-20, 50, 8, 2, 0, False),    # I - east

    WallRenderConfig(-20, 58, 8, 2, 0, True),     # K - west
    WallRenderConfig(16, 86, 6, 2, 0, True),      # L - west

    WallRenderConfig(62, 44, 8, 6, 4, False),     # I - south
    WallRenderConfig(58, 50, 8, 10, 0, False),    # J - south
    WallRenderConfig(58, 60, 8, 6, 4, False),     # K - south

    WallRenderConfig(-56, 25, 12, 3, 0, False),   # M - east

    WallRenderConfig(-56, 38, 12, 3, 0, True),    # O - west

    WallRenderConfig(151, 22, 12, 3, 13, False),  # M - south
    WallRenderConfig(138, 41, 12, 3, 13, False),  # O - south
    WallRenderConfig(138, 25, 12, 16, 0, False),  # N - south

    WallRenderConfig(-101, 0, 15, 3, 0, False),   # P - east

    WallRenderConfig(-101, 19, 15, 3, 0, True)    # Q - west
]


def load_vmp(vmp_filename):
    with open(vmp_filename, 'r') as fp:
        global vmp
        vmp = json.load(fp)
        return vmp


def get_vmp_bg_texture():
    gfx = f'build/vcn_{vmp["name"]}_bg.png'
    surface = sdl2.sdlimage.IMG_Load(bytes(gfx, 'utf-8'))
    sdl2.SDL_SetColorKey(surface, sdl2.SDL_TRUE, 0)
    texture = sdl2.SDL_CreateTextureFromSurface(renderer, surface)
    return texture


def get_vmp_wall_texture():
    surface = sdl2.sdlimage.IMG_Load(bytes(f'build/vcn_{vmp["name"]}_walls.png', 'utf-8'))
    sdl2.SDL_SetColorKey(surface, sdl2.SDL_TRUE, 0)
    texture = sdl2.SDL_CreateTextureFromSurface(renderer, surface)
    sdl2.SDL_SetTextureBlendMode(texture, sdl2.SDL_BLENDMODE_BLEND)
    return texture


def load_maze(maz_filename):
    global maze
    with open(maz_filename, 'r') as fp:
        maze = json.load(fp)

    return maze


def draw_bg():
    for block_y in range(VP_HEIGHT_BLOCKS):
        for block_x in range(VP_WIDTH_BLOCKS):
            block_index = block_y * VP_WIDTH_BLOCKS + block_x

            tile = vmp['bgTiles'][block_index]
            flag = sdl2.SDL_FLIP_HORIZONTAL if tile['flipped'] else sdl2.SDL_FLIP_NONE

            tileset_block_x = tile['vcn_block'] % 32
            tileset_block_y = tile['vcn_block'] // 32

            src_rect = sdl2.SDL_Rect(tileset_block_x * 8, tileset_block_y * 8, 8, 8)
            dst_rect = sdl2.SDL_Rect(block_x * 8, block_y * 8, 8, 8)
            sdl2.SDL_RenderCopyEx(renderer, bg_texture, src_rect, dst_rect, c_double(0.0), None, flag)


def draw_walls(pos_x, pos_y, direction):
    """
    # @formatter:off
    
    Field of vision: the 17 map positions required to read for rendering a screen and the 25 possible wall 
    configurations that these positions might contain.
    
    A|B|C|D|E|F|G
      ¯ ¯ ¯ ¯ ¯
      H|I|J|K|L
        ¯ ¯ ¯
        M|N|O
        ¯ ¯ ¯
        P|^|Q
        
    # @formatter:on

    """

    for i in range(25):
        if direction == Direction.West or direction == Direction.East:
            # side-ways view, x goes up-down in the field of vision while y goes left-right
            x = maze_pos_offsets[i].delta_y * direction.scale_x
            y = maze_pos_offsets[i].delta_x * direction.scale_y
        else:
            # vertical view, x goes left-right in the field of vision while y goes up-down
            x = maze_pos_offsets[i].delta_x * direction.scale_x
            y = maze_pos_offsets[i].delta_y * direction.scale_y

        wall_pos_x = x + pos_x
        wall_pos_y = y + pos_y

        if wall_pos_y < 0 or wall_pos_x < 0 or wall_pos_y > 31 or wall_pos_x > 31:
            continue

        wall_direction = maze_pos_offsets[i].direction.from_view_dir(direction)

        wall_mapping_index = maze['walls'][wall_pos_x][wall_pos_y][wall_direction.symbol]

        draw_wall(wall_mapping_index, i)


def draw_wall(wall_mapping_index, wall_position):
    # walls
    if wall_mapping_index == 1 or wall_mapping_index == 2:

        wall_type = wall_mapping_index - 1

        cfg = walls_render_config[wall_position]

        tiles_offset = cfg.base_offset

        tileset = vmp['wallTiles'][wall_type]['tiles']

        for t in range(cfg.blk_height):

            for s in range(cfg.blk_width):

                if cfg.flip:
                    viewport_block_index = cfg.view_offset + cfg.blk_width - (s + 1) + t * VP_WIDTH_BLOCKS
                else:
                    viewport_block_index = s + t * VP_WIDTH_BLOCKS + cfg.view_offset

                viewport_block_x = viewport_block_index % VP_WIDTH_BLOCKS
                viewport_block_y = viewport_block_index // VP_WIDTH_BLOCKS

                tile = tileset[tiles_offset]
                flip = tile['flipped'] != cfg.flip  # xor
                flag = sdl2.SDL_FLIP_HORIZONTAL if flip else sdl2.SDL_FLIP_NONE

                vcn_block = tile['vcn_block']
                # vcn_block += 128
                tileset_block_x = vcn_block % 32
                tileset_block_y = vcn_block // 32

                src_rect = sdl2.SDL_Rect(tileset_block_x * 8, tileset_block_y * 8, 8, 8)
                dst_rect = sdl2.SDL_Rect(viewport_block_x * 8, viewport_block_y * 8, 8, 8)

                sdl2.SDL_RenderCopyEx(renderer, walls_texture, src_rect, dst_rect, c_double(0.0),
                                      None, flag)

                tiles_offset += 1

            tiles_offset += cfg.skip


def run_raw():
    global renderer, bg_texture, maze, vmp, walls_texture

    sdl2.SDL_Init(sdl2.SDL_INIT_VIDEO)
    window = sdl2.SDL_CreateWindow(b"Eye of the Beholder 2",
                                   sdl2.SDL_WINDOWPOS_CENTERED, sdl2.SDL_WINDOWPOS_CENTERED,
                                   800, 600, sdl2.SDL_WINDOW_SHOWN | sdl2.SDL_WINDOW_RESIZABLE)

    renderer = sdl2.SDL_CreateRenderer(window, -1,
                                       sdl2.SDL_RENDERER_ACCELERATED + sdl2.SDL_RENDERER_TARGETTEXTURE + sdl2.SDL_RENDERER_PRESENTVSYNC)
    sdl2.SDL_SetRenderDrawBlendMode(renderer, sdl2.SDL_BLENDMODE_BLEND)

    render_target = sdl2.SDL_CreateTexture(renderer, sdl2.SDL_PIXELFORMAT_RGB888, sdl2.SDL_TEXTUREACCESS_TARGET,
                                           VP_WIDTH_PIXELS,
                                           VP_HEIGHT_PIXELS)

    sdl2.SDL_SetTextureBlendMode(render_target, sdl2.SDL_BLENDMODE_BLEND)

    sdl2.sdlimage.IMG_Init(sdl2.sdlimage.IMG_INIT_PNG)

    maze = load_maze('build/level1.maz')

    vmp = load_vmp('build/dung.vmp.json')

    bg_texture = get_vmp_bg_texture()
    walls_texture = get_vmp_wall_texture()

    running = True
    event = sdl2.SDL_Event()
    while running:
        while sdl2.SDL_PollEvent(byref(event)) != 0:
            if event.type == sdl2.SDL_QUIT:
                running = False
                break

        sdl2.SDL_SetRenderTarget(renderer, render_target)
        sdl2.SDL_SetRenderDrawColor(renderer, 0, 0, 0, 255)
        sdl2.SDL_RenderClear(renderer)

        draw_bg()

        draw_walls(5, 7, Direction.North)

        sdl2.SDL_SetRenderTarget(renderer, None)

        sdl2.SDL_RenderCopy(renderer, render_target, None, None)
        sdl2.SDL_RenderPresent(renderer)

    sdl2.SDL_DestroyWindow(window)
    sdl2.SDL_Quit()
    return 0


if __name__ == "__main__":
    sys.exit(run_raw())

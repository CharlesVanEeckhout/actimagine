# bitdepth 8
# this is only used for the y plane buffer


def pred4x4_vertical(plane_buffer, dst):
    # fill the 4x4 block with the top edge pixels
    for y in range(4):
        for x in range(4):
            plane_buffer[dst["y"] + y][dst["x"] + x] = plane_buffer[dst["y"] - 1][dst["x"] + x]


def pred4x4_horizontal(plane_buffer, dst):
    # fill the 4x4 block with the left edge pixels
    for y in range(4):
        for x in range(4):
            plane_buffer[dst["y"] + y][dst["x"] + x] = plane_buffer[dst["y"] + y][dst["x"] - 1]


def pred4x4_128_dc(plane_buffer, dst):
    # fill the 4x4 block with gray
    for y in range(4):
        for x in range(4):
            plane_buffer[dst["y"] + y][dst["x"] + x] = 128


def pred4x4_top_dc(plane_buffer, dst):
    # fill the 4x4 block with average of top edge pixels
    dc = (
        plane_buffer[dst["y"] - 1][dst["x"] + 0] +
        plane_buffer[dst["y"] - 1][dst["x"] + 1] +
        plane_buffer[dst["y"] - 1][dst["x"] + 2] +
        plane_buffer[dst["y"] - 1][dst["x"] + 3] +
        2
    ) // 4
    for y in range(4):
        for x in range(4):
            plane_buffer[dst["y"] + y][dst["x"] + x] = dc


def pred4x4_left_dc(plane_buffer, dst):
    # fill the 4x4 block with average of left edge pixels
    dc = (
        plane_buffer[dst["y"] + 0][dst["x"] - 1] +
        plane_buffer[dst["y"] + 1][dst["x"] - 1] +
        plane_buffer[dst["y"] + 2][dst["x"] - 1] +
        plane_buffer[dst["y"] + 3][dst["x"] - 1] +
        2
    ) // 4
    for y in range(4):
        for x in range(4):
            plane_buffer[dst["y"] + y][dst["x"] + x] = dc


def pred4x4_dc(plane_buffer, dst):
    # fill the 4x4 block with average of top edge and left edge pixels
    dc = (
        plane_buffer[dst["y"] - 1][dst["x"] + 0] +
        plane_buffer[dst["y"] - 1][dst["x"] + 1] +
        plane_buffer[dst["y"] - 1][dst["x"] + 2] +
        plane_buffer[dst["y"] - 1][dst["x"] + 3] +
        plane_buffer[dst["y"] + 0][dst["x"] - 1] +
        plane_buffer[dst["y"] + 1][dst["x"] - 1] +
        plane_buffer[dst["y"] + 2][dst["x"] - 1] +
        plane_buffer[dst["y"] + 3][dst["x"] - 1] +
        4
    ) // 8
    for y in range(4):
        for x in range(4):
            plane_buffer[dst["y"] + y][dst["x"] + x] = dc


def pred4x4_down_left(plane_buffer, dst):
    # fill the 4x4 block with smudging pixels from borders with slope of (-1,+1)
    t0 = plane_buffer[dst["y"] - 1][dst["x"] + 0]
    t1 = plane_buffer[dst["y"] - 1][dst["x"] + 1]
    t2 = plane_buffer[dst["y"] - 1][dst["x"] + 2]
    t3 = plane_buffer[dst["y"] - 1][dst["x"] + 3]

    t4 = plane_buffer[dst["y"] - 1][dst["x"] + 4]
    t5 = plane_buffer[dst["y"] - 1][dst["x"] + 5]
    t6 = plane_buffer[dst["y"] - 1][dst["x"] + 6]
    t7 = plane_buffer[dst["y"] - 1][dst["x"] + 7]

    pixels = [
        (t0 + 2*t1 + t2 + 2) // 4, # (0,0)
        (t1 + 2*t2 + t3 + 2) // 4, # (1,0) (0,1)
        (t2 + 2*t3 + t4 + 2) // 4, # (2,0) (1,1) (0,2)
        (t3 + 2*t4 + t5 + 2) // 4, # (3,0) (2,1) (1,2) (0,3)
        (t4 + 2*t5 + t6 + 2) // 4, # (3,1) (2,2) (1,3)
        (t5 + 2*t6 + t7 + 2) // 4, # (3,2) (2,3)
        (t6 + 3*t7 + 2) // 4       # (3,3)
    ]

    for y in range(4):
        for x in range(4):
            plane_buffer[dst["y"] + y][dst["x"] + x] = pixels[x + y]


def pred4x4_down_right(plane_buffer, dst):
    # fill the 4x4 block with smudging pixels from borders with slope of (+1,+1)
    lt = plane_buffer[dst["y"] - 1][dst["x"] - 1]

    t0 = plane_buffer[dst["y"] - 1][dst["x"] + 0]
    t1 = plane_buffer[dst["y"] - 1][dst["x"] + 1]
    t2 = plane_buffer[dst["y"] - 1][dst["x"] + 2]
    t3 = plane_buffer[dst["y"] - 1][dst["x"] + 3]

    l0 = plane_buffer[dst["y"] + 0][dst["x"] - 1]
    l1 = plane_buffer[dst["y"] + 1][dst["x"] - 1]
    l2 = plane_buffer[dst["y"] + 2][dst["x"] - 1]
    l3 = plane_buffer[dst["y"] + 3][dst["x"] - 1]

    pixels = [
        (l3 + 2*l2 + l1 + 2) // 4, # (0,3)
        (l2 + 2*l1 + l0 + 2) // 4, # (0,2) (1,3)
        (l1 + 2*l0 + lt + 2) // 4, # (0,1) (1,2) (2,3)
        (l0 + 2*lt + t0 + 2) // 4, # (0,0) (1,1) (2,2) (3,3)
        (lt + 2*t0 + t1 + 2) // 4, # (1,0) (2,1) (3,2)
        (t0 + 2*t1 + t2 + 2) // 4, # (2,0) (3,1)
        (t1 + 2*t2 + t3 + 2) // 4  # (3,0)
    ]

    for y in range(4):
        for x in range(4):
            plane_buffer[dst["y"] + y][dst["x"] + x] = pixels[3 + x - y]


def pred4x4_vertical_right(plane_buffer, dst):
    # fill the 4x4 block with smudging pixels from borders with slope of (+1,+2)
    lt = plane_buffer[dst["y"] - 1][dst["x"] - 1]

    t0 = plane_buffer[dst["y"] - 1][dst["x"] + 0]
    t1 = plane_buffer[dst["y"] - 1][dst["x"] + 1]
    t2 = plane_buffer[dst["y"] - 1][dst["x"] + 2]
    t3 = plane_buffer[dst["y"] - 1][dst["x"] + 3]

    l0 = plane_buffer[dst["y"] + 0][dst["x"] - 1]
    l1 = plane_buffer[dst["y"] + 1][dst["x"] - 1]
    l2 = plane_buffer[dst["y"] + 2][dst["x"] - 1]
    #l3 = plane_buffer[dst["y"] + 3][dst["x"] - 1]

    pixels = [
        (l0 + 2*l1 + l2 + 2) // 4, # (0,3)
        (lt + 2*l0 + l1 + 2) // 4, # (0,2)
        (l0 + 2*lt + t0 + 2) // 4, # (0,1) (1,3)
        (lt + t0 + 1) // 2,        # (0,0) (1,2)
        (lt + 2*t0 + t1 + 2) // 4, # (1,1) (2,3)
        (t0 + t1 + 1) // 2,        # (1,0) (2,2)
        (t0 + 2*t1 + t2 + 2) // 4, # (2,1) (3,3)
        (t1 + t2 + 1) // 2,        # (2,0) (3,2)
        (t1 + 2*t2 + t3 + 2) // 4, # (3,1)
        (t2 + t3 + 1) // 2,        # (3,0)
    ]

    for y in range(4):
        for x in range(4):
            plane_buffer[dst["y"] + y][dst["x"] + x] = pixels[3 + 2*x - y]


def pred4x4_horizontal_down(plane_buffer, dst):
    # fill the 4x4 block with smudging pixels from borders with slope of (+2,+1)
    lt = plane_buffer[dst["y"] - 1][dst["x"] - 1]

    t0 = plane_buffer[dst["y"] - 1][dst["x"] + 0]
    t1 = plane_buffer[dst["y"] - 1][dst["x"] + 1]
    t2 = plane_buffer[dst["y"] - 1][dst["x"] + 2]
    #t3 = plane_buffer[dst["y"] - 1][dst["x"] + 3]

    l0 = plane_buffer[dst["y"] + 0][dst["x"] - 1]
    l1 = plane_buffer[dst["y"] + 1][dst["x"] - 1]
    l2 = plane_buffer[dst["y"] + 2][dst["x"] - 1]
    l3 = plane_buffer[dst["y"] + 3][dst["x"] - 1]

    pixels = [
        (t0 + 2*t1 + t2 + 2) // 4, # (3,0)
        (lt + 2*t0 + t1 + 2) // 4, # (2,0)
        (l0 + 2*lt + t0 + 2) // 4, # (1,0) (3,1)
        (lt + l0 + 1) // 2,        # (0,0) (2,1)
        (lt + 2*l0 + l1 + 2) // 4, # (1,1) (3,2)
        (l0 + l1 + 1) // 2,        # (0,1) (2,2)
        (l0 + 2*l1 + l2 + 2) // 4, # (1,2) (3,3)
        (l1 + l2 + 1) // 2,        # (0,2) (2,3)
        (l1 + 2*l2 + l3 + 2) // 4, # (1,3)
        (l2 + l3 + 1) // 2,        # (0,3)
    ]

    for y in range(4):
        for x in range(4):
            plane_buffer[dst["y"] + y][dst["x"] + x] = pixels[3 - x + 2*y]


def pred4x4_vertical_left(plane_buffer, dst):
    # fill the 4x4 block with smudging pixels from borders with slope of (-1,+2)
    t0 = plane_buffer[dst["y"] - 1][dst["x"] + 0]
    t1 = plane_buffer[dst["y"] - 1][dst["x"] + 1]
    t2 = plane_buffer[dst["y"] - 1][dst["x"] + 2]
    t3 = plane_buffer[dst["y"] - 1][dst["x"] + 3]

    t4 = plane_buffer[dst["y"] - 1][dst["x"] + 4]
    t5 = plane_buffer[dst["y"] - 1][dst["x"] + 5]
    t6 = plane_buffer[dst["y"] - 1][dst["x"] + 6]
    #t7 = plane_buffer[dst["y"] - 1][dst["x"] + 7]

    pixels = [
        (t0 + t1 + 1) // 2,        # (0,0)
        (t0 + 2*t1 + t2 + 2) // 4, # (0,1)
        (t1 + t2 + 1) // 2,        # (1,0) (0,2)
        (t1 + 2*t2 + t3 + 2) // 4, # (1,1) (0,3)
        (t2 + t3 + 1) // 2,        # (2,0) (1,2)
        (t2 + 2*t3 + t4 + 2) // 4, # (2,1) (1,3)
        (t3 + t4 + 1) // 2,        # (3,0) (2,2)
        (t3 + 2*t4 + t5 + 2) // 4, # (3,1) (2,3)
        (t4 + t5 + 1) // 2,        # (3,2)
        (t4 + 2*t5 + t6 + 2) // 4, # (3,3)
    ]

    for y in range(4):
        for x in range(4):
            plane_buffer[dst["y"] + y][dst["x"] + x] = pixels[2*x + y]


def pred4x4_horizontal_up(plane_buffer, dst):
    # fill the 4x4 block with smudging pixels from borders with slope of (+2,-1)
    l0 = plane_buffer[dst["y"] + 0][dst["x"] - 1]
    l1 = plane_buffer[dst["y"] + 1][dst["x"] - 1]
    l2 = plane_buffer[dst["y"] + 2][dst["x"] - 1]
    l3 = plane_buffer[dst["y"] + 3][dst["x"] - 1]

    pixels = [
        (l0 + l1 + 1) // 2,        # (0,0)
        (l0 + 2*l1 + l2 + 2) // 4, # (1,0)
        (l1 + l2 + 1) // 2,        # (2,0) (0,1)
        (l1 + 2*l2 + l3 + 2) // 4, # (3,0) (1,1)
        (l2 + l3 + 1) // 2,        # (2,1) (0,2)
        (l2 + 2*l3 + l3 + 2) // 4, # (3,1) (1,2)
        l3                         # (2,2) (0,3) (3,2) (1,3) (2,3) (3,3)
    ]

    for y in range(4):
        for x in range(4):
            plane_buffer[dst["y"] + y][dst["x"] + x] = pixels[min(x + 2*y, 6)]

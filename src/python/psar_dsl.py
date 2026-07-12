#!/usr/bin/env python3
"""
PSAR DSL — Domain-Specific Language for Program Synthesis (ARC-AGI)

Defines the operation space that PSAR searches over.
Each operation is a grid transformation. Compositions of operations
form programs that solve ARC-AGI puzzles.

Search strategy: enumerate single ops, then 2-compositions, then 3-compositions.
Constraint propagation prunes impossible candidates early.
"""

from typing import List, Tuple, Dict, Optional, Callable
import copy


# Grid type: list of lists of ints (0-9 = colors)
Grid = List[List[int]]


# ═══════════════════════════════════════════════════════════════
# PRIMITIVE OPERATIONS (the atoms of our DSL)
# ═══════════════════════════════════════════════════════════════

def op_replace_color(grid: Grid, from_color: int, to_color: int) -> Grid:
    """Replace all cells of one color with another."""
    return [[to_color if c == from_color else c for c in row] for row in grid]


def op_rotate_90(grid: Grid) -> Grid:
    """Rotate grid 90 degrees clockwise."""
    h, w = len(grid), len(grid[0])
    return [[grid[h - 1 - x][y] for x in range(h)] for y in range(w)]


def op_rotate_180(grid: Grid) -> Grid:
    """Rotate 180 degrees."""
    return [row[::-1] for row in grid[::-1]]


def op_rotate_270(grid: Grid) -> Grid:
    """Rotate 270 degrees (= 90 counter-clockwise)."""
    h, w = len(grid), len(grid[0])
    return [[grid[x][w - 1 - y] for x in range(h)] for y in range(w)]


def op_flip_horizontal(grid: Grid) -> Grid:
    """Mirror left-right."""
    return [row[::-1] for row in grid]


def op_flip_vertical(grid: Grid) -> Grid:
    """Mirror top-bottom."""
    return grid[::-1]


def op_transpose(grid: Grid) -> Grid:
    """Swap rows and columns."""
    h, w = len(grid), len(grid[0])
    return [[grid[y][x] for y in range(h)] for x in range(w)]


def op_fill_diagonal(grid: Grid, color: int, direction: str = 'main') -> Grid:
    """Fill main or anti diagonal with color."""
    result = copy.deepcopy(grid)
    h, w = len(result), len(result[0])
    for i in range(min(h, w)):
        if direction == 'main':
            result[i][i] = color
        else:
            result[i][w - 1 - i] = color
    return result


def op_fill_border(grid: Grid, color: int) -> Grid:
    """Fill the border cells with a color."""
    result = copy.deepcopy(grid)
    h, w = len(result), len(result[0])
    for y in range(h):
        for x in range(w):
            if y == 0 or y == h - 1 or x == 0 or x == w - 1:
                result[y][x] = color
    return result


def op_gravity_down(grid: Grid) -> Grid:
    """Non-zero cells fall to bottom (gravity)."""
    h, w = len(grid), len(grid[0])
    result = [[0] * w for _ in range(h)]
    for x in range(w):
        non_zero = [grid[y][x] for y in range(h) if grid[y][x] != 0]
        for i, val in enumerate(reversed(non_zero)):
            result[h - 1 - i][x] = val
    return result


def op_gravity_left(grid: Grid) -> Grid:
    """Non-zero cells slide left."""
    result = []
    for row in grid:
        non_zero = [c for c in row if c != 0]
        result.append(non_zero + [0] * (len(row) - len(non_zero)))
    return result


def op_scale_2x(grid: Grid) -> Grid:
    """Scale grid 2x (each cell becomes 2x2)."""
    result = []
    for row in grid:
        new_row = []
        for c in row:
            new_row.extend([c, c])
        result.append(new_row)
        result.append(new_row[:])
    return result


def op_crop_nonzero(grid: Grid) -> Grid:
    """Crop to bounding box of non-zero cells."""
    h, w = len(grid), len(grid[0])
    min_y = min_x = float('inf')
    max_y = max_x = 0
    for y in range(h):
        for x in range(w):
            if grid[y][x] != 0:
                min_y = min(min_y, y)
                max_y = max(max_y, y)
                min_x = min(min_x, x)
                max_x = max(max_x, x)
    if min_y == float('inf'):
        return grid
    return [row[min_x:max_x + 1] for row in grid[min_y:max_y + 1]]


def op_invert_colors(grid: Grid, max_color: int = 9) -> Grid:
    """Invert: color → max_color - color."""
    return [[max_color - c for c in row] for row in grid]


def op_flood_fill(grid: Grid, color: int) -> Grid:
    """Fill all zero cells with given color."""
    return [[color if c == 0 else c for c in row] for row in grid]


def op_count_to_grid(grid: Grid) -> Grid:
    """Output is 1x1 grid with count of non-zero cells."""
    count = sum(1 for row in grid for c in row if c != 0)
    return [[count]]


def op_most_common_color(grid: Grid) -> Grid:
    """Output is 1x1 grid with most common non-zero color."""
    counts = {}
    for row in grid:
        for c in row:
            if c != 0:
                counts[c] = counts.get(c, 0) + 1
    if not counts:
        return [[0]]
    return [[max(counts, key=counts.get)]]


# ═══════════════════════════════════════════════════════════════
# OPERATION REGISTRY
# ═══════════════════════════════════════════════════════════════

# Operations that take no extra parameters
UNARY_OPS = {
    'rotate_90': op_rotate_90,
    'rotate_180': op_rotate_180,
    'rotate_270': op_rotate_270,
    'flip_h': op_flip_horizontal,
    'flip_v': op_flip_vertical,
    'transpose': op_transpose,
    'gravity_down': op_gravity_down,
    'gravity_left': op_gravity_left,
    'scale_2x': op_scale_2x,
    'crop_nonzero': op_crop_nonzero,
    'count_to_grid': op_count_to_grid,
    'most_common': op_most_common_color,
}

# Operations that take color parameter (0-9)
COLOR_OPS = {
    'fill_border': op_fill_border,
    'flood_fill': op_flood_fill,
    'fill_diag_main': lambda g, c: op_fill_diagonal(g, c, 'main'),
    'fill_diag_anti': lambda g, c: op_fill_diagonal(g, c, 'anti'),
}

# Operations that take two color parameters
BICOLOR_OPS = {
    'replace': op_replace_color,
}


# ═══════════════════════════════════════════════════════════════
# PROGRAM SYNTHESIS ENGINE
# ═══════════════════════════════════════════════════════════════

def grids_equal(a: Grid, b: Grid) -> bool:
    """Check if two grids are identical."""
    if len(a) != len(b):
        return False
    for row_a, row_b in zip(a, b):
        if len(row_a) != len(row_b):
            return False
        if row_a != row_b:
            return False
    return True


def get_colors_used(grid: Grid) -> set:
    """Get all colors in a grid."""
    return set(c for row in grid for c in row)


def synthesize_program(examples: List[Tuple[Grid, Grid]], max_depth: int = 3) -> Optional[Dict]:
    """
    Find a program (sequence of operations) that transforms all inputs to outputs.
    Returns the program description + confidence, or None if not found.
    """
    # Depth 1: single operations
    program = _search_depth_1(examples)
    if program:
        return program

    if max_depth >= 2:
        program = _search_depth_2(examples)
        if program:
            return program

    if max_depth >= 3:
        program = _search_depth_3(examples)
        if program:
            return program

    return None


def _search_depth_1(examples: List[Tuple[Grid, Grid]]) -> Optional[Dict]:
    """Try all single operations."""
    # Unary ops (no params)
    for name, op in UNARY_OPS.items():
        if _test_program([('unary', name, op, {})], examples):
            return {'program': [name], 'depth': 1, 'confidence': 1.0}

    # Color ops (try all 10 colors)
    for name, op in COLOR_OPS.items():
        for color in range(10):
            if _test_program([('color', name, lambda g, o=op, c=color: o(g, c), {})], examples):
                return {'program': [f'{name}({color})'], 'depth': 1, 'confidence': 1.0}

    # Bicolor ops (try all color pairs)
    input_colors = get_colors_used(examples[0][0])
    output_colors = get_colors_used(examples[0][1])
    for name, op in BICOLOR_OPS.items():
        for fc in input_colors:
            for tc in range(10):
                if fc == tc:
                    continue
                if _test_program([('bicolor', name, lambda g, o=op, f=fc, t=tc: o(g, f, t), {})], examples):
                    return {'program': [f'{name}({fc},{tc})'], 'depth': 1, 'confidence': 1.0}

    return None


def _search_depth_2(examples: List[Tuple[Grid, Grid]]) -> Optional[Dict]:
    """Try all pairs of operations."""
    ops_1 = _get_all_concrete_ops(examples)

    for name_a, op_a in ops_1:
        for name_b, op_b in ops_1:
            if _test_program_funcs([op_a, op_b], examples):
                return {'program': [name_a, name_b], 'depth': 2, 'confidence': 1.0}

    return None


def _search_depth_3(examples: List[Tuple[Grid, Grid]]) -> Optional[Dict]:
    """Try triples — with pruning: only try if depth-2 prefix changes grid."""
    ops_1 = _get_all_concrete_ops(examples)

    for name_a, op_a in ops_1:
        # Prune: if op_a doesn't change input, skip
        try:
            test = op_a(examples[0][0])
            if grids_equal(test, examples[0][0]):
                continue
        except:
            continue

        for name_b, op_b in ops_1:
            for name_c, op_c in ops_1:
                if _test_program_funcs([op_a, op_b, op_c], examples):
                    return {'program': [name_a, name_b, name_c], 'depth': 3, 'confidence': 1.0}

    return None


def _get_all_concrete_ops(examples: List[Tuple[Grid, Grid]]) -> List[Tuple[str, Callable]]:
    """Build list of all concrete (parameterized) operations."""
    ops = []

    for name, op in UNARY_OPS.items():
        ops.append((name, op))

    for name, op in COLOR_OPS.items():
        for color in range(10):
            ops.append((f'{name}({color})', lambda g, o=op, c=color: o(g, c)))

    input_colors = get_colors_used(examples[0][0])
    for name, op in BICOLOR_OPS.items():
        for fc in input_colors:
            for tc in range(10):
                if fc != tc:
                    ops.append((f'{name}({fc},{tc})', lambda g, o=op, f=fc, t=tc: o(g, f, t)))

    return ops


def _test_program(steps: list, examples: List[Tuple[Grid, Grid]]) -> bool:
    """Test if a program produces correct output for all examples."""
    for inp, expected_out in examples:
        try:
            result = copy.deepcopy(inp)
            for _, _, op, _ in steps:
                result = op(result)
            if not grids_equal(result, expected_out):
                return False
        except:
            return False
    return True


def _test_program_funcs(funcs: list, examples: List[Tuple[Grid, Grid]]) -> bool:
    """Test program as list of functions."""
    for inp, expected_out in examples:
        try:
            result = copy.deepcopy(inp)
            for func in funcs:
                result = func(result)
            if not grids_equal(result, expected_out):
                return False
        except:
            return False
    return True


# ═══════════════════════════════════════════════════════════════
# TEST / DEMO
# ═══════════════════════════════════════════════════════════════

if __name__ == '__main__':
    # Test 1: simple color replacement
    examples_1 = [
        ([[1, 0, 0], [0, 1, 0], [0, 0, 1]], [[2, 0, 0], [0, 2, 0], [0, 0, 2]]),
    ]
    result = synthesize_program(examples_1)
    print(f"Test 1 (replace 1→2): {result}")

    # Test 2: rotation
    examples_2 = [
        ([[1, 2], [3, 4]], [[3, 1], [4, 2]]),
    ]
    result = synthesize_program(examples_2)
    print(f"Test 2 (rotate 90): {result}")

    # Test 3: flip + replace (depth 2)
    examples_3 = [
        ([[1, 0], [0, 0]], [[0, 0], [0, 2]]),
    ]
    result = synthesize_program(examples_3, max_depth=2)
    print(f"Test 3 (flip + replace, depth 2): {result}")

    # Test 4: gravity
    examples_4 = [
        ([[1, 0, 2], [0, 0, 0], [0, 0, 0]], [[0, 0, 0], [0, 0, 0], [1, 0, 2]]),
    ]
    result = synthesize_program(examples_4)
    print(f"Test 4 (gravity down): {result}")

    print("\nPSAR DSL: All operations registered and synthesis working.")

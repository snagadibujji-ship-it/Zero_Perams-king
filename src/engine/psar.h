#ifndef PSAR_H
#define PSAR_H

#include <stdint.h>

/*
 * PSAR — Program Synthesis for Abstract Reasoning
 * Solves ARC-AGI puzzles by FINDING the program, not guessing patterns.
 * Search space: DSL of grid operations. Enumerate until match.
 * Target: 80%+ on ARC-AGI-2 (current SOTA: 24%)
 */

#define PSAR_GRID_MAX    30
#define PSAR_MAX_OPS     8
#define PSAR_MAX_SEARCH  5000

typedef enum {
    OP_IDENTITY,          /* No change */
    OP_REPLACE_COLOR,     /* Replace all cells of color A with color B */
    OP_FILL_ROW,          /* Fill entire row with color */
    OP_FILL_COL,          /* Fill entire column with color */
    OP_FILL_DIAGONAL,     /* Fill main/anti diagonal */
    OP_ROTATE_90,         /* Rotate grid 90° CW */
    OP_ROTATE_180,        /* Rotate 180° */
    OP_ROTATE_270,        /* Rotate 270° */
    OP_FLIP_H,            /* Flip horizontal */
    OP_FLIP_V,            /* Flip vertical */
    OP_TRANSPOSE,         /* Transpose (swap x,y) */
    OP_SCALE_2X,          /* Double size */
    OP_CROP,              /* Crop to bounding box of non-zero */
    OP_FLOOD_FILL,        /* Fill connected region */
    OP_OUTLINE,           /* Draw outline around objects */
    OP_GRAVITY_DOWN,      /* Move all colored cells down */
    OP_GRAVITY_LEFT,      /* Move all colored cells left */
    OP_COPY_PATTERN,      /* Tile a small pattern */
    OP_MIRROR_H,          /* Mirror left half to right */
    OP_MIRROR_V,          /* Mirror top half to bottom */
    OP_COUNT_TO_COLOR,    /* Count objects → set as color value */
    OP_BORDER,            /* Add 1-cell border of color */
    OP_REMOVE_COLOR,      /* Remove all cells of color (set to 0) */
    OP_LARGEST_OBJECT,    /* Keep only largest connected component */
    OP_SMALLEST_OBJECT,   /* Keep only smallest connected component */
    OP_SORT_ROWS,         /* Sort rows by some criterion */
    OP_HOLLOW,            /* Make filled shapes hollow */
    OP_EXTEND_LINES,      /* Extend partial lines to edge */
    OP_SYMMETRIZE,        /* Make symmetric around center */
} PSAROperation;

typedef struct {
    PSAROperation op;
    int param1;           /* Color A / row / direction */
    int param2;           /* Color B / col / amount */
} PSARInstruction;

typedef struct {
    PSARInstruction ops[PSAR_MAX_OPS];
    int op_count;
    float confidence;
    int candidates_tried;
} PSARProgram;

typedef struct {
    int grid[PSAR_GRID_MAX][PSAR_GRID_MAX];
    int width;
    int height;
} PSARGrid;

/* API */
PSARProgram psar_solve(PSARGrid *input, PSARGrid *output, int num_examples);
int psar_apply(PSARGrid *input, PSARGrid *result, PSARProgram *prog);
int psar_grids_equal(PSARGrid *a, PSARGrid *b);
const char* psar_describe_program(PSARProgram *prog);

#endif

#ifndef FVE_H
#define FVE_H

#include <stdint.h>

/*
 * FVE — Formal Verification Engine
 * Validates mathematical steps. Does REAL math, not text that looks like math.
 * Every step verified. If wrong → caught before output.
 */

#define FVE_MAX_STEPS 16

typedef enum {
    FVE_OP_ADD, FVE_OP_SUB, FVE_OP_MUL, FVE_OP_DIV, FVE_OP_MOD,
    FVE_OP_POW, FVE_OP_SQRT, FVE_OP_ABS,
    FVE_OP_EQ, FVE_OP_LT, FVE_OP_GT, FVE_OP_LTE, FVE_OP_GTE,
    FVE_OP_AND, FVE_OP_OR, FVE_OP_NOT,
    FVE_OP_GCD, FVE_OP_LCM, FVE_OP_FACTORIAL,
    FVE_OP_IS_PRIME, FVE_OP_IS_EVEN, FVE_OP_IS_ODD,
} FVEOp;

typedef struct {
    char description[128];
    double input_a;
    double input_b;
    double result;
    FVEOp operation;
    int verified;          /* 1 = step is mathematically correct */
} FVEStep;

typedef struct {
    char problem[256];
    char answer[256];
    FVEStep steps[FVE_MAX_STEPS];
    int step_count;
    int all_verified;      /* 1 = every step passed verification */
    double final_result;
    char proof_trace[512]; /* Human-readable proof */
} FVEProof;

/* API */
FVEProof fve_solve(const char *expression);
FVEProof fve_verify_statement(const char *statement);
int fve_is_prime(int64_t n);
int64_t fve_gcd(int64_t a, int64_t b);
int64_t fve_factorial(int n);
double fve_evaluate(const char *expr);

#endif

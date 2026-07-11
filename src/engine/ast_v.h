#ifndef AST_V_H
#define AST_V_H

#include "pcse.h"

/*
 * AST — Adversarial Self-Tribunal
 * Before ANY answer exits: prosecute → defend → judge.
 * Catches contradictions, myths, and low-confidence claims.
 */

typedef enum {
    VERDICT_CONFIRMED,     /* Defense won — answer is solid */
    VERDICT_REVISED,       /* Prosecution found issue — answer corrected */
    VERDICT_UNCERTAIN,     /* Deadlock — present both sides */
    VERDICT_BLOCKED,       /* Myth detected — reject false claim */
} ASTVerdict;

typedef struct {
    char challenge[256];
    float strength;
    int upheld;  /* 1 = prosecution won this point */
} ASTChallenge;

typedef struct {
    ASTVerdict verdict;
    ProofChain original;
    char final_answer[512];
    float final_confidence;
    ASTChallenge challenges[4];
    int challenge_count;
    char judgment_reason[256];
} ASTResult;

/* API */
ASTResult ast_evaluate(ProofChain *candidate);
int ast_is_myth(const char *claim);

#endif

#ifndef PCSE_H
#define PCSE_H

#include <stdint.h>

/*
 * PCSE — Proof-Chain Synthesis Engine
 * Not "chain of thought" — chain of PROOF.
 * Every answer has a verifiable derivation chain.
 */

#define PCSE_MAX_STEPS 16
#define PCSE_MAX_AXIOMS 8

typedef enum {
    PROOF_DIRECT_LOOKUP,     /* Fact exists in KG */
    PROOF_INHERITANCE,       /* IS_A chain walk */
    PROOF_EXCEPTION,         /* Specific overrides general */
    PROOF_CAUSAL_FORWARD,    /* A→B→C */
    PROOF_CAUSAL_BACKWARD,   /* C←B←A */
    PROOF_TRANSITIVE,        /* A→B→C means A→C */
    PROOF_INVERSE,           /* parent↔child */
    PROOF_ARITHMETIC,        /* Computed from numbers */
    PROOF_SET_OPERATION,     /* count, filter, aggregate */
    PROOF_TEMPORAL,          /* before/after ordering */
    PROOF_SPATIAL,           /* near, inside, between */
    PROOF_ANALOGY,           /* X~Y, Y has Z → X probably has Z */
    PROOF_CONTRADICTION,     /* A says X, B says not-X */
    PROOF_NEGATION_ABSENCE,  /* No evidence → probably not */
    PROOF_COMPOSITION,       /* has_part chains */
    PROOF_SCALE,             /* bigger/smaller from measurements */
} ProofType;

typedef struct {
    char description[128];
    uint32_t concept_id;
    float confidence;
    ProofType type;
} ProofStep;

typedef struct {
    char answer[512];
    float confidence;
    ProofType proof_type;
    ProofStep steps[PCSE_MAX_STEPS];
    int step_count;
    int proven;              /* 1 = proven, 0 = unproven/speculative */
    char explanation[256];   /* Human-readable proof summary */
} ProofChain;

/* API */
ProofChain pcse_prove(const char *question);
ProofChain pcse_verify(const char *statement);  /* Check if statement is provably true */
const char* pcse_proof_type_name(ProofType type);
int pcse_is_proven(ProofChain *chain);

#endif

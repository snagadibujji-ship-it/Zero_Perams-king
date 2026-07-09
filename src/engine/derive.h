#ifndef DERIVE_H
#define DERIVE_H
#include "concept.h"

typedef struct {
    char answer[512];
    float confidence;
    int derivation_type;
    int hops;
    uint32_t chain[16];
    int chain_len;
} DeriveResult;

#define DERIVE_DIRECT     0
#define DERIVE_INHERIT    1
#define DERIVE_CONFLICT   2
#define DERIVE_CAUSAL     3
#define DERIVE_ANALOGY    4
#define DERIVE_COMPOSE    5
#define DERIVE_WHATIF     6
#define DERIVE_UNKNOWN    7

DeriveResult derive_answer(const char *subject, const char *predicate, const char *context);
DeriveResult derive_inheritance(uint32_t subject_id, const char *property);
DeriveResult derive_conflict(uint32_t subject_id, uint32_t context_id);
DeriveResult derive_causal(uint32_t cause_id, uint32_t effect_id, int max_hops);
DeriveResult derive_analogy(uint32_t concept_a, uint32_t concept_b);
DeriveResult derive_whatif(const char *subject, const char *change);
#endif

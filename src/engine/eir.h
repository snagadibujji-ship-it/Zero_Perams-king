#ifndef EIR_H
#define EIR_H

#include <stdint.h>

/*
 * EIR — Emergent Inference Reactor
 * 12 inference strategies that derive millions of answers from stored facts.
 * Each strategy produces new knowledge from existing relations.
 */

#define EIR_MAX_RESULTS 32
#define EIR_MAX_CHAIN   16

typedef enum {
    EIR_TRANSITIVE,        /* parent(A,B) + parent(B,C) → grandparent(A,C) */
    EIR_INVERSE,           /* capital(Paris,France) → has_capital(France,Paris) */
    EIR_INHERITANCE,       /* mammal(dog) + warm_blooded(mammal) → warm_blooded(dog) */
    EIR_ARITHMETIC,        /* born(1879) + died(1955) → lived(76 years) */
    EIR_SET_COUNT,         /* count(X where orbits(X,sun) AND planet(X)) → 8 */
    EIR_COMPARATIVE,       /* pop(India,1.4B) vs pop(USA,335M) → India bigger */
    EIR_TEMPORAL,          /* born(Newton,1643) + born(Einstein,1879) → Newton first */
    EIR_NEGATION,          /* no_record(moons_of(mercury)) → 0 moons */
    EIR_SPATIAL_COMPOSE,   /* in(Paris,France) + in(France,Europe) → Paris in Europe */
    EIR_FUNCTIONAL,        /* purpose(engine,motion) + fuel(engine,gas) → converts fuel to motion */
    EIR_STATISTICAL,       /* aggregate(GDP_per_capita, all_countries) → world average */
    EIR_CAUSAL_PROPAGATE,  /* drought→crop_fail→food_shortage→price_increase */
} EIRStrategy;

typedef struct {
    char answer[512];
    float confidence;
    EIRStrategy strategy_used;
    uint32_t chain[EIR_MAX_CHAIN];
    int chain_len;
    int hops;
} EIRResult;

typedef struct {
    uint32_t inferences_made;
    uint32_t strategy_hits[12];
    uint32_t total_queries;
} EIRStats;

/* API */
EIRResult eir_infer(const char *subject, const char *predicate, const char *object);
EIRResult eir_transitive(uint32_t start_id, uint8_t rel_type, int max_hops);
EIRResult eir_inverse(uint32_t concept_id, uint8_t rel_type);
EIRResult eir_arithmetic(uint32_t id_a, uint32_t id_b, const char *operation);
EIRResult eir_comparative(uint32_t id_a, uint32_t id_b, const char *property);
EIRResult eir_negation(uint32_t concept_id, const char *property);
EIRResult eir_spatial(uint32_t concept_id, int max_hops);
EIRResult eir_causal_propagate(uint32_t start_id, int max_hops);
void eir_stats(EIRStats *stats);

#endif

#ifndef SOKT_H
#define SOKT_H

#include <stdint.h>

/*
 * SOKT — Self-Organizing Knowledge Topology
 * Hot/warm/cold tiering based on access patterns.
 * Co-accessed concepts migrate to adjacent memory for cache locality.
 */

#define SOKT_NUCLEAR_SIZE  500    /* L1-hot concepts */
#define SOKT_PLASMA_SIZE   5000   /* L2-warm concepts */
#define SOKT_COACCESS_DIM  256    /* Co-access matrix dimension */

typedef struct {
    uint32_t concept_id;
    uint32_t access_count;
    uint32_t last_access;      /* Turn number of last access */
} SOKTEntry;

typedef struct {
    /* Tiered zones */
    SOKTEntry nuclear[SOKT_NUCLEAR_SIZE];   /* Hottest 500 */
    int nuclear_count;
    
    SOKTEntry plasma[SOKT_PLASMA_SIZE];     /* Warm 5000 */
    int plasma_count;
    
    /* Co-access tracking */
    uint8_t coaccess[SOKT_COACCESS_DIM][SOKT_COACCESS_DIM];  /* 64KB matrix */
    uint32_t coaccess_ids[SOKT_COACCESS_DIM];  /* Which concept IDs in matrix */
    int coaccess_count;
    
    /* Global turn counter */
    uint32_t current_turn;
    
    /* Prefetch hints */
    uint32_t last_accessed[4];   /* Last 4 concepts accessed (for prefetch) */
    int last_idx;
} SOKTIndex;

/* API */
void sokt_init(SOKTIndex *idx);
void sokt_record_access(SOKTIndex *idx, uint32_t concept_id);
void sokt_record_coaccess(SOKTIndex *idx, uint32_t id_a, uint32_t id_b);
int  sokt_is_nuclear(SOKTIndex *idx, uint32_t concept_id);
int  sokt_is_plasma(SOKTIndex *idx, uint32_t concept_id);
void sokt_rebalance(SOKTIndex *idx);  /* Promote/demote based on access */
void sokt_get_prefetch_hints(SOKTIndex *idx, uint32_t concept_id, uint32_t *hints, int *count);
void sokt_stats(SOKTIndex *idx);

#endif

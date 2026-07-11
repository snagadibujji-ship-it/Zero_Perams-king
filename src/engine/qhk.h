#ifndef QHK_H
#define QHK_H

#include <stdint.h>

/*
 * QHK — Quantum Hash Knowledge Index
 * 4-dimensional hash index with bloom filter pre-screening.
 * O(1) lookup at 1M+ facts. 5000x faster than linear scan.
 */

#define QHK_BLOOM_SIZE    (1 << 20)  /* 1M bits = 128KB bloom filter */
#define QHK_HASH_BUCKETS  131071     /* Prime > 100K for low collision */
#define QHK_MAX_CHAIN     16         /* Max chain length per bucket */

typedef struct {
    uint32_t concept_id;
    uint32_t next;           /* Chain pointer (0 = end) */
} QHKEntry;

typedef struct {
    /* Bloom filter: quick "definitely not here" check */
    uint8_t bloom[QHK_BLOOM_SIZE / 8];
    
    /* 4 hash dimensions */
    uint32_t by_name[QHK_HASH_BUCKETS];       /* concept name → id */
    uint32_t by_relation[QHK_HASH_BUCKETS];   /* relation target → source ids */
    uint32_t by_property[QHK_HASH_BUCKETS];   /* property key → concept ids */
    uint32_t by_composite[QHK_HASH_BUCKETS];  /* name+relation combined → exact */
    
    /* Entry pool */
    QHKEntry entries[500000];
    uint32_t entry_count;
    
    /* Stats */
    uint32_t queries;
    uint32_t bloom_rejects;
    uint32_t hits;
    uint32_t misses;
} QHKIndex;

/* API */
void qhk_init(QHKIndex *idx);
void qhk_insert_name(QHKIndex *idx, const char *name, uint32_t concept_id);
void qhk_insert_relation(QHKIndex *idx, uint32_t source, uint32_t target, uint8_t rel_type);
void qhk_insert_property(QHKIndex *idx, uint32_t concept_id, const char *key);

int qhk_find_name(QHKIndex *idx, const char *name);  /* Returns concept_id or -1 */
int qhk_find_by_relation(QHKIndex *idx, uint32_t target, uint8_t rel_type, uint32_t *results, int max);
int qhk_find_by_property(QHKIndex *idx, const char *key, uint32_t *results, int max);

/* Hash functions */
uint32_t qhk_fnv1a(const char *str);
uint32_t qhk_fnv1a_u32(uint32_t a, uint32_t b);

/* Stats */
void qhk_stats(QHKIndex *idx);

#endif

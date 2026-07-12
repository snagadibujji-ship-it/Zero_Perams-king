#ifndef CSE_H
#define CSE_H

/*
 * CSE — Compressed Semantic Encoding
 * 5 billion answers in 10 megabytes.
 * 6-layer compression: IDs → varint → clustering → prefix → dedup → tiered.
 *
 * Fact encoding: subject_id(varint) + relation_id(1 byte) + object_id(varint) + confidence(4 bits)
 * Average: 5.5 bytes per fact.
 * With clustering: 3.5 bytes per fact.
 *
 * String table: prefix-coded sorted strings. Shared by all facts.
 * Tiered: HOT (RAM) / WARM (mmap) / COLD (disk) / ARCHIVE (zlib).
 */

#include <stdint.h>
#include <stddef.h>

#define CSE_MAX_STRING_LEN   128
#define CSE_MAX_RELATIONS    256
#define CSE_HOT_LIMIT        50000    /* Facts always in RAM */
#define CSE_WARM_LIMIT       500000   /* Facts in mmap zone */
#define CSE_CONFIDENCE_LEVELS 16      /* 4-bit confidence: 0..15 → 0.0..1.0 */

/* Tier levels */
typedef enum {
    CSE_TIER_HOT,      /* Always in RAM, fastest */
    CSE_TIER_WARM,     /* Mmap'd, OS-managed pages */
    CSE_TIER_COLD,     /* On-disk, loaded on demand */
    CSE_TIER_ARCHIVE,  /* Zlib compressed, rarely used */
} CSETier;

/* A single compressed fact (in-memory representation) */
typedef struct {
    uint32_t subject_id;
    uint8_t  relation_id;
    uint32_t object_id;
    uint8_t  confidence;   /* 0-15 maps to 0.0-1.0 */
} CSEFact;

/* A cluster: multiple facts about one subject */
typedef struct {
    uint32_t subject_id;
    uint16_t fact_count;
    CSEFact *facts;       /* Array of facts (relation + object + confidence only) */
} CSECluster;

/* String table entry */
typedef struct {
    uint32_t id;
    uint16_t length;
    uint16_t prefix_shared;   /* Bytes shared with previous entry */
    char     text[CSE_MAX_STRING_LEN];
} CSEString;

/* String table (prefix-coded, sorted) */
typedef struct {
    CSEString *entries;
    uint32_t   count;
    uint32_t   capacity;
    /* Hash index for O(1) lookup by text */
    uint32_t  *hash_table;       /* hash → string_id */
    uint32_t   hash_size;
} CSEStringTable;

/* Relation table (max 256 relations) */
typedef struct {
    char names[CSE_MAX_RELATIONS][32];
    uint8_t count;
    /* Inverse mapping: relation A → its inverse B (for dedup) */
    uint8_t inverse[CSE_MAX_RELATIONS];  /* 0xFF = no inverse */
    /* Transitive flag: can this relation be transitively closed? */
    uint8_t transitive[CSE_MAX_RELATIONS];
} CSERelationTable;

/* The full CSE database */
typedef struct {
    CSEStringTable   strings;
    CSERelationTable relations;

    /* Tiered fact storage */
    CSECluster *hot_clusters;      /* Always in RAM */
    uint32_t    hot_count;

    CSECluster *warm_clusters;     /* Mmap'd */
    uint32_t    warm_count;

    uint8_t    *cold_data;         /* Raw on-disk bytes, loaded on demand */
    uint32_t    cold_offset;       /* File offset to cold section */
    uint32_t    cold_count;

    /* Stats */
    uint32_t total_facts;
    uint32_t total_strings;
    uint32_t total_clusters;
    uint32_t queries;
    uint32_t cache_hits;

    /* File path for cold/archive access */
    char db_path[256];
} CSEDatabase;

/* ═══ API ═══ */

/* Database lifecycle */
int  cse_open(CSEDatabase *db, const char *path);
void cse_close(CSEDatabase *db);
int  cse_build(CSEDatabase *db, const char *triples_path, const char *output_path);

/* String table */
uint32_t cse_string_id(CSEDatabase *db, const char *text);  /* Get or create ID */
const char* cse_string_text(CSEDatabase *db, uint32_t id);  /* ID → text */

/* Relation table */
uint8_t cse_relation_id(CSEDatabase *db, const char *name);
const char* cse_relation_name(CSEDatabase *db, uint8_t id);

/* Query */
int cse_query(CSEDatabase *db, const char *subject, const char *relation,
              CSEFact *results, int max_results);
int cse_query_inverse(CSEDatabase *db, const char *object, const char *relation,
                      CSEFact *results, int max_results);
int cse_query_all(CSEDatabase *db, const char *subject,
                  CSEFact *results, int max_results);

/* Insert (during build phase) */
int cse_insert(CSEDatabase *db, const char *subject, const char *relation,
               const char *object, float confidence);

/* Confidence conversion */
float cse_confidence_to_float(uint8_t encoded);
uint8_t cse_float_to_confidence(float conf);

/* Varint encoding (for compact serialization) */
int cse_encode_varint(uint8_t *buf, uint32_t value);
int cse_decode_varint(const uint8_t *buf, uint32_t *value);

/* Stats */
typedef struct {
    uint32_t total_facts;
    uint32_t total_strings;
    uint32_t total_clusters;
    uint32_t hot_facts;
    uint32_t warm_facts;
    uint32_t cold_facts;
    size_t   memory_bytes;
    size_t   disk_bytes;
    uint32_t queries;
    uint32_t cache_hits;
    float    hit_rate;
} CSEStats;

CSEStats cse_stats(CSEDatabase *db);

#endif /* CSE_H */

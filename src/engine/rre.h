#ifndef RRE_H
#define RRE_H

/*
 * RRE — Reverse Reasoning Engine
 * Pre-generates answerable questions from stored facts.
 * "I know what I can answer before you ask."
 */

#include <stdint.h>

#define RRE_MAX_TEMPLATES 16
#define RRE_MAX_QUESTIONS 32
#define RRE_HASH_SIZE     65536

/* A question template for a relation type */
typedef struct {
    char templates[RRE_MAX_TEMPLATES][128];  /* "What is the {rel} of {subject}?" */
    int count;
} RRETemplateSet;

/* Pre-indexed answerable question */
typedef struct {
    uint32_t question_hash;     /* Hash of normalized question */
    uint32_t subject_id;        /* Points to the fact's subject */
    uint8_t  relation_id;       /* Which relation answers this */
    uint32_t object_id;         /* The answer */
    uint8_t  confidence;        /* How confident the answer is */
} RREEntry;

/* Full RRE index */
typedef struct {
    RREEntry *entries;
    uint32_t  count;
    uint32_t  capacity;
    /* Hash table: question_hash → entry index */
    uint32_t  hash_table[RRE_HASH_SIZE];
    /* Stats */
    uint32_t  questions_indexed;
    uint32_t  lookups;
    uint32_t  hits;
} RREIndex;

/* API */
int  rre_init(RREIndex *idx, uint32_t capacity);
void rre_free(RREIndex *idx);
int  rre_index_fact(RREIndex *idx, uint32_t subj_id, uint8_t rel_id,
                    uint32_t obj_id, uint8_t confidence,
                    const char *subj_text, const char *rel_text, const char *obj_text);
int  rre_lookup(RREIndex *idx, const char *question, uint32_t *obj_id, uint8_t *confidence);
int  rre_can_answer(RREIndex *idx, const char *question);
int  rre_generate_questions(RREIndex *idx, uint32_t subj_id, char questions[][256], int max);
uint32_t rre_coverage_count(RREIndex *idx);

#endif

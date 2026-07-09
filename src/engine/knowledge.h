#ifndef KNOWLEDGE_H
#define KNOWLEDGE_H

#include <stdint.h>
#include <stddef.h>

typedef struct {
    uint32_t subject_id;
    uint16_t relation_id;
    uint32_t object_id;
    uint8_t confidence;
    uint8_t source;
    uint32_t timestamp;
} Fact;

typedef struct {
    Fact *facts;
    size_t count;
    size_t capacity;
    char **strings;
    size_t string_count;
    size_t string_capacity;
} KnowledgeGraph;

int kg_init(KnowledgeGraph *graph);
void kg_destroy(KnowledgeGraph *graph);
int kg_add_fact(KnowledgeGraph *graph, const char *subject, const char *relation, const char *object, uint8_t confidence);
int kg_query(const KnowledgeGraph *graph, const char *subject, const char *relation, Fact *results, int max_results);
const char *kg_get_string(const KnowledgeGraph *graph, uint32_t id);

#endif /* KNOWLEDGE_H */

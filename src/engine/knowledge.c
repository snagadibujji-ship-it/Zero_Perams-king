/**
 * knowledge.c - Knowledge Graph Engine
 * Implements fact storage with string interning for compact representation.
 */
#define _POSIX_C_SOURCE 200809L

#include "knowledge.h"
#include <stdlib.h>
#include <string.h>
#include <stdio.h>

#define INITIAL_FACT_CAPACITY  1024
#define INITIAL_STRING_CAPACITY 256

/* Internal: find or create a string in the intern table, return its ID */
static uint32_t kg_intern_string(KnowledgeGraph *graph, const char *str) {
    if (!str) return UINT32_MAX;

    /* Search for existing string */
    for (size_t i = 0; i < graph->string_count; i++) {
        if (strcmp(graph->strings[i], str) == 0) {
            return (uint32_t)i;
        }
    }

    /* Not found - add new string */
    if (graph->string_count >= graph->string_capacity) {
        size_t new_cap = graph->string_capacity * 2;
        char **new_strings = realloc(graph->strings, new_cap * sizeof(char *));
        if (!new_strings) return UINT32_MAX;
        graph->strings = new_strings;
        graph->string_capacity = new_cap;
    }

    graph->strings[graph->string_count] = strdup(str);
    if (!graph->strings[graph->string_count]) return UINT32_MAX;

    return (uint32_t)(graph->string_count++);
}

int kg_init(KnowledgeGraph *graph) {
    if (!graph) return -1;

    graph->facts = malloc(INITIAL_FACT_CAPACITY * sizeof(Fact));
    if (!graph->facts) return -1;

    graph->strings = malloc(INITIAL_STRING_CAPACITY * sizeof(char *));
    if (!graph->strings) {
        free(graph->facts);
        graph->facts = NULL;
        return -1;
    }

    graph->count = 0;
    graph->capacity = INITIAL_FACT_CAPACITY;
    graph->string_count = 0;
    graph->string_capacity = INITIAL_STRING_CAPACITY;

    return 0;
}

void kg_destroy(KnowledgeGraph *graph) {
    if (!graph) return;

    /* Free all interned strings */
    for (size_t i = 0; i < graph->string_count; i++) {
        free(graph->strings[i]);
    }
    free(graph->strings);
    free(graph->facts);

    graph->facts = NULL;
    graph->strings = NULL;
    graph->count = 0;
    graph->capacity = 0;
    graph->string_count = 0;
    graph->string_capacity = 0;
}

int kg_add_fact(KnowledgeGraph *graph, const char *subject,
                const char *relation, const char *object, uint8_t confidence) {
    if (!graph || !subject || !relation || !object) return -1;

    /* Intern all strings */
    uint32_t subj_id = kg_intern_string(graph, subject);
    uint32_t rel_id = kg_intern_string(graph, relation);
    uint32_t obj_id = kg_intern_string(graph, object);

    if (subj_id == UINT32_MAX || rel_id == UINT32_MAX || obj_id == UINT32_MAX) {
        return -1;
    }

    /* Grow facts array if needed */
    if (graph->count >= graph->capacity) {
        size_t new_cap = graph->capacity * 2;
        Fact *new_facts = realloc(graph->facts, new_cap * sizeof(Fact));
        if (!new_facts) return -1;
        graph->facts = new_facts;
        graph->capacity = new_cap;
    }

    /* Store the fact */
    Fact *f = &graph->facts[graph->count];
    f->subject_id = subj_id;
    f->relation_id = (uint16_t)rel_id;
    f->object_id = obj_id;
    f->confidence = confidence;
    f->source = 0;
    f->timestamp = 0;

    return (int)(graph->count++);
}

int kg_query(const KnowledgeGraph *graph, const char *subject,
             const char *relation, Fact *results, int max_results) {
    if (!graph || !results || max_results <= 0) return 0;

    /* Resolve query strings to IDs */
    uint32_t subj_id = UINT32_MAX;
    uint32_t rel_id = UINT32_MAX;

    if (subject) {
        for (size_t i = 0; i < graph->string_count; i++) {
            if (strcmp(graph->strings[i], subject) == 0) {
                subj_id = (uint32_t)i;
                break;
            }
        }
        /* Subject specified but not found - no matches possible */
        if (subj_id == UINT32_MAX) return 0;
    }

    if (relation) {
        for (size_t i = 0; i < graph->string_count; i++) {
            if (strcmp(graph->strings[i], relation) == 0) {
                rel_id = (uint32_t)i;
                break;
            }
        }
        /* Relation specified but not found - no matches possible */
        if (rel_id == UINT32_MAX) return 0;
    }

    /* Scan facts for matches */
    int found = 0;
    for (size_t i = 0; i < graph->count && found < max_results; i++) {
        const Fact *f = &graph->facts[i];
        int match = 1;

        if (subject && f->subject_id != subj_id) match = 0;
        if (relation && f->relation_id != (uint16_t)rel_id) match = 0;

        if (match) {
            results[found++] = *f;
        }
    }

    return found;
}

const char *kg_get_string(const KnowledgeGraph *graph, uint32_t id) {
    if (!graph || id >= (uint32_t)graph->string_count) return NULL;
    return graph->strings[id];
}

/* ====================================================================== */
#ifdef TEST_MODE

static void test_knowledge_graph(void) {
    KnowledgeGraph kg;
    Fact results[16];
    int rc, count;

    printf("=== Knowledge Graph Tests ===\n");

    /* Test 1: Init */
    rc = kg_init(&kg);
    printf("[%s] kg_init\n", rc == 0 ? "PASS" : "FAIL");

    /* Test 2: Add 5 facts */
    int f0 = kg_add_fact(&kg, "sun", "is_a", "star", 100);
    int f1 = kg_add_fact(&kg, "sun", "has_property", "hot", 95);
    int f2 = kg_add_fact(&kg, "earth", "is_a", "planet", 100);
    int f3 = kg_add_fact(&kg, "earth", "orbits", "sun", 100);
    int f4 = kg_add_fact(&kg, "moon", "orbits", "earth", 100);

    printf("[%s] kg_add_fact (5 facts, indices %d-%d)\n",
           (f0 == 0 && f1 == 1 && f2 == 2 && f3 == 3 && f4 == 4) ? "PASS" : "FAIL",
           f0, f4);

    /* Test 3: Query by subject "sun" → should find 2 facts */
    count = kg_query(&kg, "sun", NULL, results, 16);
    printf("[%s] query subject='sun' → %d facts (expected 2)\n",
           count == 2 ? "PASS" : "FAIL", count);

    /* Test 4: Query by subject "earth" → should find 2 facts */
    count = kg_query(&kg, "earth", NULL, results, 16);
    printf("[%s] query subject='earth' → %d facts (expected 2)\n",
           count == 2 ? "PASS" : "FAIL", count);

    /* Test 5: Query by subject+relation → specific fact */
    count = kg_query(&kg, "earth", "orbits", results, 16);
    printf("[%s] query subject='earth' relation='orbits' → %d fact (expected 1)\n",
           count == 1 ? "PASS" : "FAIL", count);
    if (count == 1) {
        const char *obj = kg_get_string(&kg, results[0].object_id);
        printf("[%s] object = '%s' (expected 'sun')\n",
               (obj && strcmp(obj, "sun") == 0) ? "PASS" : "FAIL", obj ? obj : "NULL");
    }

    /* Test 6: Query by relation only */
    count = kg_query(&kg, NULL, "orbits", results, 16);
    printf("[%s] query relation='orbits' → %d facts (expected 2)\n",
           count == 2 ? "PASS" : "FAIL", count);

    /* Test 7: Wildcard query (NULL, NULL) → all facts */
    count = kg_query(&kg, NULL, NULL, results, 16);
    printf("[%s] wildcard query → %d facts (expected 5)\n",
           count == 5 ? "PASS" : "FAIL", count);

    /* Test 8: String interning - same string gives same ID */
    uint32_t id1 = kg_intern_string(&kg, "sun");
    uint32_t id2 = kg_intern_string(&kg, "sun");
    uint32_t id3 = kg_intern_string(&kg, "earth");
    printf("[%s] string interning: sun=%u==%u, earth=%u (different)\n",
           (id1 == id2 && id1 != id3) ? "PASS" : "FAIL", id1, id2, id3);

    /* Test 9: kg_get_string */
    const char *s = kg_get_string(&kg, id1);
    printf("[%s] kg_get_string(%u) = '%s'\n",
           (s && strcmp(s, "sun") == 0) ? "PASS" : "FAIL", id1, s ? s : "NULL");

    /* Test 10: Query for non-existent subject */
    count = kg_query(&kg, "mars", NULL, results, 16);
    printf("[%s] query non-existent subject → %d (expected 0)\n",
           count == 0 ? "PASS" : "FAIL", count);

    /* Test 11: Destroy and verify no crash */
    size_t str_count_before = kg.string_count;
    size_t fact_count_before = kg.count;
    kg_destroy(&kg);
    printf("[%s] kg_destroy (freed %zu strings, %zu facts, ptrs nulled: %s)\n",
           (kg.facts == NULL && kg.strings == NULL) ? "PASS" : "FAIL",
           str_count_before, fact_count_before,
           (kg.facts == NULL && kg.strings == NULL) ? "yes" : "no");

    /* Test 12: Double-destroy safety */
    kg_destroy(&kg);
    printf("[PASS] double kg_destroy (no crash)\n");

    printf("=== All Knowledge Graph Tests Complete ===\n");
}

int main(void) {
    test_knowledge_graph();
    return 0;
}

#endif /* TEST_MODE */

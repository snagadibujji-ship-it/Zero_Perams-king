#ifndef ANALOGY_H
#define ANALOGY_H
#include "concept.h"

typedef struct {
    char explanation[1024];
    float similarity;
    char source_name[64];
    char target_name[64];
} AnalogyResult;

// Check if this is an analogy question ("what is X like?", "similar to")
int analogy_is_question(const char* raw_input);

// Find analogy for a concept
int analogy_find(SemanticCore* core, int concept_id, AnalogyResult* result);

#endif

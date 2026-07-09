#ifndef CAUSAL_H
#define CAUSAL_H
#include "concept.h"
#include "knowledge.h"
#include "parser.h"

typedef struct {
    char explanation[1024];
    float confidence;
    int chain_depth;
} CausalResult;

// Check if this is a "why" question
int causal_is_why(const ParsedIntent* intent, const char* raw);

// Answer "why" by finding causal chains
int causal_answer(SemanticCore* core, KnowledgeGraph* kg, const char* topic, CausalResult* result);

#endif

#ifndef REASON_H
#define REASON_H

#include "knowledge.h"
#include "parser.h"

typedef enum {
    REASON_DIRECT_LOOKUP,    // Found exact fact
    REASON_PATTERN_MATCH,    // Matched question pattern
    REASON_CHAIN,            // Inferred via A->B->C
    REASON_ANALOGY,          // Similar to known situation
    REASON_GAP               // Don't know, admit it
} ReasonLevel;

typedef struct {
    char answer[2048];       // The answer text
    float confidence;        // 0.0 - 1.0
    ReasonLevel level;       // Which layer produced this
    char explanation[256];   // How we got the answer
} ReasonResult;

// Main reasoning function - tries all 5 layers in order
void reason_query(KnowledgeGraph* kg, ParsedIntent* intent, ReasonResult* result);

// Individual layers (for testing)
int reason_direct_lookup(KnowledgeGraph* kg, const char* subject, const char* relation, ReasonResult* result);
int reason_pattern_match(KnowledgeGraph* kg, ParsedIntent* intent, ReasonResult* result);
int reason_chain(KnowledgeGraph* kg, const char* subject, const char* target_relation, ReasonResult* result);

#endif

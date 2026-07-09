#ifndef RESPONSE_PLAN_H
#define RESPONSE_PLAN_H

#include "concept.h"
#include "semantic.h"

#define MAX_RESPONSE_LEN 2048

typedef struct {
    char text[MAX_RESPONSE_LEN];
    int sections;          // How many info sections included
    float confidence;
} PlannedResponse;

// Generate a rich, structured response about a concept
// This is the "brain" that assembles knowledge into human-like answers
int response_plan_about(SemanticCore* core, SynonymDB* synonyms, 
                        int concept_id, PlannedResponse* resp);

// Generate response for a specific question type
int response_plan_query(SemanticCore* core, SynonymDB* synonyms,
                        int concept_id, const char* question_type, 
                        PlannedResponse* resp);

#endif

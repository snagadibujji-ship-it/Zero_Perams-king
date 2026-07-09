#ifndef NARRATIVE_FRAME_H
#define NARRATIVE_FRAME_H

#include "concept.h"

// Generate an engaging opening for "What is X?" responses
int frame_opening(SemanticCore* core, int concept_id, char* out, int maxlen);

// Generate a closing/summary sentence
int frame_closing(SemanticCore* core, int concept_id, int sections_used, char* out, int maxlen);

// Get familiarity level of a concept (1=very common, 5=obscure)
int frame_familiarity(SemanticCore* core, int concept_id);

#endif

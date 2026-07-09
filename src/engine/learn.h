#ifndef LEARN_H
#define LEARN_H

#include "knowledge.h"

#define LEARN_FILE "user_data/learned.bin"
#define MAX_TEACH_BUFFER 256

typedef struct {
    int facts_learned_session;   // Facts learned this session
    int facts_learned_total;     // All-time count
    int pending_consolidation;   // Facts in buffer not yet saved
} LearnStats;

// Initialize learning system (loads saved knowledge)
int learn_init(KnowledgeGraph* kg);

// Process a teach intent - extract and store the fact
// Returns: 1 if fact learned, 0 if couldn't parse, -1 on error
int learn_from_input(KnowledgeGraph* kg, const char* raw_input);

// Save all learned facts to disk
int learn_save(KnowledgeGraph* kg);

// Load previously learned facts from disk
int learn_load(KnowledgeGraph* kg);

// Get learning stats
LearnStats learn_get_stats(void);

#endif

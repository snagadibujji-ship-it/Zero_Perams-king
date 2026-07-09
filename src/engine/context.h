#ifndef CONTEXT_H
#define CONTEXT_H

#include <time.h>
#include "memory.h"
#include "parser.h"

#define MAX_CONTEXTS 10
#define CONTEXT_LABEL_LEN 128

typedef enum {
    CTX_ACTIVE,
    CTX_PAUSED,
    CTX_RESOLVED,
    CTX_ARCHIVED
} ContextState;

typedef struct {
    int id;
    char label[CONTEXT_LABEL_LEN];
    ContextState state;
    WorkingMemory memory;       // Each topic has its own memory
    char last_subject[256];     // What was being discussed
    time_t created_at;
    time_t last_active;
    int message_count;
} TopicContext;

typedef struct {
    TopicContext contexts[MAX_CONTEXTS];
    int count;
    int active_id;              // Currently active context
    int next_id;               // ID counter
} ContextManager;

// Initialize context manager
void context_init(ContextManager* cm);

// Detect if user switched topics (returns new context ID or -1 if same topic)
int context_detect_switch(ContextManager* cm, ParsedIntent* intent);

// Switch to a specific context
void context_switch(ContextManager* cm, int context_id);

// Get active context
TopicContext* context_get_active(ContextManager* cm);

// Create new context
int context_create(ContextManager* cm, const char* label);

// List all contexts (format into buffer)
void context_list(ContextManager* cm, char* buffer, size_t buflen);

// Get memory for active context
WorkingMemory* context_get_memory(ContextManager* cm);

#endif

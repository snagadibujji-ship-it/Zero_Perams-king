#ifndef MEMORY_H
#define MEMORY_H

#include <stdint.h>
#include <stddef.h>

typedef enum {
    ROLE_USER,
    ROLE_AI
} MemoryRole;

typedef struct {
    MemoryRole role;
    char content[1024];
    uint32_t timestamp;
} MemoryEntry;

typedef struct {
    MemoryEntry entries[50];
    int count;
    int current_topic_id;
    char topic_label[256];
} WorkingMemory;

void memory_init(WorkingMemory *mem);
int memory_add(WorkingMemory *mem, MemoryRole role, const char *content);
int memory_get_context(const WorkingMemory *mem, char *buffer, size_t max_len);
void memory_clear(WorkingMemory *mem);

#endif /* MEMORY_H */

#include "memory.h"
#include <string.h>
#include <stdio.h>
#include <time.h>

#define MAX_ENTRIES 50

void memory_init(WorkingMemory *mem) {
    memset(mem, 0, sizeof(WorkingMemory));
    mem->count = 0;
}

int memory_add(WorkingMemory *mem, MemoryRole role, const char *content) {
    if (!mem || !content) return -1;

    if (mem->count >= MAX_ENTRIES) {
        /* Shift everything left, drop oldest */
        memmove(&mem->entries[0], &mem->entries[1],
                (MAX_ENTRIES - 1) * sizeof(MemoryEntry));
        mem->count = MAX_ENTRIES - 1;
    }

    MemoryEntry *e = &mem->entries[mem->count];
    e->role = role;
    strncpy(e->content, content, sizeof(e->content) - 1);
    e->content[sizeof(e->content) - 1] = '\0';
    e->timestamp = (uint32_t)time(NULL);
    mem->count++;
    return 0;
}

int memory_get_context(const WorkingMemory *mem, char *buffer, size_t max_len) {
    if (!mem || !buffer || max_len == 0) return 0;

    buffer[0] = '\0';
    int written = 0;

    for (int i = 0; i < mem->count; i++) {
        const char *prefix = (mem->entries[i].role == ROLE_USER) ? "User" : "AI";
        int n = snprintf(buffer + written, max_len - written,
                         "%s: %s\n", prefix, mem->entries[i].content);
        if (n < 0 || (size_t)(written + n) >= max_len) break;
        written += n;
    }
    return written;
}

void memory_clear(WorkingMemory *mem) {
    if (mem) mem->count = 0;
}

/* ─── TEST MODE ─── */
#ifdef TEST_MODE
#include <assert.h>

int main(void) {
    WorkingMemory mem;
    char buf[8192];
    int ret;

    printf("=== Memory Tests ===\n");

    /* Test 1: init and add 3 entries */
    memory_init(&mem);
    assert(mem.count == 0);

    memory_add(&mem, ROLE_USER, "Hello");
    memory_add(&mem, ROLE_AI, "Hi there!");
    memory_add(&mem, ROLE_USER, "How are you?");
    assert(mem.count == 3);
    printf("[PASS] Add 3 entries, count=%d\n", mem.count);

    /* Test 2: get context, verify format */
    ret = memory_get_context(&mem, buf, sizeof(buf));
    assert(ret > 0);
    assert(strstr(buf, "User: Hello\n") != NULL);
    assert(strstr(buf, "AI: Hi there!\n") != NULL);
    assert(strstr(buf, "User: How are you?\n") != NULL);
    printf("[PASS] Context format correct (%d bytes)\n", ret);

    /* Test 3: add 55 entries, count stays at 50 */
    memory_init(&mem);
    for (int i = 0; i < 55; i++) {
        char msg[64];
        snprintf(msg, sizeof(msg), "Message %d", i);
        memory_add(&mem, (i % 2 == 0) ? ROLE_USER : ROLE_AI, msg);
    }
    assert(mem.count == MAX_ENTRIES);
    /* Verify oldest were dropped: first entry should be "Message 5" */
    assert(strstr(mem.entries[0].content, "Message 5") != NULL);
    printf("[PASS] Overflow handled, count=%d, oldest dropped\n", mem.count);

    /* Test 4: clear */
    memory_clear(&mem);
    assert(mem.count == 0);
    printf("[PASS] Clear, count=%d\n", mem.count);

    printf("=== All memory tests passed! ===\n");
    return 0;
}
#endif

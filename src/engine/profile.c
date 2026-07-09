#define _POSIX_C_SOURCE 200809L
#include "profile.h"
#include <stdio.h>
#include <string.h>

static Profiler g_profiler;

void profiler_init(void) {
    memset(&g_profiler, 0, sizeof(Profiler));
}

struct timespec profiler_start(void) {
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return ts;
}

void profiler_stop(const char* name, struct timespec start) {
    struct timespec end;
    clock_gettime(CLOCK_MONOTONIC, &end);

    double elapsed_ms = (end.tv_sec - start.tv_sec) * 1000.0
                      + (end.tv_nsec - start.tv_nsec) / 1000000.0;

    /* Find existing entry */
    ProfileEntry* entry = NULL;
    for (int i = 0; i < g_profiler.count; i++) {
        if (strcmp(g_profiler.entries[i].name, name) == 0) {
            entry = &g_profiler.entries[i];
            break;
        }
    }

    /* Create new entry if not found */
    if (!entry) {
        if (g_profiler.count >= MAX_PROFILE_ENTRIES) return;
        entry = &g_profiler.entries[g_profiler.count++];
        entry->name = name;
        entry->total_ms = 0.0;
        entry->call_count = 0;
        entry->min_ms = elapsed_ms;
        entry->max_ms = elapsed_ms;
    }

    entry->total_ms += elapsed_ms;
    entry->call_count++;
    if (elapsed_ms < entry->min_ms) entry->min_ms = elapsed_ms;
    if (elapsed_ms > entry->max_ms) entry->max_ms = elapsed_ms;
}

void profiler_report(char* buffer, size_t buflen) {
    int offset = 0;
    offset += snprintf(buffer + offset, buflen - offset,
        "  %-20s %-8s %-10s %-8s %-8s %-8s\n",
        "Function", "Calls", "Total(ms)", "Avg(ms)", "Min(ms)", "Max(ms)");

    for (int i = 0; i < g_profiler.count && (size_t)offset < buflen - 1; i++) {
        ProfileEntry* e = &g_profiler.entries[i];
        double avg = e->call_count > 0 ? e->total_ms / e->call_count : 0.0;
        offset += snprintf(buffer + offset, buflen - offset,
            "  %-20s %-8d %-10.2f %-8.3f %-8.3f %-8.3f\n",
            e->name, e->call_count, e->total_ms, avg, e->min_ms, e->max_ms);
    }
}

void profiler_reset(void) {
    g_profiler.count = 0;
    memset(g_profiler.entries, 0, sizeof(g_profiler.entries));
}

/* ===== TEST_MODE ===== */
#ifdef TEST_MODE
#include <assert.h>
#include <unistd.h>

static void busy_wait_us(int us) {
    struct timespec start, now;
    clock_gettime(CLOCK_MONOTONIC, &start);
    do {
        clock_gettime(CLOCK_MONOTONIC, &now);
    } while ((now.tv_sec - start.tv_sec) * 1000000 +
             (now.tv_nsec - start.tv_nsec) / 1000 < us);
}

int main(void) {
    profiler_init();

    /* Test basic timing */
    for (int i = 0; i < 5; i++) {
        struct timespec t = profiler_start();
        busy_wait_us(100); /* ~0.1ms */
        profiler_stop("test_func", t);
    }

    assert(g_profiler.count == 1);
    assert(g_profiler.entries[0].call_count == 5);
    assert(g_profiler.entries[0].total_ms > 0.0);
    assert(g_profiler.entries[0].min_ms <= g_profiler.entries[0].max_ms);
    assert(g_profiler.entries[0].min_ms > 0.0);

    /* Test multiple entries */
    struct timespec t2 = profiler_start();
    busy_wait_us(200);
    profiler_stop("other_func", t2);

    assert(g_profiler.count == 2);

    /* Test report */
    char buf[1024];
    profiler_report(buf, sizeof(buf));
    assert(strstr(buf, "test_func") != NULL);
    assert(strstr(buf, "other_func") != NULL);

    /* Test reset */
    profiler_reset();
    assert(g_profiler.count == 0);

    printf("All profiler tests passed!\n");
    profiler_report(buf, sizeof(buf));
    printf("%s", buf);
    return 0;
}
#endif

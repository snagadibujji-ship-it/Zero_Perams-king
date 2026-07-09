#ifndef PROFILE_H
#define PROFILE_H

#include <time.h>

#define MAX_PROFILE_ENTRIES 32

typedef struct {
    const char* name;
    double total_ms;
    int call_count;
    double min_ms;
    double max_ms;
} ProfileEntry;

typedef struct {
    ProfileEntry entries[MAX_PROFILE_ENTRIES];
    int count;
} Profiler;

// Initialize profiler
void profiler_init(void);

// Start timing a section (returns a timespec to pass to stop)
struct timespec profiler_start(void);

// Stop timing and record under given name
void profiler_stop(const char* name, struct timespec start);

// Get profiler report as formatted string
void profiler_report(char* buffer, size_t buflen);

// Reset all counters
void profiler_reset(void);

#endif

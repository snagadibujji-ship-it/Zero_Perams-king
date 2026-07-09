#ifndef GAP_TRACKER_H
#define GAP_TRACKER_H

#include <time.h>

#define MAX_GAPS 256
#define GAP_TOPIC_LEN 128
#define GAP_FILE "user_data/gaps.dat"

typedef struct {
    char topic[GAP_TOPIC_LEN];
    int times_asked;
    int times_failed;
    float gap_score;
    time_t first_seen;
    time_t last_seen;
    int filled;
} KnowledgeGap;

typedef struct {
    KnowledgeGap gaps[MAX_GAPS];
    int count;
} GapTracker;

void gap_init(void);
void gap_track(const char *topic);
int gap_get_top(int n, KnowledgeGap *out);
void gap_clear(const char *topic);
int gap_save(void);
int gap_load(void);
int gap_count(void);

#endif

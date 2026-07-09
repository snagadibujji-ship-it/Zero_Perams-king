#ifndef PROACTIVE_H
#define PROACTIVE_H

#define MAX_TRACKED_TOPICS 64
#define PROACTIVE_TOPIC_LEN 128
#define PROACTIVE_SUGGESTION_LEN 512

typedef struct {
    char topic[PROACTIVE_TOPIC_LEN];
    int ask_count;
    int fail_count;
    int consecutive_fails;
} TrackedTopic;

typedef struct {
    TrackedTopic topics[MAX_TRACKED_TOPICS];
    int count;
    int total_consecutive_fails;
    int deadline_detected;
} ProactiveState;

void proactive_init(void);
void proactive_record_ask(const char *topic);
void proactive_record_fail(const char *topic);
void proactive_record_success(void);
void proactive_check_deadline(const char *input);
const char *proactive_check(void);

#endif

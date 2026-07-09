#ifndef PERSISTENT_CTX_H
#define PERSISTENT_CTX_H

#include <time.h>

#define PCTX_MAX_TOPICS 64
#define PCTX_TOPIC_LEN 128
#define PCTX_FILE "user_data/session.dat"

typedef struct {
    char topic[PCTX_TOPIC_LEN];
    time_t timestamp;
    int visit_count;
} SessionTopic;

typedef struct {
    SessionTopic topics[PCTX_MAX_TOPICS];
    int count;
    time_t session_start;
    time_t last_save;
} PersistentContext;

void ctx_persistent_init(void);
void ctx_save_topic(const char *topic);
int ctx_get_last_topics(int n, SessionTopic *out);
int ctx_save_session(void);
int ctx_load_session(void);
int ctx_topic_count(void);

#endif

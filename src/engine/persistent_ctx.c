/**
 * persistent_ctx.c - Phase 15: Persistent Session Context
 */
#define _POSIX_C_SOURCE 200809L

#include "persistent_ctx.h"
#include <stdio.h>
#include <string.h>
#include <strings.h>
#include <sys/stat.h>

static PersistentContext g_pctx = { .count = 0 };

static void ensure_dir(const char *path) {
    struct stat st;
    if (stat(path, &st) != 0) mkdir(path, 0755);
}

void ctx_persistent_init(void) {
    memset(&g_pctx, 0, sizeof(g_pctx));
    g_pctx.session_start = time(NULL);
    ensure_dir("user_data");
    ctx_load_session();
}

void ctx_save_topic(const char *topic) {
    if (!topic || !topic[0]) return;

    /* Check if topic already exists */
    for (int i = 0; i < g_pctx.count; i++) {
        if (strcasecmp(g_pctx.topics[i].topic, topic) == 0) {
            g_pctx.topics[i].timestamp = time(NULL);
            g_pctx.topics[i].visit_count++;
            ctx_save_session();
            return;
        }
    }

    /* Add new topic */
    if (g_pctx.count >= PCTX_MAX_TOPICS) {
        /* Shift out oldest */
        memmove(&g_pctx.topics[0], &g_pctx.topics[1],
                (size_t)(PCTX_MAX_TOPICS - 1) * sizeof(SessionTopic));
        g_pctx.count--;
    }
    int idx = g_pctx.count++;
    memset(&g_pctx.topics[idx], 0, sizeof(SessionTopic));
    strncpy(g_pctx.topics[idx].topic, topic, PCTX_TOPIC_LEN - 1);
    g_pctx.topics[idx].timestamp = time(NULL);
    g_pctx.topics[idx].visit_count = 1;
    ctx_save_session();
}

int ctx_get_last_topics(int n, SessionTopic *out) {
    if (!out || n <= 0) return 0;
    int start = g_pctx.count - n;
    if (start < 0) start = 0;
    int result = g_pctx.count - start;
    memcpy(out, &g_pctx.topics[start], (size_t)result * sizeof(SessionTopic));
    return result;
}

int ctx_save_session(void) {
    ensure_dir("user_data");
    FILE *f = fopen(PCTX_FILE, "wb");
    if (!f) return -1;
    g_pctx.last_save = time(NULL);
    fwrite(&g_pctx.count, sizeof(int), 1, f);
    fwrite(&g_pctx.session_start, sizeof(time_t), 1, f);
    fwrite(g_pctx.topics, sizeof(SessionTopic), (size_t)g_pctx.count, f);
    fclose(f);
    return 0;
}

int ctx_load_session(void) {
    FILE *f = fopen(PCTX_FILE, "rb");
    if (!f) return -1;
    if (fread(&g_pctx.count, sizeof(int), 1, f) != 1) { fclose(f); return -1; }
    if (g_pctx.count < 0 || g_pctx.count > PCTX_MAX_TOPICS) {
        g_pctx.count = 0; fclose(f); return -1;
    }
    if (fread(&g_pctx.session_start, sizeof(time_t), 1, f) != 1) {
        g_pctx.count = 0; fclose(f); return -1;
    }
    if (fread(g_pctx.topics, sizeof(SessionTopic), (size_t)g_pctx.count, f) != (size_t)g_pctx.count) {
        g_pctx.count = 0; fclose(f); return -1;
    }
    fclose(f);
    return g_pctx.count;
}

int ctx_topic_count(void) { return g_pctx.count; }

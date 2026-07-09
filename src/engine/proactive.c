/**
 * proactive.c - Phase 14: Proactive Suggestions
 */
#define _POSIX_C_SOURCE 200809L

#include "proactive.h"
#include <stdio.h>
#include <string.h>
#include <strings.h>
#include <ctype.h>

static ProactiveState g_proactive = { .count = 0 };
static char g_suggestion[PROACTIVE_SUGGESTION_LEN];

static int str_contains_ci(const char *haystack, const char *needle) {
    if (!haystack || !needle) return 0;
    size_t hlen = strlen(haystack);
    size_t nlen = strlen(needle);
    if (nlen > hlen) return 0;
    for (size_t i = 0; i <= hlen - nlen; i++) {
        int match = 1;
        for (size_t j = 0; j < nlen; j++) {
            if (tolower((unsigned char)haystack[i+j]) != tolower((unsigned char)needle[j])) {
                match = 0; break;
            }
        }
        if (match) return 1;
    }
    return 0;
}

void proactive_init(void) {
    memset(&g_proactive, 0, sizeof(g_proactive));
}

static int find_topic(const char *topic) {
    for (int i = 0; i < g_proactive.count; i++) {
        if (strcasecmp(g_proactive.topics[i].topic, topic) == 0) return i;
    }
    return -1;
}

void proactive_record_ask(const char *topic) {
    if (!topic || !topic[0]) return;
    int idx = find_topic(topic);
    if (idx >= 0) {
        g_proactive.topics[idx].ask_count++;
    } else if (g_proactive.count < MAX_TRACKED_TOPICS) {
        idx = g_proactive.count++;
        memset(&g_proactive.topics[idx], 0, sizeof(TrackedTopic));
        strncpy(g_proactive.topics[idx].topic, topic, PROACTIVE_TOPIC_LEN - 1);
        g_proactive.topics[idx].ask_count = 1;
    }
}

void proactive_record_fail(const char *topic) {
    if (!topic || !topic[0]) return;
    g_proactive.total_consecutive_fails++;
    int idx = find_topic(topic);
    if (idx >= 0) {
        g_proactive.topics[idx].fail_count++;
        g_proactive.topics[idx].consecutive_fails++;
    } else {
        proactive_record_ask(topic);
        idx = find_topic(topic);
        if (idx >= 0) {
            g_proactive.topics[idx].fail_count = 1;
            g_proactive.topics[idx].consecutive_fails = 1;
        }
    }
}

void proactive_record_success(void) {
    g_proactive.total_consecutive_fails = 0;
    for (int i = 0; i < g_proactive.count; i++)
        g_proactive.topics[i].consecutive_fails = 0;
}

void proactive_check_deadline(const char *input) {
    static const char *deadline_words[] = {
        "deadline", "due", "urgent", "asap", "by tomorrow",
        "by friday", "by monday", "end of day", "eod", NULL
    };
    for (int i = 0; deadline_words[i]; i++) {
        if (str_contains_ci(input, deadline_words[i])) {
            g_proactive.deadline_detected = 1;
            return;
        }
    }
}

const char *proactive_check(void) {
    g_suggestion[0] = '\0';
    if (g_proactive.total_consecutive_fails >= 3) {
        snprintf(g_suggestion, sizeof(g_suggestion),
            "[Suggestion] I've struggled with the last %d questions. "
            "Try rephrasing, or enable /autosearch.",
            g_proactive.total_consecutive_fails);
        return g_suggestion;
    }
    for (int i = 0; i < g_proactive.count; i++) {
        if (g_proactive.topics[i].ask_count >= 5) {
            snprintf(g_suggestion, sizeof(g_suggestion),
                "[Suggestion] You've asked about '%s' %d times. "
                "Want me to do a deep web search?",
                g_proactive.topics[i].topic, g_proactive.topics[i].ask_count);
            return g_suggestion;
        }
    }
    if (g_proactive.deadline_detected) {
        snprintf(g_suggestion, sizeof(g_suggestion),
            "[Suggestion] Deadline detected! Enable /workspace focus to stay on track.");
        g_proactive.deadline_detected = 0;
        return g_suggestion;
    }
    return NULL;
}

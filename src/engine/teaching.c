/**
 * teaching.c - Phase 17: Socratic Teaching & Spaced Repetition
 */
#define _POSIX_C_SOURCE 200809L

#include "teaching.h"
#include <stdio.h>
#include <string.h>
#include <strings.h>
#include <stdlib.h>

static TeachingEngine g_teach = { .count = 0, .socratic_mode = 0 };
static char g_teach_buf[TEACH_QUESTION_LEN];

void teaching_init(void) {
    memset(&g_teach, 0, sizeof(g_teach));
}

void teaching_set_socratic(int enabled) {
    g_teach.socratic_mode = enabled;
}

int teaching_is_socratic(void) {
    return g_teach.socratic_mode;
}

const char *teach_mode_response(const char *question) {
    if (!question || !question[0]) return NULL;
    g_teach_buf[0] = '\0';

    /* Generate a Socratic guiding question based on the input */
    if (strstr(question, "what is") || strstr(question, "What is")) {
        snprintf(g_teach_buf, sizeof(g_teach_buf),
            "Good question! Before I tell you, what do you already know about this topic? "
            "What comes to mind when you think about it?");
    } else if (strstr(question, "how") || strstr(question, "How")) {
        snprintf(g_teach_buf, sizeof(g_teach_buf),
            "Let's think through this step by step. "
            "What do you think the first step might be? What would need to happen?");
    } else if (strstr(question, "why") || strstr(question, "Why")) {
        snprintf(g_teach_buf, sizeof(g_teach_buf),
            "That's a deep question. Can you think of what might cause this? "
            "What factors could be involved?");
    } else {
        snprintf(g_teach_buf, sizeof(g_teach_buf),
            "Interesting! What's your current understanding of this? "
            "Let's build from what you already know.");
    }
    return g_teach_buf;
}

static int find_card(const char *concept) {
    for (int i = 0; i < g_teach.count; i++) {
        if (strcasecmp(g_teach.cards[i].concept, concept) == 0) return i;
    }
    return -1;
}

void teach_add_card(const char *concept) {
    if (!concept || !concept[0]) return;
    if (find_card(concept) >= 0) return; /* Already exists */
    if (g_teach.count >= TEACH_MAX_CARDS) return;

    int idx = g_teach.count++;
    memset(&g_teach.cards[idx], 0, sizeof(SpacedRepCard));
    strncpy(g_teach.cards[idx].concept, concept, TEACH_CONCEPT_LEN - 1);
    g_teach.cards[idx].ease = 2.5f;
    g_teach.cards[idx].interval_days = 1;
    g_teach.cards[idx].last_tested = time(NULL);
    g_teach.cards[idx].repetitions = 0;
}

const char *teach_quiz(const char *topic) {
    if (!topic || !topic[0]) {
        /* Pick a due card */
        time_t now = time(NULL);
        for (int i = 0; i < g_teach.count; i++) {
            double days_since = difftime(now, g_teach.cards[i].last_tested) / 86400.0;
            if (days_since >= g_teach.cards[i].interval_days) {
                snprintf(g_teach_buf, sizeof(g_teach_buf),
                    "Quiz: What can you tell me about '%s'?", g_teach.cards[i].concept);
                return g_teach_buf;
            }
        }
        return "No cards due for review right now!";
    }

    /* Quiz on specific topic */
    snprintf(g_teach_buf, sizeof(g_teach_buf),
        "Quiz: Explain '%s' in your own words. What is it, and why does it matter?", topic);
    teach_add_card(topic);
    return g_teach_buf;
}

int teach_review_due(void) {
    time_t now = time(NULL);
    int due = 0;
    for (int i = 0; i < g_teach.count; i++) {
        double days_since = difftime(now, g_teach.cards[i].last_tested) / 86400.0;
        if (days_since >= g_teach.cards[i].interval_days) due++;
    }
    return due;
}

void teach_record_result(const char *concept, int correct) {
    int idx = find_card(concept);
    if (idx < 0) {
        teach_add_card(concept);
        idx = find_card(concept);
        if (idx < 0) return;
    }

    g_teach.cards[idx].last_tested = time(NULL);
    g_teach.cards[idx].repetitions++;

    if (correct) {
        /* SM-2 algorithm simplified */
        g_teach.cards[idx].ease += 0.1f;
        if (g_teach.cards[idx].ease > 3.0f) g_teach.cards[idx].ease = 3.0f;
        g_teach.cards[idx].interval_days = (int)(g_teach.cards[idx].interval_days * g_teach.cards[idx].ease);
        if (g_teach.cards[idx].interval_days > 365) g_teach.cards[idx].interval_days = 365;
    } else {
        g_teach.cards[idx].ease -= 0.2f;
        if (g_teach.cards[idx].ease < 1.3f) g_teach.cards[idx].ease = 1.3f;
        g_teach.cards[idx].interval_days = 1;
    }
}

/**
 * gap_tracker.c - Phase 8: Self-Improvement via Knowledge Gap Tracking
 */
#define _POSIX_C_SOURCE 200809L

#include "gap_tracker.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <strings.h>
#include <sys/stat.h>

static GapTracker g_gaps = { .count = 0 };

static void ensure_dir(const char *path) {
    struct stat st;
    if (stat(path, &st) != 0) mkdir(path, 0755);
}

void gap_init(void) {
    memset(&g_gaps, 0, sizeof(g_gaps));
    ensure_dir("user_data");
    gap_load();
}

static int find_gap(const char *topic) {
    for (int i = 0; i < g_gaps.count; i++) {
        if (strcasecmp(g_gaps.gaps[i].topic, topic) == 0) return i;
    }
    return -1;
}

void gap_track(const char *topic) {
    if (!topic || !topic[0]) return;
    int idx = find_gap(topic);
    if (idx >= 0) {
        g_gaps.gaps[idx].times_asked++;
        g_gaps.gaps[idx].times_failed++;
        g_gaps.gaps[idx].last_seen = time(NULL);
        double age_hours = difftime(time(NULL), g_gaps.gaps[idx].first_seen) / 3600.0;
        if (age_hours < 1.0) age_hours = 1.0;
        g_gaps.gaps[idx].gap_score = (float)(g_gaps.gaps[idx].times_failed * 10.0 / age_hours)
                                   + (float)(g_gaps.gaps[idx].times_asked * 2.0);
    } else {
        if (g_gaps.count >= MAX_GAPS) {
            int min_idx = 0;
            float min_score = g_gaps.gaps[0].gap_score;
            for (int i = 1; i < g_gaps.count; i++) {
                if (g_gaps.gaps[i].gap_score < min_score) {
                    min_score = g_gaps.gaps[i].gap_score;
                    min_idx = i;
                }
            }
            idx = min_idx;
        } else {
            idx = g_gaps.count++;
        }
        memset(&g_gaps.gaps[idx], 0, sizeof(KnowledgeGap));
        strncpy(g_gaps.gaps[idx].topic, topic, GAP_TOPIC_LEN - 1);
        g_gaps.gaps[idx].times_asked = 1;
        g_gaps.gaps[idx].times_failed = 1;
        g_gaps.gaps[idx].gap_score = 10.0f;
        g_gaps.gaps[idx].first_seen = time(NULL);
        g_gaps.gaps[idx].last_seen = time(NULL);
    }
    gap_save();
}

static int cmp_gap_score(const void *a, const void *b) {
    const KnowledgeGap *ga = (const KnowledgeGap *)a;
    const KnowledgeGap *gb = (const KnowledgeGap *)b;
    if (gb->gap_score > ga->gap_score) return 1;
    if (gb->gap_score < ga->gap_score) return -1;
    return 0;
}

int gap_get_top(int n, KnowledgeGap *out) {
    if (!out || n <= 0) return 0;
    KnowledgeGap active[MAX_GAPS];
    int active_count = 0;
    for (int i = 0; i < g_gaps.count; i++) {
        if (!g_gaps.gaps[i].filled) active[active_count++] = g_gaps.gaps[i];
    }
    qsort(active, (size_t)active_count, sizeof(KnowledgeGap), cmp_gap_score);
    int result_count = active_count < n ? active_count : n;
    memcpy(out, active, (size_t)result_count * sizeof(KnowledgeGap));
    return result_count;
}

void gap_clear(const char *topic) {
    int idx = find_gap(topic);
    if (idx >= 0) {
        g_gaps.gaps[idx].filled = 1;
        g_gaps.gaps[idx].gap_score = 0.0f;
        gap_save();
    }
}

int gap_save(void) {
    ensure_dir("user_data");
    FILE *f = fopen(GAP_FILE, "wb");
    if (!f) return -1;
    fwrite(&g_gaps.count, sizeof(int), 1, f);
    fwrite(g_gaps.gaps, sizeof(KnowledgeGap), (size_t)g_gaps.count, f);
    fclose(f);
    return 0;
}

int gap_load(void) {
    FILE *f = fopen(GAP_FILE, "rb");
    if (!f) return -1;
    if (fread(&g_gaps.count, sizeof(int), 1, f) != 1) { fclose(f); return -1; }
    if (g_gaps.count < 0 || g_gaps.count > MAX_GAPS) { g_gaps.count = 0; fclose(f); return -1; }
    if (fread(g_gaps.gaps, sizeof(KnowledgeGap), (size_t)g_gaps.count, f) != (size_t)g_gaps.count) {
        g_gaps.count = 0; fclose(f); return -1;
    }
    fclose(f);
    return g_gaps.count;
}

int gap_count(void) {
    int active = 0;
    for (int i = 0; i < g_gaps.count; i++) {
        if (!g_gaps.gaps[i].filled) active++;
    }
    return active;
}

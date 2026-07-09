/**
 * workflow.c - Phase 22: Workflow Automation Engine
 */
#define _POSIX_C_SOURCE 200809L

#include "workflow.h"
#include <stdio.h>
#include <string.h>
#include <strings.h>
#include <stdlib.h>
#include <ctype.h>
#include <time.h>

static WorkflowEngine g_wf = { .count = 0 };
static char g_wf_result[WF_OUTPUT_LEN];

/* Forward declaration */
int workflow_execute(Workflow *wf, char *output, size_t max_len);

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

void workflow_init(void) {
    memset(&g_wf, 0, sizeof(g_wf));
}

int workflow_create(const char *name, WorkflowTriggerType trig_type,
                   const char *trig_value, WorkflowActionType act_type,
                   const char *act_value) {
    if (!name || !trig_value || !act_value) return -1;
    if (g_wf.count >= WF_MAX_WORKFLOWS) return -1;

    Workflow *w = &g_wf.workflows[g_wf.count];
    memset(w, 0, sizeof(Workflow));
    strncpy(w->name, name, WF_NAME_LEN - 1);
    w->trigger_type = trig_type;
    strncpy(w->trigger_value, trig_value, WF_VALUE_LEN - 1);
    w->action_type = act_type;
    strncpy(w->action_value, act_value, WF_VALUE_LEN - 1);
    w->enabled = 1;
    w->fire_count = 0;
    g_wf.count++;
    return g_wf.count - 1;
}

int workflow_remove(const char *name) {
    for (int i = 0; i < g_wf.count; i++) {
        if (strcasecmp(g_wf.workflows[i].name, name) == 0) {
            memmove(&g_wf.workflows[i], &g_wf.workflows[i+1],
                    (size_t)(g_wf.count - i - 1) * sizeof(Workflow));
            g_wf.count--;
            return 0;
        }
    }
    return -1;
}

void workflow_enable(const char *name, int enabled) {
    for (int i = 0; i < g_wf.count; i++) {
        if (strcasecmp(g_wf.workflows[i].name, name) == 0) {
            g_wf.workflows[i].enabled = enabled;
            return;
        }
    }
}

const char *workflow_check_triggers(const char *input) {
    g_wf_result[0] = '\0';
    for (int i = 0; i < g_wf.count; i++) {
        Workflow *w = &g_wf.workflows[i];
        if (!w->enabled) continue;

        int triggered = 0;
        switch (w->trigger_type) {
            case WF_TRIG_KEYWORD:
                if (input && str_contains_ci(input, w->trigger_value))
                    triggered = 1;
                break;
            case WF_TRIG_TIME: {
                time_t now = time(NULL);
                struct tm *tm = localtime(&now);
                int hour = atoi(w->trigger_value);
                if (tm->tm_hour == hour) triggered = 1;
                break;
            }
            case WF_TRIG_CONDITION:
                /* Simple condition: check if file exists */
                if (w->trigger_value[0] == '/') {
                    FILE *f = fopen(w->trigger_value, "r");
                    if (f) { fclose(f); triggered = 1; }
                }
                break;
        }

        if (triggered) {
            char out[WF_OUTPUT_LEN];
            workflow_execute(w, out, sizeof(out));
            snprintf(g_wf_result, sizeof(g_wf_result),
                "[Workflow '%s' fired] %s", w->name, out);
            return g_wf_result;
        }
    }
    return NULL;
}

int workflow_execute(Workflow *wf, char *output, size_t max_len) {
    if (!wf || !output) return -1;
    output[0] = '\0';
    wf->fire_count++;

    switch (wf->action_type) {
        case WF_ACT_SHELL: {
            FILE *p = popen(wf->action_value, "r");
            if (!p) { snprintf(output, max_len, "Failed to run: %s", wf->action_value); return -1; }
            size_t total = 0;
            char buf[256];
            while (fgets(buf, sizeof(buf), p) && total < max_len - 1) {
                size_t len = strlen(buf);
                if (total + len >= max_len) break;
                memcpy(output + total, buf, len);
                total += len;
            }
            output[total] = '\0';
            pclose(p);
            return 0;
        }
        case WF_ACT_NOTIFY:
            snprintf(output, max_len, "[NOTIFY] %s", wf->action_value);
            return 0;
        case WF_ACT_SEARCH:
            snprintf(output, max_len, "[SEARCH] Would search for: %s", wf->action_value);
            return 0;
    }
    return -1;
}

int workflow_count(void) { return g_wf.count; }

int workflow_list(char *output, size_t max_len) {
    size_t off = 0;
    for (int i = 0; i < g_wf.count && off < max_len - 100; i++) {
        Workflow *w = &g_wf.workflows[i];
        off += (size_t)snprintf(output + off, max_len - off,
            "  [%s] %s -> %s (fired %d times)\n",
            w->enabled ? "ON" : "OFF", w->name, w->action_value, w->fire_count);
    }
    return (int)off;
}

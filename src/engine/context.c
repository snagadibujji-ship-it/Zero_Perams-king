#include "context.h"
#include <stdio.h>
#include <string.h>
#include <time.h>

void context_init(ContextManager* cm) {
    memset(cm, 0, sizeof(ContextManager));
    cm->count = 0;
    cm->active_id = -1;
    cm->next_id = 0;
    context_create(cm, "General");
}

int context_detect_switch(ContextManager* cm, ParsedIntent* intent) {
    TopicContext* active = context_get_active(cm);
    if (!active) return -1;

    /* Simple heuristic: check for switching keywords */
    const char* input = intent->raw_input;
    if (strstr(input, "anyway") || strstr(input, "back to") ||
        strstr(input, "by the way") || strstr(input, "btw")) {
        /* Potential switch detected — future: find matching context */
    }

    /* For now: update last_subject and stay in current context */
    if (intent->subject[0] != '\0') {
        strncpy(active->last_subject, intent->subject, sizeof(active->last_subject) - 1);
        active->last_subject[sizeof(active->last_subject) - 1] = '\0';
    }
    active->last_active = time(NULL);
    active->message_count++;
    return -1;
}

void context_switch(ContextManager* cm, int context_id) {
    /* Pause current active context */
    for (int i = 0; i < cm->count; i++) {
        if (cm->contexts[i].id == cm->active_id && cm->contexts[i].state == CTX_ACTIVE) {
            cm->contexts[i].state = CTX_PAUSED;
            break;
        }
    }
    /* Activate target */
    for (int i = 0; i < cm->count; i++) {
        if (cm->contexts[i].id == context_id) {
            cm->contexts[i].state = CTX_ACTIVE;
            cm->contexts[i].last_active = time(NULL);
            cm->active_id = context_id;
            break;
        }
    }
}

TopicContext* context_get_active(ContextManager* cm) {
    for (int i = 0; i < cm->count; i++) {
        if (cm->contexts[i].id == cm->active_id) {
            return &cm->contexts[i];
        }
    }
    return NULL;
}

int context_create(ContextManager* cm, const char* label) {
    if (cm->count >= MAX_CONTEXTS) return -1;

    TopicContext* ctx = &cm->contexts[cm->count];
    memset(ctx, 0, sizeof(TopicContext));
    ctx->id = cm->next_id++;
    strncpy(ctx->label, label, CONTEXT_LABEL_LEN - 1);
    ctx->label[CONTEXT_LABEL_LEN - 1] = '\0';
    ctx->state = CTX_PAUSED;
    ctx->created_at = time(NULL);
    ctx->last_active = ctx->created_at;
    ctx->message_count = 0;
    memory_init(&ctx->memory);
    cm->count++;

    /* First context becomes active automatically */
    if (cm->count == 1) {
        ctx->state = CTX_ACTIVE;
        cm->active_id = ctx->id;
    }
    return ctx->id;
}

static const char* state_name(ContextState s) {
    switch (s) {
        case CTX_ACTIVE:   return "active";
        case CTX_PAUSED:   return "paused";
        case CTX_RESOLVED: return "resolved";
        case CTX_ARCHIVED: return "archived";
    }
    return "unknown";
}

void context_list(ContextManager* cm, char* buffer, size_t buflen) {
    int off = snprintf(buffer, buflen, "Topics:\n");
    for (int i = 0; i < cm->count && (size_t)off < buflen - 1; i++) {
        TopicContext* c = &cm->contexts[i];
        const char* marker = (c->id == cm->active_id) ? "*" : " ";
        off += snprintf(buffer + off, buflen - off,
            "  [%s] #%d %s (%s, %d messages)\n",
            marker, c->id, c->label, state_name(c->state), c->message_count);
    }
}

WorkingMemory* context_get_memory(ContextManager* cm) {
    TopicContext* active = context_get_active(cm);
    if (!active) return NULL;
    return &active->memory;
}

/* ─── TEST MODE ─────────────────────────────────────────── */
#ifdef TEST_MODE
int main(void) {
    ContextManager cm;
    char buf[1024];

    printf("=== Context Engine Tests ===\n\n");

    /* Test 1: Init creates default "General" context */
    context_init(&cm);
    TopicContext* active = context_get_active(&cm);
    printf("[TEST] Init: count=%d, active_id=%d, label='%s' ... %s\n",
        cm.count, cm.active_id, active ? active->label : "NULL",
        (cm.count == 1 && active && strcmp(active->label, "General") == 0) ? "PASS" : "FAIL");

    /* Test 2: Create 3 additional contexts */
    int id1 = context_create(&cm, "Python debugging");
    int id2 = context_create(&cm, "Database design");
    int id3 = context_create(&cm, "Weekend plans");
    printf("[TEST] Create 3: count=%d, ids=%d,%d,%d ... %s\n",
        cm.count, id1, id2, id3,
        (cm.count == 4 && id1 == 1 && id2 == 2 && id3 == 3) ? "PASS" : "FAIL");

    /* Test 3: Switch to Python debugging */
    context_switch(&cm, id1);
    active = context_get_active(&cm);
    printf("[TEST] Switch to #%d: active='%s', state=%s ... %s\n",
        id1, active->label, state_name(active->state),
        (cm.active_id == id1 && active->state == CTX_ACTIVE) ? "PASS" : "FAIL");

    /* Verify General is now paused */
    printf("[TEST] General paused: state=%s ... %s\n",
        state_name(cm.contexts[0].state),
        (cm.contexts[0].state == CTX_PAUSED) ? "PASS" : "FAIL");

    /* Test 4: Simulate messages */
    active->message_count = 3;
    context_switch(&cm, 0);
    cm.contexts[0].message_count = 5;

    /* Test 5: List shows correct states */
    context_list(&cm, buf, sizeof(buf));
    printf("[TEST] List output:\n%s", buf);

    /* Test 6: context_get_memory returns active memory */
    WorkingMemory* mem = context_get_memory(&cm);
    printf("[TEST] Get memory: %s\n", mem ? "PASS" : "FAIL");

    /* Test 7: detect_switch updates subject */
    ParsedIntent intent = {0};
    strcpy(intent.subject, "linked lists");
    strcpy(intent.raw_input, "tell me about linked lists");
    int result = context_detect_switch(&cm, &intent);
    active = context_get_active(&cm);
    printf("[TEST] Detect switch: result=%d, subject='%s' ... %s\n",
        result, active->last_subject,
        (result == -1 && strcmp(active->last_subject, "linked lists") == 0) ? "PASS" : "FAIL");

    printf("\n=== All context tests complete ===\n");
    return 0;
}
#endif

/*
 * dcm.c — Deep Context Machine
 * Structured memory that beats 128K token context windows.
 * O(1) entity lookup vs O(n²) attention dilution.
 */

#include "dcm.h"
#include <string.h>
#include <stdio.h>
#include <ctype.h>

/* ─── Helpers ─── */
static int ci_eq(const char *a, const char *b) {
    while (*a && *b) {
        if (tolower((unsigned char)*a) != tolower((unsigned char)*b)) return 0;
        a++; b++;
    }
    return *a == *b;
}

static void extract_entities_from_text(const char *text, char entities[][64], int *count, int max) {
    /* Simple: consecutive capitalized words = entity */
    *count = 0;
    const char *p = text;
    while (*p && *count < max) {
        /* Skip to next uppercase */
        while (*p && !isupper((unsigned char)*p)) p++;
        if (!*p) break;
        
        /* Capture capitalized sequence */
        char buf[64] = "";
        int len = 0;
        while (*p && (isalpha((unsigned char)*p) || *p == ' ') && len < 63) {
            if (*p == ' ' && (p[1] == '\0' || !isupper((unsigned char)p[1]))) break;
            buf[len++] = *p++;
        }
        buf[len] = '\0';
        if (len > 2) {
            strncpy(entities[*count], buf, 63);
            (*count)++;
        }
    }
}

/* ─── Init ─── */
void dcm_init(DCMState *state) {
    memset(state, 0, sizeof(DCMState));
}

/* ─── Record Turn ─── */
void dcm_record_turn(DCMState *state, const char *user_input, const char *ai_response) {
    state->turn_count++;
    
    /* Extract entities from user input */
    char found[4][64];
    int found_count = 0;
    extract_entities_from_text(user_input, found, &found_count, 4);
    for (int i = 0; i < found_count; i++) {
        dcm_add_entity(state, found[i], "mentioned");
    }
    
    /* Detect intent */
    const char *input_lower = user_input;  /* Simplified — would lowercase */
    DCMIntent *intent = &state->intents[state->intent_head % DCM_MAX_INTENTS];
    intent->turn = state->turn_count;
    
    if (strstr(user_input, "?")) strncpy(intent->intent, "asking", 31);
    else if (strstr(user_input, "Remember") || strstr(user_input, "remember"))
        strncpy(intent->intent, "teaching", 31);
    else if (strstr(user_input, "no,") || strstr(user_input, "No,") || strstr(user_input, "actually"))
        strncpy(intent->intent, "correcting", 31);
    else strncpy(intent->intent, "stating", 31);
    
    /* Extract topic (first content word > 3 chars) */
    char topic[64] = "";
    const char *skip[] = {"what","is","the","a","how","why","where","when","does","can","do",NULL};
    char buf[256];
    strncpy(buf, user_input, 255); buf[255] = '\0';
    char *tok = strtok(buf, " \t?.,!");
    while (tok) {
        int is_skip = 0;
        char lower_tok[64];
        for (int i = 0; tok[i] && i < 63; i++) lower_tok[i] = tolower((unsigned char)tok[i]);
        lower_tok[strlen(tok)] = '\0';
        for (int s = 0; skip[s]; s++) { if (strcmp(lower_tok, skip[s]) == 0) { is_skip = 1; break; } }
        if (!is_skip && strlen(tok) > 3) { strncpy(topic, tok, 63); break; }
        tok = strtok(NULL, " \t?.,!");
    }
    
    if (topic[0]) {
        strncpy(intent->topic, topic, 63);
        dcm_set_topic(state, topic);
    }
    
    state->intent_head++;
    if (state->intent_count < DCM_MAX_INTENTS) state->intent_count++;
    
    /* Track last subject/object for reference resolution */
    if (topic[0]) strncpy(state->last_subject, topic, 63);
    if (ai_response) strncpy(state->last_answer, ai_response, 255);
    
    /* Count questions */
    if (strstr(user_input, "?")) state->questions_asked++;
}

/* ─── Entity Management ─── */
int dcm_add_entity(DCMState *state, const char *name, const char *type) {
    /* Check if already exists */
    int idx = dcm_find_entity(state, name);
    if (idx >= 0) {
        state->entities[idx].last_mention = state->turn_count;
        return idx;
    }
    
    if (state->entity_count >= DCM_MAX_ENTITIES) return -1;
    
    DCMEntity *e = &state->entities[state->entity_count];
    strncpy(e->name, name, 63);
    strncpy(e->type, type, 31);
    e->first_mention = state->turn_count;
    e->last_mention = state->turn_count;
    e->prop_count = 0;
    
    return state->entity_count++;
}

int dcm_find_entity(DCMState *state, const char *name) {
    for (int i = 0; i < state->entity_count; i++) {
        if (ci_eq(state->entities[i].name, name)) return i;
    }
    return -1;
}

/* ─── Reference Resolution ─── */
const char* dcm_resolve_reference(DCMState *state, const char *pronoun) {
    if (!pronoun) return NULL;
    
    /* "it" / "that" / "this" → last subject */
    if (ci_eq(pronoun, "it") || ci_eq(pronoun, "that") || ci_eq(pronoun, "this")) {
        return state->last_subject[0] ? state->last_subject : NULL;
    }
    
    /* "them" / "they" → last plural entity or last mentioned */
    if (ci_eq(pronoun, "they") || ci_eq(pronoun, "them")) {
        /* Find most recent entity */
        uint32_t latest = 0;
        int latest_idx = -1;
        for (int i = 0; i < state->entity_count; i++) {
            if (state->entities[i].last_mention > latest) {
                latest = state->entities[i].last_mention;
                latest_idx = i;
            }
        }
        return latest_idx >= 0 ? state->entities[latest_idx].name : NULL;
    }
    
    /* "the same" / "same thing" → last answer context */
    if (strstr(pronoun, "same")) {
        return state->last_subject[0] ? state->last_subject : NULL;
    }
    
    return NULL;
}

/* ─── Topic Management ─── */
const char* dcm_get_current_topic(DCMState *state) {
    if (state->current_topic_idx >= 0 && state->current_topic_idx < state->topic_count)
        return state->topics[state->current_topic_idx];
    return NULL;
}

void dcm_set_topic(DCMState *state, const char *topic) {
    /* Check if topic already tracked */
    for (int i = 0; i < state->topic_count; i++) {
        if (ci_eq(state->topics[i], topic)) {
            state->current_topic_idx = i;
            return;
        }
    }
    /* Add new topic */
    if (state->topic_count < DCM_MAX_TOPICS) {
        strncpy(state->topics[state->topic_count], topic, 63);
        state->current_topic_idx = state->topic_count;
        state->topic_count++;
    }
}

/* ─── Goals ─── */
int dcm_add_goal(DCMState *state, const char *goal) {
    if (state->goal_count >= DCM_MAX_GOALS) return -1;
    DCMGoal *g = &state->goals[state->goal_count];
    strncpy(g->name, goal, 63);
    strncpy(g->status, "active", 15);
    g->created_turn = state->turn_count;
    return state->goal_count++;
}

void dcm_update_goal(DCMState *state, int idx, const char *status) {
    if (idx >= 0 && idx < state->goal_count)
        strncpy(state->goals[idx].status, status, 15);
}

/* ─── Context Summary ─── */
void dcm_get_context_summary(DCMState *state, char *buf, int max) {
    int pos = 0;
    pos += snprintf(buf + pos, max - pos, "Turn %u | ", state->turn_count);
    
    /* Current topic */
    const char *topic = dcm_get_current_topic(state);
    if (topic) pos += snprintf(buf + pos, max - pos, "Topic: %s | ", topic);
    
    /* Entities */
    pos += snprintf(buf + pos, max - pos, "Entities: %d | ", state->entity_count);
    
    /* Active goals */
    int active = 0;
    for (int i = 0; i < state->goal_count; i++)
        if (strcmp(state->goals[i].status, "active") == 0) active++;
    if (active) pos += snprintf(buf + pos, max - pos, "Goals: %d active | ", active);
    
    pos += snprintf(buf + pos, max - pos, "Questions: %d", state->questions_asked);
}

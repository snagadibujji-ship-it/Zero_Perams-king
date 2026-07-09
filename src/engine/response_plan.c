/*
 * response_plan.c - Intelligent Response Planner
 * Assembles knowledge from the semantic core into structured,
 * natural-sounding multi-sentence responses.
 * Enhanced with discourse flow, sentence variety, and narrative framing.
 */
#include "response_plan.h"
#include "discourse.h"
#include "sentence_variety.h"
#include "narrative_frame.h"
#include <stdio.h>
#include <string.h>
#include <ctype.h>

/* ─── Helpers ─── */
static void capitalize(char* s) {
    if (s[0] >= 'a' && s[0] <= 'z') s[0] -= 32;
}

static const char* article_for(const char* word) {
    if (!word || !word[0]) return "a";
    /* "uni..." words sound like "you-ni" so use "a" not "an" */
    if (strncmp(word, "uni", 3) == 0) return "a";
    if (strncmp(word, "eu", 2) == 0) return "a";  /* "European" */
    return (word[0]=='a'||word[0]=='e'||word[0]=='i'||word[0]=='o'||word[0]=='u') ? "an" : "a";
}

static void append(char* buf, size_t bufsize, const char* text) {
    size_t len = strlen(buf);
    if (len + strlen(text) + 1 < bufsize) {
        strcat(buf, text);
    }
}

static int already_mentioned(const char* buf, const char* phrase) {
    return strstr(buf, phrase) != NULL;
}

/* ─── Build "What is X?" response ─── */
int response_plan_about(SemanticCore* core, SynonymDB* synonyms,
                        int concept_id, PlannedResponse* resp) {
    (void)synonyms;
    if (!core || concept_id < 0 || !resp) return -1;
    
    memset(resp, 0, sizeof(PlannedResponse));
    char* out = resp->text;
    size_t maxlen = sizeof(resp->text);
    
    const char* name = semantic_get_name(core, concept_id);
    if (!name) return -1;
    
    ConceptRecord* concept = semantic_get_concept(core, concept_id);
    if (!concept) return -1;
    
    sv_reset(); /* Reset sentence variety tracker */
    SectionType last_section = SEC_DEFINITION;
    
    /* ─── Opening Frame ─── */
    char frame_buf[512] = {0};
    if (frame_opening(core, concept_id, frame_buf, sizeof(frame_buf)) > 0) {
        append(out, maxlen, frame_buf);
        append(out, maxlen, " ");
        resp->sections++;
    }
    
    /* ─── Section 1: Definition (IS_A chain) ─── */
    uint32_t is_a_targets[8];
    int is_a_count = semantic_get_relations(core, concept_id, REL_IS_A, is_a_targets, 8);
    
    if (is_a_count > 0 && resp->sections == 0) {
        /* Only add IS_A if frame didn't already cover it */
        char sent[256];
        const char* parent = semantic_get_name(core, is_a_targets[0]);
        if (parent) {
            sv_is_a(name, parent, sent, sizeof(sent));
            append(out, maxlen, sent);
            /* Add secondary classifications */
            for (int i = 1; i < is_a_count && i < 3; i++) {
                const char* extra = semantic_get_name(core, is_a_targets[i]);
                if (extra && !already_mentioned(out, extra)) {
                    size_t len = strlen(out);
                    const char* art = (extra[0]=='a'||extra[0]=='e'||extra[0]=='i'||extra[0]=='o'||extra[0]=='u') ? "an" : "a";
                    snprintf(out + len, maxlen - len, ", and %s %s", art, extra);
                }
            }
            append(out, maxlen, ". ");
            last_section = SEC_DEFINITION;
            resp->sections++;
        }
    }
    
    /* ─── Section 2: "is" properties with transition ─── */
    int is_count = 0;
    char is_buf[512] = {0};
    for (uint16_t i = 0; i < concept->property_count && i < 20; i++) {
        PropertyRecord* p = &core->properties[concept->first_property + i];
        const char* key = core->string_table + p->key_offset;
        const char* val = core->string_table + p->value_offset;
        if (strcmp(key, "is") == 0 && !already_mentioned(out, val) && !already_mentioned(is_buf, val)) {
            if (is_count == 0) {
                const char* trans = discourse_transition(last_section, SEC_PROPERTY);
                snprintf(is_buf, sizeof(is_buf), "%s%s is %s", trans,
                         discourse_subject_ref(name, resp->sections + 1), val);
            } else if (is_count < 3) {
                size_t len = strlen(is_buf);
                snprintf(is_buf + len, sizeof(is_buf) - len, ", %s", val);
            }
            is_count++;
        }
    }
    if (is_count > 0) {
        append(out, maxlen, is_buf);
        append(out, maxlen, ". ");
        last_section = SEC_PROPERTY;
        resp->sections++;
    }
    
    /* ─── Section 3: "has" properties with variety ─── */
    int has_count = 0;
    char has_buf[512] = {0};
    for (uint16_t i = 0; i < concept->property_count && i < 20; i++) {
        PropertyRecord* p = &core->properties[concept->first_property + i];
        const char* key = core->string_table + p->key_offset;
        const char* val = core->string_table + p->value_offset;
        if (strcmp(key, "has") == 0 && !already_mentioned(out, val) && !already_mentioned(has_buf, val)) {
            if (has_count == 0) {
                const char* trans = discourse_transition(last_section, SEC_PHYSICAL);
                char sent[256];
                sv_has(name, val, sent, sizeof(sent));
                snprintf(has_buf, sizeof(has_buf), "%s%s", trans, sent);
            } else if (has_count < 5) {
                size_t len = strlen(has_buf);
                snprintf(has_buf + len, sizeof(has_buf) - len, ", %s", val);
            }
            has_count++;
        }
    }
    if (has_count > 0) {
        append(out, maxlen, has_buf);
        append(out, maxlen, ". ");
        last_section = SEC_PHYSICAL;
        resp->sections++;
    }
    
    /* ─── Section 4: Capabilities with variety ─── */
    uint32_t cap_targets[8];
    int cap_count = semantic_get_relations(core, concept_id, REL_CAPABLE_OF, cap_targets, 8);
    if (cap_count > 0) {
        const char* trans = discourse_transition(last_section, SEC_CAPABILITY);
        char sent[256];
        const char* first_cap = semantic_get_name(core, cap_targets[0]);
        if (first_cap) {
            sv_can(name, first_cap, sent, sizeof(sent));
            size_t len = strlen(out);
            snprintf(out + len, maxlen - len, "%s%s", trans, sent);
            for (int i = 1; i < cap_count && i < 4; i++) {
                const char* cap = semantic_get_name(core, cap_targets[i]);
                if (cap && !already_mentioned(out, cap)) {
                    len = strlen(out);
                    if (i == cap_count - 1 || i == 3)
                        snprintf(out + len, maxlen - len, ", and %s", cap);
                    else
                        snprintf(out + len, maxlen - len, ", %s", cap);
                }
            }
            append(out, maxlen, ". ");
            last_section = SEC_CAPABILITY;
            resp->sections++;
        }
    }
    
    /* ─── Section 5: USED_FOR ─── */
    uint32_t use_targets[4];
    int use_count = semantic_get_relations(core, concept_id, REL_USED_FOR, use_targets, 4);
    if (use_count > 0) {
        const char* use = semantic_get_name(core, use_targets[0]);
        if (use) {
            char sent[256];
            sv_used_for(name, use, sent, sizeof(sent));
            size_t len = strlen(out);
            snprintf(out + len, maxlen - len, "%s. ", sent);
            last_section = SEC_PURPOSE;
            resp->sections++;
        }
    }
    
    /* ─── Section 6: MADE_OF ─── */
    uint32_t mat_targets[4];
    int mat_count = semantic_get_relations(core, concept_id, REL_MADE_OF, mat_targets, 4);
    if (mat_count > 0) {
        const char* mat = semantic_get_name(core, mat_targets[0]);
        if (mat) {
            char sent[256];
            sv_made_of(name, mat, sent, sizeof(sent));
            size_t len = strlen(out);
            snprintf(out + len, maxlen - len, "%s. ", sent);
            last_section = SEC_COMPOSITION;
            resp->sections++;
        }
    }
    
    /* ─── Section 7: LOCATED_IN ─── */
    uint32_t loc_targets[4];
    int loc_count = semantic_get_relations(core, concept_id, REL_LOCATED_IN, loc_targets, 4);
    if (loc_count > 0) {
        const char* loc = semantic_get_name(core, loc_targets[0]);
        if (loc) {
            char sent[256];
            sv_located_in(name, loc, sent, sizeof(sent));
            size_t len = strlen(out);
            snprintf(out + len, maxlen - len, "%s. ", sent);
            last_section = SEC_LOCATION;
            resp->sections++;
        }
    }
    
    /* ─── Section 8: CAUSES ─── */
    uint32_t cause_targets[4];
    int cause_count = semantic_get_relations(core, concept_id, REL_CAUSES, cause_targets, 4);
    if (cause_count > 0) {
        const char* effect = semantic_get_name(core, cause_targets[0]);
        if (effect) {
            char sent[256];
            sv_causes(name, effect, sent, sizeof(sent));
            size_t len = strlen(out);
            snprintf(out + len, maxlen - len, "%s. ", sent);
            last_section = SEC_CAUSE;
            resp->sections++;
        }
    }
    
    /* ─── Closing Frame ─── */
    char close_buf[256] = {0};
    if (frame_closing(core, concept_id, resp->sections, close_buf, sizeof(close_buf)) > 0) {
        append(out, maxlen, close_buf);
    }
    
    /* If we got nothing */
    if (resp->sections == 0) {
        snprintf(out, maxlen, "I know about %s but don't have detailed information yet.", name);
    }
    
    resp->confidence = resp->sections >= 4 ? 0.9f : (resp->sections >= 2 ? 0.75f : 0.5f);
    return 0;
}

/* ─── Build response for specific question type ─── */
int response_plan_query(SemanticCore* core, SynonymDB* synonyms,
                        int concept_id, const char* question_type,
                        PlannedResponse* resp) {
    if (!core || concept_id < 0 || !resp) return -1;
    
    /* For now, "about" handles all question types */
    /* Future: specialize for "why", "how", "when" etc. */
    (void)question_type;
    return response_plan_about(core, synonyms, concept_id, resp);
}

#ifdef TEST_MODE
#include <assert.h>
int main(void) {
    printf("=== Response Planner Tests ===\n");
    /* Can't test without a real knowledge.dat, just test NULL handling */
    PlannedResponse resp;
    assert(response_plan_about(NULL, NULL, 0, &resp) == -1);
    printf("[PASS] NULL handling\n");
    printf("=== Done ===\n");
    return 0;
}
#endif

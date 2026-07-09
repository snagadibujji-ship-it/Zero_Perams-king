/*
 * analogy.c — Analogical reasoning engine
 * Finds structurally similar concepts by comparing siblings in the
 * concept hierarchy, counting shared/differing properties.
 */
#include "analogy.h"
#include <string.h>
#include <stdio.h>
#include <ctype.h>

static const char* analogy_keywords[] = {
    "like", "similar", "compared to", "analogy",
    "remind", "analogous", "resemble", NULL
};

static int contains_ci(const char* haystack, const char* needle) {
    size_t hlen = strlen(haystack), nlen = strlen(needle);
    if (nlen > hlen) return 0;
    for (size_t i = 0; i <= hlen - nlen; i++) {
        int match = 1;
        for (size_t j = 0; j < nlen && match; j++)
            if (tolower((unsigned char)haystack[i+j]) != tolower((unsigned char)needle[j]))
                match = 0;
        if (match) return 1;
    }
    return 0;
}

int analogy_is_question(const char* raw_input) {
    if (!raw_input) return 0;
    for (int i = 0; analogy_keywords[i]; i++)
        if (contains_ci(raw_input, analogy_keywords[i])) return 1;
    return 0;
}

/* ─── Helpers ────────────────────────────────────────────────── */
#define MAX_SIBLINGS 64
#define MAX_PROPS    MAX_PROPERTIES

static int count_shared(SemanticCore* core,
                        PropertyRecord* a, int na,
                        PropertyRecord* b, int nb,
                        char shared[][128], int max) {
    int count = 0;
    for (int i = 0; i < na && count < max; i++) {
        const char* ka = core->string_table + a[i].key_offset;
        for (int j = 0; j < nb; j++) {
            if (strcmp(ka, core->string_table + b[j].key_offset) == 0) {
                snprintf(shared[count++], 128, "%s", ka);
                break;
            }
        }
    }
    return count;
}

static const char* find_unique_prop(SemanticCore* core,
                                    PropertyRecord* a, int na,
                                    PropertyRecord* b, int nb) {
    static char buf[256];
    for (int i = 0; i < na; i++) {
        const char* ka = core->string_table + a[i].key_offset;
        int found = 0;
        for (int j = 0; j < nb && !found; j++)
            if (strcmp(ka, core->string_table + b[j].key_offset) == 0) found = 1;
        if (!found) {
            snprintf(buf, sizeof(buf), "%s %s",
                     ka, core->string_table + a[i].value_offset);
            return buf;
        }
    }
    return NULL;
}

/* ─── Main Analogy Search ────────────────────────────────────── */

int analogy_find(SemanticCore* core, int concept_id, AnalogyResult* result) {
    if (!core || !result || concept_id < 0) return -1;
    if ((uint32_t)concept_id >= core->header->concept_count) return -1;

    memset(result, 0, sizeof(AnalogyResult));

    ConceptRecord* src = semantic_get_concept(core, (uint32_t)concept_id);
    const char* src_name = semantic_get_name(core, (uint32_t)concept_id);
    if (!src || !src_name) return -1;
    snprintf(result->source_name, sizeof(result->source_name), "%s", src_name);

    uint32_t parent_id = src->parent_id;
    if (parent_id == (uint32_t)concept_id) return -1; /* root */
    const char* parent_name = semantic_get_name(core, parent_id);

    /* Find siblings (same parent) */
    uint32_t siblings[MAX_SIBLINGS];
    int sib_count = 0;
    for (uint32_t i = 0; i < core->header->concept_count && sib_count < MAX_SIBLINGS; i++) {
        if (i == (uint32_t)concept_id) continue;
        ConceptRecord* c = semantic_get_concept(core, i);
        if (c && c->parent_id == parent_id)
            siblings[sib_count++] = i;
    }
    if (sib_count == 0) return -1;

    /* Get source properties */
    PropertyRecord src_props[MAX_PROPS];
    int src_pc = semantic_get_all_properties(core, (uint32_t)concept_id, src_props, MAX_PROPS);

    /* Score siblings: shared props + differences + similarity */
    int best_idx = -1, best_score = -1;
    float best_sim = 0.0f;

    for (int s = 0; s < sib_count; s++) {
        PropertyRecord sp[MAX_PROPS];
        int spc = semantic_get_all_properties(core, siblings[s], sp, MAX_PROPS);
        char sh[MAX_PROPS][128];
        int sc = count_shared(core, src_props, src_pc, sp, spc, sh, MAX_PROPS);
        int diff = (src_pc - sc) + (spc - sc);
        int score = sc * 3 + (diff > 0 ? 2 : -5);

        float sim = semantic_similarity(core, (uint32_t)concept_id, siblings[s]);
        if (sim > 0.0f) score += (int)(sim * 5);

        if (score > best_score) {
            best_score = score;
            best_idx = s;
            best_sim = sim;
        }
    }
    if (best_idx < 0) return -1;

    uint32_t tid = siblings[best_idx];
    const char* tgt_name = semantic_get_name(core, tid);
    if (!tgt_name) return -1;
    snprintf(result->target_name, sizeof(result->target_name), "%s", tgt_name);

    /* Build explanation */
    PropertyRecord tgt_props[MAX_PROPS];
    int tgt_pc = semantic_get_all_properties(core, tid, tgt_props, MAX_PROPS);
    char shared[MAX_PROPS][128];
    int sc = count_shared(core, src_props, src_pc, tgt_props, tgt_pc, shared, MAX_PROPS);

    char shared_str[256] = "";
    for (int i = 0; i < sc && i < 3; i++) {
        if (i > 0) strncat(shared_str, " and ", sizeof(shared_str) - strlen(shared_str) - 1);
        strncat(shared_str, shared[i], sizeof(shared_str) - strlen(shared_str) - 1);
    }

    const char* sd = find_unique_prop(core, src_props, src_pc, tgt_props, tgt_pc);
    const char* td = find_unique_prop(core, tgt_props, tgt_pc, src_props, src_pc);

    if (sd && td) {
        snprintf(result->explanation, sizeof(result->explanation),
                 "%s is similar to %s — both are %s that have %s. "
                 "However, %s has %s while %s has %s.",
                 src_name, tgt_name, parent_name ? parent_name : "things",
                 sc > 0 ? shared_str : "common traits",
                 src_name, sd, tgt_name, td);
    } else {
        snprintf(result->explanation, sizeof(result->explanation),
                 "%s is similar to %s — both are %s that share %s.",
                 src_name, tgt_name, parent_name ? parent_name : "things",
                 sc > 0 ? shared_str : "common traits");
    }

    /* Confidence */
    if (best_sim > 0.0f)
        result->similarity = best_sim;
    else if (src_pc + tgt_pc > 0)
        result->similarity = (float)(sc * 2) / (float)(src_pc + tgt_pc);
    else
        result->similarity = 0.5f;

    return 0;
}

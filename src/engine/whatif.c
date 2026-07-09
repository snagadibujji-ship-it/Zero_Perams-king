/*
 * whatif.c — Counterfactual Reasoning Engine
 *
 * Given a subject and a hypothetical change, finds current properties,
 * applies the change conceptually, and traces consequences via causal chains.
 * E.g., "What if the sun disappeared?" → trace effects on plants, temperature, etc.
 */

#include "derive.h"
#include <string.h>
#include <stdio.h>

extern SemanticCore g_semantic_core;

#define MAX_CONSEQUENCES 8
#define DECAY_PER_HOP    0.85f

/* ─── Helpers ────────────────────────────────────────────────── */

/* Find concepts that depend on or are caused by the subject */
static int find_dependents(SemanticCore *core, uint32_t subj_id,
                           uint32_t *dependents, int max)
{
    int count = 0;

    /* Things that the subject CAUSES */
    count = semantic_get_relations(core, subj_id, REL_CAUSES, dependents, max);

    /* Also check things that contain or are part of subject */
    if (count < max) {
        uint32_t extra[MAX_RELATIONS];
        int extra_count = semantic_get_relations(core, subj_id, REL_CONTAINS, extra, MAX_RELATIONS);
        for (int i = 0; i < extra_count && count < max; i++) {
            dependents[count++] = extra[i];
        }
    }

    return count;
}

/* Trace one level of causal consequences */
static int trace_consequences(SemanticCore *core, uint32_t cause_id,
                              uint32_t *consequences, int max, int depth)
{
    if (depth <= 0 || max <= 0) return 0;

    uint32_t direct[MAX_RELATIONS];
    int direct_count = semantic_get_relations(core, cause_id, REL_CAUSES, direct, MAX_RELATIONS);

    int total = 0;
    for (int i = 0; i < direct_count && total < max; i++) {
        consequences[total++] = direct[i];
    }

    /* Recurse one more level for deeper effects */
    if (depth > 1 && total < max) {
        for (int i = 0; i < direct_count && total < max; i++) {
            uint32_t deeper[MAX_RELATIONS];
            int deeper_count = semantic_get_relations(core, direct[i], REL_CAUSES, deeper, MAX_RELATIONS);
            for (int j = 0; j < deeper_count && total < max; j++) {
                /* Avoid duplicates */
                int dup = 0;
                for (int k = 0; k < total; k++) {
                    if (consequences[k] == deeper[j]) { dup = 1; break; }
                }
                if (!dup) consequences[total++] = deeper[j];
            }
        }
    }

    return total;
}

/* ─── Main What-If Engine ────────────────────────────────────── */

DeriveResult derive_whatif(const char *subject, const char *change)
{
    DeriveResult result;
    memset(&result, 0, sizeof(result));
    result.derivation_type = DERIVE_WHATIF;
    result.confidence = 0.0f;

    SemanticCore *core = &g_semantic_core;

    if (!subject || !change) return result;

    /* Resolve subject */
    int subj_id = semantic_find(core, subject);
    if (subj_id < 0)
        subj_id = semantic_find_by_synonym(core, subject);
    if (subj_id < 0) return result;

    const char *subj_name = semantic_get_name(core, (uint32_t)subj_id);
    if (!subj_name) return result;

    /* Find what depends on or is caused by this subject */
    uint32_t dependents[MAX_CONSEQUENCES];
    int dep_count = find_dependents(core, (uint32_t)subj_id, dependents, MAX_CONSEQUENCES);

    /* Trace deeper consequences */
    uint32_t consequences[MAX_CONSEQUENCES];
    int cons_count = 0;
    for (int i = 0; i < dep_count && cons_count < MAX_CONSEQUENCES; i++) {
        uint32_t deeper[MAX_CONSEQUENCES];
        int d = trace_consequences(core, dependents[i], deeper, MAX_CONSEQUENCES - cons_count, 2);
        for (int j = 0; j < d && cons_count < MAX_CONSEQUENCES; j++) {
            consequences[cons_count++] = deeper[j];
        }
    }
    (void)cons_count;       /* used for deeper analysis in future */
    (void)consequences;

    /* Build result */
    result.chain[0] = (uint32_t)subj_id;
    result.chain_len = 1;
    for (int i = 0; i < dep_count && result.chain_len < 16; i++) {
        result.chain[result.chain_len++] = dependents[i];
    }

    result.hops = dep_count > 0 ? dep_count : 0;
    result.confidence = dep_count > 0 ? 0.7f * DECAY_PER_HOP : 0.2f;

    /* Compose answer */
    if (dep_count > 0) {
        const char *first_dep = semantic_get_name(core, dependents[0]);
        if (!first_dep) first_dep = "related things";

        if (dep_count == 1) {
            snprintf(result.answer, sizeof(result.answer),
                     "If %s happens to %s, then %s would follow.",
                     change, subj_name, first_dep);
            result.confidence = 0.65f;
        } else {
            int written = snprintf(result.answer, sizeof(result.answer),
                                   "If %s happens to %s, then %s",
                                   change, subj_name, first_dep);
            for (int i = 1; i < dep_count && i < 3 && written < (int)sizeof(result.answer) - 64; i++) {
                const char *dep_name = semantic_get_name(core, dependents[i]);
                if (dep_name) {
                    written += snprintf(result.answer + written,
                                        sizeof(result.answer) - (size_t)written,
                                        ", %s", dep_name);
                }
            }
            snprintf(result.answer + written, sizeof(result.answer) - (size_t)written,
                     " would be affected.");
            result.confidence = 0.6f;
        }
    } else {
        snprintf(result.answer, sizeof(result.answer),
                 "If %s happens to %s, the consequences are unclear from available knowledge.",
                 change, subj_name);
        result.confidence = 0.15f;
    }

    return result;
}

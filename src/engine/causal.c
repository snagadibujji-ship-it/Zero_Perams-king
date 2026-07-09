/*
 * causal.c — Causal reasoning engine
 *
 * Finds causal chains in the semantic core and knowledge graph
 * to answer "why" questions with multi-hop explanations.
 */

#include "causal.h"
#include <string.h>
#include <stdio.h>
#include <ctype.h>

/* ─── Helper: case-insensitive substring search ──────────────── */
static int contains_ci(const char *haystack, const char *needle)
{
    if (!haystack || !needle) return 0;
    size_t hlen = strlen(haystack);
    size_t nlen = strlen(needle);
    if (nlen > hlen) return 0;

    for (size_t i = 0; i <= hlen - nlen; i++) {
        size_t j;
        for (j = 0; j < nlen; j++) {
            if (tolower((unsigned char)haystack[i + j]) != tolower((unsigned char)needle[j]))
                break;
        }
        if (j == nlen) return 1;
    }
    return 0;
}

/* ─── causal_is_why ──────────────────────────────────────────── */
int causal_is_why(const ParsedIntent *intent, const char *raw)
{
    (void)intent;  /* May use intent_type in future */

    if (!raw) return 0;

    if (contains_ci(raw, "why"))         return 1;
    if (contains_ci(raw, "because"))     return 1;
    if (contains_ci(raw, "what causes")) return 1;
    if (contains_ci(raw, "how come"))    return 1;

    return 0;
}

/* ─── causal_answer ──────────────────────────────────────────── */
int causal_answer(SemanticCore *core, KnowledgeGraph *kg, const char *topic, CausalResult *result)
{
    if (!core || !topic || !result) return 0;

    memset(result, 0, sizeof(CausalResult));

    /* Find the concept in semantic core */
    int concept_id = semantic_find(core, topic);
    if (concept_id < 0) {
        /* Try synonym lookup */
        concept_id = semantic_find_by_synonym(core, topic);
    }
    if (concept_id < 0 && !kg) return 0;

    /* Collect causal chain: walk up to 3 hops via CAUSED_BY */
    const char *chain[4] = {NULL, NULL, NULL, NULL};
    int chain_len = 0;

    chain[0] = topic;
    chain_len = 1;

    if (concept_id >= 0) {
        uint32_t current = (uint32_t)concept_id;

        /* Hop 1: look for direct CAUSED_BY from our concept */
        uint32_t targets[MAX_RELATIONS];
        int found = semantic_get_relations(core, current, REL_CAUSED_BY, targets, MAX_RELATIONS);

        if (found > 0) {
            const char *cause1 = semantic_get_name(core, targets[0]);
            if (cause1) {
                chain[chain_len++] = cause1;

                /* Hop 2: follow the chain */
                int found2 = semantic_get_relations(core, targets[0], REL_CAUSED_BY, targets + 1, MAX_RELATIONS - 1);
                if (found2 > 0) {
                    const char *cause2 = semantic_get_name(core, targets[1]);
                    if (cause2) {
                        chain[chain_len++] = cause2;

                        /* Hop 3: one more level */
                        int found3 = semantic_get_relations(core, targets[1], REL_CAUSED_BY, targets + 2, MAX_RELATIONS - 2);
                        if (found3 > 0) {
                            const char *cause3 = semantic_get_name(core, targets[2]);
                            if (cause3) {
                                chain[chain_len++] = cause3;
                            }
                        }
                    }
                }
            }
        }

        /* Reverse-search: scan ALL relations for target==our_concept with type==CAUSES */
        if (chain_len == 1 && core->header) {
            for (uint32_t i = 0; i < core->header->relation_count && chain_len < 4; i++) {
                RelationRecord *rel = &core->relations[i];
                if (rel->target_id == (uint32_t)concept_id &&
                    rel->relation_type == REL_CAUSES) {
                    const char *cause = semantic_get_name(core, rel->source_id);
                    if (cause) {
                        chain[chain_len++] = cause;
                    }
                }
            }
        }
    }

    /* Also scan KG for 'causes' relation */
    if (kg && chain_len < 4) {
        Fact kg_results[8];
        int kg_found = kg_query(kg, NULL, "causes", kg_results, 8);
        for (int i = 0; i < kg_found && chain_len < 4; i++) {
            const char *obj = kg_get_string(kg, kg_results[i].object_id);
            const char *subj = kg_get_string(kg, kg_results[i].subject_id);
            /* If object matches our topic, the subject is a cause */
            if (obj && contains_ci(obj, topic) && subj) {
                /* Avoid duplicates */
                int dup = 0;
                for (int c = 0; c < chain_len; c++) {
                    if (chain[c] && contains_ci(chain[c], subj)) { dup = 1; break; }
                }
                if (!dup) {
                    chain[chain_len++] = subj;
                }
            }
        }
    }

    /* No causal info found */
    if (chain_len <= 1) return 0;

    /* Format explanation based on chain length */
    result->chain_depth = chain_len - 1;

    if (chain_len == 2) {
        snprintf(result->explanation, sizeof(result->explanation),
                 "%s happens because of %s.",
                 chain[0], chain[1]);
        result->confidence = 0.6f;
    } else if (chain_len == 3) {
        snprintf(result->explanation, sizeof(result->explanation),
                 "%s happens because %s, which is caused by %s.",
                 chain[0], chain[1], chain[2]);
        result->confidence = 0.8f;
    } else {
        snprintf(result->explanation, sizeof(result->explanation),
                 "%s happens because %s, which is caused by %s, which traces back to %s.",
                 chain[0], chain[1], chain[2], chain[3]);
        result->confidence = 0.8f;
    }

    return 1;
}

/*
 * conflict.c — Conflict Detection Engine
 *
 * Detects when a subject requires something that the context cannot provide.
 * For example: "fish in desert" → fish needs water, desert lacks water.
 */

#include "derive.h"
#include <string.h>
#include <stdio.h>
#include <ctype.h>

extern SemanticCore g_semantic_core;

/* ─── Helpers ────────────────────────────────────────────────── */

static int str_contains_ci(const char *haystack, const char *needle)
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

/* Check if a property key indicates a requirement/need */
static int is_need_key(const char *key)
{
    return str_contains_ci(key, "needs") ||
           str_contains_ci(key, "requires") ||
           str_contains_ci(key, "depends_on") ||
           str_contains_ci(key, "must_have");
}

/* Check if context has a property value that negates or lacks a need */
static int context_lacks(SemanticCore *core, uint32_t context_id, const char *need)
{
    PropertyRecord props[MAX_PROPERTIES];
    int count = semantic_get_all_properties(core, context_id, props, MAX_PROPERTIES);

    /* Check if context explicitly has the opposite */
    for (int i = 0; i < count; i++) {
        const char *key = core->string_table + props[i].key_offset;
        const char *val = core->string_table + props[i].value_offset;

        /* Check for explicit negation: "has_no_X" or "lacks_X" */
        if (str_contains_ci(key, "lacks") && str_contains_ci(val, need))
            return 1;
        if (str_contains_ci(key, "has_no") && str_contains_ci(val, need))
            return 1;
        if (str_contains_ci(val, "no") && str_contains_ci(val, need))
            return 1;
    }

    /* Check if context simply doesn't have the needed property */
    const char *has_it = semantic_get_property(core, context_id, need);
    if (!has_it) {
        /* Also check via relation: does context CONTAIN or HAS the need? */
        uint32_t targets[MAX_RELATIONS];
        int rel_count = semantic_get_relations(core, context_id, REL_HAS, targets, MAX_RELATIONS);
        for (int i = 0; i < rel_count; i++) {
            const char *name = semantic_get_name(core, targets[i]);
            if (name && str_contains_ci(name, need))
                return 0;  /* context does have it */
        }
        rel_count = semantic_get_relations(core, context_id, REL_CONTAINS, targets, MAX_RELATIONS);
        for (int i = 0; i < rel_count; i++) {
            const char *name = semantic_get_name(core, targets[i]);
            if (name && str_contains_ci(name, need))
                return 0;  /* context does contain it */
        }
        return 1;  /* context lacks the need */
    }

    return 0;
}

/* ─── Main Conflict Detection ────────────────────────────────── */

DeriveResult derive_conflict(uint32_t subject_id, uint32_t context_id)
{
    DeriveResult result;
    memset(&result, 0, sizeof(result));
    result.derivation_type = DERIVE_CONFLICT;
    result.confidence = 0.0f;

    SemanticCore *core = &g_semantic_core;

    const char *subj_name = semantic_get_name(core, subject_id);
    const char *ctx_name = semantic_get_name(core, context_id);
    if (!subj_name || !ctx_name) return result;

    /* Get all properties of subject (with inheritance) */
    PropertyRecord subj_props[MAX_PROPERTIES];
    int prop_count = semantic_get_all_properties(core, subject_id, subj_props, MAX_PROPERTIES);

    /* Look for needs/requires properties */
    for (int i = 0; i < prop_count; i++) {
        const char *key = core->string_table + subj_props[i].key_offset;
        const char *val = core->string_table + subj_props[i].value_offset;

        if (!is_need_key(key)) continue;

        /* Check if context lacks this need */
        if (context_lacks(core, context_id, val)) {
            result.confidence = 0.85f;
            result.chain[0] = subject_id;
            result.chain[1] = context_id;
            result.chain_len = 2;
            result.hops = 1;

            snprintf(result.answer, sizeof(result.answer),
                     "%s cannot function in %s because it requires %s but %s does not have %s.",
                     subj_name, ctx_name, val, ctx_name, val);
            return result;
        }
    }

    /* Also check DESIRES relations as soft needs */
    uint32_t desires[MAX_RELATIONS];
    int desire_count = semantic_get_relations(core, subject_id, REL_DESIRES, desires, MAX_RELATIONS);
    for (int i = 0; i < desire_count; i++) {
        const char *desire_name = semantic_get_name(core, desires[i]);
        if (desire_name && context_lacks(core, context_id, desire_name)) {
            result.confidence = 0.7f;
            result.chain[0] = subject_id;
            result.chain[1] = context_id;
            result.chain_len = 2;
            result.hops = 1;

            snprintf(result.answer, sizeof(result.answer),
                     "%s cannot function in %s because it requires %s but %s does not have %s.",
                     subj_name, ctx_name, desire_name, ctx_name, desire_name);
            return result;
        }
    }

    return result;
}

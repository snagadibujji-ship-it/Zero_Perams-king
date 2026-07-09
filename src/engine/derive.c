/*
 * derive.c — Core Generative Reasoning Engine
 *
 * Orchestrates multi-strategy inference: conflict detection, causal chains,
 * inheritance walks, analogy matching, and counterfactual reasoning.
 * Returns the best result ranked by confidence.
 */

#include "derive.h"
#include <string.h>
#include <stdio.h>
#include <ctype.h>

/* External semantic core — initialized in main */
extern SemanticCore g_semantic_core;

/* Forward declarations for sub-engines in other files */
extern DeriveResult derive_conflict(uint32_t subject_id, uint32_t context_id);
extern DeriveResult derive_causal(uint32_t cause_id, uint32_t effect_id, int max_hops);
extern DeriveResult derive_whatif(const char *subject, const char *change);

/* ─── Helpers ────────────────────────────────────────────────── */

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

static DeriveResult make_unknown(void)
{
    DeriveResult r;
    memset(&r, 0, sizeof(r));
    r.derivation_type = DERIVE_UNKNOWN;
    r.confidence = 0.0f;
    snprintf(r.answer, sizeof(r.answer), "I don't have enough information to answer that.");
    return r;
}

static int is_causal_predicate(const char *predicate)
{
    return contains_ci(predicate, "cause") ||
           contains_ci(predicate, "why") ||
           contains_ci(predicate, "leads") ||
           contains_ci(predicate, "result") ||
           contains_ci(predicate, "because");
}

static int is_whatif_predicate(const char *predicate)
{
    return contains_ci(predicate, "what if") ||
           contains_ci(predicate, "what happens") ||
           contains_ci(predicate, "hypothetical") ||
           contains_ci(predicate, "suppose");
}

/* ─── Inheritance Walk ────────────────────────────────────────── */

DeriveResult derive_inheritance(uint32_t subject_id, const char *property)
{
    DeriveResult result;
    memset(&result, 0, sizeof(result));
    result.derivation_type = DERIVE_INHERIT;
    result.confidence = 0.0f;

    SemanticCore *core = &g_semantic_core;

    if (!property) return result;

    const char *subj_name = semantic_get_name(core, subject_id);
    if (!subj_name) return result;

    /* First: check if subject directly has this property */
    const char *direct = semantic_get_property(core, subject_id, property);
    if (direct) {
        result.confidence = 0.95f;
        result.derivation_type = DERIVE_DIRECT;
        result.chain[0] = subject_id;
        result.chain_len = 1;
        result.hops = 0;
        snprintf(result.answer, sizeof(result.answer),
                 "Yes, %s has %s: %s.", subj_name, property, direct);
        return result;
    }

    /* Walk up IS-A chain looking for the property */
    uint32_t ancestors[INHERIT_DEPTH];
    int anc_count = semantic_get_ancestors(core, subject_id, ancestors, INHERIT_DEPTH);

    for (int i = 0; i < anc_count; i++) {
        const char *inherited = semantic_get_property(core, ancestors[i], property);
        if (inherited) {
            const char *parent_name = semantic_get_name(core, ancestors[i]);
            if (!parent_name) parent_name = "ancestor";

            result.confidence = 0.85f - (float)i * 0.05f;  /* Decay per hop */
            if (result.confidence < 0.3f) result.confidence = 0.3f;
            result.hops = i + 1;

            /* Build chain: subject → ... → ancestor_with_property */
            result.chain[0] = subject_id;
            result.chain_len = 1;
            for (int j = 0; j <= i && result.chain_len < 16; j++) {
                result.chain[result.chain_len++] = ancestors[j];
            }

            snprintf(result.answer, sizeof(result.answer),
                     "Yes, %s has %s because it is a %s, and all %ss have %s.",
                     subj_name, property, parent_name, parent_name, property);
            return result;
        }
    }

    /* Check relations for capability/property match */
    uint32_t targets[MAX_RELATIONS];
    int rel_count = semantic_get_relations(core, subject_id, REL_CAPABLE_OF, targets, MAX_RELATIONS);
    for (int i = 0; i < rel_count; i++) {
        const char *cap_name = semantic_get_name(core, targets[i]);
        if (cap_name && strcmp(cap_name, property) == 0) {
            result.confidence = 0.8f;
            result.chain[0] = subject_id;
            result.chain[1] = targets[i];
            result.chain_len = 2;
            result.hops = 1;
            snprintf(result.answer, sizeof(result.answer),
                     "Yes, %s is capable of %s.", subj_name, property);
            return result;
        }
    }

    return result;
}

/* ─── Analogy Engine (DeriveResult wrapper) ──────────────────── */

DeriveResult derive_analogy(uint32_t concept_a, uint32_t concept_b)
{
    DeriveResult result;
    memset(&result, 0, sizeof(result));
    result.derivation_type = DERIVE_ANALOGY;
    result.confidence = 0.0f;

    SemanticCore *core = &g_semantic_core;

    const char *name_a = semantic_get_name(core, concept_a);
    const char *name_b = semantic_get_name(core, concept_b);
    if (!name_a || !name_b) return result;

    /* Get properties of both concepts */
    PropertyRecord props_a[MAX_PROPERTIES];
    PropertyRecord props_b[MAX_PROPERTIES];
    int na = semantic_get_all_properties(core, concept_a, props_a, MAX_PROPERTIES);
    int nb = semantic_get_all_properties(core, concept_b, props_b, MAX_PROPERTIES);

    /* Find shared property keys */
    char shared[8][128];
    int shared_count = 0;

    for (int i = 0; i < na && shared_count < 8; i++) {
        const char *ka = core->string_table + props_a[i].key_offset;
        for (int j = 0; j < nb; j++) {
            const char *kb = core->string_table + props_b[j].key_offset;
            if (strcmp(ka, kb) == 0) {
                strncpy(shared[shared_count], ka, 127);
                shared[shared_count][127] = '\0';
                shared_count++;
                break;
            }
        }
    }

    /* Also check graph distance / similarity */
    float sim = semantic_similarity(core, concept_a, concept_b);

    result.chain[0] = concept_a;
    result.chain[1] = concept_b;
    result.chain_len = 2;
    result.hops = 1;

    if (shared_count >= 2) {
        result.confidence = 0.5f + sim * 0.4f;
        if (result.confidence > 0.95f) result.confidence = 0.95f;
        snprintf(result.answer, sizeof(result.answer),
                 "%s is similar to %s — both %s and %s.",
                 name_a, name_b, shared[0], shared[1]);
    } else if (shared_count == 1) {
        result.confidence = 0.3f + sim * 0.3f;
        snprintf(result.answer, sizeof(result.answer),
                 "%s is similar to %s — both share %s.",
                 name_a, name_b, shared[0]);
    } else if (sim > 0.3f) {
        result.confidence = sim * 0.5f;
        snprintf(result.answer, sizeof(result.answer),
                 "%s and %s are somewhat related in the concept hierarchy.",
                 name_a, name_b);
    } else {
        result.confidence = 0.1f;
        snprintf(result.answer, sizeof(result.answer),
                 "%s and %s don't appear to have much in common.",
                 name_a, name_b);
    }

    return result;
}

/* ─── Main Inference Orchestrator ────────────────────────────── */

DeriveResult derive_answer(const char *subject, const char *predicate, const char *context)
{
    DeriveResult best = make_unknown();
    DeriveResult candidate;
    SemanticCore *core = &g_semantic_core;

    if (!subject || !predicate) return best;

    /* Resolve subject concept ID */
    int subj_id = semantic_find(core, subject);
    if (subj_id < 0)
        subj_id = semantic_find_by_synonym(core, subject);
    if (subj_id < 0)
        return best;

    /* Strategy 1: Conflict detection (if context provided) */
    if (context && context[0] != '\0') {
        int ctx_id = semantic_find(core, context);
        if (ctx_id < 0)
            ctx_id = semantic_find_by_synonym(core, context);
        if (ctx_id >= 0) {
            candidate = derive_conflict((uint32_t)subj_id, (uint32_t)ctx_id);
            if (candidate.confidence > best.confidence)
                best = candidate;
        }
    }

    /* Strategy 2: What-if / counterfactual (if predicate suggests it) */
    if (is_whatif_predicate(predicate)) {
        candidate = derive_whatif(subject, predicate);
        if (candidate.confidence > best.confidence)
            best = candidate;
    }

    /* Strategy 3: Causal chain (if predicate suggests causation) */
    if (is_causal_predicate(predicate)) {
        /* Try to find a target concept from the predicate */
        int pred_id = semantic_find(core, predicate);
        if (pred_id < 0)
            pred_id = semantic_find_by_synonym(core, predicate);
        if (pred_id >= 0) {
            candidate = derive_causal((uint32_t)subj_id, (uint32_t)pred_id, 10);
            if (candidate.confidence > best.confidence)
                best = candidate;
        }
        /* Also try with context as target */
        if (context && context[0] != '\0') {
            int ctx_id = semantic_find(core, context);
            if (ctx_id >= 0) {
                candidate = derive_causal((uint32_t)subj_id, (uint32_t)ctx_id, 10);
                if (candidate.confidence > best.confidence)
                    best = candidate;
            }
        }
    }

    /* Strategy 4: Inheritance walk (general property questions) */
    candidate = derive_inheritance((uint32_t)subj_id, predicate);
    if (candidate.confidence > best.confidence)
        best = candidate;

    /* Strategy 5: Analogy (find similar concepts) */
    if (context && context[0] != '\0') {
        int ctx_id = semantic_find(core, context);
        if (ctx_id >= 0) {
            candidate = derive_analogy((uint32_t)subj_id, (uint32_t)ctx_id);
            if (candidate.confidence > best.confidence)
                best = candidate;
        }
    }

    return best;
}

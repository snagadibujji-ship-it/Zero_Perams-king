/*
 * compose.c — Natural Language Composition from Derivation Results
 *
 * Generates human-readable explanations from structured DeriveResult data
 * using template-based NLG with type-specific formatting.
 */

#include "derive.h"
#include <string.h>
#include <stdio.h>

extern SemanticCore g_semantic_core;

/* ─── Template Composers ─────────────────────────────────────── */

static void compose_conflict(DeriveResult *result)
{
    /* Already composed by conflict.c, but can reformat if needed */
    /* Template: "[X] cannot function in [Y] because it requires [need] but [Y] does not have [need]." */
    if (result->answer[0] == '\0' && result->chain_len >= 2) {
        SemanticCore *core = &g_semantic_core;
        const char *subj = semantic_get_name(core, result->chain[0]);
        const char *ctx = semantic_get_name(core, result->chain[1]);
        if (subj && ctx) {
            snprintf(result->answer, sizeof(result->answer),
                     "%s cannot function in %s due to incompatible requirements.",
                     subj, ctx);
        }
    }
}

static void compose_causal(DeriveResult *result)
{
    /* Template: "This happens because [A] causes [B], which causes [C]." */
    if (result->answer[0] != '\0') return;  /* Already composed by chain.c */

    SemanticCore *core = &g_semantic_core;
    if (result->chain_len < 2) return;

    const char *first = semantic_get_name(core, result->chain[0]);
    if (!first) return;

    int written = snprintf(result->answer, sizeof(result->answer),
                           "This happens because %s causes ", first);

    for (int i = 1; i < result->chain_len && written < (int)sizeof(result->answer) - 64; i++) {
        const char *step = semantic_get_name(core, result->chain[i]);
        if (!step) step = "?";
        if (i == result->chain_len - 1) {
            written += snprintf(result->answer + written,
                                sizeof(result->answer) - (size_t)written,
                                "%s.", step);
        } else {
            written += snprintf(result->answer + written,
                                sizeof(result->answer) - (size_t)written,
                                "%s, which causes ", step);
        }
    }
}

static void compose_inherit(DeriveResult *result, const char *property)
{
    /* Template: "Yes, [X] has [property] because it is a [parent], and all [parent]s have [property]." */
    if (result->answer[0] != '\0') return;

    SemanticCore *core = &g_semantic_core;
    if (result->chain_len < 2) return;

    const char *child = semantic_get_name(core, result->chain[0]);
    const char *parent = semantic_get_name(core, result->chain[result->chain_len - 1]);
    if (!child || !parent || !property) return;

    snprintf(result->answer, sizeof(result->answer),
             "Yes, %s has %s because it is a %s, and all %ss have %s.",
             child, property, parent, parent, property);
}

static void compose_analogy(DeriveResult *result)
{
    /* Template: "[X] is similar to [Y] — both [shared1] and [shared2]." */
    /* Already composed by analogy engine; this is a fallback */
    if (result->answer[0] != '\0') return;

    SemanticCore *core = &g_semantic_core;
    if (result->chain_len < 2) return;

    const char *a = semantic_get_name(core, result->chain[0]);
    const char *b = semantic_get_name(core, result->chain[1]);
    if (a && b) {
        snprintf(result->answer, sizeof(result->answer),
                 "%s is similar to %s based on shared characteristics.", a, b);
    }
}

static void compose_whatif(DeriveResult *result)
{
    /* Template: "If [change] happens to [subject], then [consequence] would follow." */
    /* Already composed by whatif.c; fallback only */
    if (result->answer[0] != '\0') return;

    if (result->chain_len >= 1) {
        SemanticCore *core = &g_semantic_core;
        const char *subj = semantic_get_name(core, result->chain[0]);
        if (subj) {
            snprintf(result->answer, sizeof(result->answer),
                     "If that change happens to %s, consequences would follow from the causal chain.",
                     subj);
        }
    }
}

/* ─── Public API ─────────────────────────────────────────────── */

void compose_derivation(DeriveResult *result, const char *property)
{
    if (!result) return;

    switch (result->derivation_type) {
    case DERIVE_CONFLICT:
        compose_conflict(result);
        break;
    case DERIVE_CAUSAL:
        compose_causal(result);
        break;
    case DERIVE_INHERIT:
        compose_inherit(result, property);
        break;
    case DERIVE_ANALOGY:
        compose_analogy(result);
        break;
    case DERIVE_WHATIF:
        compose_whatif(result);
        break;
    case DERIVE_UNKNOWN:
    default:
        if (result->answer[0] == '\0') {
            snprintf(result->answer, sizeof(result->answer),
                     "I don't have enough information to answer that.");
        }
        break;
    }
}

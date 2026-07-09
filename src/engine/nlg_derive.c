/*
 * nlg_derive.c — Extended NLG with Confidence Signaling
 *
 * Wraps derivation results with confidence-appropriate hedging:
 *   High (>0.9):    Direct statement
 *   Medium (0.6-0.9): "likely" / "based on..."
 *   Low (0.3-0.6):   "possibly" / "it seems..."
 *   Very low (<0.3):  "I'm not certain but..."
 */

#include "derive.h"
#include <string.h>
#include <stdio.h>

extern SemanticCore g_semantic_core;

/* ─── Confidence Prefixes ────────────────────────────────────── */

static const char *high_confidence_prefixes[] = {
    "",
    "Clearly, ",
    "Definitively, ",
    NULL
};

static const char *medium_confidence_prefixes[] = {
    "Based on what I know, ",
    "It is likely that ",
    "From the available information, ",
    NULL
};

static const char *low_confidence_prefixes[] = {
    "Possibly, ",
    "It seems that ",
    "There's some indication that ",
    NULL
};

static const char *very_low_confidence_prefixes[] = {
    "I'm not certain, but ",
    "This is uncertain, however ",
    "With low confidence, ",
    NULL
};

/* Simple hash for variety in prefix selection */
static int prefix_selector(const char *answer)
{
    unsigned int hash = 0;
    if (answer) {
        for (int i = 0; answer[i] && i < 32; i++)
            hash = hash * 31 + (unsigned char)answer[i];
    }
    return (int)(hash % 3);
}

/* ─── Public API ─────────────────────────────────────────────── */

void nlg_apply_confidence(DeriveResult *result)
{
    if (!result || result->answer[0] == '\0') return;

    /* Don't re-wrap if it's an unknown/failure result */
    if (result->derivation_type == DERIVE_UNKNOWN) return;

    char original[512];
    strncpy(original, result->answer, sizeof(original) - 1);
    original[sizeof(original) - 1] = '\0';

    const char *prefix = "";
    int sel = prefix_selector(original);

    if (result->confidence > 0.9f) {
        prefix = high_confidence_prefixes[sel];
    } else if (result->confidence > 0.6f) {
        prefix = medium_confidence_prefixes[sel];
    } else if (result->confidence > 0.3f) {
        prefix = low_confidence_prefixes[sel];
    } else {
        prefix = very_low_confidence_prefixes[sel];
    }

    if (prefix[0] != '\0') {
        snprintf(result->answer, sizeof(result->answer), "%s%s", prefix, original);
    }
}

/* Add confidence suffix for transparency */
void nlg_add_confidence_note(DeriveResult *result)
{
    if (!result || result->answer[0] == '\0') return;
    if (result->derivation_type == DERIVE_UNKNOWN) return;

    size_t len = strlen(result->answer);
    size_t remaining = sizeof(result->answer) - len - 1;

    if (remaining > 30) {
        const char *method = "unknown";
        switch (result->derivation_type) {
        case DERIVE_DIRECT:   method = "direct lookup"; break;
        case DERIVE_INHERIT:  method = "inheritance"; break;
        case DERIVE_CONFLICT: method = "conflict detection"; break;
        case DERIVE_CAUSAL:   method = "causal reasoning"; break;
        case DERIVE_ANALOGY:  method = "analogy"; break;
        case DERIVE_WHATIF:   method = "counterfactual"; break;
        case DERIVE_COMPOSE:  method = "composition"; break;
        default: break;
        }

        snprintf(result->answer + len, remaining,
                 " [via %s, confidence: %.0f%%]",
                 method, (double)(result->confidence * 100.0f));
    }
}

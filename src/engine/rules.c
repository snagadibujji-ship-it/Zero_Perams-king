/*
 * rules.c — Paradox Rule Storage & Post-Reasoning Validation
 *
 * Fires AFTER normal reasoning to check if an obvious answer might be wrong.
 * For example: "Can a whale breathe underwater?" — inheritance says yes (mammal→breathes),
 * but a paradox rule catches that whales breathe air despite living in water.
 */

#include "derive.h"
#include <string.h>
#include <stdio.h>
#include <ctype.h>

extern SemanticCore g_semantic_core;

/* ─── Rule Definitions ───────────────────────────────────────── */

#define MAX_RULES 64

typedef enum {
    RULE_EXCEPTION,       /* X is a Y, but X does NOT have property P of Y */
    RULE_CONTEXT_FLIP,    /* Property P is true in context A but false in context B */
    RULE_NEGATION,        /* If A then NOT B (even though inheritance suggests B) */
    RULE_CONDITIONAL      /* A has P only if condition C */
} RuleType;

typedef struct {
    RuleType type;
    uint32_t subject_id;      /* Concept this rule applies to (0 = wildcard) */
    uint32_t parent_id;       /* Parent whose property is being overridden */
    char property[64];        /* Property being excepted */
    char correction[256];     /* What should be said instead */
    float priority;           /* Higher = fires first */
} ParadoxRule;

static ParadoxRule g_rules[MAX_RULES];
static int g_rule_count = 0;

/* ─── Rule Registration ──────────────────────────────────────── */

int rules_add_exception(uint32_t subject_id, uint32_t parent_id,
                        const char *property, const char *correction)
{
    if (g_rule_count >= MAX_RULES) return -1;

    ParadoxRule *r = &g_rules[g_rule_count];
    r->type = RULE_EXCEPTION;
    r->subject_id = subject_id;
    r->parent_id = parent_id;
    strncpy(r->property, property ? property : "", sizeof(r->property) - 1);
    r->property[sizeof(r->property) - 1] = '\0';
    strncpy(r->correction, correction ? correction : "", sizeof(r->correction) - 1);
    r->correction[sizeof(r->correction) - 1] = '\0';
    r->priority = 1.0f;

    g_rule_count++;
    return 0;
}

int rules_add_negation(uint32_t subject_id, const char *property,
                       const char *correction)
{
    if (g_rule_count >= MAX_RULES) return -1;

    ParadoxRule *r = &g_rules[g_rule_count];
    r->type = RULE_NEGATION;
    r->subject_id = subject_id;
    r->parent_id = 0;
    strncpy(r->property, property ? property : "", sizeof(r->property) - 1);
    r->property[sizeof(r->property) - 1] = '\0';
    strncpy(r->correction, correction ? correction : "", sizeof(r->correction) - 1);
    r->correction[sizeof(r->correction) - 1] = '\0';
    r->priority = 1.5f;  /* Negations override inheritance */

    g_rule_count++;
    return 0;
}

int rules_add_conditional(uint32_t subject_id, const char *property,
                          const char *condition, const char *correction)
{
    if (g_rule_count >= MAX_RULES) return -1;
    (void)condition;  /* Stored in correction for now */

    ParadoxRule *r = &g_rules[g_rule_count];
    r->type = RULE_CONDITIONAL;
    r->subject_id = subject_id;
    r->parent_id = 0;
    strncpy(r->property, property ? property : "", sizeof(r->property) - 1);
    r->property[sizeof(r->property) - 1] = '\0';
    strncpy(r->correction, correction ? correction : "", sizeof(r->correction) - 1);
    r->correction[sizeof(r->correction) - 1] = '\0';
    r->priority = 0.8f;

    g_rule_count++;
    return 0;
}

/* ─── Rule Checking (Post-Reasoning Validation) ──────────────── */

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

int rules_check(DeriveResult *result, uint32_t subject_id, const char *property)
{
    if (!result || !property) return 0;

    int corrections = 0;

    for (int i = 0; i < g_rule_count; i++) {
        ParadoxRule *r = &g_rules[i];

        /* Check if rule applies to this subject */
        if (r->subject_id != 0 && r->subject_id != subject_id)
            continue;

        /* Check if rule applies to this property */
        if (r->property[0] != '\0' && !contains_ci(property, r->property))
            continue;

        /* Rule matches — apply correction */
        switch (r->type) {
        case RULE_EXCEPTION:
            /* Inheritance gave us a property that this concept actually lacks */
            if (result->derivation_type == DERIVE_INHERIT) {
                /* Check if the inheritance chain went through the parent being excepted */
                int chain_has_parent = 0;
                for (int c = 0; c < result->chain_len; c++) {
                    if (result->chain[c] == r->parent_id) {
                        chain_has_parent = 1;
                        break;
                    }
                }
                if (chain_has_parent && r->correction[0] != '\0') {
                    snprintf(result->answer, sizeof(result->answer), "%s", r->correction);
                    result->confidence *= 0.5f;  /* Reduce confidence due to exception */
                    corrections++;
                }
            }
            break;

        case RULE_NEGATION:
            if (r->correction[0] != '\0') {
                snprintf(result->answer, sizeof(result->answer), "%s", r->correction);
                result->confidence = 0.9f;  /* High confidence in negation */
                result->derivation_type = DERIVE_CONFLICT;
                corrections++;
            }
            break;

        case RULE_CONDITIONAL:
            if (r->correction[0] != '\0') {
                size_t len = strlen(result->answer);
                if (len < sizeof(result->answer) - 128) {
                    snprintf(result->answer + len,
                             sizeof(result->answer) - len,
                             " (Note: %s)", r->correction);
                }
                result->confidence *= 0.8f;
                corrections++;
            }
            break;

        case RULE_CONTEXT_FLIP:
            /* Context-dependent — reduce confidence */
            result->confidence *= 0.6f;
            corrections++;
            break;
        }
    }

    return corrections;
}

/* ─── Initialization & Cleanup ───────────────────────────────── */

void rules_init(void)
{
    g_rule_count = 0;
    memset(g_rules, 0, sizeof(g_rules));
}

int rules_count(void)
{
    return g_rule_count;
}

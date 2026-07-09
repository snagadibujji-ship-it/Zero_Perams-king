#include "reason.h"
#include <string.h>
#include <stdio.h>
#include <ctype.h>

#define MAX_FACTS 64

/* Helper: lowercase a string in place */
static void str_lower(char *dst, const char *src, size_t max) {
    size_t i;
    for (i = 0; i < max - 1 && src[i]; i++)
        dst[i] = (char)tolower((unsigned char)src[i]);
    dst[i] = '\0';
}

/* Helper: check if haystack contains needle (case-insensitive) */
static int str_contains(const char *haystack, const char *needle) {
    char h[512], n[256];
    str_lower(h, haystack, sizeof(h));
    str_lower(n, needle, sizeof(n));
    return strstr(h, n) != NULL;
}

/* Helper: try a single KG query, fill result if found */
static int try_query(KnowledgeGraph *kg, const char *subject, const char *relation, ReasonResult *result) {
    Fact facts[MAX_FACTS];
    char subj_low[256], rel_low[256];
    int n;

    str_lower(subj_low, subject, sizeof(subj_low));
    str_lower(rel_low, relation, sizeof(rel_low));

    n = kg_query(kg, subj_low, rel_low, facts, MAX_FACTS);
    if (n > 0) {
        const char *obj = kg_get_string(kg, facts[0].object_id);
        if (obj) {
            snprintf(result->answer, sizeof(result->answer), "%s", obj);
            result->confidence = facts[0].confidence / 255.0f;
            return 1;
        }
    }
    return 0;
}

/* Layer 1: Direct lookup with relation suffix variants */
int reason_direct_lookup(KnowledgeGraph *kg, const char *subject, const char *relation, ReasonResult *result) {
    static const char *suffixes[] = {"", "_is", "_of", "_at", "_by", "_in"};
    char combined[256];
    int i;

    /* If relation is provided, try it directly first */
    if (relation && relation[0]) {
        if (try_query(kg, subject, relation, result)) {
            result->level = REASON_DIRECT_LOOKUP;
            snprintf(result->explanation, sizeof(result->explanation),
                     "Direct lookup: %s -> %s", subject, relation);
            return 1;
        }
    }

    /* Try subject with common relation suffixes */
    for (i = 0; i < (int)(sizeof(suffixes) / sizeof(suffixes[0])); i++) {
        if (relation && relation[0]) {
            snprintf(combined, sizeof(combined), "%s%s", relation, suffixes[i]);
            if (try_query(kg, subject, combined, result)) {
                result->level = REASON_DIRECT_LOOKUP;
                snprintf(result->explanation, sizeof(result->explanation),
                         "Direct lookup: %s -> %s", subject, combined);
                return 1;
            }
        }
    }

    return 0;
}

/* Layer 2: Pattern matching on parsed intent */
int reason_pattern_match(KnowledgeGraph *kg, ParsedIntent *intent, ReasonResult *result) {
    char relation[256];
    const char *subj = intent->subject;
    const char *obj = intent->object;
    const char *raw = intent->raw_input;

    /* Pattern: "capital of X" */
    if (str_contains(raw, "capital")) {
        const char *target = obj[0] ? obj : subj;
        if (try_query(kg, target, "capital_is", result)) {
            result->level = REASON_PATTERN_MATCH;
            snprintf(result->explanation, sizeof(result->explanation),
                     "Pattern: capital of %s", target);
            return 1;
        }
    }

    /* Pattern: "who created/made/invented X" */
    if (str_contains(raw, "created") || str_contains(raw, "made") ||
        str_contains(raw, "invented") || str_contains(raw, "who")) {
        const char *target = obj[0] ? obj : subj;
        if (try_query(kg, target, "created_by", result)) {
            result->level = REASON_PATTERN_MATCH;
            snprintf(result->explanation, sizeof(result->explanation),
                     "Pattern: creator of %s", target);
            return 1;
        }
    }

    /* Pattern: "X boil/freeze" */
    if (str_contains(raw, "boil")) {
        const char *target = subj[0] ? subj : obj;
        if (try_query(kg, target, "boils_at", result)) {
            result->level = REASON_PATTERN_MATCH;
            snprintf(result->explanation, sizeof(result->explanation),
                     "Pattern: boiling point of %s", target);
            return 1;
        }
    }
    if (str_contains(raw, "freeze")) {
        const char *target = subj[0] ? subj : obj;
        if (try_query(kg, target, "freezes_at", result)) {
            result->level = REASON_PATTERN_MATCH;
            snprintf(result->explanation, sizeof(result->explanation),
                     "Pattern: freezing point of %s", target);
            return 1;
        }
    }

    /* Pattern: "X orbit" */
    if (str_contains(raw, "orbit")) {
        const char *target = subj[0] ? subj : obj;
        if (try_query(kg, target, "orbits", result)) {
            result->level = REASON_PATTERN_MATCH;
            snprintf(result->explanation, sizeof(result->explanation),
                     "Pattern: orbit of %s", target);
            return 1;
        }
    }

    /* Pattern: "what is the X of Y" → try Y, X_is or Y, X_of */
    if (intent->predicate[0] && (obj[0] || subj[0])) {
        const char *target = obj[0] ? obj : subj;
        snprintf(relation, sizeof(relation), "%s_is", intent->predicate);
        if (try_query(kg, target, relation, result)) {
            result->level = REASON_PATTERN_MATCH;
            snprintf(result->explanation, sizeof(result->explanation),
                     "Pattern: %s of %s", intent->predicate, target);
            return 1;
        }
        snprintf(relation, sizeof(relation), "%s_of", intent->predicate);
        if (try_query(kg, target, relation, result)) {
            result->level = REASON_PATTERN_MATCH;
            snprintf(result->explanation, sizeof(result->explanation),
                     "Pattern: %s of %s", intent->predicate, target);
            return 1;
        }
    }

    return 0;
}

/* Layer 3: Chain reasoning (2-hop: subject → intermediate → target) */
int reason_chain(KnowledgeGraph *kg, const char *subject, const char *target_relation, ReasonResult *result) {
    Fact first_hop[MAX_FACTS];
    Fact second_hop[MAX_FACTS];
    char subj_low[256], rel_low[256];
    int n1, n2, i, j;

    str_lower(subj_low, subject, sizeof(subj_low));

    /* Get all facts about subject (NULL relation = wildcard) */
    n1 = kg_query(kg, subj_low, NULL, first_hop, MAX_FACTS);
    if (n1 <= 0) return 0;

    str_lower(rel_low, target_relation, sizeof(rel_low));

    /* For each fact's object, query it as subject with target_relation */
    for (i = 0; i < n1; i++) {
        const char *intermediate = kg_get_string(kg, first_hop[i].object_id);
        if (!intermediate) continue;

        n2 = kg_query(kg, intermediate, rel_low, second_hop, MAX_FACTS);
        if (n2 > 0) {
            const char *final_obj = kg_get_string(kg, second_hop[0].object_id);
            if (final_obj) {
                const char *rel1 = kg_get_string(kg, first_hop[i].relation_id);
                snprintf(result->answer, sizeof(result->answer), "%s", final_obj);
                result->confidence = (first_hop[i].confidence / 255.0f) *
                                     (second_hop[0].confidence / 255.0f);
                result->level = REASON_CHAIN;
                snprintf(result->explanation, sizeof(result->explanation),
                         "Chain: %s -[%s]-> %s -[%s]-> %s",
                         subj_low, rel1 ? rel1 : "?", intermediate,
                         target_relation, final_obj);
                return 1;
            }
        }

        /* Third hop: try each second-hop object */
        for (j = 0; j < n2; j++) {
            const char *hop2_obj = kg_get_string(kg, second_hop[j].object_id);
            if (!hop2_obj) continue;
            Fact third_hop[MAX_FACTS];
            int n3 = kg_query(kg, hop2_obj, rel_low, third_hop, MAX_FACTS);
            if (n3 > 0) {
                const char *final3 = kg_get_string(kg, third_hop[0].object_id);
                if (final3) {
                    snprintf(result->answer, sizeof(result->answer), "%s", final3);
                    result->confidence = 0.5f;
                    result->level = REASON_CHAIN;
                    snprintf(result->explanation, sizeof(result->explanation),
                             "Chain (3-hop): %s -> ... -> %s", subj_low, final3);
                    return 1;
                }
            }
        }
    }

    return 0;
}

/* Master reasoning function */
void reason_query(KnowledgeGraph *kg, ParsedIntent *intent, ReasonResult *result) {
    memset(result, 0, sizeof(ReasonResult));

    /* Layer 1: Direct lookup */
    if (intent->subject[0]) {
        if (reason_direct_lookup(kg, intent->subject, intent->predicate, result))
            return;
        /* Try with object as subject */
        if (intent->object[0]) {
            if (reason_direct_lookup(kg, intent->object, intent->predicate, result))
                return;
        }
    }

    /* Layer 2: Pattern match */
    if (reason_pattern_match(kg, intent, result))
        return;

    /* Layer 3: Chain reasoning */
    if (intent->subject[0] && intent->predicate[0]) {
        if (reason_chain(kg, intent->subject, intent->predicate, result))
            return;
    }

    /* Layer 4: Analogy (not implemented) — fall through to gap */

    /* Layer 5: Gap — admit we don't know */
    snprintf(result->answer, sizeof(result->answer), "I don't know that yet.");
    result->confidence = 0.0f;
    result->level = REASON_GAP;
    snprintf(result->explanation, sizeof(result->explanation), "No reasoning path found");
}

/* ========================= TEST MODE ========================= */
#ifdef TEST_MODE
#include <assert.h>

static void setup_test_kg(KnowledgeGraph *kg) {
    kg_init(kg);
    kg_add_fact(kg, "france", "capital_is", "paris", 250);
    kg_add_fact(kg, "japan", "capital_is", "tokyo", 250);
    kg_add_fact(kg, "python", "created_by", "guido van rossum", 240);
    kg_add_fact(kg, "c", "created_by", "dennis ritchie", 240);
    kg_add_fact(kg, "water", "boils_at", "100c", 250);
    kg_add_fact(kg, "water", "freezes_at", "0c", 250);
    kg_add_fact(kg, "earth", "orbits", "sun", 250);
    kg_add_fact(kg, "sun", "type_is", "star", 250);
    kg_add_fact(kg, "mars", "orbits", "sun", 250);
    kg_add_fact(kg, "linux", "created_by", "linus torvalds", 240);
}

int main(void) {
    KnowledgeGraph kg; ReasonResult r; ParsedIntent intent;
    printf("=== Reason Engine Tests ===\n");

    /* Test 1: Direct lookup */
    setup_test_kg(&kg);
    assert(reason_direct_lookup(&kg, "france", "capital_is", &r) == 1);
    assert(strcmp(r.answer, "paris") == 0 && r.level == REASON_DIRECT_LOOKUP);
    printf("  [PASS] Direct lookup: france capital_is -> paris\n");
    kg_destroy(&kg);

    /* Test 2: Pattern match - who created python */
    setup_test_kg(&kg);
    memset(&intent, 0, sizeof(intent));
    strcpy(intent.raw_input, "who created python?");
    strcpy(intent.subject, "python"); strcpy(intent.predicate, "created");
    intent.intent_type = INTENT_QUERY;
    assert(reason_pattern_match(&kg, &intent, &r) == 1);
    assert(strcmp(r.answer, "guido van rossum") == 0 && r.level == REASON_PATTERN_MATCH);
    printf("  [PASS] Pattern match: who created python -> guido van rossum\n");
    kg_destroy(&kg);

    /* Test 3: Chain reasoning - earth orbits sun, sun type_is star */
    setup_test_kg(&kg);
    assert(reason_chain(&kg, "earth", "type_is", &r) == 1);
    assert(strcmp(r.answer, "star") == 0 && r.level == REASON_CHAIN);
    printf("  [PASS] Chain: earth -[orbits]-> sun -[type_is]-> star\n");
    kg_destroy(&kg);

    /* Test 4: Gap - unknown topic */
    setup_test_kg(&kg);
    memset(&intent, 0, sizeof(intent));
    strcpy(intent.raw_input, "what is quantum entanglement?");
    strcpy(intent.subject, "quantum entanglement"); strcpy(intent.predicate, "definition");
    intent.intent_type = INTENT_QUERY;
    reason_query(&kg, &intent, &r);
    assert(r.level == REASON_GAP && r.confidence == 0.0f);
    assert(strstr(r.answer, "don't know") != NULL);
    printf("  [PASS] Gap: unknown topic -> admits ignorance\n");
    kg_destroy(&kg);

    /* Test 5: Full pipeline - capital of france */
    setup_test_kg(&kg);
    memset(&intent, 0, sizeof(intent));
    strcpy(intent.raw_input, "what is the capital of france?");
    strcpy(intent.subject, "france"); strcpy(intent.predicate, "capital");
    intent.intent_type = INTENT_QUERY;
    reason_query(&kg, &intent, &r);
    assert(strcmp(r.answer, "paris") == 0 && r.confidence > 0.9f);
    printf("  [PASS] Full query: capital of france -> paris\n");
    kg_destroy(&kg);

    printf("=== All tests passed! ===\n");
    return 0;
}
#endif /* TEST_MODE */

#include "selftest.h"
#include <stdio.h>
#include <string.h>

/* Baseline facts that should always exist */
static struct { const char* subj; const char* rel; const char* obj; } BASELINE[] = {
    {"france", "capital_is", "paris"},
    {"japan", "capital_is", "tokyo"},
    {"germany", "capital_is", "berlin"},
    {"python", "created_by", "guido van rossum"},
    {"earth", "orbits", "sun"},
    {"water", "boils_at", "100c"},
    {"india", "capital_is", "new delhi"},
    {"linux", "created_by", "linus torvalds"},
    {"italy", "capital_is", "rome"},
    {"brazil", "capital_is", "brasilia"},
};
#define BASELINE_COUNT 10

int selftest_baseline(KnowledgeGraph* kg) {
    int passed = 0;
    Fact results[4];
    for (int i = 0; i < BASELINE_COUNT; i++) {
        int n = kg_query(kg, BASELINE[i].subj, BASELINE[i].rel, results, 4);
        if (n > 0) {
            const char* obj = kg_get_string(kg, results[0].object_id);
            if (obj && strcmp(obj, BASELINE[i].obj) == 0) {
                passed++;
            }
        }
    }
    return passed;
}

int selftest_consistency(KnowledgeGraph* kg) {
    int contradictions = 0;
    /* Check: same subject+relation should not have conflicting objects */
    for (size_t i = 0; i < kg->count; i++) {
        for (size_t j = i + 1; j < kg->count; j++) {
            if (kg->facts[i].subject_id == kg->facts[j].subject_id &&
                kg->facts[i].relation_id == kg->facts[j].relation_id &&
                kg->facts[i].object_id != kg->facts[j].object_id) {
                /* Same subject+relation but different object = potential contradiction */
                /* Only count if relation implies uniqueness (capital_is, created_by) */
                const char* rel = kg_get_string(kg, kg->facts[i].relation_id);
                if (rel && (strstr(rel, "capital_is") || strstr(rel, "created_by") ||
                           strstr(rel, "name_is"))) {
                    contradictions++;
                }
            }
        }
    }
    return contradictions;
}

int selftest_coverage(KnowledgeGraph* kg) {
    if (kg->count < 20) return 0;
    if (kg->string_count < 10) return 0;
    return 1;
}

SelfTestResult selftest_run(KnowledgeGraph* kg) {
    SelfTestResult r = {0};
    
    /* Baseline test */
    int baseline_passed = selftest_baseline(kg);
    r.tests_run += BASELINE_COUNT;
    r.tests_passed += baseline_passed;
    r.tests_failed += (BASELINE_COUNT - baseline_passed);
    if (baseline_passed < BASELINE_COUNT) {
        snprintf(r.last_failure, sizeof(r.last_failure),
                 "Baseline: %d/%d facts verified", baseline_passed, BASELINE_COUNT);
    }
    
    /* Consistency test */
    r.contradictions_found = selftest_consistency(kg);
    r.tests_run++;
    if (r.contradictions_found == 0) {
        r.tests_passed++;
    } else {
        r.tests_failed++;
        snprintf(r.last_failure, sizeof(r.last_failure),
                 "Found %d contradictions in knowledge graph", r.contradictions_found);
    }
    
    /* Coverage test */
    r.tests_run++;
    if (selftest_coverage(kg)) {
        r.tests_passed++;
    } else {
        r.tests_failed++;
        snprintf(r.last_failure, sizeof(r.last_failure),
                 "Coverage too low: %zu facts, %zu strings", kg->count, kg->string_count);
    }
    
    return r;
}

#ifdef TEST_MODE
int main(void) {
    printf("=== Self-Test Engine Tests ===\n");
    KnowledgeGraph kg;
    kg_init(&kg);
    
    /* Add baseline facts */
    for (int i = 0; i < BASELINE_COUNT; i++) {
        kg_add_fact(&kg, BASELINE[i].subj, BASELINE[i].rel, BASELINE[i].obj, 100);
    }
    /* Add more to pass coverage */
    kg_add_fact(&kg, "sun", "type_is", "star", 100);
    kg_add_fact(&kg, "moon", "orbits", "earth", 100);
    kg_add_fact(&kg, "c", "created_by", "dennis ritchie", 100);
    kg_add_fact(&kg, "javascript", "created_by", "brendan eich", 100);
    kg_add_fact(&kg, "java", "created_by", "james gosling", 100);
    kg_add_fact(&kg, "mars", "type_is", "planet", 100);
    kg_add_fact(&kg, "mercury", "type_is", "planet", 100);
    kg_add_fact(&kg, "venus", "type_is", "planet", 100);
    kg_add_fact(&kg, "jupiter", "type_is", "planet", 100);
    kg_add_fact(&kg, "saturn", "type_is", "planet", 100);
    
    /* Test 1: Baseline */
    int bp = selftest_baseline(&kg);
    printf("[%s] Baseline: %d/%d\n", bp == BASELINE_COUNT ? "PASS" : "FAIL", bp, BASELINE_COUNT);
    
    /* Test 2: Consistency (should be 0 contradictions) */
    int c = selftest_consistency(&kg);
    printf("[%s] Consistency: %d contradictions\n", c == 0 ? "PASS" : "FAIL", c);
    
    /* Test 3: Coverage */
    int cov = selftest_coverage(&kg);
    printf("[%s] Coverage: %zu facts, %zu strings\n", cov ? "PASS" : "FAIL", kg.count, kg.string_count);
    
    /* Test 4: Full run */
    SelfTestResult r = selftest_run(&kg);
    printf("[%s] Full run: %d/%d passed\n", 
           r.tests_failed == 0 ? "PASS" : "FAIL", r.tests_passed, r.tests_run);
    
    /* Test 5: Add contradiction and detect */
    kg_add_fact(&kg, "france", "capital_is", "lyon", 50);  /* WRONG */
    int c2 = selftest_consistency(&kg);
    printf("[%s] Contradiction detection: found %d\n", c2 > 0 ? "PASS" : "FAIL", c2);
    
    kg_destroy(&kg);
    printf("=== All self-test tests complete ===\n");
    return 0;
}
#endif

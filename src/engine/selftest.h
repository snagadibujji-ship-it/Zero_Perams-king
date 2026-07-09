#ifndef SELFTEST_H
#define SELFTEST_H

#include "knowledge.h"

typedef struct {
    int tests_run;
    int tests_passed;
    int tests_failed;
    int contradictions_found;
    int orphans_found;
    char last_failure[256];
} SelfTestResult;

SelfTestResult selftest_run(KnowledgeGraph* kg);
int selftest_baseline(KnowledgeGraph* kg);
int selftest_consistency(KnowledgeGraph* kg);
int selftest_coverage(KnowledgeGraph* kg);

#endif

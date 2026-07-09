/*
 * planner.c — Intent classification and task decomposition
 * Phase 7 Agent System
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <ctype.h>
#include "planner.h"

/* ─── Keyword tables for intent classification ────────────────── */

static const char *compare_keywords[] = {"compare", "vs", "versus", "difference", "differ", "better", NULL};
static const char *explain_keywords[] = {"why", "explain", "how does", "reason", "because", NULL};
static const char *create_keywords[]  = {"write", "create", "generate", "make", "build", "implement", NULL};
static const char *find_keywords[]    = {"find", "search", "where", "locate", "lookup", "look up", NULL};
static const char *analyze_keywords[] = {"analyze", "check", "inspect", "review", "evaluate", "assess", NULL};
static const char *do_keywords[]      = {"do", "run", "execute", "perform", "launch", "start", NULL};
static const char *learn_keywords[]   = {"remember", "learn", "teach", "store", "save that", NULL};
static const char *whatif_keywords[]  = {"what if", "what would", "suppose", "imagine if", "hypothetically", NULL};

/* ─── Helper: case-insensitive substring search ───────────────── */

static int contains_ci(const char *haystack, const char *needle) {
    if (!haystack || !needle) return 0;
    size_t hlen = strlen(haystack);
    size_t nlen = strlen(needle);
    if (nlen > hlen) return 0;
    for (size_t i = 0; i <= hlen - nlen; i++) {
        int match = 1;
        for (size_t j = 0; j < nlen; j++) {
            if (tolower((unsigned char)haystack[i + j]) != tolower((unsigned char)needle[j])) {
                match = 0;
                break;
            }
        }
        if (match) return 1;
    }
    return 0;
}

static int matches_keywords(const char *input, const char **keywords) {
    for (int i = 0; keywords[i] != NULL; i++) {
        if (contains_ci(input, keywords[i])) return 1;
    }
    return 0;
}

/* ─── Intent Classification ───────────────────────────────────── */

PlanIntentType plan_classify_intent(const char *input) {
    if (!input) return PLAN_INTENT_FIND;

    /* Check multi-word patterns first (more specific) */
    if (matches_keywords(input, whatif_keywords))   return PLAN_INTENT_WHATIF;
    if (matches_keywords(input, compare_keywords))  return PLAN_INTENT_COMPARE;
    if (matches_keywords(input, explain_keywords))  return PLAN_INTENT_EXPLAIN;
    if (matches_keywords(input, create_keywords))   return PLAN_INTENT_CREATE;
    if (matches_keywords(input, analyze_keywords))  return PLAN_INTENT_ANALYZE;
    if (matches_keywords(input, do_keywords))       return PLAN_INTENT_DO;
    if (matches_keywords(input, learn_keywords))    return PLAN_INTENT_LEARN;
    if (matches_keywords(input, find_keywords))     return PLAN_INTENT_FIND;

    /* Default: treat as a find/query */
    return PLAN_INTENT_FIND;
}

/* ─── Task Decomposition per Intent ───────────────────────────── */

static void decompose_compare(Plan *plan, const char *request) {
    /* Task 0: query knowledge about subject A */
    PlanTask *t0 = &plan->tasks[0];
    t0->id = 0;
    snprintf(t0->description, sizeof(t0->description), "Retrieve knowledge about first subject");
    t0->agent_id = 0;  /* knowledge agent */
    t0->n_depends = 0;
    t0->status = PLAN_TASK_PENDING;
    t0->confidence = 0.0f;
    t0->retries = 0;

    /* Task 1: query knowledge about subject B */
    PlanTask *t1 = &plan->tasks[1];
    t1->id = 1;
    snprintf(t1->description, sizeof(t1->description), "Retrieve knowledge about second subject");
    t1->agent_id = 0;  /* knowledge agent */
    t1->n_depends = 0;
    t1->status = PLAN_TASK_PENDING;
    t1->confidence = 0.0f;
    t1->retries = 0;

    /* Task 2: reasoning to compare (depends on 0 and 1) */
    PlanTask *t2 = &plan->tasks[2];
    t2->id = 2;
    snprintf(t2->description, sizeof(t2->description), "Compare and contrast findings: %s", request);
    t2->agent_id = 1;  /* reasoning agent */
    t2->depends_on[0] = 0;
    t2->depends_on[1] = 1;
    t2->n_depends = 2;
    t2->status = PLAN_TASK_PENDING;
    t2->confidence = 0.0f;
    t2->retries = 0;

    plan->n_tasks = 3;
}

static void decompose_explain(Plan *plan, const char *request) {
    PlanTask *t0 = &plan->tasks[0];
    t0->id = 0;
    snprintf(t0->description, sizeof(t0->description), "Lookup relevant knowledge: %s", request);
    t0->agent_id = 0;  /* knowledge */
    t0->n_depends = 0;
    t0->status = PLAN_TASK_PENDING;
    t0->confidence = 0.0f;
    t0->retries = 0;

    PlanTask *t1 = &plan->tasks[1];
    t1->id = 1;
    snprintf(t1->description, sizeof(t1->description), "Derive causal explanation: %s", request);
    t1->agent_id = 1;  /* reasoning */
    t1->depends_on[0] = 0;
    t1->n_depends = 1;
    t1->status = PLAN_TASK_PENDING;
    t1->confidence = 0.0f;
    t1->retries = 0;

    plan->n_tasks = 2;
}

static void decompose_create(Plan *plan, const char *request) {
    PlanTask *t0 = &plan->tasks[0];
    t0->id = 0;
    snprintf(t0->description, sizeof(t0->description), "Generate code: %s", request);
    t0->agent_id = 2;  /* code agent */
    t0->n_depends = 0;
    t0->status = PLAN_TASK_PENDING;
    t0->confidence = 0.0f;
    t0->retries = 0;

    plan->n_tasks = 1;
}

static void decompose_find(Plan *plan, const char *request) {
    PlanTask *t0 = &plan->tasks[0];
    t0->id = 0;
    snprintf(t0->description, sizeof(t0->description), "Search knowledge graph: %s", request);
    t0->agent_id = 0;  /* knowledge */
    t0->n_depends = 0;
    t0->status = PLAN_TASK_PENDING;
    t0->confidence = 0.0f;
    t0->retries = 0;

    /* Task 1: fallback web search if local fails */
    PlanTask *t1 = &plan->tasks[1];
    t1->id = 1;
    snprintf(t1->description, sizeof(t1->description), "Web search fallback: %s", request);
    t1->agent_id = 3;  /* web agent */
    t1->depends_on[0] = 0;
    t1->n_depends = 1;
    t1->status = PLAN_TASK_PENDING;
    t1->confidence = 0.0f;
    t1->retries = 0;

    plan->n_tasks = 2;
}

static void decompose_analyze(Plan *plan, const char *request) {
    PlanTask *t0 = &plan->tasks[0];
    t0->id = 0;
    snprintf(t0->description, sizeof(t0->description), "Gather data for analysis: %s", request);
    t0->agent_id = 0;  /* knowledge */
    t0->n_depends = 0;
    t0->status = PLAN_TASK_PENDING;
    t0->confidence = 0.0f;
    t0->retries = 0;

    PlanTask *t1 = &plan->tasks[1];
    t1->id = 1;
    snprintf(t1->description, sizeof(t1->description), "Perform reasoning analysis: %s", request);
    t1->agent_id = 1;  /* reasoning */
    t1->depends_on[0] = 0;
    t1->n_depends = 1;
    t1->status = PLAN_TASK_PENDING;
    t1->confidence = 0.0f;
    t1->retries = 0;

    PlanTask *t2 = &plan->tasks[2];
    t2->id = 2;
    snprintf(t2->description, sizeof(t2->description), "Calculate metrics if applicable");
    t2->agent_id = 5;  /* math */
    t2->depends_on[0] = 0;
    t2->n_depends = 1;
    t2->status = PLAN_TASK_PENDING;
    t2->confidence = 0.0f;
    t2->retries = 0;

    plan->n_tasks = 3;
}

static void decompose_do(Plan *plan, const char *request) {
    PlanTask *t0 = &plan->tasks[0];
    t0->id = 0;
    snprintf(t0->description, sizeof(t0->description), "Execute action: %s", request);
    t0->agent_id = 4;  /* file/shell agent */
    t0->n_depends = 0;
    t0->status = PLAN_TASK_PENDING;
    t0->confidence = 0.0f;
    t0->retries = 0;

    plan->n_tasks = 1;
}

static void decompose_learn(Plan *plan, const char *request) {
    PlanTask *t0 = &plan->tasks[0];
    t0->id = 0;
    snprintf(t0->description, sizeof(t0->description), "Store knowledge: %s", request);
    t0->agent_id = 6;  /* memory agent */
    t0->n_depends = 0;
    t0->status = PLAN_TASK_PENDING;
    t0->confidence = 0.0f;
    t0->retries = 0;

    plan->n_tasks = 1;
}

static void decompose_whatif(Plan *plan, const char *request) {
    PlanTask *t0 = &plan->tasks[0];
    t0->id = 0;
    snprintf(t0->description, sizeof(t0->description), "Lookup baseline state: %s", request);
    t0->agent_id = 0;  /* knowledge */
    t0->n_depends = 0;
    t0->status = PLAN_TASK_PENDING;
    t0->confidence = 0.0f;
    t0->retries = 0;

    PlanTask *t1 = &plan->tasks[1];
    t1->id = 1;
    snprintf(t1->description, sizeof(t1->description), "Simulate scenario: %s", request);
    t1->agent_id = 7;  /* creative/whatif agent */
    t1->depends_on[0] = 0;
    t1->n_depends = 1;
    t1->status = PLAN_TASK_PENDING;
    t1->confidence = 0.0f;
    t1->retries = 0;

    PlanTask *t2 = &plan->tasks[2];
    t2->id = 2;
    snprintf(t2->description, sizeof(t2->description), "Reason about consequences");
    t2->agent_id = 1;  /* reasoning */
    t2->depends_on[0] = 1;
    t2->n_depends = 1;
    t2->status = PLAN_TASK_PENDING;
    t2->confidence = 0.0f;
    t2->retries = 0;

    plan->n_tasks = 3;
}

/* ─── Main Plan Creation ──────────────────────────────────────── */

Plan* plan_create(const char *request) {
    if (!request) return NULL;

    Plan *plan = (Plan*)calloc(1, sizeof(Plan));
    if (!plan) return NULL;

    snprintf(plan->goal, sizeof(plan->goal), "%s", request);
    plan->intent = plan_classify_intent(request);
    plan->overall_confidence = 0.0f;
    plan->elapsed_ms = 0;

    switch (plan->intent) {
        case PLAN_INTENT_COMPARE: decompose_compare(plan, request); break;
        case PLAN_INTENT_EXPLAIN: decompose_explain(plan, request); break;
        case PLAN_INTENT_CREATE:  decompose_create(plan, request);  break;
        case PLAN_INTENT_FIND:    decompose_find(plan, request);    break;
        case PLAN_INTENT_ANALYZE: decompose_analyze(plan, request); break;
        case PLAN_INTENT_DO:      decompose_do(plan, request);      break;
        case PLAN_INTENT_LEARN:   decompose_learn(plan, request);   break;
        case PLAN_INTENT_WHATIF:  decompose_whatif(plan, request);  break;
    }

    return plan;
}

void plan_free(Plan *plan) {
    if (plan) free(plan);
}

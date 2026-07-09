/*
 * executor.c — Plan execution loop with dependency resolution
 * Phase 7 Agent System
 *
 * Finds ready tasks (all dependencies met), executes them via agent pool,
 * handles failures (retry with alt agent or mark failed), composes final answer.
 */

#define _POSIX_C_SOURCE 199309L

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include "planner.h"

#define MAX_RETRIES 2
#define ANSWER_BUF_SIZE 4096

/* ─── Helpers ─────────────────────────────────────────────────── */

static int task_is_ready(Plan *plan, int task_idx) {
    PlanTask *task = &plan->tasks[task_idx];
    if (task->status != PLAN_TASK_PENDING) return 0;

    for (int i = 0; i < task->n_depends; i++) {
        int dep_id = task->depends_on[i];
        if (dep_id < 0 || dep_id >= plan->n_tasks) continue;
        PlanTask *dep = &plan->tasks[dep_id];
        if (dep->status != PLAN_TASK_DONE && dep->status != PLAN_TASK_SKIPPED) {
            return 0;
        }
    }
    return 1;
}

static int all_tasks_complete(Plan *plan) {
    for (int i = 0; i < plan->n_tasks; i++) {
        PlanTaskStatus s = plan->tasks[i].status;
        if (s == PLAN_TASK_PENDING || s == PLAN_TASK_RUNNING) return 0;
    }
    return 1;
}

static int select_alt_agent(int original_agent_id) {
    /* Return an alternative agent for retry.
     * Strategy: knowledge->reasoning, reasoning->knowledge, code->creative,
     * web->knowledge, file->knowledge, math->reasoning, memory->knowledge, creative->reasoning */
    static const int alt_map[PLAN_MAX_AGENTS] = {1, 0, 7, 0, 0, 1, 0, 1};
    if (original_agent_id < 0 || original_agent_id >= PLAN_MAX_AGENTS)
        return 0;
    return alt_map[original_agent_id];
}

/* ─── Check if a dependent task should be skipped (e.g., find+web fallback) ── */

static int should_skip_fallback(Plan *plan, PlanTask *task) {
    /* For FIND intent: if task 1 (web) depends on task 0 (kg) and task 0 succeeded
     * with high confidence, skip the web fallback */
    if (plan->intent == PLAN_INTENT_FIND && task->id == 1 && task->n_depends == 1) {
        int dep_id = task->depends_on[0];
        if (dep_id >= 0 && dep_id < plan->n_tasks) {
            PlanTask *dep = &plan->tasks[dep_id];
            if (dep->status == PLAN_TASK_DONE && dep->confidence >= 0.7f) {
                return 1;
            }
        }
    }
    return 0;
}

/* ─── Execute a Single Task ───────────────────────────────────── */

static void execute_task(Plan *plan, int task_idx) {
    PlanTask *task = &plan->tasks[task_idx];

    /* Check if this task should be skipped */
    if (should_skip_fallback(plan, task)) {
        task->status = PLAN_TASK_SKIPPED;
        snprintf(task->result, sizeof(task->result), "(skipped — sufficient confidence from dependency)");
        return;
    }

    task->status = PLAN_TASK_RUNNING;

    /* Safety check on the task description */
    SafetyVerdict sv = safety_check(task->description);
    if (sv == SAFETY_BLOCK) {
        task->status = PLAN_TASK_FAILED;
        snprintf(task->result, sizeof(task->result), "BLOCKED by safety gate");
        task->confidence = 0.0f;
        return;
    }

    /* Execute via agent pool */
    int success = agent_pool_execute(task->agent_id, task->description,
                                     task->result, (int)sizeof(task->result));

    if (success) {
        task->status = PLAN_TASK_DONE;
        task->confidence = 0.75f;  /* Default confidence for successful execution */
    } else {
        /* Retry with alternative agent */
        task->retries++;
        if (task->retries <= MAX_RETRIES) {
            int alt = select_alt_agent(task->agent_id);
            success = agent_pool_execute(alt, task->description,
                                         task->result, (int)sizeof(task->result));
            if (success) {
                task->status = PLAN_TASK_DONE;
                task->confidence = 0.5f;  /* Lower confidence for alt-agent result */
            } else {
                task->status = PLAN_TASK_FAILED;
                task->confidence = 0.0f;
            }
        } else {
            task->status = PLAN_TASK_FAILED;
            task->confidence = 0.0f;
        }
    }
}

/* ─── Main Execution Loop ─────────────────────────────────────── */

int plan_execute(Plan *plan) {
    if (!plan || plan->n_tasks <= 0) return 0;

    struct timespec start, end;
    clock_gettime(CLOCK_MONOTONIC, &start);

    agent_pool_init();
    tools_init();

    int iterations = 0;
    int max_iterations = plan->n_tasks * (MAX_RETRIES + 1) + 1;

    while (!all_tasks_complete(plan) && iterations < max_iterations) {
        int made_progress = 0;

        for (int i = 0; i < plan->n_tasks; i++) {
            if (task_is_ready(plan, i)) {
                execute_task(plan, i);
                made_progress = 1;
            }
        }

        /* If no progress and not complete, mark remaining as failed (deadlock) */
        if (!made_progress) {
            for (int i = 0; i < plan->n_tasks; i++) {
                if (plan->tasks[i].status == PLAN_TASK_PENDING) {
                    plan->tasks[i].status = PLAN_TASK_FAILED;
                    snprintf(plan->tasks[i].result, sizeof(plan->tasks[i].result),
                             "Deadlock: dependencies unresolvable");
                }
            }
            break;
        }

        iterations++;
    }

    /* Calculate overall confidence */
    float conf_sum = 0.0f;
    int conf_count = 0;
    for (int i = 0; i < plan->n_tasks; i++) {
        if (plan->tasks[i].status == PLAN_TASK_DONE) {
            conf_sum += plan->tasks[i].confidence;
            conf_count++;
        }
    }
    plan->overall_confidence = conf_count > 0 ? conf_sum / (float)conf_count : 0.0f;

    clock_gettime(CLOCK_MONOTONIC, &end);
    plan->elapsed_ms = (int)((end.tv_sec - start.tv_sec) * 1000 +
                             (end.tv_nsec - start.tv_nsec) / 1000000);

    return conf_count;  /* Number of successfully completed tasks */
}

/* ─── Compose Final Answer ────────────────────────────────────── */

static char answer_buffer[ANSWER_BUF_SIZE];

const char* plan_get_answer(Plan *plan) {
    if (!plan) return "No plan available.";

    answer_buffer[0] = '\0';
    int offset = 0;
    int tasks_with_results = 0;

    /* Collect results from completed tasks in order */
    for (int i = 0; i < plan->n_tasks; i++) {
        PlanTask *task = &plan->tasks[i];
        if (task->status == PLAN_TASK_DONE && task->result[0] != '\0') {
            int written;
            if (plan->n_tasks == 1) {
                /* Single-task plan: just return the result directly */
                written = snprintf(answer_buffer + offset,
                                   (size_t)(ANSWER_BUF_SIZE - offset),
                                   "%s", task->result);
            } else if (tasks_with_results == 0) {
                written = snprintf(answer_buffer + offset,
                                   (size_t)(ANSWER_BUF_SIZE - offset),
                                   "%s", task->result);
            } else {
                written = snprintf(answer_buffer + offset,
                                   (size_t)(ANSWER_BUF_SIZE - offset),
                                   " | %s", task->result);
            }
            if (written > 0 && offset + written < ANSWER_BUF_SIZE) {
                offset += written;
            }
            tasks_with_results++;
        }
    }

    if (tasks_with_results == 0) {
        /* All tasks failed */
        snprintf(answer_buffer, ANSWER_BUF_SIZE,
                 "I couldn't complete that request. %d/%d tasks failed.",
                 plan->n_tasks, plan->n_tasks);
    }

    return answer_buffer;
}

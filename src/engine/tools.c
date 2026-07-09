/*
 * tools.c — 12 tools for the agent planner system
 * Phase 7 Agent System
 *
 * Tools: kg_query, kg_learn, calculate, memory_recall, memory_store,
 *        web_search, file_read, file_list, shell_exec, timer, code_gen, derive
 */

#define _POSIX_C_SOURCE 199309L

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include "planner.h"

/* ─── Tool Registry ───────────────────────────────────────────── */

static PlanTool tool_registry[PLAN_MAX_TOOLS] = {
    { "kg_query",      "Query knowledge graph for facts about a subject",    SAFETY_SAFE,      500  },
    { "kg_learn",      "Add a new fact to the knowledge graph",              SAFETY_SAFE,      200  },
    { "calculate",     "Evaluate a mathematical expression",                 SAFETY_SAFE,      100  },
    { "memory_recall", "Recall from conversation working memory",            SAFETY_SAFE,      50   },
    { "memory_store",  "Store information in working memory",                SAFETY_SAFE,      50   },
    { "web_search",    "Search Wikipedia/DuckDuckGo for information",        SAFETY_ASK_USER,  5000 },
    { "file_read",     "Read contents of a local file",                      SAFETY_ASK_USER,  1000 },
    { "file_list",     "List files in a directory",                          SAFETY_SAFE,      500  },
    { "shell_exec",    "Execute a shell command",                            SAFETY_DANGEROUS, 10000},
    { "timer",         "Measure elapsed time for operations",                SAFETY_SAFE,      10   },
    { "code_gen",      "Generate code in Python/C/JS/Bash",                  SAFETY_SAFE,      2000 },
    { "derive",        "Derive new knowledge via inference chains",          SAFETY_SAFE,      1000 }
};

static int tools_initialized = 0;

/* ─── Tool Management ─────────────────────────────────────────── */

void tools_init(void) {
    tools_initialized = 1;
}

PlanTool* tools_get(int id) {
    if (id < 0 || id >= PLAN_MAX_TOOLS) return NULL;
    return &tool_registry[id];
}

/* ─── Tool Implementations ────────────────────────────────────── */

static int tool_kg_query(const char *input, char *output, int output_max) {
    /* Would call kg_query() from knowledge.h */
    snprintf(output, (size_t)output_max, "KG result for: %.200s", input);
    return 1;
}

static int tool_kg_learn(const char *input, char *output, int output_max) {
    /* Would call learn_from_input() from learn.h */
    snprintf(output, (size_t)output_max, "Learned: %.200s", input);
    return 1;
}

static int tool_calculate(const char *input, char *output, int output_max) {
    /* Simple expression evaluator */
    double a = 0, b = 0;
    char op = '+';
    if (sscanf(input, "%lf %c %lf", &a, &op, &b) == 3) {
        double result = 0;
        switch (op) {
            case '+': result = a + b; break;
            case '-': result = a - b; break;
            case '*': result = a * b; break;
            case '/': result = (b != 0) ? a / b : 0; break;
            case '%': result = (b != 0) ? (double)((long)a % (long)b) : 0; break;
            default:  result = 0; break;
        }
        snprintf(output, (size_t)output_max, "%.6g", result);
    } else {
        snprintf(output, (size_t)output_max, "Cannot parse expression: %.100s", input);
        return 0;
    }
    return 1;
}

static int tool_memory_recall(const char *input, char *output, int output_max) {
    /* Would call memory_get_context() from memory.h */
    snprintf(output, (size_t)output_max, "Memory recall for: %.200s", input);
    return 1;
}

static int tool_memory_store(const char *input, char *output, int output_max) {
    /* Would call memory_add() from memory.h */
    snprintf(output, (size_t)output_max, "Stored in memory: %.200s", input);
    return 1;
}

static int tool_web_search(const char *input, char *output, int output_max) {
    /* Would invoke Python web_search bridge */
    snprintf(output, (size_t)output_max, "Web search: %.200s (requires Python bridge)", input);
    return 1;
}

static int tool_file_read(const char *input, char *output, int output_max) {
    if (!input || strlen(input) == 0) {
        snprintf(output, (size_t)output_max, "Error: no filename specified");
        return 0;
    }
    /* Safety check */
    SafetyVerdict v = safety_check_command(input);
    if (v == SAFETY_BLOCK) {
        snprintf(output, (size_t)output_max, "BLOCKED: unsafe file path");
        return 0;
    }
    FILE *f = fopen(input, "r");
    if (!f) {
        snprintf(output, (size_t)output_max, "Error: cannot open '%s'", input);
        return 0;
    }
    size_t n = fread(output, 1, (size_t)(output_max - 1), f);
    output[n] = '\0';
    fclose(f);
    return 1;
}

static int tool_file_list(const char *input, char *output, int output_max) {
    char cmd[512];
    snprintf(cmd, sizeof(cmd), "ls -la %.400s 2>&1", input ? input : ".");
    FILE *fp = popen(cmd, "r");
    if (!fp) {
        snprintf(output, (size_t)output_max, "Error: cannot list directory");
        return 0;
    }
    size_t total = 0;
    while (total < (size_t)(output_max - 1) && fgets(output + total, output_max - (int)total, fp)) {
        total = strlen(output);
    }
    pclose(fp);
    return 1;
}

static int tool_shell_exec(const char *input, char *output, int output_max) {
    if (!input || strlen(input) == 0) {
        snprintf(output, (size_t)output_max, "Error: no command specified");
        return 0;
    }
    SafetyVerdict v = safety_check_command(input);
    if (v == SAFETY_BLOCK) {
        snprintf(output, (size_t)output_max, "BLOCKED: forbidden command");
        return 0;
    }
    if (v == SAFETY_WARN) {
        snprintf(output, (size_t)output_max, "WARNING: dangerous command, requires confirmation");
        return 0;
    }
    FILE *fp = popen(input, "r");
    if (!fp) {
        snprintf(output, (size_t)output_max, "Error: cannot execute command");
        return 0;
    }
    size_t total = 0;
    while (total < (size_t)(output_max - 1) && fgets(output + total, output_max - (int)total, fp)) {
        total = strlen(output);
    }
    pclose(fp);
    return 1;
}

static int tool_timer(const char *input, char *output, int output_max) {
    (void)input;
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    snprintf(output, (size_t)output_max, "%ld.%09ld", ts.tv_sec, ts.tv_nsec);
    return 1;
}

static int tool_code_gen(const char *input, char *output, int output_max) {
    /* Would call codegen_generate() from codegen.h */
    snprintf(output, (size_t)output_max, "Generated code for: %.200s", input);
    return 1;
}

static int tool_derive(const char *input, char *output, int output_max) {
    /* Would call derive_answer() from derive.h */
    snprintf(output, (size_t)output_max, "Derived: %.200s", input);
    return 1;
}

/* ─── Dispatch Table ──────────────────────────────────────────── */

typedef int (*ToolExecFn)(const char*, char*, int);

static ToolExecFn tool_executors[PLAN_MAX_TOOLS] = {
    tool_kg_query,      /* 0 */
    tool_kg_learn,      /* 1 */
    tool_calculate,     /* 2 */
    tool_memory_recall, /* 3 */
    tool_memory_store,  /* 4 */
    tool_web_search,    /* 5 */
    tool_file_read,     /* 6 */
    tool_file_list,     /* 7 */
    tool_shell_exec,    /* 8 */
    tool_timer,         /* 9 */
    tool_code_gen,      /* 10 */
    tool_derive         /* 11 */
};

int tool_execute(int tool_id, const char *input, char *output, int output_max) {
    if (!tools_initialized) tools_init();
    if (tool_id < 0 || tool_id >= PLAN_MAX_TOOLS) return 0;
    if (!output || output_max <= 0) return 0;

    /* Check safety level */
    PlanTool *tool = &tool_registry[tool_id];
    if (tool->safety == SAFETY_FORBIDDEN) {
        snprintf(output, (size_t)output_max, "FORBIDDEN: tool disabled");
        return 0;
    }

    return tool_executors[tool_id](input ? input : "", output, output_max);
}

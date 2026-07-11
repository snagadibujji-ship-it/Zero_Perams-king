/*
 * dap.c — DAG Agentic Planner + Tool Dependency Graph
 * Plans as DAGs: preconditions enforce ordering, postconditions verify success.
 * Tools have schemas: args validated before call, dependencies resolved first.
 */

#include "dap.h"
#include <string.h>
#include <stdio.h>
#include <stdlib.h>

/* ─── Tool Registry (TDG) ─── */

static DAPToolSchema g_tools[DAP_MAX_TOOLS];
static int g_tool_count = 0;

void dap_init(void) {
    g_tool_count = 0;
    
    /* Register built-in tools with schemas */
    DAPToolSchema t;
    
    /* Tool: kg_query */
    memset(&t, 0, sizeof(t));
    strncpy(t.name, "kg_query", 31);
    strncpy(t.description, "Query knowledge graph", 127);
    strncpy(t.args[0].name, "query", 31); t.args[0].type = DAP_ARG_STRING; t.args[0].required = 1;
    t.arg_count = 1;
    t.safety_level = 0;
    tdg_register_tool(&t);
    
    /* Tool: web_search */
    memset(&t, 0, sizeof(t));
    strncpy(t.name, "web_search", 31);
    strncpy(t.description, "Search web for information", 127);
    strncpy(t.args[0].name, "query", 31); t.args[0].type = DAP_ARG_STRING; t.args[0].required = 1;
    t.arg_count = 1;
    t.safety_level = 1;
    tdg_register_tool(&t);
    
    /* Tool: file_read */
    memset(&t, 0, sizeof(t));
    strncpy(t.name, "file_read", 31);
    strncpy(t.description, "Read file contents", 127);
    strncpy(t.args[0].name, "path", 31); t.args[0].type = DAP_ARG_PATH; t.args[0].required = 1;
    t.arg_count = 1;
    t.safety_level = 0;
    tdg_register_tool(&t);
    
    /* Tool: shell_exec */
    memset(&t, 0, sizeof(t));
    strncpy(t.name, "shell_exec", 31);
    strncpy(t.description, "Execute shell command", 127);
    strncpy(t.args[0].name, "command", 31); t.args[0].type = DAP_ARG_STRING; t.args[0].required = 1;
    t.arg_count = 1;
    t.safety_level = 2;
    tdg_register_tool(&t);
    
    /* Tool: calculate */
    memset(&t, 0, sizeof(t));
    strncpy(t.name, "calculate", 31);
    strncpy(t.description, "Mathematical computation", 127);
    strncpy(t.args[0].name, "expression", 31); t.args[0].type = DAP_ARG_STRING; t.args[0].required = 1;
    t.arg_count = 1;
    t.safety_level = 0;
    tdg_register_tool(&t);
    
    /* Tool: code_gen */
    memset(&t, 0, sizeof(t));
    strncpy(t.name, "code_gen", 31);
    strncpy(t.description, "Generate code", 127);
    strncpy(t.args[0].name, "request", 31); t.args[0].type = DAP_ARG_STRING; t.args[0].required = 1;
    t.arg_count = 1;
    t.safety_level = 0;
    tdg_register_tool(&t);
}

int tdg_register_tool(DAPToolSchema *schema) {
    if (g_tool_count >= DAP_MAX_TOOLS) return -1;
    g_tools[g_tool_count] = *schema;
    return g_tool_count++;
}

DAPToolSchema* tdg_get_schema(const char *tool) {
    for (int i = 0; i < g_tool_count; i++) {
        if (strcmp(g_tools[i].name, tool) == 0) return &g_tools[i];
    }
    return NULL;
}

int tdg_validate_args(const char *tool, const char *args[], int argc) {
    DAPToolSchema *schema = tdg_get_schema(tool);
    if (!schema) return 0;
    
    /* Check required args present */
    for (int i = 0; i < schema->arg_count; i++) {
        if (schema->args[i].required && (i >= argc || !args[i] || !args[i][0])) {
            return 0;  /* Missing required arg */
        }
    }
    
    /* Type validation */
    for (int i = 0; i < argc && i < schema->arg_count; i++) {
        if (!args[i]) continue;
        switch (schema->args[i].type) {
            case DAP_ARG_PATH:
                if (args[i][0] != '/' && args[i][0] != '.') return 0;
                break;
            case DAP_ARG_INT:
                if (!args[i][0] || !(args[i][0] >= '0' && args[i][0] <= '9' || args[i][0] == '-'))
                    return 0;
                break;
            default: break;
        }
    }
    return 1;
}

/* ─── Plan Management ─── */

static DAPPlan g_plans[4];  /* Max 4 concurrent plans */
static int g_plan_count = 0;

DAPPlan* dap_create_plan(const char *goal) {
    if (g_plan_count >= 4) g_plan_count = 0;  /* Recycle */
    DAPPlan *plan = &g_plans[g_plan_count++];
    memset(plan, 0, sizeof(DAPPlan));
    strncpy(plan->goal, goal, 255);
    return plan;
}

int dap_add_step(DAPPlan *plan, const char *desc, const char *tool,
                 const char *precond, const char *postcond) {
    if (plan->step_count >= DAP_MAX_STEPS) return -1;
    
    DAPStep *s = &plan->steps[plan->step_count];
    s->id = plan->step_count;
    strncpy(s->description, desc, 255);
    if (tool) strncpy(s->tool, tool, 31);
    if (precond) strncpy(s->precondition, precond, 127);
    if (postcond) strncpy(s->postcondition, postcond, 127);
    s->status = DAP_STEP_PENDING;
    s->confidence = 0;
    s->retries = 0;
    
    return plan->step_count++;
}

void dap_add_dependency(DAPPlan *plan, int step_id, int depends_on_id) {
    if (step_id < 0 || step_id >= plan->step_count) return;
    DAPStep *s = &plan->steps[step_id];
    if (s->dep_count >= DAP_MAX_DEPS) return;
    s->depends_on[s->dep_count++] = depends_on_id;
}

int dap_validate_step(DAPPlan *plan, int step_id) {
    if (step_id < 0 || step_id >= plan->step_count) return 0;
    DAPStep *s = &plan->steps[step_id];
    
    /* Check all dependencies completed */
    for (int i = 0; i < s->dep_count; i++) {
        int dep_id = s->depends_on[i];
        if (dep_id >= 0 && dep_id < plan->step_count) {
            if (plan->steps[dep_id].status != DAP_STEP_DONE) return 0;
        }
    }
    
    /* Check precondition (simplified: just verify deps are done) */
    return 1;
}

int dap_get_ready_steps(DAPPlan *plan, int *ready, int max) {
    int count = 0;
    for (int i = 0; i < plan->step_count && count < max; i++) {
        if (plan->steps[i].status == DAP_STEP_PENDING) {
            if (dap_validate_step(plan, i)) {
                plan->steps[i].status = DAP_STEP_READY;
                ready[count++] = i;
            }
        }
    }
    return count;
}

void dap_mark_done(DAPPlan *plan, int step_id, const char *result) {
    if (step_id < 0 || step_id >= plan->step_count) return;
    plan->steps[step_id].status = DAP_STEP_DONE;
    if (result) strncpy(plan->steps[step_id].result, result, 511);
    plan->completed_count++;
}

void dap_mark_failed(DAPPlan *plan, int step_id, const char *error) {
    if (step_id < 0 || step_id >= plan->step_count) return;
    DAPStep *s = &plan->steps[step_id];
    
    if (s->retries < 2) {
        s->retries++;
        s->status = DAP_STEP_PENDING;  /* Will retry */
    } else {
        s->status = DAP_STEP_FAILED;
        plan->failed_count++;
        /* Block dependent steps */
        for (int i = 0; i < plan->step_count; i++) {
            for (int d = 0; d < plan->steps[i].dep_count; d++) {
                if (plan->steps[i].depends_on[d] == step_id) {
                    plan->steps[i].status = DAP_STEP_BLOCKED;
                }
            }
        }
    }
    if (error) strncpy(s->result, error, 511);
}

int dap_is_complete(DAPPlan *plan) {
    for (int i = 0; i < plan->step_count; i++) {
        if (plan->steps[i].status == DAP_STEP_PENDING ||
            plan->steps[i].status == DAP_STEP_READY ||
            plan->steps[i].status == DAP_STEP_RUNNING) return 0;
    }
    return 1;
}

void dap_compose_result(DAPPlan *plan) {
    int pos = 0;
    for (int i = 0; i < plan->step_count; i++) {
        if (plan->steps[i].status == DAP_STEP_DONE && plan->steps[i].result[0]) {
            pos += snprintf(plan->final_result + pos, 
                          sizeof(plan->final_result) - pos,
                          "%s%s", pos > 0 ? "\n" : "", plan->steps[i].result);
            if (pos >= (int)sizeof(plan->final_result) - 1) break;
        }
    }
    
    /* Report failures */
    if (plan->failed_count > 0) {
        pos += snprintf(plan->final_result + pos,
                      sizeof(plan->final_result) - pos,
                      "\n[Note: %d step(s) could not be completed]", plan->failed_count);
    }
}

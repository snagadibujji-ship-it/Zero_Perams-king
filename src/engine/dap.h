#ifndef DAP_H
#define DAP_H

#include <stdint.h>

/*
 * DAP — DAG Agentic Planner
 * Models tasks as DAGs with preconditions/postconditions.
 * Never skips steps. Never retries with same bad args.
 * 
 * TDG — Tool Dependency Graph (integrated)
 * Every tool has schema. Args validated BEFORE calling.
 */

#define DAP_MAX_STEPS     32
#define DAP_MAX_TOOLS     16
#define DAP_MAX_DEPS      8
#define DAP_MAX_ARGS      8

typedef enum {
    DAP_STEP_PENDING,
    DAP_STEP_READY,       /* All deps satisfied */
    DAP_STEP_RUNNING,
    DAP_STEP_DONE,
    DAP_STEP_FAILED,
    DAP_STEP_BLOCKED,     /* Dep failed, can't proceed */
} DAPStepStatus;

typedef enum {
    DAP_ARG_STRING,
    DAP_ARG_INT,
    DAP_ARG_PATH,
    DAP_ARG_URL,
    DAP_ARG_DATE_ISO,
    DAP_ARG_ENUM,
} DAPArgType;

/* Tool schema (TDG) */
typedef struct {
    char name[32];
    char description[128];
    struct {
        char name[32];
        DAPArgType type;
        int required;
    } args[DAP_MAX_ARGS];
    int arg_count;
    char depends_on[4][32];   /* Must run AFTER these tools */
    int dep_count;
    int safety_level;         /* 0=safe, 1=ask, 2=dangerous */
} DAPToolSchema;

/* Plan step */
typedef struct {
    int id;
    char description[256];
    char tool[32];
    char args[DAP_MAX_ARGS][128];
    int arg_count;
    int depends_on[DAP_MAX_DEPS];
    int dep_count;
    DAPStepStatus status;
    char result[512];
    char precondition[128];
    char postcondition[128];
    float confidence;
    int retries;
} DAPStep;

/* Full plan */
typedef struct {
    char goal[256];
    DAPStep steps[DAP_MAX_STEPS];
    int step_count;
    int completed_count;
    int failed_count;
    int current_step;
    char final_result[1024];
} DAPPlan;

/* API */
void dap_init(void);
DAPPlan* dap_create_plan(const char *goal);
int  dap_add_step(DAPPlan *plan, const char *desc, const char *tool, 
                  const char *precond, const char *postcond);
void dap_add_dependency(DAPPlan *plan, int step_id, int depends_on_id);
int  dap_validate_step(DAPPlan *plan, int step_id);  /* Check preconditions */
int  dap_get_ready_steps(DAPPlan *plan, int *ready, int max);
void dap_mark_done(DAPPlan *plan, int step_id, const char *result);
void dap_mark_failed(DAPPlan *plan, int step_id, const char *error);
int  dap_is_complete(DAPPlan *plan);
void dap_compose_result(DAPPlan *plan);

/* TDG */
int  tdg_register_tool(DAPToolSchema *schema);
int  tdg_validate_args(const char *tool, const char *args[], int argc);
DAPToolSchema* tdg_get_schema(const char *tool);

#endif

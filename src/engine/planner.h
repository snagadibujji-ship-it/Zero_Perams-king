#ifndef PLANNER_H
#define PLANNER_H

#define PLAN_MAX_TASKS 32
#define PLAN_MAX_AGENTS 8
#define PLAN_MAX_TOOLS 12

typedef enum {
    PLAN_INTENT_COMPARE,
    PLAN_INTENT_EXPLAIN,
    PLAN_INTENT_CREATE,
    PLAN_INTENT_FIND,
    PLAN_INTENT_ANALYZE,
    PLAN_INTENT_DO,
    PLAN_INTENT_LEARN,
    PLAN_INTENT_WHATIF
} PlanIntentType;

typedef enum {
    PLAN_TASK_PENDING,
    PLAN_TASK_RUNNING,
    PLAN_TASK_DONE,
    PLAN_TASK_FAILED,
    PLAN_TASK_SKIPPED
} PlanTaskStatus;

typedef enum {
    SAFETY_SAFE,
    SAFETY_ASK_USER,
    SAFETY_DANGEROUS,
    SAFETY_FORBIDDEN
} SafetyLevel;

typedef struct {
    char name[32];
    char description[128];
    SafetyLevel safety;
    int timeout_ms;
} PlanTool;

typedef struct {
    char name[32];
    char specialty[128];
    int tool_ids[8];
    int n_tools;
    int tasks_done;
    int tasks_failed;
} PlanAgent;

typedef struct {
    int id;
    char description[256];
    int agent_id;
    int depends_on[8];
    int n_depends;
    PlanTaskStatus status;
    char result[2048];
    float confidence;
    int retries;
} PlanTask;

typedef struct {
    char goal[256];
    PlanIntentType intent;
    PlanTask tasks[PLAN_MAX_TASKS];
    int n_tasks;
    float overall_confidence;
    int elapsed_ms;
} Plan;

/* planner.c */
Plan* plan_create(const char *request);
PlanIntentType plan_classify_intent(const char *input);
void plan_free(Plan *plan);

/* executor.c */
int plan_execute(Plan *plan);
const char* plan_get_answer(Plan *plan);

/* agent_pool.c */
void agent_pool_init(void);
PlanAgent* agent_pool_get(int id);
int agent_pool_execute(int agent_id, const char *task_desc, char *result, int result_max);

/* tools.c */
void tools_init(void);
PlanTool* tools_get(int id);
int tool_execute(int tool_id, const char *input, char *output, int output_max);

/* safety.c */
typedef enum { SAFETY_ALLOW, SAFETY_WARN, SAFETY_BLOCK } SafetyVerdict;
SafetyVerdict safety_check(const char *action);
SafetyVerdict safety_check_command(const char *cmd);

#endif /* PLANNER_H */

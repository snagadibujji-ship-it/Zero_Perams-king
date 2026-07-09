#ifndef WORKFLOW_H
#define WORKFLOW_H

#include <stddef.h>

#define WF_MAX_WORKFLOWS 32
#define WF_NAME_LEN 64
#define WF_VALUE_LEN 256
#define WF_OUTPUT_LEN 1024

typedef enum {
    WF_TRIG_KEYWORD = 0,
    WF_TRIG_TIME,
    WF_TRIG_CONDITION
} WorkflowTriggerType;

typedef enum {
    WF_ACT_SHELL = 0,
    WF_ACT_NOTIFY,
    WF_ACT_SEARCH
} WorkflowActionType;

typedef struct {
    char name[WF_NAME_LEN];
    WorkflowTriggerType trigger_type;
    char trigger_value[WF_VALUE_LEN];
    WorkflowActionType action_type;
    char action_value[WF_VALUE_LEN];
    int enabled;
    int fire_count;
} Workflow;

typedef struct {
    Workflow workflows[WF_MAX_WORKFLOWS];
    int count;
} WorkflowEngine;

void workflow_init(void);
int workflow_create(const char *name, WorkflowTriggerType trig_type,
                   const char *trig_value, WorkflowActionType act_type,
                   const char *act_value);
int workflow_remove(const char *name);
void workflow_enable(const char *name, int enabled);
const char *workflow_check_triggers(const char *input);
int workflow_execute(Workflow *wf, char *output, size_t max_len);
int workflow_count(void);
int workflow_list(char *output, size_t max_len);

#endif

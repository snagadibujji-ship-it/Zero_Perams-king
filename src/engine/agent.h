#ifndef AGENT_H
#define AGENT_H

#include <stddef.h>

#define MAX_CMD_OUTPUT 4096
#define MAX_TASKS 16
#define AGENT_TIMEOUT_S 30

typedef enum {
    TASK_PENDING,
    TASK_RUNNING,
    TASK_SUCCESS,
    TASK_FAILED,
    TASK_TIMEOUT
} TaskState;

typedef enum {
    DANGER_SAFE,        // ls, cat, echo, pwd
    DANGER_LOW,         // mkdir, cp, pip install
    DANGER_MODERATE,    // rm file, chmod, git commit
    DANGER_HIGH,        // rm -rf, git push --force, sudo
    DANGER_FORBIDDEN    // rm -rf /, fork bombs
} DangerLevel;

typedef struct {
    int id;
    char command[512];
    char output[MAX_CMD_OUTPUT];
    int exit_code;
    TaskState state;
    DangerLevel danger;
    double duration_ms;
} Task;

typedef struct {
    Task tasks[MAX_TASKS];
    int task_count;
    int tasks_completed;
    int tasks_failed;
} AgentState;

// Initialize agent
void agent_init(AgentState* state);

// Execute a shell command safely (checks danger level)
// Returns: task ID (>=0) on execution, -1 if blocked, -2 if forbidden
int agent_execute(AgentState* state, const char* command);

// Check danger level of a command
DangerLevel agent_classify_danger(const char* command);

// Get last task result
Task* agent_get_last_task(AgentState* state);

// Get task by ID
Task* agent_get_task(AgentState* state, int task_id);

// Format task result for display
void agent_format_result(Task* task, char* buffer, size_t buflen);

#endif

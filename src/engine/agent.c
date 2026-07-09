#define _POSIX_C_SOURCE 200809L
#include "agent.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <sys/wait.h>

/* ── Helpers ──────────────────────────────────────────────────────── */
static int starts_with(const char* str, const char* prefix) {
    return strncmp(str, prefix, strlen(prefix)) == 0;
}

static int contains(const char* str, const char* sub) {
    return strstr(str, sub) != NULL;
}

static const char* danger_name(DangerLevel d) {
    switch (d) {
        case DANGER_SAFE:      return "SAFE";
        case DANGER_LOW:       return "LOW";
        case DANGER_MODERATE:  return "MODERATE";
        case DANGER_HIGH:      return "HIGH";
        case DANGER_FORBIDDEN: return "FORBIDDEN";
    }
    return "UNKNOWN";
}

static const char* state_name(TaskState s) {
    switch (s) {
        case TASK_PENDING: return "PENDING";
        case TASK_RUNNING: return "RUNNING";
        case TASK_SUCCESS: return "SUCCESS";
        case TASK_FAILED:  return "FAILED";
        case TASK_TIMEOUT: return "TIMEOUT";
    }
    return "UNKNOWN";
}

/* ── API Implementation ───────────────────────────────────────────── */
void agent_init(AgentState* state) {
    memset(state, 0, sizeof(AgentState));
}

DangerLevel agent_classify_danger(const char* command) {
    if (!command || !*command) return DANGER_MODERATE;

    /* FORBIDDEN — never execute */
    if (contains(command, "rm -rf /") ||
        contains(command, ":()") ||
        contains(command, "dd if=/dev/zero of=/dev/sd") ||
        contains(command, "mkfs") ||
        contains(command, "> /dev/sd"))
        return DANGER_FORBIDDEN;

    /* HIGH — needs confirmation */
    if (starts_with(command, "sudo") ||
        contains(command, "rm -rf") ||
        contains(command, "--force") ||
        contains(command, "push -f") ||
        contains(command, "DROP TABLE") ||
        contains(command, "kill -9"))
        return DANGER_HIGH;

    /* MODERATE */
    if (starts_with(command, "rm ") ||
        contains(command, "chmod") ||
        contains(command, "chown") ||
        contains(command, "git commit") ||
        contains(command, "docker rm"))
        return DANGER_MODERATE;

    /* LOW */
    if (starts_with(command, "mkdir") ||
        starts_with(command, "cp ") ||
        contains(command, "pip install") ||
        contains(command, "npm install") ||
        starts_with(command, "touch "))
        return DANGER_LOW;

    /* SAFE */
    if (starts_with(command, "ls") ||
        starts_with(command, "cat") ||
        starts_with(command, "echo") ||
        starts_with(command, "pwd") ||
        starts_with(command, "date") ||
        starts_with(command, "whoami") ||
        starts_with(command, "head") ||
        starts_with(command, "tail") ||
        starts_with(command, "wc") ||
        starts_with(command, "grep") ||
        starts_with(command, "find") ||
        starts_with(command, "which"))
        return DANGER_SAFE;

    /* Default: unknown commands → moderate */
    return DANGER_MODERATE;
}

int agent_execute(AgentState* state, const char* command) {
    if (!state || !command) return -1;
    if (state->task_count >= MAX_TASKS) return -1;

    DangerLevel danger = agent_classify_danger(command);

    if (danger == DANGER_FORBIDDEN) return -2;
    if (danger == DANGER_HIGH) return -1;

    /* Allocate task slot */
    int id = state->task_count;
    Task* task = &state->tasks[id];
    state->task_count++;

    task->id = id;
    strncpy(task->command, command, sizeof(task->command) - 1);
    task->command[sizeof(task->command) - 1] = '\0';
    task->danger = danger;
    task->state = TASK_RUNNING;
    task->output[0] = '\0';
    task->exit_code = -1;

    /* Measure execution time */
    struct timespec t_start, t_end;
    clock_gettime(CLOCK_MONOTONIC, &t_start);

    /* Execute with popen */
    char cmd_buf[600];
    snprintf(cmd_buf, sizeof(cmd_buf), "%s 2>&1", command);
    FILE* fp = popen(cmd_buf, "r");
    if (!fp) {
        task->state = TASK_FAILED;
        task->exit_code = -1;
        task->duration_ms = 0;
        state->tasks_failed++;
        return id;
    }

    /* Capture output */
    size_t total = 0;
    size_t n;
    while ((n = fread(task->output + total, 1,
                      MAX_CMD_OUTPUT - 1 - total, fp)) > 0) {
        total += n;
        if (total >= MAX_CMD_OUTPUT - 1) break;
    }
    task->output[total] = '\0';

    int status = pclose(fp);

    clock_gettime(CLOCK_MONOTONIC, &t_end);
    task->duration_ms = (t_end.tv_sec - t_start.tv_sec) * 1000.0 +
                        (t_end.tv_nsec - t_start.tv_nsec) / 1e6;

    /* Determine exit code */
    if (WIFEXITED(status)) {
        task->exit_code = WEXITSTATUS(status);
    } else {
        task->exit_code = -1;
    }

    if (task->exit_code == 0) {
        task->state = TASK_SUCCESS;
        state->tasks_completed++;
    } else {
        task->state = TASK_FAILED;
        state->tasks_failed++;
    }

    return id;
}

Task* agent_get_last_task(AgentState* state) {
    if (!state || state->task_count == 0) return NULL;
    return &state->tasks[state->task_count - 1];
}

Task* agent_get_task(AgentState* state, int task_id) {
    if (!state || task_id < 0 || task_id >= state->task_count) return NULL;
    return &state->tasks[task_id];
}

void agent_format_result(Task* task, char* buffer, size_t buflen) {
    if (!task || !buffer || buflen == 0) return;

    int written = snprintf(buffer, buflen,
        "[TASK #%d] %s (%s)\n"
        "Status: %s (exit %d, %.0fms)\n"
        "Output:\n",
        task->id, task->command, danger_name(task->danger),
        state_name(task->state), task->exit_code, task->duration_ms);

    if (written < 0 || (size_t)written >= buflen) return;

    /* Indent output lines */
    size_t remaining = buflen - (size_t)written;
    char* pos = buffer + written;
    const char* line = task->output;

    while (*line && remaining > 4) {
        const char* eol = strchr(line, '\n');
        size_t len = eol ? (size_t)(eol - line + 1) : strlen(line);

        int n = snprintf(pos, remaining, "  %.*s", (int)len, line);
        if (n < 0 || (size_t)n >= remaining) break;
        pos += n;
        remaining -= (size_t)n;
        line += len;
    }
}

/* ── TEST_MODE ────────────────────────────────────────────────────── */
#ifdef TEST_MODE
#include <assert.h>
#include <sys/wait.h>
int main(void) {
    printf("=== Agent Engine Tests ===\n");

    /* Classification tests */
    assert(agent_classify_danger("ls") == DANGER_SAFE);
    assert(agent_classify_danger("ls -la") == DANGER_SAFE);
    assert(agent_classify_danger("echo hello") == DANGER_SAFE);
    assert(agent_classify_danger("cat file.txt") == DANGER_SAFE);
    assert(agent_classify_danger("pwd") == DANGER_SAFE);
    assert(agent_classify_danger("grep foo bar") == DANGER_SAFE);
    printf("[PASS] SAFE classification\n");

    assert(agent_classify_danger("mkdir /tmp/test") == DANGER_LOW);
    assert(agent_classify_danger("cp a b") == DANGER_LOW);
    assert(agent_classify_danger("touch newfile") == DANGER_LOW);
    assert(agent_classify_danger("pip install flask") == DANGER_LOW);
    printf("[PASS] LOW classification\n");

    assert(agent_classify_danger("rm file.txt") == DANGER_MODERATE);
    assert(agent_classify_danger("chmod 755 f") == DANGER_MODERATE);
    assert(agent_classify_danger("git commit -m x") == DANGER_MODERATE);
    printf("[PASS] MODERATE classification\n");

    assert(agent_classify_danger("sudo rm file") == DANGER_HIGH);
    assert(agent_classify_danger("kill -9 1234") == DANGER_HIGH);
    assert(agent_classify_danger("git push --force") == DANGER_HIGH);
    printf("[PASS] HIGH classification\n");

    assert(agent_classify_danger("rm -rf /") == DANGER_FORBIDDEN);
    assert(agent_classify_danger(":() { :|:& };:") == DANGER_FORBIDDEN);
    assert(agent_classify_danger("dd if=/dev/zero of=/dev/sda") == DANGER_FORBIDDEN);
    printf("[PASS] FORBIDDEN classification\n");
    /* Execution tests */
    AgentState state;
    agent_init(&state);
    assert(state.task_count == 0);
    printf("[PASS] agent_init\n");

    int id = agent_execute(&state, "echo hello");
    assert(id == 0);
    Task* t = agent_get_task(&state, id);
    assert(t != NULL);
    assert(t->state == TASK_SUCCESS);
    assert(t->exit_code == 0);
    assert(contains(t->output, "hello"));
    printf("[PASS] execute 'echo hello' → SUCCESS, output contains 'hello'\n");

    id = agent_execute(&state, "ls /tmp");
    assert(id == 1);
    t = agent_get_task(&state, id);
    assert(t->state == TASK_SUCCESS);
    printf("[PASS] execute 'ls /tmp' → SUCCESS\n");

    id = agent_execute(&state, "false");
    assert(id == 2);
    t = agent_get_task(&state, id);
    assert(t->state == TASK_FAILED);
    assert(t->exit_code != 0);
    printf("[PASS] execute 'false' → FAILED\n");

    id = agent_execute(&state, "rm -rf /");
    assert(id == -2);
    printf("[PASS] forbidden command → returns -2\n");

    id = agent_execute(&state, "sudo reboot");
    assert(id == -1);
    printf("[PASS] high-danger command → returns -1\n");

    /* Format test */
    Task* last = agent_get_last_task(&state);
    assert(last != NULL);
    assert(last->id == 2);
    char buf[2048];
    agent_format_result(last, buf, sizeof(buf));
    assert(contains(buf, "[TASK #2]"));
    assert(contains(buf, "FAILED"));
    printf("[PASS] agent_format_result\n");

    assert(state.task_count == 3);
    assert(state.tasks_completed == 2);
    assert(state.tasks_failed == 1);
    printf("[PASS] task counters correct\n");

    printf("\n=== ALL TESTS PASSED ===\n");
    return 0;
}
#endif

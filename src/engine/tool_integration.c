/**
 * tool_integration.c - Phase 16: System Tool Integration
 */
#define _GNU_SOURCE

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <ctype.h>
#include <unistd.h>

#define MAX_TOOLS 16
#define TOOL_NAME_LEN 32
#define TOOL_PATH_LEN 256
#define TOOL_OUTPUT_LEN 4096

typedef struct {
    char name[TOOL_NAME_LEN];
    char path[TOOL_PATH_LEN];
    int available;
} SystemTool;

typedef struct {
    SystemTool tools[MAX_TOOLS];
    int count;
    int detected;
} ToolRegistry;

static ToolRegistry g_tools = { .count = 0, .detected = 0 };

static int check_tool_exists(const char *name, char *path_out, size_t path_len) {
    char cmd[128];
    snprintf(cmd, sizeof(cmd), "which %s 2>/dev/null", name);
    FILE *p = popen(cmd, "r");
    if (!p) return 0;
    char buf[256];
    if (fgets(buf, sizeof(buf), p)) {
        size_t len = strlen(buf);
        if (len > 0 && buf[len-1] == '\n') buf[len-1] = '\0';
        if (path_out) strncpy(path_out, buf, path_len - 1);
        pclose(p);
        return 1;
    }
    pclose(p);
    return 0;
}

void tool_detect_available(void) {
    static const char *known_tools[] = {
        "git", "python3", "node", "gcc", "make",
        "docker", "curl", "wget", "find", "grep",
        "df", "top", NULL
    };

    g_tools.count = 0;
    for (int i = 0; known_tools[i] && g_tools.count < MAX_TOOLS; i++) {
        SystemTool *t = &g_tools.tools[g_tools.count];
        memset(t, 0, sizeof(SystemTool));
        strncpy(t->name, known_tools[i], TOOL_NAME_LEN - 1);
        t->available = check_tool_exists(known_tools[i], t->path, TOOL_PATH_LEN);
        g_tools.count++;
    }
    g_tools.detected = 1;
}

int tool_is_available(const char *name) {
    if (!g_tools.detected) tool_detect_available();
    for (int i = 0; i < g_tools.count; i++) {
        if (strcmp(g_tools.tools[i].name, name) == 0)
            return g_tools.tools[i].available;
    }
    return 0;
}

static int run_cmd(const char *cmd, char *output, size_t max_len) {
    FILE *p = popen(cmd, "r");
    if (!p) return -1;
    size_t total = 0;
    char buf[256];
    while (fgets(buf, sizeof(buf), p) && total < max_len - 1) {
        size_t len = strlen(buf);
        if (total + len >= max_len) len = max_len - total - 1;
        memcpy(output + total, buf, len);
        total += len;
    }
    output[total] = '\0';
    int ret = pclose(p);
    return WEXITSTATUS(ret);
}

int tool_run_git_status(char *output, size_t max_len) {
    if (!tool_is_available("git")) return -1;
    return run_cmd("git status --short 2>/dev/null", output, max_len);
}

int tool_run_git_diff(char *output, size_t max_len) {
    if (!tool_is_available("git")) return -1;
    return run_cmd("git diff --stat 2>/dev/null", output, max_len);
}

int tool_run_find(const char *pattern, char *output, size_t max_len) {
    if (!pattern) return -1;
    char cmd[512];
    snprintf(cmd, sizeof(cmd), "find . -name '%s' -type f 2>/dev/null | head -20", pattern);
    return run_cmd(cmd, output, max_len);
}

int tool_run_disk_space(char *output, size_t max_len) {
    return run_cmd("df -h / 2>/dev/null", output, max_len);
}

/* Map natural language to tool commands */
const char *tool_map_natural(const char *input) {
    if (!input) return NULL;

    static const struct { const char *phrase; const char *cmd; } mappings[] = {
        { "what changed", "git diff --stat" },
        { "git status", "git status --short" },
        { "disk space", "df -h" },
        { "who am i", "whoami" },
        { "current directory", "pwd" },
        { "list files", "ls -la" },
        { "running processes", "ps aux | head -20" },
        { "memory usage", "free -h" },
        { "network status", "ip addr show 2>/dev/null || ifconfig" },
        { NULL, NULL }
    };

    for (int i = 0; mappings[i].phrase; i++) {
        if (strcasestr(input, mappings[i].phrase))
            return mappings[i].cmd;
    }
    return NULL;
}

int tool_list_available(char *output, size_t max_len) {
    if (!g_tools.detected) tool_detect_available();
    size_t offset = 0;
    for (int i = 0; i < g_tools.count && offset < max_len - 50; i++) {
        if (g_tools.tools[i].available) {
            offset += (size_t)snprintf(output + offset, max_len - offset,
                "  %s: %s\n", g_tools.tools[i].name, g_tools.tools[i].path);
        }
    }
    return (int)offset;
}

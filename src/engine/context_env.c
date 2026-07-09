/**
 * context_env.c - Phase 23: Environment Context Detection
 */
#define _POSIX_C_SOURCE 200809L

#include "context_env.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <unistd.h>
#include <sys/stat.h>
#include <sys/ioctl.h>

static EnvironmentInfo g_env;
static char g_env_suggestion[ENV_SUGGEST_LEN];
static int g_env_initialized = 0;

void env_init(void) {
    memset(&g_env, 0, sizeof(g_env));
    g_env_initialized = 0;
}

static int check_network(void) {
    /* Quick check: try to resolve a common host */
    FILE *p = popen("ping -c 1 -W 1 8.8.8.8 2>/dev/null | grep -c 'bytes from'", "r");
    if (!p) return 0;
    char buf[16];
    int result = 0;
    if (fgets(buf, sizeof(buf), p)) {
        result = atoi(buf) > 0 ? 1 : 0;
    }
    pclose(p);
    return result;
}

EnvironmentInfo env_detect(void) {
    /* OS */
#ifdef __linux__
    strncpy(g_env.os_name, "Linux", ENV_STR_LEN - 1);
#elif defined(__APPLE__)
    strncpy(g_env.os_name, "macOS", ENV_STR_LEN - 1);
#else
    strncpy(g_env.os_name, "Unix", ENV_STR_LEN - 1);
#endif

    /* CWD */
    if (getcwd(g_env.cwd, ENV_STR_LEN) == NULL) {
        strncpy(g_env.cwd, "unknown", ENV_STR_LEN - 1);
    }

    /* Hour */
    time_t now = time(NULL);
    struct tm *tm = localtime(&now);
    g_env.hour = tm->tm_hour;

    /* Terminal width */
    g_env.terminal_width = env_get_terminal_width();

    /* Network */
    g_env.network_available = check_network();

    /* Git repo */
    g_env.in_git_repo = env_in_git_repo();

    /* Username */
    char *user = getenv("USER");
    if (user) strncpy(g_env.username, user, sizeof(g_env.username) - 1);
    else strncpy(g_env.username, "unknown", sizeof(g_env.username) - 1);

    g_env_initialized = 1;
    return g_env;
}

int env_is_night(void) {
    if (!g_env_initialized) env_detect();
    return (g_env.hour >= 23 || g_env.hour < 6);
}

int env_is_offline(void) {
    if (!g_env_initialized) env_detect();
    return !g_env.network_available;
}

int env_in_git_repo(void) {
    struct stat st;
    return (stat(".git", &st) == 0 && S_ISDIR(st.st_mode));
}

int env_get_terminal_width(void) {
    struct winsize ws;
    if (ioctl(STDOUT_FILENO, TIOCGWINSZ, &ws) == 0) {
        return ws.ws_col > 0 ? ws.ws_col : 80;
    }
    return 80;
}

const char *env_suggest(void) {
    if (!g_env_initialized) env_detect();
    g_env_suggestion[0] = '\0';

    if (env_is_night()) {
        snprintf(g_env_suggestion, sizeof(g_env_suggestion),
            "It's late (%d:00). Remember to save your work!", g_env.hour);
        return g_env_suggestion;
    }

    if (env_is_offline()) {
        snprintf(g_env_suggestion, sizeof(g_env_suggestion),
            "You're offline. Web search is unavailable. Using local knowledge only.");
        return g_env_suggestion;
    }

    if (g_env.in_git_repo) {
        snprintf(g_env_suggestion, sizeof(g_env_suggestion),
            "You're in a git repo. I can help with: git status, diffs, commits.");
        return g_env_suggestion;
    }

    return NULL;
}

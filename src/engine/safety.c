/*
 * safety.c — Safety gate for the agent planner system
 * Phase 7 Agent System
 *
 * Checks every action against forbidden patterns.
 * Returns ALLOW / WARN / BLOCK.
 */

#include <stdio.h>
#include <string.h>
#include <ctype.h>
#include "planner.h"

/* ─── Forbidden Patterns (always blocked) ─────────────────────── */

static const char *forbidden_patterns[] = {
    "rm -rf /",
    "rm -rf /*",
    "rm -rf ~",
    "rm -rf $HOME",
    "mkfs",
    "format c:",
    "dd if=/dev/zero",
    "dd if=/dev/urandom",
    "dd of=/dev/sd",
    "dd of=/dev/nvme",
    "> /dev/sda",
    "chmod -R 777 /",
    "chown -R",
    ":(){ :|:& };:",       /* fork bomb */
    "fork bomb",
    "/dev/null >",
    "shutdown",
    "reboot",
    "init 0",
    "init 6",
    "halt",
    "poweroff",
    "kill -9 1",
    "kill -9 -1",
    "pkill -9",
    "wget|sh",
    "curl|sh",
    "wget|bash",
    "curl|bash",
    "python -c 'import os; os.system",
    "nc -e /bin/",
    "ncat -e",
    "/etc/shadow",
    "/etc/passwd",
    "iptables -F",
    "iptables --flush",
    "cat /proc/kcore",
    NULL
};

/* ─── Dangerous Patterns (warn, require confirmation) ─────────── */

static const char *dangerous_patterns[] = {
    "rm -rf",
    "rm -r",
    "rm -f",
    "sudo",
    "su -",
    "chmod",
    "chown",
    "git push --force",
    "git reset --hard",
    "git clean -f",
    "kill",
    "pkill",
    "systemctl stop",
    "systemctl disable",
    "apt remove",
    "apt purge",
    "pip uninstall",
    "npm uninstall",
    "docker rm",
    "docker rmi",
    "DROP TABLE",
    "DROP DATABASE",
    "DELETE FROM",
    "TRUNCATE",
    NULL
};

/* ─── Helper: case-insensitive contains ───────────────────────── */

static int ci_contains(const char *haystack, const char *needle) {
    if (!haystack || !needle) return 0;
    size_t hlen = strlen(haystack);
    size_t nlen = strlen(needle);
    if (nlen == 0 || nlen > hlen) return 0;

    for (size_t i = 0; i <= hlen - nlen; i++) {
        int match = 1;
        for (size_t j = 0; j < nlen; j++) {
            if (tolower((unsigned char)haystack[i + j]) != tolower((unsigned char)needle[j])) {
                match = 0;
                break;
            }
        }
        if (match) return 1;
    }
    return 0;
}

/* ─── Safety Check (general action description) ───────────────── */

SafetyVerdict safety_check(const char *action) {
    if (!action || strlen(action) == 0) return SAFETY_ALLOW;

    /* Check forbidden patterns first */
    for (int i = 0; forbidden_patterns[i] != NULL; i++) {
        if (ci_contains(action, forbidden_patterns[i])) {
            return SAFETY_BLOCK;
        }
    }

    /* Check dangerous patterns */
    for (int i = 0; dangerous_patterns[i] != NULL; i++) {
        if (ci_contains(action, dangerous_patterns[i])) {
            return SAFETY_WARN;
        }
    }

    return SAFETY_ALLOW;
}

/* ─── Safety Check (shell command specifically) ───────────────── */

SafetyVerdict safety_check_command(const char *cmd) {
    if (!cmd || strlen(cmd) == 0) return SAFETY_ALLOW;

    /* All forbidden patterns apply */
    for (int i = 0; forbidden_patterns[i] != NULL; i++) {
        if (ci_contains(cmd, forbidden_patterns[i])) {
            return SAFETY_BLOCK;
        }
    }

    /* Additional command-specific checks */
    /* Block commands that pipe to shells */
    if ((ci_contains(cmd, "wget") || ci_contains(cmd, "curl")) &&
        (ci_contains(cmd, "| sh") || ci_contains(cmd, "| bash") ||
         ci_contains(cmd, "|sh") || ci_contains(cmd, "|bash"))) {
        return SAFETY_BLOCK;
    }

    /* Block writing to device files */
    if (ci_contains(cmd, ">/dev/") || ci_contains(cmd, "> /dev/")) {
        if (!ci_contains(cmd, "/dev/null")) {
            return SAFETY_BLOCK;
        }
    }

    /* Check dangerous patterns */
    for (int i = 0; dangerous_patterns[i] != NULL; i++) {
        if (ci_contains(cmd, dangerous_patterns[i])) {
            return SAFETY_WARN;
        }
    }

    return SAFETY_ALLOW;
}

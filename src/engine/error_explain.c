#include <string.h>
#include <stdio.h>
#include "error_explain.h"

static struct {
    const char* pattern;
    const char* category;
    const char* explanation;
    const char* suggestion;
    int severity;
} ERROR_DB[] = {
    {"command not found", "missing_tool", "The command isn't installed on your system", "Install it with: apt install <package> or check your PATH", 2},
    {"No such file", "file_missing", "The file or directory doesn't exist", "Check the path for typos, or create it first", 2},
    {"Permission denied", "permission", "You don't have access to this resource", "Try: chmod or run with sudo", 3},
    {"Connection refused", "network", "The target service isn't running or is blocking connections", "Check if the service is running and the port is correct", 3},
    {"Segmentation fault", "crash", "The program accessed invalid memory", "Check for null pointers, buffer overflows, or use-after-free bugs", 5},
    {"ModuleNotFoundError", "missing_module", "A Python module is not installed", "Install it with: pip install <module>", 2},
    {"ImportError", "missing_module", "A Python import failed", "Check module name spelling or install with pip", 2},
    {"SyntaxError", "syntax", "The code has a syntax mistake", "Check for missing brackets, quotes, or typos near the reported line", 2},
    {"TypeError", "type_error", "A value has the wrong type for the operation", "Check argument types and function signatures", 3},
    {"NameError", "undefined", "A variable or function name is not defined", "Check spelling or ensure it's imported/declared before use", 2},
    {"undefined", "undefined", "A variable or property is not defined", "Ensure the name is declared or imported before use", 2},
    {"EADDRINUSE", "port_conflict", "The network port is already in use", "Kill the process using that port or choose a different port", 3},
    {"address already in use", "port_conflict", "The network port is already in use", "Find the process: lsof -i :<port> then kill it", 3},
    {"out of memory", "resource", "The system ran out of available memory", "Close other programs or increase available RAM/swap", 4},
    {"OOM", "resource", "Out of memory - the process was killed", "Reduce memory usage or increase system memory", 4},
    {"No space left", "disk_full", "The disk is full", "Free space: remove old files, logs, or docker images", 4},
    {"disk full", "disk_full", "The disk has no remaining space", "Clean up with: df -h to find full partitions, then remove unneeded files", 4},
    {"timed out", "timeout", "The operation took too long and was cancelled", "Check network connectivity or increase the timeout value", 3},
    {"timeout", "timeout", "The operation exceeded its time limit", "Verify the remote service is reachable and responsive", 3},
    {"merge conflict", "git_conflict", "Git found conflicting changes in the same file", "Edit the file to resolve <<<< ==== >>>> markers, then git add", 2},
    {"undefined reference", "linker", "The linker can't find a function implementation", "Ensure the source file is compiled and linked, check spelling", 3},
    {"compilation error", "compile", "The code failed to compile", "Read the error line number and fix the syntax or type issue", 3},
    {"pip install failed", "package", "Python package installation failed", "Try: pip install --upgrade pip, then retry. Check for missing system libs", 2},
    {"npm ERR", "package", "Node.js package manager encountered an error", "Try: rm -rf node_modules && npm install, or check package.json", 2},
    {"docker: command not found", "missing_tool", "Docker is not installed on this system", "Install Docker: https://docs.docker.com/get-docker/", 2},
    {"git push rejected", "git_rejected", "The remote rejected your push", "Pull first: git pull --rebase origin <branch>, then push again", 2},
    {"SSL certificate", "ssl", "SSL/TLS certificate verification failed", "Check system time, update ca-certificates, or verify the cert chain", 3},
    {"DNS resolution failed", "dns", "Could not resolve the hostname to an IP address", "Check internet connection and DNS settings (/etc/resolv.conf)", 3},
    {"No such process", "process", "The process doesn't exist or already exited", "Check running processes with: ps aux | grep <name>", 1},
    {"Broken pipe", "io", "The receiving end of a pipe closed unexpectedly", "The downstream process crashed or exited; check its logs", 2},
    {"stack overflow", "crash", "Too much recursion or stack usage", "Check for infinite recursion or reduce stack-heavy allocations", 4},
    {"division by zero", "math", "Attempted to divide by zero", "Add a check: if (divisor != 0) before dividing", 3},
    {"NullPointerException", "null_ref", "Tried to use a null/uninitialized reference", "Add null checks before accessing the object", 4},
    {"null pointer", "null_ref", "Dereferenced a null pointer", "Ensure pointers are initialized and checked before use", 4},
    {"index out of range", "bounds", "Accessed an array/list beyond its size", "Check the length before indexing; use bounds-safe access", 3},
    {"out of bounds", "bounds", "Array or buffer access exceeded valid range", "Validate index is within 0..length-1", 3},
    {"KeyError", "key_error", "Accessed a dictionary with a non-existent key", "Use .get(key, default) or check 'if key in dict' first", 2},
    {"key error", "key_error", "A lookup key was not found in the collection", "Verify the key exists before accessing it", 2},
    {"file is binary", "binary", "Attempted a text operation on a binary file", "Use binary mode (rb/wb) or a hex editor for binary files", 1},
    {"Too many open files", "resource", "The process exceeded the file descriptor limit", "Close unused files or increase limit: ulimit -n 4096", 3},
    {"resource temporarily unavailable", "resource", "The system is out of a needed resource (processes/memory)", "Wait and retry, or increase limits with ulimit", 4},
};

#define ERROR_DB_SIZE (int)(sizeof(ERROR_DB) / sizeof(ERROR_DB[0]))

int error_explain(const char* error_text, ErrorExplanation* result) {
    if (!error_text || !result) return -1;
    memset(result, 0, sizeof(ErrorExplanation));

    for (int i = 0; i < ERROR_DB_SIZE; i++) {
        if (strstr(error_text, ERROR_DB[i].pattern)) {
            snprintf(result->explanation, sizeof(result->explanation), "%s", ERROR_DB[i].explanation);
            snprintf(result->suggestion, sizeof(result->suggestion), "%s", ERROR_DB[i].suggestion);
            snprintf(result->category, sizeof(result->category), "%s", ERROR_DB[i].category);
            result->severity = ERROR_DB[i].severity;
            return 0;
        }
    }
    snprintf(result->explanation, sizeof(result->explanation), "Unknown error");
    snprintf(result->suggestion, sizeof(result->suggestion), "Search online for the exact error message");
    snprintf(result->category, sizeof(result->category), "unknown");
    result->severity = 1;
    return 1;
}

const char* error_category_name(const char* category) {
    if (!category) return "Unknown";
    if (strcmp(category, "missing_tool") == 0) return "Missing Tool";
    if (strcmp(category, "file_missing") == 0) return "File Not Found";
    if (strcmp(category, "permission") == 0) return "Permission Issue";
    if (strcmp(category, "network") == 0) return "Network Error";
    if (strcmp(category, "crash") == 0) return "Program Crash";
    if (strcmp(category, "missing_module") == 0) return "Missing Module";
    if (strcmp(category, "syntax") == 0) return "Syntax Error";
    if (strcmp(category, "type_error") == 0) return "Type Error";
    if (strcmp(category, "undefined") == 0) return "Undefined Reference";
    if (strcmp(category, "port_conflict") == 0) return "Port Conflict";
    if (strcmp(category, "resource") == 0) return "Resource Exhaustion";
    if (strcmp(category, "disk_full") == 0) return "Disk Full";
    if (strcmp(category, "timeout") == 0) return "Timeout";
    if (strcmp(category, "git_conflict") == 0) return "Git Conflict";
    if (strcmp(category, "linker") == 0) return "Linker Error";
    if (strcmp(category, "compile") == 0) return "Compilation Error";
    if (strcmp(category, "package") == 0) return "Package Error";
    if (strcmp(category, "git_rejected") == 0) return "Git Push Rejected";
    if (strcmp(category, "ssl") == 0) return "SSL/TLS Error";
    if (strcmp(category, "dns") == 0) return "DNS Error";
    if (strcmp(category, "process") == 0) return "Process Error";
    if (strcmp(category, "io") == 0) return "I/O Error";
    if (strcmp(category, "math") == 0) return "Math Error";
    if (strcmp(category, "null_ref") == 0) return "Null Reference";
    if (strcmp(category, "bounds") == 0) return "Out of Bounds";
    if (strcmp(category, "key_error") == 0) return "Key Error";
    if (strcmp(category, "binary") == 0) return "Binary File";
    if (strcmp(category, "unknown") == 0) return "Unknown";
    return "Unknown";
}

#ifdef TEST_MODE
#include <assert.h>
int main(void) {
    ErrorExplanation ex;
    int rc;

    rc = error_explain("bash: gcc: command not found", &ex);
    assert(rc == 0);
    assert(strcmp(ex.category, "missing_tool") == 0);
    assert(ex.severity == 2);

    rc = error_explain("Error: No such file or directory", &ex);
    assert(rc == 0);
    assert(strcmp(ex.category, "file_missing") == 0);

    rc = error_explain("Permission denied (publickey)", &ex);
    assert(rc == 0);
    assert(strcmp(ex.category, "permission") == 0);
    assert(ex.severity == 3);

    rc = error_explain("Segmentation fault (core dumped)", &ex);
    assert(rc == 0);
    assert(strcmp(ex.category, "crash") == 0);
    assert(ex.severity == 5);

    rc = error_explain("EADDRINUSE: port 3000", &ex);
    assert(rc == 0);
    assert(strcmp(ex.category, "port_conflict") == 0);

    printf("All 5 tests passed!\n");
    return 0;
}
#endif

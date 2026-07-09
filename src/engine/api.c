#define _GNU_SOURCE
#define _POSIX_C_SOURCE 200809L
#include "api.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <signal.h>
#include <sys/socket.h>
#include <sys/wait.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <time.h>
#include <sys/select.h>

static volatile int server_running = 1;
static pid_t child_pid = 0;
static time_t start_time = 0;
static int total_requests = 0;

static void sig_handler(int sig) {
    (void)sig;
    server_running = 0;
}

static void send_response(int fd, int code, const char* body) {
    char resp[API_MAX_BODY];
    int len = snprintf(resp, sizeof(resp),
        "HTTP/1.1 %d OK\r\n"
        "Content-Type: application/json\r\n"
        "Content-Length: %zu\r\n"
        "Connection: close\r\n\r\n%s",
        code, strlen(body), body);
    write(fd, resp, len);
}

static void handle_request(int client_fd) {
    char buf[API_MAX_BODY];
    int n = read(client_fd, buf, sizeof(buf) - 1);
    if (n <= 0) { close(client_fd); return; }
    buf[n] = '\0';
    total_requests++;

    /* Parse method and path */
    char method[8] = {0}, path[128] = {0};
    sscanf(buf, "%7s %127s", method, path);

    /* Find body (after \r\n\r\n) */
    char* body = strstr(buf, "\r\n\r\n");
    if (body) body += 4; else body = "";

    char response[API_MAX_BODY];

    if (strcmp(method, "GET") == 0 && strcmp(path, "/health") == 0) {
        time_t uptime = time(NULL) - start_time;
        snprintf(response, sizeof(response),
            "{\"status\":\"ok\",\"uptime\":%ld}", (long)uptime);
        send_response(client_fd, 200, response);
    }
    else if (strcmp(method, "GET") == 0 && strcmp(path, "/stats") == 0) {
        snprintf(response, sizeof(response),
            "{\"facts\":0,\"queries\":%d}", total_requests);
        send_response(client_fd, 200, response);
    }
    else if (strcmp(method, "POST") == 0 && strcmp(path, "/chat") == 0) {
        /* Echo back a simple response for now */
        snprintf(response, sizeof(response),
            "{\"response\":\"Echo: %.512s\",\"confidence\":0.5}", body);
        send_response(client_fd, 200, response);
    }
    else {
        snprintf(response, sizeof(response),
            "{\"error\":\"not found\",\"path\":\"%s\"}", path);
        send_response(client_fd, 404, response);
    }

    close(client_fd);
}

static void server_loop(int port) {
    signal(SIGTERM, sig_handler);
    signal(SIGINT, sig_handler);
    start_time = time(NULL);

    int sock = socket(AF_INET, SOCK_STREAM, 0);
    if (sock < 0) { perror("socket"); exit(1); }

    int opt = 1;
    setsockopt(sock, SOL_SOCKET, SO_REUSEADDR, &opt, sizeof(opt));

    struct sockaddr_in addr = {0};
    addr.sin_family = AF_INET;
    addr.sin_addr.s_addr = htonl(INADDR_LOOPBACK);
    addr.sin_port = htons(port);

    if (bind(sock, (struct sockaddr*)&addr, sizeof(addr)) < 0) {
        perror("bind"); close(sock); exit(1);
    }
    if (listen(sock, 16) < 0) {
        perror("listen"); close(sock); exit(1);
    }

    printf("[API] Server listening on 127.0.0.1:%d\n", port);

    while (server_running) {
        fd_set fds;
        FD_ZERO(&fds);
        FD_SET(sock, &fds);

        struct timeval tv = {1, 0}; /* 1s timeout for graceful shutdown */
        int ready = select(sock + 1, &fds, NULL, NULL, &tv);

        if (ready > 0 && FD_ISSET(sock, &fds)) {
            struct sockaddr_in client_addr;
            socklen_t client_len = sizeof(client_addr);
            int client_fd = accept(sock, (struct sockaddr*)&client_addr, &client_len);
            if (client_fd >= 0) {
                handle_request(client_fd);
            }
        }
    }

    printf("[API] Server shutting down (served %d requests)\n", total_requests);
    close(sock);
    exit(0);
}

int api_start(ApiServer* server, int port) {
    if (!server) return -1;
    memset(server, 0, sizeof(ApiServer));
    server->port = port;

    pid_t pid = fork();
    if (pid < 0) {
        perror("fork");
        return -1;
    }
    if (pid == 0) {
        /* Child process — run the server */
        server_loop(port);
        /* never returns */
    }

    /* Parent */
    child_pid = pid;
    server->running = 1;
    usleep(100000); /* 100ms for child to bind */
    return 0;
}

void api_stop(ApiServer* server) {
    if (!server || !server->running) return;
    if (child_pid > 0) {
        kill(child_pid, SIGTERM);
        waitpid(child_pid, NULL, 0);
        child_pid = 0;
    }
    server->running = 0;
}

int api_is_running(ApiServer* server) {
    if (!server || child_pid <= 0) return 0;
    /* kill with signal 0 checks if process exists */
    if (kill(child_pid, 0) == 0) {
        server->running = 1;
        return 1;
    }
    server->running = 0;
    return 0;
}

/* ─── TEST MODE ─────────────────────────────────────────────── */
#ifdef TEST_MODE
int main(void) {
    printf("=== API Server Test ===\n");
    ApiServer srv;

    printf("[TEST] Starting server on port %d...\n", API_PORT);
    if (api_start(&srv, API_PORT) != 0) {
        printf("[FAIL] Could not start server\n");
        return 1;
    }

    sleep(1);

    if (api_is_running(&srv)) {
        printf("[PASS] Server is running (pid %d)\n", child_pid);
    } else {
        printf("[FAIL] Server not running\n");
        return 1;
    }

    printf("[TEST] Stopping server...\n");
    api_stop(&srv);

    usleep(200000);

    if (!api_is_running(&srv)) {
        printf("[PASS] Server stopped successfully\n");
    } else {
        printf("[FAIL] Server still running\n");
        return 1;
    }

    printf("=== All API tests passed ===\n");
    return 0;
}
#endif

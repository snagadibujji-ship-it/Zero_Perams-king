#ifndef API_H
#define API_H

#define API_PORT 7777
#define API_MAX_BODY 8192

typedef struct {
    int running;
    int port;
    int socket_fd;
    int requests_served;
} ApiServer;

// Start API server in background (non-blocking, uses fork)
int api_start(ApiServer* server, int port);

// Stop API server
void api_stop(ApiServer* server);

// Check if running
int api_is_running(ApiServer* server);

#endif

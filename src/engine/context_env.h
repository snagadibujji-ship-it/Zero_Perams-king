#ifndef CONTEXT_ENV_H
#define CONTEXT_ENV_H

#define ENV_STR_LEN 256
#define ENV_SUGGEST_LEN 512

typedef struct {
    char os_name[ENV_STR_LEN];
    char cwd[ENV_STR_LEN];
    int hour;
    int terminal_width;
    int network_available;
    int in_git_repo;
    char username[64];
} EnvironmentInfo;

void env_init(void);
EnvironmentInfo env_detect(void);
int env_is_night(void);
int env_is_offline(void);
int env_in_git_repo(void);
const char *env_suggest(void);
int env_get_terminal_width(void);

#endif

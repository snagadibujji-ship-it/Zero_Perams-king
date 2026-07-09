#ifndef PERSONALITY_H
#define PERSONALITY_H

#include <stddef.h>

#define MAX_RESPONSE_LEN 2048

typedef enum {
    MOOD_NEUTRAL = 0,
    MOOD_FRUSTRATED,
    MOOD_CURIOUS,
    MOOD_RUSHED,
    MOOD_HAPPY,
    MOOD_CONFUSED
} UserMood;

typedef struct {
    float formality;
    float verbosity;
    float humor;
    float empathy;
} Personality;

void personality_init(void);
void personality_set(float formality, float verbosity, float humor, float empathy);
Personality personality_get(void);
UserMood mood_detect(const char *text);
const char *mood_name(UserMood mood);
void personality_adjust_response(char *response, size_t max_len, UserMood mood);

#endif

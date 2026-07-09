#ifndef TEACHING_H
#define TEACHING_H

#include <time.h>

#define TEACH_MAX_CARDS 256
#define TEACH_CONCEPT_LEN 128
#define TEACH_QUESTION_LEN 512

typedef struct {
    char concept[TEACH_CONCEPT_LEN];
    time_t last_tested;
    int interval_days;
    float ease;
    int repetitions;
} SpacedRepCard;

typedef struct {
    SpacedRepCard cards[TEACH_MAX_CARDS];
    int count;
    int socratic_mode;
} TeachingEngine;

void teaching_init(void);
void teaching_set_socratic(int enabled);
int teaching_is_socratic(void);
const char *teach_mode_response(const char *question);
void teach_add_card(const char *concept);
const char *teach_quiz(const char *topic);
int teach_review_due(void);
void teach_record_result(const char *concept, int correct);

#endif

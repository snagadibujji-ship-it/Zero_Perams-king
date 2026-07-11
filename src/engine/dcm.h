#ifndef DCM_H
#define DCM_H

#include <stdint.h>

/*
 * DCM — Deep Context Machine
 * Structured conversation state that NEVER forgets.
 * Entity registry + intent stack + topic graph + reference resolution.
 */

#define DCM_MAX_ENTITIES    64
#define DCM_MAX_INTENTS     20
#define DCM_MAX_TOPICS      32
#define DCM_MAX_GOALS       8

typedef struct {
    char name[64];
    char type[32];        /* person, place, thing, project, concept */
    char properties[4][128];  /* key properties mentioned */
    int prop_count;
    uint32_t first_mention;   /* Turn number */
    uint32_t last_mention;
} DCMEntity;

typedef struct {
    char intent[32];      /* asking, reporting, requesting, correcting, teaching */
    char topic[64];
    char emotion[16];     /* neutral, frustrated, curious, happy, confused */
    uint32_t turn;
} DCMIntent;

typedef struct {
    char name[64];
    char status[16];      /* active, completed, blocked, abandoned */
    char steps_done[256];
    char steps_remaining[256];
    uint32_t created_turn;
} DCMGoal;

typedef struct {
    /* Entity Registry — permanent for session */
    DCMEntity entities[DCM_MAX_ENTITIES];
    int entity_count;
    
    /* Intent Stack — last N turns */
    DCMIntent intents[DCM_MAX_INTENTS];
    int intent_count;
    int intent_head;  /* Ring buffer pointer */
    
    /* Topic tracking */
    char topics[DCM_MAX_TOPICS][64];
    int topic_count;
    int current_topic_idx;
    
    /* Goal tracker */
    DCMGoal goals[DCM_MAX_GOALS];
    int goal_count;
    
    /* Reference resolution state */
    char last_subject[64];
    char last_object[64];
    char last_answer[256];
    uint32_t turn_count;
    
    /* Conversation metadata */
    uint32_t session_start;
    int questions_asked;
    int corrections_made;
} DCMState;

/* API */
void dcm_init(DCMState *state);
void dcm_record_turn(DCMState *state, const char *user_input, const char *ai_response);
int  dcm_add_entity(DCMState *state, const char *name, const char *type);
int  dcm_find_entity(DCMState *state, const char *name);
const char* dcm_resolve_reference(DCMState *state, const char *pronoun);
const char* dcm_get_current_topic(DCMState *state);
void dcm_set_topic(DCMState *state, const char *topic);
int  dcm_add_goal(DCMState *state, const char *goal);
void dcm_update_goal(DCMState *state, int idx, const char *status);
void dcm_get_context_summary(DCMState *state, char *buf, int max);

#endif

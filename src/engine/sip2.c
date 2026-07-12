/*
 * sip2.c — Self-Interrogation Protocol
 * AI asks ITSELF questions to discover gaps. Fills them automatically.
 * "I know what I don't know — and I fix it while you sleep."
 */

#include <string.h>
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <time.h>

#define SIP2_MAX_GAPS        1000
#define SIP2_MAX_QUESTIONS   16
#define SIP2_BATCH_SIZE      100

/* Question templates to ask about any concept */
static const char *SELF_QUESTIONS[] = {
    "what is %s",
    "what type is %s",
    "where is %s located",
    "when was %s created",
    "who created %s",
    "why is %s important",
    "what is %s made of",
    "what does %s cause",
    "what is %s used for",
    "how does %s work",
    NULL
};

/* Priority levels for gap filling */
typedef enum {
    SIP2_PRIORITY_CRITICAL,   /* User asked about this and we failed */
    SIP2_PRIORITY_HIGH,       /* Highly connected concept, many edges */
    SIP2_PRIORITY_MEDIUM,     /* Moderately connected */
    SIP2_PRIORITY_LOW,        /* Leaf node, rarely accessed */
} SIP2Priority;

/* A knowledge gap */
typedef struct {
    uint32_t concept_id;
    char     concept_text[64];
    char     missing_relation[32];   /* What we don't know about it */
    SIP2Priority priority;
    uint32_t times_asked;            /* How many users hit this gap */
    uint32_t connectivity;           /* How many edges this concept has */
    time_t   first_detected;
    time_t   last_asked;
    uint8_t  filled;                 /* 1 = gap has been filled */
} SIP2Gap;

/* Coverage report */
typedef struct {
    uint32_t total_concepts;
    uint32_t fully_covered;          /* Can answer all question templates */
    uint32_t partially_covered;      /* Can answer some */
    uint32_t zero_coverage;          /* Can't answer anything */
    uint32_t gaps_detected;
    uint32_t gaps_filled;
    float    coverage_percent;
} SIP2Coverage;

/* Self-interrogation engine */
typedef struct {
    SIP2Gap  gaps[SIP2_MAX_GAPS];
    uint32_t gap_count;
    SIP2Coverage coverage;
    uint32_t interrogations_run;
    uint32_t concepts_tested;
    time_t   last_run;
} SIP2Engine;

/* ─── API ─── */

static void sip2_init(SIP2Engine *engine) {
    memset(engine, 0, sizeof(*engine));
}

/*
 * Test a single concept: generate all question templates, check which
 * ones the system can answer. Record gaps.
 *
 * can_answer_func: callback that tests if system can answer a question
 *   Returns: 1 = can answer, 0 = gap
 */
typedef int (*SIP2CanAnswerFn)(const char *question, void *ctx);

static int sip2_test_concept(SIP2Engine *engine, uint32_t concept_id,
                             const char *concept_text, uint32_t connectivity,
                             SIP2CanAnswerFn can_answer, void *ctx) {
    int answerable = 0;
    int total = 0;

    for (int i = 0; SELF_QUESTIONS[i]; i++) {
        char question[256];
        snprintf(question, sizeof(question), SELF_QUESTIONS[i], concept_text);
        total++;

        if (can_answer(question, ctx)) {
            answerable++;
        } else {
            /* Record gap */
            if (engine->gap_count < SIP2_MAX_GAPS) {
                SIP2Gap *gap = &engine->gaps[engine->gap_count];
                gap->concept_id = concept_id;
                strncpy(gap->concept_text, concept_text, 63);
                /* Extract relation from template */
                if (strstr(SELF_QUESTIONS[i], "what is %s")) strncpy(gap->missing_relation, "definition", 31);
                else if (strstr(SELF_QUESTIONS[i], "where")) strncpy(gap->missing_relation, "location", 31);
                else if (strstr(SELF_QUESTIONS[i], "when")) strncpy(gap->missing_relation, "time", 31);
                else if (strstr(SELF_QUESTIONS[i], "who")) strncpy(gap->missing_relation, "creator", 31);
                else if (strstr(SELF_QUESTIONS[i], "made of")) strncpy(gap->missing_relation, "composition", 31);
                else strncpy(gap->missing_relation, "general", 31);

                gap->priority = connectivity > 10 ? SIP2_PRIORITY_HIGH :
                               connectivity > 3  ? SIP2_PRIORITY_MEDIUM : SIP2_PRIORITY_LOW;
                gap->connectivity = connectivity;
                gap->first_detected = time(NULL);
                gap->times_asked = 0;
                gap->filled = 0;
                engine->gap_count++;
            }
        }
    }

    engine->concepts_tested++;
    return answerable;
}

/*
 * Run self-interrogation on a batch of concepts.
 * Returns number of gaps found.
 */
static int sip2_run_batch(SIP2Engine *engine, uint32_t *concept_ids,
                          const char **concept_texts, uint32_t *connectivities,
                          uint32_t count, SIP2CanAnswerFn can_answer, void *ctx) {
    engine->interrogations_run++;
    engine->last_run = time(NULL);

    uint32_t gaps_before = engine->gap_count;
    uint32_t fully_covered = 0;
    uint32_t partial = 0;
    uint32_t zero_cov = 0;

    uint32_t batch = count < SIP2_BATCH_SIZE ? count : SIP2_BATCH_SIZE;
    for (uint32_t i = 0; i < batch; i++) {
        int score = sip2_test_concept(engine, concept_ids[i], concept_texts[i],
                                      connectivities[i], can_answer, ctx);
        int total_qs = 0;
        for (int q = 0; SELF_QUESTIONS[q]; q++) total_qs++;

        if (score == total_qs) fully_covered++;
        else if (score > 0) partial++;
        else zero_cov++;
    }

    /* Update coverage */
    engine->coverage.total_concepts += batch;
    engine->coverage.fully_covered += fully_covered;
    engine->coverage.partially_covered += partial;
    engine->coverage.zero_coverage += zero_cov;
    engine->coverage.gaps_detected = engine->gap_count;
    engine->coverage.coverage_percent = engine->coverage.total_concepts > 0 ?
        (float)engine->coverage.fully_covered / engine->coverage.total_concepts * 100 : 0;

    return (int)(engine->gap_count - gaps_before);
}

/* Get top N gaps sorted by priority */
static int sip2_get_top_gaps(SIP2Engine *engine, SIP2Gap *output, int max_output) {
    /* Simple sort by priority then connectivity */
    /* Copy unfilled gaps */
    SIP2Gap *unfilled[SIP2_MAX_GAPS];
    int uf_count = 0;
    for (uint32_t i = 0; i < engine->gap_count && uf_count < SIP2_MAX_GAPS; i++) {
        if (!engine->gaps[i].filled) {
            unfilled[uf_count++] = &engine->gaps[i];
        }
    }

    /* Sort: priority ASC (critical first), then connectivity DESC */
    for (int i = 0; i < uf_count - 1; i++) {
        for (int j = i + 1; j < uf_count; j++) {
            if (unfilled[j]->priority < unfilled[i]->priority ||
                (unfilled[j]->priority == unfilled[i]->priority &&
                 unfilled[j]->connectivity > unfilled[i]->connectivity)) {
                SIP2Gap *tmp = unfilled[i];
                unfilled[i] = unfilled[j];
                unfilled[j] = tmp;
            }
        }
    }

    int count = uf_count < max_output ? uf_count : max_output;
    for (int i = 0; i < count; i++) {
        output[i] = *unfilled[i];
    }
    return count;
}

/* Mark gap as filled (after web search imported the fact) */
static void sip2_mark_filled(SIP2Engine *engine, uint32_t concept_id, const char *relation) {
    for (uint32_t i = 0; i < engine->gap_count; i++) {
        if (engine->gaps[i].concept_id == concept_id &&
            strcmp(engine->gaps[i].missing_relation, relation) == 0) {
            engine->gaps[i].filled = 1;
            engine->coverage.gaps_filled++;
            break;
        }
    }
}

/* Boost priority when a user actually hits the gap */
static void sip2_user_hit_gap(SIP2Engine *engine, const char *concept_text) {
    for (uint32_t i = 0; i < engine->gap_count; i++) {
        if (strstr(engine->gaps[i].concept_text, concept_text)) {
            engine->gaps[i].times_asked++;
            engine->gaps[i].last_asked = time(NULL);
            if (engine->gaps[i].priority > SIP2_PRIORITY_CRITICAL) {
                engine->gaps[i].priority--;  /* Escalate priority */
            }
        }
    }
}

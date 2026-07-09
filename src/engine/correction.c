/**
 * correction.c - Phase 8: User Correction Detection & Application
 */
#define _POSIX_C_SOURCE 200809L

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <ctype.h>
#include "knowledge.h"

#define CORRECTION_MAX_LEN 256

typedef struct {
    char subject[128];
    char relation[64];
    char object[128];
    int valid;
} CorrectedFact;

static int starts_with_ci(const char *str, const char *prefix) {
    while (*prefix) {
        if (tolower((unsigned char)*str) != tolower((unsigned char)*prefix)) return 0;
        str++; prefix++;
    }
    return 1;
}

static const char *skip_ws_comma(const char *s) {
    while (*s && (isspace((unsigned char)*s) || *s == ',')) s++;
    return s;
}

static int extract_is_fact(const char *text, CorrectedFact *fact) {
    const char *is_ptr = strstr(text, " is ");
    const char *are_ptr = strstr(text, " are ");
    const char *rel_ptr = NULL;
    int rel_len = 0;

    if (is_ptr && (!are_ptr || is_ptr < are_ptr)) {
        rel_ptr = is_ptr; rel_len = 4;
    } else if (are_ptr) {
        rel_ptr = are_ptr; rel_len = 5;
    }
    if (!rel_ptr) return 0;

    size_t subj_len = (size_t)(rel_ptr - text);
    if (subj_len == 0 || subj_len >= sizeof(fact->subject)) return 0;
    memcpy(fact->subject, text, subj_len);
    fact->subject[subj_len] = '\0';

    strncpy(fact->relation, "is", sizeof(fact->relation) - 1);

    const char *obj_start = rel_ptr + rel_len;
    while (*obj_start && isspace((unsigned char)*obj_start)) obj_start++;
    if (!*obj_start) return 0;

    strncpy(fact->object, obj_start, sizeof(fact->object) - 1);
    size_t olen = strlen(fact->object);
    while (olen > 0 && (fact->object[olen-1] == '.' || fact->object[olen-1] == '!'
                       || isspace((unsigned char)fact->object[olen-1]))) {
        fact->object[--olen] = '\0';
    }
    fact->valid = 1;
    return 1;
}

CorrectedFact correction_detect(const char *input) {
    CorrectedFact fact = { .valid = 0 };
    if (!input || !input[0]) return fact;

    static const char *prefixes[] = {
        "actually,", "actually ", "no,", "no ",
        "wrong,", "wrong ", "incorrect,",
        "that's wrong,", "not true,", "correction:", NULL
    };

    const char *remainder = NULL;
    for (int i = 0; prefixes[i]; i++) {
        if (starts_with_ci(input, prefixes[i])) {
            remainder = input + strlen(prefixes[i]);
            remainder = skip_ws_comma(remainder);
            break;
        }
    }
    if (!remainder || !*remainder) return fact;
    extract_is_fact(remainder, &fact);
    return fact;
}

int correction_apply(KnowledgeGraph *kg, CorrectedFact *fact) {
    if (!kg || !fact || !fact->valid) return 0;

    /* Check if a conflicting fact exists by querying subject+relation */
    Fact results[8];
    int found = kg_query(kg, fact->subject, fact->relation, results, 8);
    if (found > 0) {
        /* Update confidence of old facts to 0 (effectively removing them) */
        for (int i = 0; i < found; i++) {
            results[i].confidence = 0;
        }
    }

    /* Add corrected fact with high confidence */
    int idx = kg_add_fact(kg, fact->subject, fact->relation, fact->object, 95);
    return idx >= 0 ? 1 : 0;
}

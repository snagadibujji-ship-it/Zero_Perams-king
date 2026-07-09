#include "extract.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <ctype.h>

/* --- Internal helpers --- */

static void trim(char* s) {
    char* start = s;
    while (*start && isspace((unsigned char)*start)) start++;
    if (start != s) memmove(s, start, strlen(start) + 1);
    char* end = s + strlen(s) - 1;
    while (end >= s && isspace((unsigned char)*end)) *end-- = '\0';
}

static void lowercase(char* s) {
    for (; *s; s++) *s = (char)tolower((unsigned char)*s);
}

static int add_fact(ExtractionResult* result, const char* subj,
                    const char* rel, const char* obj, int conf) {
    if (result->count >= result->capacity) {
        int new_cap = result->capacity * 2;
        ExtractedFact* tmp = realloc(result->facts, sizeof(ExtractedFact) * new_cap);
        if (!tmp) return 0;
        result->facts = tmp;
        result->capacity = new_cap;
    }
    ExtractedFact* f = &result->facts[result->count];
    strncpy(f->subject, subj, MAX_EXTRACT_SUBJECT - 1);
    f->subject[MAX_EXTRACT_SUBJECT - 1] = '\0';
    strncpy(f->relation, rel, 63);
    f->relation[63] = '\0';
    strncpy(f->object, obj, MAX_EXTRACT_VALUE - 1);
    f->object[MAX_EXTRACT_VALUE - 1] = '\0';
    f->confidence = conf;
    trim(f->subject); trim(f->relation); trim(f->object);
    result->count++;
    return 1;
}

static const char* strip_article(const char* s) {
    if (strncmp(s, "a ", 2) == 0) return s + 2;
    if (strncmp(s, "an ", 3) == 0) return s + 3;
    if (strncmp(s, "the ", 4) == 0) return s + 4;
    return s;
}

/* Macro: match "marker" in buf, split into subj (before) and obj (after) */
#define MATCH(marker, relation, conf) do { \
    p = strstr(buf, marker); \
    if (p) { \
        strncpy(subj, buf, (size_t)(p - buf)); subj[p - buf] = '\0'; \
        strncpy(obj, p + strlen(marker), MAX_EXTRACT_VALUE - 1); obj[MAX_EXTRACT_VALUE-1] = '\0'; \
        return add_fact(result, strip_article(subj), relation, strip_article(obj), conf); \
    } \
} while(0)

/* Reverse: obj=before marker, subj=after marker (for contains/includes) */
#define MATCH_REV(marker, relation, conf) do { \
    p = strstr(buf, marker); \
    if (p) { \
        strncpy(subj, buf, (size_t)(p - buf)); subj[p - buf] = '\0'; \
        strncpy(obj, p + strlen(marker), MAX_EXTRACT_VALUE - 1); obj[MAX_EXTRACT_VALUE-1] = '\0'; \
        return add_fact(result, strip_article(obj), relation, strip_article(subj), conf); \
    } \
} while(0)

/* --- Public API --- */

void extract_init(ExtractionResult* result, int initial_capacity) {
    if (initial_capacity < 4) initial_capacity = 4;
    result->facts = malloc(sizeof(ExtractedFact) * initial_capacity);
    result->count = 0;
    result->capacity = initial_capacity;
}

void extract_free(ExtractionResult* result) {
    if (result->facts) { free(result->facts); result->facts = NULL; }
    result->count = 0;
    result->capacity = 0;
}

int extract_sentence(const char* sentence, ExtractionResult* result) {
    if (!sentence || !result) return 0;

    char buf[1024];
    strncpy(buf, sentence, sizeof(buf) - 1);
    buf[sizeof(buf) - 1] = '\0';
    lowercase(buf);
    trim(buf);
    if (strlen(buf) < 3) return 0;

    /* Remove trailing punctuation */
    size_t len = strlen(buf);
    while (len > 0 && (buf[len-1] == '.' || buf[len-1] == '!' || buf[len-1] == '?'))
        buf[--len] = '\0';

    char subj[MAX_EXTRACT_SUBJECT], obj[MAX_EXTRACT_VALUE];
    const char* p;

    /* "the X of Y is Z" → (Y, X_is, Z) */
    if (strncmp(buf, "the ", 4) == 0) {
        p = strstr(buf + 4, " of ");
        if (p) {
            const char* is_p = strstr(p + 4, " is ");
            if (is_p) {
                size_t xlen = (size_t)(p - (buf + 4));
                char attr[56];
                strncpy(attr, buf + 4, xlen < 55 ? xlen : 55);
                attr[xlen < 55 ? xlen : 55] = '\0';
                trim(attr);
                size_t ylen = (size_t)(is_p - (p + 4));
                strncpy(subj, p + 4, ylen); subj[ylen] = '\0';
                trim(subj);
                strncpy(obj, is_p + 4, MAX_EXTRACT_VALUE - 1); obj[MAX_EXTRACT_VALUE-1] = '\0';
                trim(obj);
                char rel[64];
                snprintf(rel, sizeof(rel), "%s_is", attr);
                return add_fact(result, strip_article(subj), rel, strip_article(obj), 90);
            }
        }
    }

    /* Specific patterns — order matters (most specific first) */
    MATCH(" was created by ",    "created_by",    90);
    MATCH(" was invented by ",   "invented_by",   90);
    MATCH(" was discovered by ", "discovered_by", 90);
    MATCH(" is located in ",     "located_in",    90);
    MATCH(" is able to ",        "capable_of",    90);
    MATCH(" is also known as ",  "synonym",       90);
    MATCH(" is the opposite of ","opposite_of",   90);
    MATCH(" is made of ",        "made_of",       90);
    MATCH(" is used for ",       "used_for",      90);
    MATCH(" is similar to ",     "similar_to",    90);
    MATCH(" is part of ",        "part_of",       90);

    /* "X is bigger/smaller/... than Y" → compared_to */
    p = strstr(buf, " than ");
    if (p) {
        const char* is_p = strstr(buf, " is ");
        if (is_p && is_p < p) {
            strncpy(subj, buf, (size_t)(is_p - buf)); subj[is_p - buf] = '\0';
            strncpy(obj, p + 6, MAX_EXTRACT_VALUE - 1); obj[MAX_EXTRACT_VALUE-1] = '\0';
            return add_fact(result, strip_article(subj), "compared_to", strip_article(obj), 90);
        }
    }

    MATCH_REV(" contains ", "part_of", 90);
    MATCH_REV(" includes ", "part_of", 90);
    MATCH(" causes ",    "causes", 90);
    MATCH(" leads to ",  "causes", 90);
    MATCH(" can ",       "capable_of", 90);

    /* "X has Y" / "X have Y" */
    p = strstr(buf, " has ");
    if (!p) p = strstr(buf, " have ");
    if (p) {
        strncpy(subj, buf, (size_t)(p - buf)); subj[p - buf] = '\0';
        int skip = (*(p+2) == 's') ? 5 : 6;
        strncpy(obj, p + skip, MAX_EXTRACT_VALUE - 1); obj[MAX_EXTRACT_VALUE-1] = '\0';
        return add_fact(result, strip_article(subj), "has", strip_article(obj), 90);
    }

    /* "X is a Y" / "X is an Y" */
    p = strstr(buf, " is a ");
    if (!p) p = strstr(buf, " is an ");
    if (p) {
        strncpy(subj, buf, (size_t)(p - buf)); subj[p - buf] = '\0';
        int skip = (*(p+4) == 'n') ? 7 : 6;
        strncpy(obj, p + skip, MAX_EXTRACT_VALUE - 1); obj[MAX_EXTRACT_VALUE-1] = '\0';
        return add_fact(result, strip_article(subj), "is_a", strip_article(obj), 90);
    }

    /* "X are Y" → is_a (plural) */
    MATCH(" are ", "is_a", 90);

    /* Generic: "X is Y" [lowest priority] */
    MATCH(" is ", "is", 60);

    return 0;
}

int extract_text(const char* text, ExtractionResult* result) {
    if (!text || !result) return 0;
    char buf[4096];
    strncpy(buf, text, sizeof(buf) - 1);
    buf[sizeof(buf) - 1] = '\0';

    int total = 0;
    for (char* c = buf; *c; c++) {
        if (*c == '.' || *c == '!' || *c == '?') *c = '\n';
    }
    char* saveptr = NULL;
    char* line = strtok_r(buf, "\n", &saveptr);
    while (line) {
        trim(line);
        if (strlen(line) > 2)
            total += extract_sentence(line, result);
        line = strtok_r(NULL, "\n", &saveptr);
    }
    return total;
}

int extract_file(const char* filepath, ExtractionResult* result) {
    if (!filepath || !result) return 0;
    FILE* fp = fopen(filepath, "r");
    if (!fp) return -1;
    int total = 0;
    char line[4096];
    while (fgets(line, sizeof(line), fp)) {
        trim(line);
        if (strlen(line) > 2)
            total += extract_text(line, result);
    }
    fclose(fp);
    return total;
}

/* --- TEST MODE --- */
#ifdef TEST_MODE
int main(void) {
    int passed = 0, tests = 0;

    #define TEST(input, exp_s, exp_r, exp_o) do { \
        tests++; \
        ExtractionResult t; extract_init(&t, 4); \
        extract_sentence(input, &t); \
        if (t.count > 0 && strcmp(t.facts[0].subject, exp_s) == 0 && \
            strcmp(t.facts[0].relation, exp_r) == 0 && \
            strcmp(t.facts[0].object, exp_o) == 0) { \
            printf("PASS: %s\n", input); passed++; \
        } else { \
            printf("FAIL: %s\n  got: (%s, %s, %s)\n", input, \
                t.count?t.facts[0].subject:"", t.count?t.facts[0].relation:"", \
                t.count?t.facts[0].object:""); \
        } \
        extract_free(&t); \
    } while(0)

    TEST("Dogs are mammals", "dogs", "is_a", "mammals");
    TEST("The capital of France is Paris", "france", "capital_is", "paris");
    TEST("Linux was created by Linus Torvalds", "linux", "created_by", "linus torvalds");
    TEST("Water is made of hydrogen and oxygen", "water", "made_of", "hydrogen and oxygen");
    TEST("A knife is used for cutting", "knife", "used_for", "cutting");
    TEST("Birds can fly", "birds", "capable_of", "fly");

    /* Multi-sentence test */
    tests++;
    ExtractionResult mt;
    extract_init(&mt, 8);
    int n = extract_text("Dogs are mammals. Birds can fly. Water is made of hydrogen and oxygen.", &mt);
    if (n == 3 && mt.count == 3) { printf("PASS: multi-sentence (3 facts)\n"); passed++; }
    else { printf("FAIL: multi-sentence got %d facts\n", mt.count); }
    extract_free(&mt);

    printf("\nResults: %d/%d passed\n", passed, tests);
    return (passed == tests) ? 0 : 1;
}
#endif

/**
 * learn.c - Learning Engine
 * Allows the AI to persistently learn new facts from the user.
 */
#define _POSIX_C_SOURCE 200809L

#include "learn.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <ctype.h>
#include <sys/stat.h>
#include <errno.h>

#define SOURCE_TAUGHT 2

static LearnStats g_stats = {0, 0, 0};

/* Convert string to lowercase in-place */
static void str_lower(char *s) {
    for (; *s; s++) *s = (char)tolower((unsigned char)*s);
}

/* Trim leading/trailing whitespace in-place, return pointer */
static char *str_trim(char *s) {
    while (isspace((unsigned char)*s)) s++;
    char *end = s + strlen(s) - 1;
    while (end > s && isspace((unsigned char)*end)) *end-- = '\0';
    return s;
}

/* Ensure directory exists (mkdir -p equivalent for single level) */
static int ensure_dir(const char *path) {
    struct stat st;
    if (stat(path, &st) == 0) return 0;
    if (mkdir(path, 0755) == 0) return 0;
    if (errno == EEXIST) return 0;
    return -1;
}

/* Add a fact with TAUGHT source */
static int add_taught_fact(KnowledgeGraph *kg, const char *subj,
                           const char *rel, const char *obj) {
    int idx = kg_add_fact(kg, subj, rel, obj, 90);
    if (idx < 0) return -1;
    kg->facts[idx].source = SOURCE_TAUGHT;
    return idx;
}

int learn_init(KnowledgeGraph *kg) {
    if (!kg) return -1;
    ensure_dir("user_data");
    int loaded = learn_load(kg);
    g_stats.facts_learned_total = loaded > 0 ? loaded : 0;
    g_stats.facts_learned_session = 0;
    g_stats.pending_consolidation = 0;
    return 0;
}

int learn_from_input(KnowledgeGraph *kg, const char *raw_input) {
    if (!kg || !raw_input) return -1;

    char buf[MAX_TEACH_BUFFER];
    strncpy(buf, raw_input, MAX_TEACH_BUFFER - 1);
    buf[MAX_TEACH_BUFFER - 1] = '\0';
    str_lower(buf);

    char *input = str_trim(buf);
    if (strlen(input) == 0) return 0;

    char subj[128];
    char *p;

    /* Pattern: "remember that X" → store raw as fact */
    if ((p = strstr(input, "remember that ")) == input) {
        char *content = str_trim(input + 14);
        if (strlen(content) > 0) {
            if (add_taught_fact(kg, "memory", "remembers", content) < 0) return -1;
            g_stats.facts_learned_session++;
            g_stats.facts_learned_total++;
            g_stats.pending_consolidation++;
            return 1;
        }
        return 0;
    }

    /* Pattern: "my name is X" → add_fact("user", "name_is", X) */
    if ((p = strstr(input, "my name is ")) == input) {
        char *name = str_trim(input + 11);
        if (strlen(name) > 0) {
            if (add_taught_fact(kg, "user", "name_is", name) < 0) return -1;
            g_stats.facts_learned_session++;
            g_stats.facts_learned_total++;
            g_stats.pending_consolidation++;
            return 1;
        }
        return 0;
    }

    /* ===================================================================
     * Pattern: "the X of Y is Z" → kg_add_fact(Y, X_is, Z)
     * e.g., "the capital of egypt is cairo" → (egypt, capital_is, cairo)
     * This is a generalized version that handles any "the ATTR of SUBJ is OBJ"
     * =================================================================== */
    if (strncmp(input, "the ", 4) == 0) {
        char *of_pos = strstr(input + 4, " of ");
        if (of_pos) {
            char *is_pos = strstr(of_pos + 4, " is ");
            if (is_pos) {
                /* Extract attribute (between "the " and " of ") */
                char attr[128] = {0};
                size_t attr_len = (size_t)(of_pos - (input + 4));
                if (attr_len > 0 && attr_len < sizeof(attr)) {
                    strncpy(attr, input + 4, attr_len);
                    attr[attr_len] = '\0';

                    /* Extract subject (between " of " and " is ") */
                    char *subj_start = of_pos + 4;
                    size_t slen = (size_t)(is_pos - subj_start);
                    if (slen > 0 && slen < sizeof(subj)) {
                        strncpy(subj, subj_start, slen);
                        subj[slen] = '\0';

                        /* Extract object (after " is ") */
                        char *object = str_trim(is_pos + 4);
                        if (strlen(object) > 0) {
                            /* Build relation: attr_is (e.g., "capital_is") */
                            char relation[128];
                            snprintf(relation, sizeof(relation), "%s_is", str_trim(attr));
                            /* Replace spaces in relation with underscores */
                            for (char *r = relation; *r; r++) {
                                if (*r == ' ') *r = '_';
                            }
                            if (add_taught_fact(kg, str_trim(subj), relation, object) < 0) return -1;
                            g_stats.facts_learned_session++;
                            g_stats.facts_learned_total++;
                            g_stats.pending_consolidation++;
                            return 1;
                        }
                    }
                }
            }
        }

        /* Pattern: "the largest X is Y" → kg_add_fact(X, largest_is, Y) */
        if (strncmp(input, "the largest ", 12) == 0) {
            char *is_pos = strstr(input + 12, " is ");
            if (is_pos) {
                size_t slen = (size_t)(is_pos - (input + 12));
                if (slen > 0 && slen < sizeof(subj)) {
                    strncpy(subj, input + 12, slen);
                    subj[slen] = '\0';
                    char *object = str_trim(is_pos + 4);
                    if (strlen(object) > 0) {
                        if (add_taught_fact(kg, str_trim(subj), "largest_is", object) < 0) return -1;
                        g_stats.facts_learned_session++;
                        g_stats.facts_learned_total++;
                        g_stats.pending_consolidation++;
                        return 1;
                    }
                }
            }
        }

        /* Pattern: "the tallest X is Y" → kg_add_fact(X, tallest_is, Y) */
        if (strncmp(input, "the tallest ", 12) == 0) {
            char *is_pos = strstr(input + 12, " is ");
            if (is_pos) {
                size_t slen = (size_t)(is_pos - (input + 12));
                if (slen > 0 && slen < sizeof(subj)) {
                    strncpy(subj, input + 12, slen);
                    subj[slen] = '\0';
                    char *object = str_trim(is_pos + 4);
                    if (strlen(object) > 0) {
                        if (add_taught_fact(kg, str_trim(subj), "tallest_is", object) < 0) return -1;
                        g_stats.facts_learned_session++;
                        g_stats.facts_learned_total++;
                        g_stats.pending_consolidation++;
                        return 1;
                    }
                }
            }
        }

        /* Pattern: "the smallest X is Y" → kg_add_fact(X, smallest_is, Y) */
        if (strncmp(input, "the smallest ", 13) == 0) {
            char *is_pos = strstr(input + 13, " is ");
            if (is_pos) {
                size_t slen = (size_t)(is_pos - (input + 13));
                if (slen > 0 && slen < sizeof(subj)) {
                    strncpy(subj, input + 13, slen);
                    subj[slen] = '\0';
                    char *object = str_trim(is_pos + 4);
                    if (strlen(object) > 0) {
                        if (add_taught_fact(kg, str_trim(subj), "smallest_is", object) < 0) return -1;
                        g_stats.facts_learned_session++;
                        g_stats.facts_learned_total++;
                        g_stats.pending_consolidation++;
                        return 1;
                    }
                }
            }
        }

        /* Pattern: "the fastest X is Y" → kg_add_fact(X, fastest_is, Y) */
        if (strncmp(input, "the fastest ", 12) == 0) {
            char *is_pos = strstr(input + 12, " is ");
            if (is_pos) {
                size_t slen = (size_t)(is_pos - (input + 12));
                if (slen > 0 && slen < sizeof(subj)) {
                    strncpy(subj, input + 12, slen);
                    subj[slen] = '\0';
                    char *object = str_trim(is_pos + 4);
                    if (strlen(object) > 0) {
                        if (add_taught_fact(kg, str_trim(subj), "fastest_is", object) < 0) return -1;
                        g_stats.facts_learned_session++;
                        g_stats.facts_learned_total++;
                        g_stats.pending_consolidation++;
                        return 1;
                    }
                }
            }
        }
    }

    /* ===================================================================
     * Pattern: "X was created in Y" → kg_add_fact(X, created_in, Y)
     * e.g., "python was created in 1991" → (python, created_in, 1991)
     * =================================================================== */
    if ((p = strstr(input, " was created in "))) {
        size_t slen = (size_t)(p - input);
        if (slen > 0 && slen < sizeof(subj)) {
            strncpy(subj, input, slen);
            subj[slen] = '\0';
            char *object = str_trim(p + 16);
            if (strlen(object) > 0) {
                if (add_taught_fact(kg, str_trim(subj), "created_in", object) < 0) return -1;
                g_stats.facts_learned_session++;
                g_stats.facts_learned_total++;
                g_stats.pending_consolidation++;
                return 1;
            }
        }
    }

    /* Pattern: "X was created by Y" */
    if ((p = strstr(input, " was created by "))) {
        size_t slen = (size_t)(p - input);
        if (slen > 0 && slen < sizeof(subj)) {
            strncpy(subj, input, slen);
            subj[slen] = '\0';
            char *object = str_trim(p + 16);
            if (strlen(object) > 0) {
                if (add_taught_fact(kg, str_trim(subj), "created_by", object) < 0) return -1;
                g_stats.facts_learned_session++;
                g_stats.facts_learned_total++;
                g_stats.pending_consolidation++;
                return 1;
            }
        }
    }

    /* Pattern: "X was born in Y" → kg_add_fact(X, born_in, Y) */
    if ((p = strstr(input, " was born in "))) {
        size_t slen = (size_t)(p - input);
        if (slen > 0 && slen < sizeof(subj)) {
            strncpy(subj, input, slen);
            subj[slen] = '\0';
            char *object = str_trim(p + 13);
            if (strlen(object) > 0) {
                if (add_taught_fact(kg, str_trim(subj), "born_in", object) < 0) return -1;
                g_stats.facts_learned_session++;
                g_stats.facts_learned_total++;
                g_stats.pending_consolidation++;
                return 1;
            }
        }
    }

    /* Pattern: "X was invented by Y" */
    if ((p = strstr(input, " was invented by "))) {
        size_t slen = (size_t)(p - input);
        if (slen > 0 && slen < sizeof(subj)) {
            strncpy(subj, input, slen);
            subj[slen] = '\0';
            char *object = str_trim(p + 17);
            if (strlen(object) > 0) {
                if (add_taught_fact(kg, str_trim(subj), "invented_by", object) < 0) return -1;
                g_stats.facts_learned_session++;
                g_stats.facts_learned_total++;
                g_stats.pending_consolidation++;
                return 1;
            }
        }
    }

    /* Pattern: "X was invented in Y" → kg_add_fact(X, invented_in, Y) */
    if ((p = strstr(input, " was invented in "))) {
        size_t slen = (size_t)(p - input);
        if (slen > 0 && slen < sizeof(subj)) {
            strncpy(subj, input, slen);
            subj[slen] = '\0';
            char *object = str_trim(p + 17);
            if (strlen(object) > 0) {
                if (add_taught_fact(kg, str_trim(subj), "invented_in", object) < 0) return -1;
                g_stats.facts_learned_session++;
                g_stats.facts_learned_total++;
                g_stats.pending_consolidation++;
                return 1;
            }
        }
    }

    /* Pattern: "X was founded in Y" → kg_add_fact(X, founded_in, Y) */
    if ((p = strstr(input, " was founded in "))) {
        size_t slen = (size_t)(p - input);
        if (slen > 0 && slen < sizeof(subj)) {
            strncpy(subj, input, slen);
            subj[slen] = '\0';
            char *object = str_trim(p + 16);
            if (strlen(object) > 0) {
                if (add_taught_fact(kg, str_trim(subj), "founded_in", object) < 0) return -1;
                g_stats.facts_learned_session++;
                g_stats.facts_learned_total++;
                g_stats.pending_consolidation++;
                return 1;
            }
        }
    }

    /* ===================================================================
     * Pattern: "X can Y" → kg_add_fact(X, can, Y)
     * e.g., "birds can fly" → (birds, can, fly)
     * =================================================================== */
    if ((p = strstr(input, " can "))) {
        size_t slen = (size_t)(p - input);
        if (slen > 0 && slen < sizeof(subj)) {
            strncpy(subj, input, slen);
            subj[slen] = '\0';
            char *object = str_trim(p + 5);
            if (strlen(object) > 0) {
                if (add_taught_fact(kg, str_trim(subj), "can", object) < 0) return -1;
                g_stats.facts_learned_session++;
                g_stats.facts_learned_total++;
                g_stats.pending_consolidation++;
                return 1;
            }
        }
    }

    /* ===================================================================
     * Pattern: "X has Y" → kg_add_fact(X, has, Y)
     * e.g., "a cat has whiskers" → (a cat, has, whiskers)
     * =================================================================== */
    if ((p = strstr(input, " has "))) {
        size_t slen = (size_t)(p - input);
        if (slen > 0 && slen < sizeof(subj)) {
            strncpy(subj, input, slen);
            subj[slen] = '\0';
            char *object = str_trim(p + 5);
            if (strlen(object) > 0) {
                if (add_taught_fact(kg, str_trim(subj), "has", object) < 0) return -1;
                g_stats.facts_learned_session++;
                g_stats.facts_learned_total++;
                g_stats.pending_consolidation++;
                return 1;
            }
        }
    }

    /* ===================================================================
     * Pattern: "X VERBs at Y" → kg_add_fact(X, VERB_at, Y)
     * e.g., "water freezes at 0 degrees" → (water, freezes_at, 0 degrees)
     * =================================================================== */
    if ((p = strstr(input, " at "))) {
        /* Find the verb: word immediately before " at " */
        /* Walk backwards from " at " to find the space before the verb */
        char *verb_end = p; /* points to space before "at" */
        char *scan = input;
        char *last_space = NULL;
        while (scan < verb_end) {
            if (*scan == ' ') last_space = scan;
            scan++;
        }
        if (last_space) {
            /* Subject is from start to last_space */
            size_t slen = (size_t)(last_space - input);
            if (slen > 0 && slen < sizeof(subj)) {
                strncpy(subj, input, slen);
                subj[slen] = '\0';

                /* Verb is from last_space+1 to verb_end */
                char verb[64] = {0};
                size_t vlen = (size_t)(verb_end - (last_space + 1));
                if (vlen > 0 && vlen < sizeof(verb)) {
                    strncpy(verb, last_space + 1, vlen);
                    verb[vlen] = '\0';

                    /* Build relation: verb_at */
                    char relation[128];
                    snprintf(relation, sizeof(relation), "%s_at", str_trim(verb));

                    char *object = str_trim(p + 4);
                    if (strlen(object) > 0) {
                        if (add_taught_fact(kg, str_trim(subj), relation, object) < 0) return -1;
                        g_stats.facts_learned_session++;
                        g_stats.facts_learned_total++;
                        g_stats.pending_consolidation++;
                        return 1;
                    }
                }
            }
        }
    }

    /* Pattern: "X is located in Y" */
    if ((p = strstr(input, " is located in "))) {
        size_t slen = (size_t)(p - input);
        if (slen > 0 && slen < sizeof(subj)) {
            strncpy(subj, input, slen);
            subj[slen] = '\0';
            char *object = str_trim(p + 15);
            if (strlen(object) > 0) {
                if (add_taught_fact(kg, str_trim(subj), "located_in", object) < 0) return -1;
                g_stats.facts_learned_session++;
                g_stats.facts_learned_total++;
                g_stats.pending_consolidation++;
                return 1;
            }
        }
    }

    /* Pattern: "X is made of Y" → kg_add_fact(X, made_of, Y) */
    if ((p = strstr(input, " is made of "))) {
        size_t slen = (size_t)(p - input);
        if (slen > 0 && slen < sizeof(subj)) {
            strncpy(subj, input, slen);
            subj[slen] = '\0';
            char *object = str_trim(p + 12);
            if (strlen(object) > 0) {
                if (add_taught_fact(kg, str_trim(subj), "made_of", object) < 0) return -1;
                g_stats.facts_learned_session++;
                g_stats.facts_learned_total++;
                g_stats.pending_consolidation++;
                return 1;
            }
        }
    }

    /* Pattern: "X is part of Y" → kg_add_fact(X, part_of, Y) */
    if ((p = strstr(input, " is part of "))) {
        size_t slen = (size_t)(p - input);
        if (slen > 0 && slen < sizeof(subj)) {
            strncpy(subj, input, slen);
            subj[slen] = '\0';
            char *object = str_trim(p + 12);
            if (strlen(object) > 0) {
                if (add_taught_fact(kg, str_trim(subj), "part_of", object) < 0) return -1;
                g_stats.facts_learned_session++;
                g_stats.facts_learned_total++;
                g_stats.pending_consolidation++;
                return 1;
            }
        }
    }

    /* ===================================================================
     * Pattern: "X is Y" (generic, must be last)
     * This is the catch-all for simple "X is Y" statements.
     * =================================================================== */
    if ((p = strstr(input, " is "))) {
        size_t slen = (size_t)(p - input);
        if (slen > 0 && slen < sizeof(subj)) {
            strncpy(subj, input, slen);
            subj[slen] = '\0';
            char *object = str_trim(p + 4);
            if (strlen(object) > 0) {
                if (add_taught_fact(kg, str_trim(subj), "is", object) < 0) return -1;
                g_stats.facts_learned_session++;
                g_stats.facts_learned_total++;
                g_stats.pending_consolidation++;
                return 1;
            }
        }
    }

    return 0; /* Couldn't parse */
}

int learn_save(KnowledgeGraph *kg) {
    if (!kg) return -1;
    ensure_dir("user_data");

    FILE *f = fopen(LEARN_FILE, "wb");
    if (!f) return -1;

    /* Count TAUGHT facts */
    uint32_t count = 0;
    for (size_t i = 0; i < kg->count; i++) {
        if (kg->facts[i].source == SOURCE_TAUGHT) count++;
    }

    fwrite(&count, sizeof(uint32_t), 1, f);

    for (size_t i = 0; i < kg->count; i++) {
        if (kg->facts[i].source != SOURCE_TAUGHT) continue;
        const char *s = kg_get_string(kg, kg->facts[i].subject_id);
        const char *r = kg_get_string(kg, (uint32_t)kg->facts[i].relation_id);
        const char *o = kg_get_string(kg, kg->facts[i].object_id);
        if (!s || !r || !o) { fclose(f); return -1; }
        fwrite(s, 1, strlen(s) + 1, f);
        fwrite(r, 1, strlen(r) + 1, f);
        fwrite(o, 1, strlen(o) + 1, f);
    }

    fclose(f);
    g_stats.pending_consolidation = 0;
    return 0;
}

int learn_load(KnowledgeGraph *kg) {
    if (!kg) return -1;

    FILE *f = fopen(LEARN_FILE, "rb");
    if (!f) return 0; /* File doesn't exist - not an error */

    uint32_t count = 0;
    if (fread(&count, sizeof(uint32_t), 1, f) != 1) {
        fclose(f);
        return 0;
    }

    int loaded = 0;
    for (uint32_t i = 0; i < count; i++) {
        char subj[128] = {0}, rel[128] = {0}, obj[128] = {0};
        /* Read null-terminated strings */
        int c, pos;

        pos = 0;
        while ((c = fgetc(f)) != EOF && c != '\0' && pos < 127)
            subj[pos++] = (char)c;
        if (c == EOF) break;

        pos = 0;
        while ((c = fgetc(f)) != EOF && c != '\0' && pos < 127)
            rel[pos++] = (char)c;
        if (c == EOF) break;

        pos = 0;
        while ((c = fgetc(f)) != EOF && c != '\0' && pos < 127)
            obj[pos++] = (char)c;
        if (c == EOF && pos == 0) break;

        if (add_taught_fact(kg, subj, rel, obj) >= 0) loaded++;
    }

    fclose(f);
    return loaded;
}

LearnStats learn_get_stats(void) {
    return g_stats;
}

/* ====================================================================== */
#ifdef TEST_MODE
#include <unistd.h>

#define TEST_FILE "user_data/learned.bin"

int main(void) {
    KnowledgeGraph kg;
    int rc;
    int pass = 0, fail = 0;

    printf("=== Learning Engine Tests ===\n\n");

    kg_init(&kg);

    /* Test 1: "Paris is beautiful" → fact(paris, is, beautiful) */
    rc = learn_from_input(&kg, "Paris is beautiful");
    Fact results[8];
    int n = kg_query(&kg, "paris", "is", results, 8);
    if (rc == 1 && n == 1) { pass++; printf("[PASS]"); } else { fail++; printf("[FAIL]"); }
    printf(" 'Paris is beautiful' → fact(paris, is, beautiful) [rc=%d, found=%d]\n", rc, n);

    /* Test 2: "the capital of Egypt is Cairo" → fact(egypt, capital_is, cairo) */
    rc = learn_from_input(&kg, "the capital of Egypt is Cairo");
    n = kg_query(&kg, "egypt", "capital_is", results, 8);
    const char *obj = n > 0 ? kg_get_string(&kg, results[0].object_id) : NULL;
    if (rc == 1 && n == 1 && obj && strcmp(obj, "cairo") == 0) { pass++; printf("[PASS]"); } else { fail++; printf("[FAIL]"); }
    printf(" 'the capital of Egypt is Cairo' → fact(egypt, capital_is, cairo) [obj=%s]\n", obj ? obj : "NULL");

    /* Test 3: "my name is Alex" → fact(user, name_is, alex) */
    rc = learn_from_input(&kg, "my name is Alex");
    n = kg_query(&kg, "user", "name_is", results, 8);
    obj = n > 0 ? kg_get_string(&kg, results[0].object_id) : NULL;
    if (rc == 1 && n == 1 && obj && strcmp(obj, "alex") == 0) { pass++; printf("[PASS]"); } else { fail++; printf("[FAIL]"); }
    printf(" 'my name is Alex' → fact(user, name_is, alex) [obj=%s]\n", obj ? obj : "NULL");

    /* Test 4: "Linux was created by Linus" */
    rc = learn_from_input(&kg, "Linux was created by Linus");
    n = kg_query(&kg, "linux", "created_by", results, 8);
    obj = n > 0 ? kg_get_string(&kg, results[0].object_id) : NULL;
    if (rc == 1 && n == 1 && obj && strcmp(obj, "linus") == 0) { pass++; printf("[PASS]"); } else { fail++; printf("[FAIL]"); }
    printf(" 'Linux was created by Linus' → fact(linux, created_by, linus) [obj=%s]\n", obj ? obj : "NULL");

    /* Test 5: "remember that water boils at 100c" */
    rc = learn_from_input(&kg, "remember that water boils at 100c");
    n = kg_query(&kg, "memory", "remembers", results, 8);
    if (rc == 1 && n >= 1) { pass++; printf("[PASS]"); } else { fail++; printf("[FAIL]"); }
    printf(" 'remember that ...' → stored [rc=%d, found=%d]\n", rc, n);

    /* Test 6: "Python was created in 1991" → fact(python, created_in, 1991) */
    rc = learn_from_input(&kg, "Python was created in 1991");
    n = kg_query(&kg, "python", "created_in", results, 8);
    obj = n > 0 ? kg_get_string(&kg, results[0].object_id) : NULL;
    if (rc == 1 && n == 1 && obj && strcmp(obj, "1991") == 0) { pass++; printf("[PASS]"); } else { fail++; printf("[FAIL]"); }
    printf(" 'Python was created in 1991' → fact(python, created_in, 1991) [obj=%s]\n", obj ? obj : "NULL");

    /* Test 7: "the largest ocean is the pacific" → fact(ocean, largest_is, the pacific) */
    rc = learn_from_input(&kg, "the largest ocean is the Pacific");
    n = kg_query(&kg, "ocean", "largest_is", results, 8);
    obj = n > 0 ? kg_get_string(&kg, results[0].object_id) : NULL;
    if (rc == 1 && n == 1 && obj && strcmp(obj, "the pacific") == 0) { pass++; printf("[PASS]"); } else { fail++; printf("[FAIL]"); }
    printf(" 'the largest ocean is the Pacific' → fact(ocean, largest_is, the pacific) [obj=%s]\n", obj ? obj : "NULL");

    /* Test 8: "Einstein was born in 1879" → fact(einstein, born_in, 1879) */
    rc = learn_from_input(&kg, "Einstein was born in 1879");
    n = kg_query(&kg, "einstein", "born_in", results, 8);
    obj = n > 0 ? kg_get_string(&kg, results[0].object_id) : NULL;
    if (rc == 1 && n == 1 && obj && strcmp(obj, "1879") == 0) { pass++; printf("[PASS]"); } else { fail++; printf("[FAIL]"); }
    printf(" 'Einstein was born in 1879' → fact(einstein, born_in, 1879) [obj=%s]\n", obj ? obj : "NULL");

    /* Test 9: "birds can fly" → fact(birds, can, fly) */
    rc = learn_from_input(&kg, "birds can fly");
    n = kg_query(&kg, "birds", "can", results, 8);
    obj = n > 0 ? kg_get_string(&kg, results[0].object_id) : NULL;
    if (rc == 1 && n == 1 && obj && strcmp(obj, "fly") == 0) { pass++; printf("[PASS]"); } else { fail++; printf("[FAIL]"); }
    printf(" 'birds can fly' → fact(birds, can, fly) [obj=%s]\n", obj ? obj : "NULL");

    /* Test 10: "a cat has whiskers" → fact(a cat, has, whiskers) */
    rc = learn_from_input(&kg, "a cat has whiskers");
    n = kg_query(&kg, "a cat", "has", results, 8);
    obj = n > 0 ? kg_get_string(&kg, results[0].object_id) : NULL;
    if (rc == 1 && n == 1 && obj && strcmp(obj, "whiskers") == 0) { pass++; printf("[PASS]"); } else { fail++; printf("[FAIL]"); }
    printf(" 'a cat has whiskers' → fact(a cat, has, whiskers) [obj=%s]\n", obj ? obj : "NULL");

    /* Test 11: "water freezes at 0 degrees" → fact(water, freezes_at, 0 degrees) */
    rc = learn_from_input(&kg, "water freezes at 0 degrees");
    n = kg_query(&kg, "water", "freezes_at", results, 8);
    obj = n > 0 ? kg_get_string(&kg, results[0].object_id) : NULL;
    if (rc == 1 && n == 1 && obj && strcmp(obj, "0 degrees") == 0) { pass++; printf("[PASS]"); } else { fail++; printf("[FAIL]"); }
    printf(" 'water freezes at 0 degrees' → fact(water, freezes_at, 0 degrees) [obj=%s]\n", obj ? obj : "NULL");

    /* Test 12: "the color of the sky is blue" → fact(the sky, color_is, blue) */
    rc = learn_from_input(&kg, "the color of the sky is blue");
    n = kg_query(&kg, "the sky", "color_is", results, 8);
    obj = n > 0 ? kg_get_string(&kg, results[0].object_id) : NULL;
    if (rc == 1 && n == 1 && obj && strcmp(obj, "blue") == 0) { pass++; printf("[PASS]"); } else { fail++; printf("[FAIL]"); }
    printf(" 'the color of the sky is blue' → fact(the sky, color_is, blue) [obj=%s]\n", obj ? obj : "NULL");

    /* Test 13: "the tallest mountain is everest" → fact(mountain, tallest_is, everest) */
    rc = learn_from_input(&kg, "the tallest mountain is everest");
    n = kg_query(&kg, "mountain", "tallest_is", results, 8);
    obj = n > 0 ? kg_get_string(&kg, results[0].object_id) : NULL;
    if (rc == 1 && n == 1 && obj && strcmp(obj, "everest") == 0) { pass++; printf("[PASS]"); } else { fail++; printf("[FAIL]"); }
    printf(" 'the tallest mountain is everest' → fact(mountain, tallest_is, everest) [obj=%s]\n", obj ? obj : "NULL");

    /* Test 14: "google was founded in 1998" → fact(google, founded_in, 1998) */
    rc = learn_from_input(&kg, "google was founded in 1998");
    n = kg_query(&kg, "google", "founded_in", results, 8);
    obj = n > 0 ? kg_get_string(&kg, results[0].object_id) : NULL;
    if (rc == 1 && n == 1 && obj && strcmp(obj, "1998") == 0) { pass++; printf("[PASS]"); } else { fail++; printf("[FAIL]"); }
    printf(" 'google was founded in 1998' → fact(google, founded_in, 1998) [obj=%s]\n", obj ? obj : "NULL");

    printf("\n--- Summary: %d passed, %d failed ---\n", pass, fail);

    /* Test: learn_save → file created */
    rc = learn_save(&kg);
    struct stat fst;
    int exists = (stat(TEST_FILE, &fst) == 0);
    if (rc == 0 && exists) { pass++; printf("[PASS]"); } else { fail++; printf("[FAIL]"); }
    printf(" learn_save → file created (rc=%d, exists=%d, size=%ld)\n", rc, exists, exists ? (long)fst.st_size : 0);

    /* Test: learn_load → facts restored */
    KnowledgeGraph kg2;
    kg_init(&kg2);
    int loaded = learn_load(&kg2);
    n = kg_query(&kg2, "paris", "is", results, 8);
    if (loaded > 0 && n == 1) { pass++; printf("[PASS]"); } else { fail++; printf("[FAIL]"); }
    printf(" learn_load → %d facts restored, paris query=%d\n", loaded, n);

    /* Cleanup */
    unlink(TEST_FILE);
    kg_destroy(&kg2);
    kg_destroy(&kg);

    printf("\n=== Learning Engine Tests Complete: %d passed, %d failed ===\n", pass, fail);
    return fail > 0 ? 1 : 0;
}

#endif /* TEST_MODE */

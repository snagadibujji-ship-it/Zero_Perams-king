/*
 * rre.c — Reverse Reasoning Engine
 * Pre-generates all answerable questions. Hash-indexed for instant match.
 * Given 5M facts → generates 25M+ question variants → O(1) lookup.
 */

#include "rre.h"
#include <string.h>
#include <stdio.h>
#include <stdlib.h>
#include <ctype.h>

/* ─── Question Templates per Relation ─── */

typedef struct { const char *relation; const char *templates[8]; } RelTemplates;

static const RelTemplates TEMPLATES[] = {
    {"capital",       {"what is the capital of %s", "capital of %s", "%s capital", "which city is the capital of %s", NULL}},
    {"capital_of",    {"what country is %s the capital of", "%s is the capital of", "%s capital of which country", NULL}},
    {"population",    {"what is the population of %s", "population of %s", "how many people live in %s", NULL}},
    {"located_in",    {"where is %s located", "where is %s", "%s is in which country", "%s location", NULL}},
    {"born_year",     {"when was %s born", "%s birth year", "what year was %s born", NULL}},
    {"died_year",     {"when did %s die", "%s death year", "what year did %s die", NULL}},
    {"born_in",       {"where was %s born", "%s birthplace", "which city was %s born in", NULL}},
    {"is_a",          {"what is %s", "what is a %s", "what type is %s", "%s is a what", NULL}},
    {"created_by",    {"who created %s", "who invented %s", "who made %s", "%s inventor", NULL}},
    {"designed_by",   {"who designed %s", "%s designer", "who created %s", NULL}},
    {"written_by",    {"who wrote %s", "%s author", "who is the author of %s", NULL}},
    {"directed_by",   {"who directed %s", "%s director", NULL}},
    {"discovered_by", {"who discovered %s", "%s discoverer", NULL}},
    {"invented_by",   {"who invented %s", "%s was invented by whom", NULL}},
    {"symbol",        {"what is the symbol of %s", "%s symbol", "chemical symbol for %s", NULL}},
    {"atomic_number", {"what is the atomic number of %s", "%s atomic number", NULL}},
    {"continent",     {"what continent is %s in", "%s is on which continent", NULL}},
    {"currency",      {"what currency does %s use", "%s currency", "money in %s", NULL}},
    {"official_language", {"what language do they speak in %s", "%s language", "official language of %s", NULL}},
    {"borders",       {"what countries border %s", "%s borders", "neighbors of %s", NULL}},
    {"genre",         {"what genre is %s", "%s genre", NULL}},
    {"nationality",   {"what nationality is %s", "where is %s from", "%s country", NULL}},
    {"known_for",     {"what is %s known for", "%s famous for", "why is %s famous", NULL}},
    {"has_property",  {"what are the properties of %s", "describe %s", NULL}},
    {"causes",        {"what does %s cause", "effect of %s", NULL}},
    {"caused_by",     {"what causes %s", "why does %s happen", "reason for %s", NULL}},
    {"part_of",       {"what is %s part of", "%s belongs to", NULL}},
    {"made_of",       {"what is %s made of", "%s composition", "%s material", NULL}},
    {"used_for",      {"what is %s used for", "purpose of %s", "%s usage", NULL}},
    {"capable_of",    {"what can %s do", "can %s", "%s abilities", NULL}},
    {NULL, {NULL}}
};

/* ─── Hash Function ─── */

static uint32_t rre_hash(const char *str) {
    uint32_t h = 2166136261u;
    while (*str) {
        h ^= (uint8_t)tolower((unsigned char)*str);
        h *= 16777619u;
        str++;
    }
    return h;
}

static void normalize_question(const char *input, char *output, int max_len) {
    int j = 0;
    for (int i = 0; input[i] && j < max_len - 1; i++) {
        char c = tolower((unsigned char)input[i]);
        if (c == '?' || c == '.' || c == '!' || c == ',') continue;
        if (c == ' ' && j > 0 && output[j-1] == ' ') continue;
        output[j++] = c;
    }
    while (j > 0 && output[j-1] == ' ') j--;
    output[j] = '\0';
}

/* ─── API ─── */

int rre_init(RREIndex *idx, uint32_t capacity) {
    memset(idx, 0, sizeof(*idx));
    idx->capacity = capacity;
    idx->entries = calloc(capacity, sizeof(RREEntry));
    if (!idx->entries) return -1;
    memset(idx->hash_table, 0xFF, sizeof(idx->hash_table));
    return 0;
}

void rre_free(RREIndex *idx) {
    free(idx->entries);
    memset(idx, 0, sizeof(*idx));
}

int rre_index_fact(RREIndex *idx, uint32_t subj_id, uint8_t rel_id,
                   uint32_t obj_id, uint8_t confidence,
                   const char *subj_text, const char *rel_text, const char *obj_text) {
    if (idx->count >= idx->capacity) return -1;

    /* Find templates for this relation */
    const RelTemplates *tmpl = NULL;
    for (int i = 0; TEMPLATES[i].relation; i++) {
        if (strcmp(TEMPLATES[i].relation, rel_text) == 0) {
            tmpl = &TEMPLATES[i];
            break;
        }
    }
    if (!tmpl) return 0;  /* No templates for this relation */

    /* Generate all question variants */
    int indexed = 0;
    for (int t = 0; tmpl->templates[t] && t < 8; t++) {
        char question[256];
        snprintf(question, sizeof(question), tmpl->templates[t], subj_text);

        char normalized[256];
        normalize_question(question, normalized, 256);

        uint32_t h = rre_hash(normalized);
        uint32_t slot = h % RRE_HASH_SIZE;

        /* Store in hash table (linear probe) */
        for (int probe = 0; probe < 16; probe++) {
            uint32_t s = (slot + probe) % RRE_HASH_SIZE;
            if (idx->hash_table[s] == 0xFFFFFFFF) {
                RREEntry *entry = &idx->entries[idx->count];
                entry->question_hash = h;
                entry->subject_id = subj_id;
                entry->relation_id = rel_id;
                entry->object_id = obj_id;
                entry->confidence = confidence;
                idx->hash_table[s] = idx->count;
                idx->count++;
                idx->questions_indexed++;
                indexed++;
                break;
            }
        }
    }

    /* Also index reverse: "Paris is the capital of ?" → france */
    if (obj_text && strlen(obj_text) > 1) {
        for (int t = 0; tmpl->templates[t] && t < 8; t++) {
            if (strstr(tmpl->templates[t], "which") || strstr(tmpl->templates[t], "what country")) {
                char question[256];
                snprintf(question, sizeof(question), tmpl->templates[t], obj_text);
                char normalized[256];
                normalize_question(question, normalized, 256);
                uint32_t h = rre_hash(normalized);
                uint32_t slot = h % RRE_HASH_SIZE;
                for (int probe = 0; probe < 16; probe++) {
                    uint32_t s = (slot + probe) % RRE_HASH_SIZE;
                    if (idx->hash_table[s] == 0xFFFFFFFF) {
                        if (idx->count < idx->capacity) {
                            RREEntry *entry = &idx->entries[idx->count];
                            entry->question_hash = h;
                            entry->subject_id = obj_id;
                            entry->relation_id = rel_id;
                            entry->object_id = subj_id;
                            entry->confidence = confidence;
                            idx->hash_table[s] = idx->count;
                            idx->count++;
                            indexed++;
                        }
                        break;
                    }
                }
            }
        }
    }

    return indexed;
}

int rre_lookup(RREIndex *idx, const char *question, uint32_t *obj_id, uint8_t *confidence) {
    idx->lookups++;
    char normalized[256];
    normalize_question(question, normalized, 256);
    uint32_t h = rre_hash(normalized);
    uint32_t slot = h % RRE_HASH_SIZE;

    for (int probe = 0; probe < 16; probe++) {
        uint32_t s = (slot + probe) % RRE_HASH_SIZE;
        uint32_t entry_idx = idx->hash_table[s];
        if (entry_idx == 0xFFFFFFFF) return 0;  /* Not found */
        if (idx->entries[entry_idx].question_hash == h) {
            *obj_id = idx->entries[entry_idx].object_id;
            *confidence = idx->entries[entry_idx].confidence;
            idx->hits++;
            return 1;  /* Found */
        }
    }
    return 0;
}

int rre_can_answer(RREIndex *idx, const char *question) {
    uint32_t obj; uint8_t conf;
    return rre_lookup(idx, question, &obj, &conf);
}

uint32_t rre_coverage_count(RREIndex *idx) {
    return idx->questions_indexed;
}

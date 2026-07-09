/*
 * concept_build.c - Concept Graph Compiler
 * Standalone tool: reads text files, extracts facts, outputs binary concept graph.
 * Usage: ./concept_build [-o output.dat] [input1.txt input2.txt ...]
 *        If no input files, generates built-in starter knowledge.
 */
#define _POSIX_C_SOURCE 200809L
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <ctype.h>

#define MAGIC      0x48414953
#define VERSION    1
#define MAX_CONCEPTS   100000
#define MAX_STRINGS    200000
#define MAX_RELATIONS  500000
#define MAX_PROPERTIES 200000
#define MAX_SYNONYMS   50000
#define MAX_STR_SIZE   (32 * 1024 * 1024)  /* 32MB string table */

/* On-disk structures (must match concept.h layout) */
typedef struct {
    uint32_t magic, version, concept_count, relation_count, synonym_count;
    uint32_t string_table_size, property_table_size;
    uint64_t string_table_offset, concept_table_offset, property_table_offset;
    uint64_t relation_table_offset, synonym_table_offset;
    uint32_t checksum, reserved;
} Header;

typedef struct {
    uint32_t name_offset, parent_id, first_property;
    uint16_t property_count, flags;
    uint32_t first_relation;
    uint16_t relation_count, depth;
} ConceptRec;

typedef struct {
    uint32_t key_offset, value_offset;
    uint16_t confidence, source;
} PropRec;

typedef struct {
    uint32_t source_id, target_id;
    uint8_t relation_type, strength;
    uint16_t confidence;
} RelRec;

typedef struct {
    uint32_t concept_id, synonym_offset;
} SynRec;

/* Build state */
static char string_table[MAX_STR_SIZE];
static uint32_t str_pos = 0;

static ConceptRec concepts[MAX_CONCEPTS];
static uint32_t concept_count = 0;

static PropRec properties[MAX_PROPERTIES];
static uint32_t prop_owner[MAX_PROPERTIES];  /* which concept owns each property */
static uint32_t prop_count = 0;

static RelRec relations[MAX_RELATIONS];
static uint32_t rel_count = 0;

static SynRec synonyms[MAX_SYNONYMS];
static uint32_t syn_count = 0;

/* Name lookup table */
static char* concept_names[MAX_CONCEPTS];

/* ─── String interning ─── */
static uint32_t intern_string(const char* s) {
    /* Linear scan (slow but simple for build tool) */
    uint32_t pos = 0;
    while (pos < str_pos) {
        if (strcmp(string_table + pos, s) == 0) return pos;
        pos += strlen(string_table + pos) + 1;
    }
    /* Add new */
    size_t len = strlen(s) + 1;
    if (str_pos + len >= MAX_STR_SIZE) return 0;
    memcpy(string_table + str_pos, s, len);
    uint32_t offset = str_pos;
    str_pos += len;
    return offset;
}

/* ─── Find or create concept ─── */
static uint32_t find_concept(const char* name) {
    for (uint32_t i = 0; i < concept_count; i++) {
        if (strcmp(concept_names[i], name) == 0) return i;
    }
    return UINT32_MAX;
}

static uint32_t get_or_create_concept(const char* name) {
    uint32_t id = find_concept(name);
    if (id != UINT32_MAX) return id;
    if (concept_count >= MAX_CONCEPTS) return 0;
    id = concept_count++;
    concepts[id].name_offset = intern_string(name);
    concepts[id].parent_id = UINT32_MAX;
    concepts[id].first_property = 0;
    concepts[id].property_count = 0;
    concepts[id].flags = 0;
    concepts[id].first_relation = 0;
    concepts[id].relation_count = 0;
    concepts[id].depth = 0;
    concept_names[id] = string_table + concepts[id].name_offset;
    return id;
}

/* ─── Add relation ─── */
static void add_relation(uint32_t src, uint32_t tgt, uint8_t type, uint8_t strength) {
    if (rel_count >= MAX_RELATIONS) return;
    relations[rel_count].source_id = src;
    relations[rel_count].target_id = tgt;
    relations[rel_count].relation_type = type;
    relations[rel_count].strength = strength;
    relations[rel_count].confidence = 90 * 256;
    rel_count++;
}

/* ─── Add property ─── */
static void add_property(uint32_t concept_id, const char* key, const char* value) {
    if (prop_count >= MAX_PROPERTIES) return;
    properties[prop_count].key_offset = intern_string(key);
    properties[prop_count].value_offset = intern_string(value);
    properties[prop_count].confidence = 90 * 256;
    properties[prop_count].source = 1;
    prop_owner[prop_count] = concept_id;
    concepts[concept_id].property_count++;
    prop_count++;
}

/* ─── Helpers ─── */
static void lowercase(char* s) { for (; *s; s++) *s = tolower(*s); }
static void trim(char* s) {
    char* end = s + strlen(s) - 1;
    while (end > s && isspace(*end)) *end-- = '\0';
    char* start = s;
    while (*start && isspace(*start)) start++;
    if (start != s) memmove(s, start, strlen(start) + 1);
}

static void strip_article(char* s) {
    if (strncmp(s, "a ", 2) == 0) memmove(s, s+2, strlen(s)-1);
    else if (strncmp(s, "an ", 3) == 0) memmove(s, s+3, strlen(s)-2);
    else if (strncmp(s, "the ", 4) == 0) memmove(s, s+4, strlen(s)-3);
    trim(s);
}

/* ─── Process one sentence ─── */
static void process_sentence(const char* line) {
    char buf[1024];
    strncpy(buf, line, sizeof(buf)-1); buf[sizeof(buf)-1] = '\0';
    lowercase(buf); trim(buf);
    if (strlen(buf) < 5) return;

    char subj[256], obj[512], rel[256];

    /* "X is a Y" / "X is an Y" */
    char *p;
    if ((p = strstr(buf, " is a ")) != NULL) {
        *p = '\0';
        strncpy(subj, buf, sizeof(subj)); strip_article(subj); trim(subj);
        strncpy(obj, p+6, sizeof(obj)); strip_article(obj); trim(obj);
        uint32_t s = get_or_create_concept(subj);
        uint32_t o = get_or_create_concept(obj);
        concepts[s].parent_id = o;
        add_relation(s, o, 0/*IS_A*/, 255);
        return;
    }
    if ((p = strstr(buf, " is an ")) != NULL) {
        *p = '\0';
        strncpy(subj, buf, sizeof(subj)); strip_article(subj); trim(subj);
        strncpy(obj, p+7, sizeof(obj)); strip_article(obj); trim(obj);
        uint32_t s = get_or_create_concept(subj);
        uint32_t o = get_or_create_concept(obj);
        concepts[s].parent_id = o;
        add_relation(s, o, 0, 255);
        return;
    }
    if ((p = strstr(buf, " are ")) != NULL && !strstr(buf, " are located") && !strstr(buf, " are made") && !strstr(buf, " are used")) {
        *p = '\0';
        strncpy(subj, buf, sizeof(subj)); strip_article(subj); trim(subj);
        strncpy(obj, p+5, sizeof(obj)); strip_article(obj); trim(obj);
        if (strlen(obj) > 2) {
            uint32_t s = get_or_create_concept(subj);
            uint32_t o = get_or_create_concept(obj);
            concepts[s].parent_id = o;
            add_relation(s, o, 0, 255);
        }
        return;
    }

    /* "the X of Y is Z" */
    if (strncmp(buf, "the ", 4) == 0 && (p = strstr(buf, " of ")) != NULL) {
        char* is = strstr(p, " is ");
        if (is) {
            char relname[128];
            size_t rlen = p-(buf+4);
            if (rlen >= sizeof(relname)) rlen = sizeof(relname)-1;
            strncpy(relname, buf+4, rlen); relname[rlen] = '\0';
            *is = '\0';
            strncpy(subj, p+4, sizeof(subj)); strip_article(subj); trim(subj);
            strncpy(obj, is+4, sizeof(obj)); strip_article(obj); trim(obj);
            snprintf(rel, sizeof(rel), "%s_is", relname); trim(rel);
            uint32_t s = get_or_create_concept(subj);
            get_or_create_concept(obj);
            add_property(s, rel, obj);
            return;
        }
    }

    /* "X was created/invented/discovered by Y" */
    if ((p = strstr(buf, " was created by ")) != NULL) {
        *p = '\0'; strncpy(subj, buf, sizeof(subj)); strip_article(subj); trim(subj);
        strncpy(obj, p+16, sizeof(obj)); trim(obj);
        uint32_t s = get_or_create_concept(subj);
        uint32_t o = get_or_create_concept(obj);
        add_relation(s, o, 13/*CREATED_BY*/, 255);
        return;
    }

    /* "X is located in Y" */
    if ((p = strstr(buf, " is located in ")) != NULL) {
        *p = '\0'; strncpy(subj, buf, sizeof(subj)); strip_article(subj); trim(subj);
        strncpy(obj, p+15, sizeof(obj)); strip_article(obj); trim(obj);
        uint32_t s = get_or_create_concept(subj);
        uint32_t o = get_or_create_concept(obj);
        add_relation(s, o, 7/*LOCATED_IN*/, 255);
        return;
    }

    /* "X has Y" */
    if ((p = strstr(buf, " has ")) != NULL) {
        *p = '\0'; strncpy(subj, buf, sizeof(subj)); strip_article(subj); trim(subj);
        strncpy(obj, p+5, sizeof(obj)); strip_article(obj); trim(obj);
        uint32_t s = get_or_create_concept(subj);
        add_property(s, "has", obj);
        return;
    }

    /* "X can Y" */
    if ((p = strstr(buf, " can ")) != NULL) {
        *p = '\0'; strncpy(subj, buf, sizeof(subj)); strip_article(subj); trim(subj);
        strncpy(obj, p+5, sizeof(obj)); trim(obj);
        uint32_t s = get_or_create_concept(subj);
        uint32_t o = get_or_create_concept(obj);
        add_relation(s, o, 11/*CAPABLE_OF*/, 200);
        return;
    }

    /* "X causes Y" */
    if ((p = strstr(buf, " causes ")) != NULL) {
        *p = '\0'; strncpy(subj, buf, sizeof(subj)); strip_article(subj); trim(subj);
        strncpy(obj, p+8, sizeof(obj)); strip_article(obj); trim(obj);
        uint32_t s = get_or_create_concept(subj);
        uint32_t o = get_or_create_concept(obj);
        add_relation(s, o, 5/*CAUSES*/, 200);
        return;
    }

    /* "X is the opposite of Y" */
    if ((p = strstr(buf, " is the opposite of ")) != NULL) {
        *p = '\0'; strncpy(subj, buf, sizeof(subj)); strip_article(subj); trim(subj);
        strncpy(obj, p+20, sizeof(obj)); strip_article(obj); trim(obj);
        uint32_t s = get_or_create_concept(subj);
        uint32_t o = get_or_create_concept(obj);
        add_relation(s, o, 4/*OPPOSITE_OF*/, 255);
        add_relation(o, s, 4, 255);
        return;
    }

    /* "X is used for Y" */
    if ((p = strstr(buf, " is used for ")) != NULL) {
        *p = '\0'; strncpy(subj, buf, sizeof(subj)); strip_article(subj); trim(subj);
        strncpy(obj, p+13, sizeof(obj)); strip_article(obj); trim(obj);
        uint32_t s = get_or_create_concept(subj);
        uint32_t o = get_or_create_concept(obj);
        add_relation(s, o, 9/*USED_FOR*/, 200);
        return;
    }

    /* "X is made of Y" */
    if ((p = strstr(buf, " is made of ")) != NULL) {
        *p = '\0'; strncpy(subj, buf, sizeof(subj)); strip_article(subj); trim(subj);
        strncpy(obj, p+12, sizeof(obj)); strip_article(obj); trim(obj);
        uint32_t s = get_or_create_concept(subj);
        uint32_t o = get_or_create_concept(obj);
        add_relation(s, o, 10/*MADE_OF*/, 200);
        return;
    }

    /* Generic "X is Y" (property) */
    if ((p = strstr(buf, " is ")) != NULL) {
        *p = '\0'; strncpy(subj, buf, sizeof(subj)); strip_article(subj); trim(subj);
        strncpy(obj, p+4, sizeof(obj)); strip_article(obj); trim(obj);
        if (strlen(subj) > 1 && strlen(obj) > 1) {
            uint32_t s = get_or_create_concept(subj);
            add_property(s, "is", obj);
        }
        return;
    }
}

/* ─── Sort and link properties to concepts ─── */
static void link_properties(void) {
    /* Sort properties by owner concept_id using parallel arrays */
    /* Simple insertion sort (good enough for build tool) */
    for (uint32_t i = 1; i < prop_count; i++) {
        PropRec tmp_p = properties[i];
        uint32_t tmp_o = prop_owner[i];
        uint32_t j = i;
        while (j > 0 && prop_owner[j-1] > tmp_o) {
            properties[j] = properties[j-1];
            prop_owner[j] = prop_owner[j-1];
            j--;
        }
        properties[j] = tmp_p;
        prop_owner[j] = tmp_o;
    }
    /* Now relink */
    for (uint32_t i = 0; i < concept_count; i++) {
        concepts[i].first_property = 0;
        concepts[i].property_count = 0;
    }
    for (uint32_t p = 0; p < prop_count; p++) {
        uint32_t owner = prop_owner[p];
        if (owner < concept_count) {
            if (concepts[owner].property_count == 0)
                concepts[owner].first_property = p;
            concepts[owner].property_count++;
        }
    }
}

/* ─── Compute depths ─── */
static void compute_depths(void) {
    for (uint32_t i = 0; i < concept_count; i++) {
        uint16_t depth = 0;
        uint32_t cur = i;
        while (concepts[cur].parent_id != UINT32_MAX && depth < 20) {
            cur = concepts[cur].parent_id;
            depth++;
        }
        concepts[i].depth = depth;
    }
}

/* ─── Assign first_relation to concepts ─── */
static int cmp_relations(const void* a, const void* b) {
    const RelRec* ra = (const RelRec*)a;
    const RelRec* rb = (const RelRec*)b;
    if (ra->source_id != rb->source_id) return (int)ra->source_id - (int)rb->source_id;
    return (int)ra->relation_type - (int)rb->relation_type;
}

static void link_relations(void) {
    /* Sort relations by source_id so each concept's relations are contiguous */
    qsort(relations, rel_count, sizeof(RelRec), cmp_relations);

    for (uint32_t i = 0; i < concept_count; i++) {
        concepts[i].first_relation = 0;
        concepts[i].relation_count = 0;
    }
    for (uint32_t r = 0; r < rel_count; r++) {
        uint32_t src = relations[r].source_id;
        if (src < concept_count) {
            if (concepts[src].relation_count == 0)
                concepts[src].first_relation = r;
            concepts[src].relation_count++;
        }
    }
}

/* ─── Write binary ─── */
static int write_output(const char* path) {
    FILE* f = fopen(path, "wb");
    if (!f) { perror("fopen"); return -1; }

    /* Compute offsets */
    uint64_t str_off = sizeof(Header);
    uint64_t con_off = str_off + str_pos;
    uint64_t prop_off = con_off + (concept_count * sizeof(ConceptRec));
    uint64_t rel_off = prop_off + (prop_count * sizeof(PropRec));
    uint64_t syn_off = rel_off + (rel_count * sizeof(RelRec));

    Header h = {0};
    h.magic = MAGIC;
    h.version = VERSION;
    h.concept_count = concept_count;
    h.relation_count = rel_count;
    h.synonym_count = syn_count;
    h.string_table_size = str_pos;
    h.property_table_size = prop_count;
    h.string_table_offset = str_off;
    h.concept_table_offset = con_off;
    h.property_table_offset = prop_off;
    h.relation_table_offset = rel_off;
    h.synonym_table_offset = syn_off;

    fwrite(&h, sizeof(Header), 1, f);
    fwrite(string_table, 1, str_pos, f);
    fwrite(concepts, sizeof(ConceptRec), concept_count, f);
    fwrite(properties, sizeof(PropRec), prop_count, f);
    fwrite(relations, sizeof(RelRec), rel_count, f);
    fwrite(synonyms, sizeof(SynRec), syn_count, f);
    fclose(f);
    return 0;
}

/* ─── Main ─── */
int main(int argc, char** argv) {
    const char* output = "src/data/knowledge.dat";
    int file_start = 1;

    /* Parse args */
    for (int i = 1; i < argc; i++) {
        if (strcmp(argv[i], "-o") == 0 && i+1 < argc) {
            output = argv[++i];
            file_start = i + 1;
        }
    }

    /* Init string table with empty string at offset 0 */
    string_table[0] = '\0';
    str_pos = 1;

    int files_processed = 0;
    for (int i = file_start; i < argc; i++) {
        FILE* f = fopen(argv[i], "r");
        if (!f) { fprintf(stderr, "Warning: can't open %s\n", argv[i]); continue; }
        char line[1024];
        while (fgets(line, sizeof(line), f)) {
            line[strcspn(line, "\n\r")] = '\0';
            if (line[0] == '\0' || line[0] == '#') continue;
            process_sentence(line);
        }
        fclose(f);
        files_processed++;
        fprintf(stderr, "[+] Processed %s (%u concepts so far)\n", argv[i], concept_count);
    }

    if (files_processed == 0) {
        fprintf(stderr, "[*] No input files \u2014 generating built-in starter knowledge...\n");
        /* Minimal built-in hierarchy */
        process_sentence("A thing is a concept");
        process_sentence("A living thing is a thing");
        process_sentence("An animal is a living thing");
        process_sentence("A mammal is an animal");
        process_sentence("A dog is a mammal");
        process_sentence("A cat is a mammal");
        process_sentence("A bird is an animal");
        process_sentence("A fish is an animal");
        process_sentence("A plant is a living thing");
        process_sentence("An object is a thing");
        process_sentence("A vehicle is an object");
        process_sentence("A tool is an object");
        process_sentence("A food is a thing");
        process_sentence("A place is a thing");
        process_sentence("A country is a place");
        process_sentence("A city is a place");
        process_sentence("A person is a living thing");
        fprintf(stderr, "[*] Built-in: %u concepts\n", concept_count);
    }

    /* Post-process */
    link_properties();
    compute_depths();
    link_relations();

    /* Write */
    if (write_output(output) == 0) {
        size_t total = sizeof(Header) + str_pos + 
                       concept_count * sizeof(ConceptRec) +
                       prop_count * sizeof(PropRec) +
                       rel_count * sizeof(RelRec) +
                       syn_count * sizeof(SynRec);
        printf("=== Concept Graph Compiled ===\n");
        printf("  Concepts:   %u\n", concept_count);
        printf("  Properties: %u\n", prop_count);
        printf("  Relations:  %u\n", rel_count);
        printf("  Synonyms:   %u\n", syn_count);
        printf("  Strings:    %u bytes\n", str_pos);
        printf("  Total size: %zu bytes (%.1f KB)\n", total, total/1024.0);
        printf("  Output:     %s\n", output);
    }
    return 0;
}

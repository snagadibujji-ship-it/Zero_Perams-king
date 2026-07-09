/* export.c — Brain export/import for portability */
#include "export.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

/* File format:
 * Header: magic(4) + version(4) + fact_count(4) + string_count(4) = 16 bytes
 * Strings: [len(2) + bytes]...
 * Facts: [subject_id(4) + relation_id(2) + object_id(4) + confidence(1)]...
 */

static int write_header(FILE *f, uint32_t fact_count, uint32_t string_count) {
    uint32_t magic = EXPORT_MAGIC;
    uint32_t version = EXPORT_VERSION;
    fwrite(&magic, 4, 1, f);
    fwrite(&version, 4, 1, f);
    fwrite(&fact_count, 4, 1, f);
    fwrite(&string_count, 4, 1, f);
    return 0;
}

static int write_strings(FILE *f, KnowledgeGraph *kg) {
    for (size_t i = 0; i < kg->string_count; i++) {
        uint16_t len = (uint16_t)strlen(kg->strings[i]);
        fwrite(&len, 2, 1, f);
        fwrite(kg->strings[i], 1, len, f);
    }
    return 0;
}

static int write_facts(FILE *f, Fact *facts, size_t count) {
    for (size_t i = 0; i < count; i++) {
        fwrite(&facts[i].subject_id, 4, 1, f);
        fwrite(&facts[i].relation_id, 2, 1, f);
        fwrite(&facts[i].object_id, 4, 1, f);
        fwrite(&facts[i].confidence, 1, 1, f);
    }
    return 0;
}

int export_brain(KnowledgeGraph *kg, const char *filepath) {
    FILE *f = fopen(filepath, "wb");
    if (!f) return -1;
    write_header(f, (uint32_t)kg->count, (uint32_t)kg->string_count);
    write_strings(f, kg);
    write_facts(f, kg->facts, kg->count);
    fclose(f);
    return 0;
}

int import_brain(KnowledgeGraph *kg, const char *filepath) {
    FILE *f = fopen(filepath, "rb");
    if (!f) return -1;

    uint32_t magic, version, fact_count, string_count;
    fread(&magic, 4, 1, f);
    fread(&version, 4, 1, f);
    fread(&fact_count, 4, 1, f);
    fread(&string_count, 4, 1, f);

    if (magic != EXPORT_MAGIC || version != EXPORT_VERSION) {
        fclose(f);
        return -1;
    }

    /* Read strings into temporary lookup */
    char **strs = malloc(string_count * sizeof(char *));
    if (!strs) { fclose(f); return -1; }
    for (uint32_t i = 0; i < string_count; i++) {
        uint16_t len;
        fread(&len, 2, 1, f);
        strs[i] = malloc(len + 1);
        fread(strs[i], 1, len, f);
        strs[i][len] = '\0';
    }

    /* Read and add facts */
    int imported = 0;
    for (uint32_t i = 0; i < fact_count; i++) {
        uint32_t subj, obj;
        uint16_t rel;
        uint8_t conf;
        fread(&subj, 4, 1, f);
        fread(&rel, 2, 1, f);
        fread(&obj, 4, 1, f);
        fread(&conf, 1, 1, f);

        if (subj < string_count && rel < string_count && obj < string_count) {
            kg_add_fact(kg, strs[subj], strs[rel], strs[obj], conf);
            imported++;
        }
    }

    for (uint32_t i = 0; i < string_count; i++) free(strs[i]);
    free(strs);
    fclose(f);
    return imported;
}

int export_learned(KnowledgeGraph *kg, const char *filepath) {
    /* Count taught facts (source == 1) */
    uint32_t taught_count = 0;
    for (size_t i = 0; i < kg->count; i++) {
        if (kg->facts[i].source == 1) taught_count++;
    }

    FILE *f = fopen(filepath, "wb");
    if (!f) return -1;

    write_header(f, taught_count, (uint32_t)kg->string_count);
    write_strings(f, kg);

    /* Write only taught facts */
    for (size_t i = 0; i < kg->count; i++) {
        if (kg->facts[i].source == 1) {
            fwrite(&kg->facts[i].subject_id, 4, 1, f);
            fwrite(&kg->facts[i].relation_id, 2, 1, f);
            fwrite(&kg->facts[i].object_id, 4, 1, f);
            fwrite(&kg->facts[i].confidence, 1, 1, f);
        }
    }
    fclose(f);
    return (int)taught_count;
}

int export_info(const char *filepath, int *fact_count, int *version) {
    FILE *f = fopen(filepath, "rb");
    if (!f) return -1;

    uint32_t magic, ver, fc, sc;
    fread(&magic, 4, 1, f);
    fread(&ver, 4, 1, f);
    fread(&fc, 4, 1, f);
    fread(&sc, 4, 1, f);
    fclose(f);

    if (magic != EXPORT_MAGIC) return -1;
    if (fact_count) *fact_count = (int)fc;
    if (version) *version = (int)ver;
    return 0;
}

#ifdef TEST_MODE
#include <assert.h>

int main(void) {
    printf("=== Export/Import Test ===\n");
    const char *path = "/tmp/test_brain.haib";

    /* Create KG with 5 facts */
    KnowledgeGraph kg;
    kg_init(&kg);
    kg_add_fact(&kg, "cat", "is_a", "animal", 95);
    kg_add_fact(&kg, "dog", "is_a", "animal", 95);
    kg_add_fact(&kg, "sun", "is_a", "star", 99);
    kg_add_fact(&kg, "water", "is_a", "liquid", 90);
    kg_add_fact(&kg, "earth", "is_a", "planet", 98);
    /* Mark some as taught */
    for (size_t i = 0; i < kg.count; i++) kg.facts[i].source = 1;

    /* Export */
    int rc = export_brain(&kg, path);
    assert(rc == 0);
    printf("[PASS] export_brain succeeded\n");

    /* Info check */
    int fc = 0, ver = 0;
    rc = export_info(path, &fc, &ver);
    assert(rc == 0 && fc == 5 && ver == 1);
    printf("[PASS] export_info: %d facts, version %d\n", fc, ver);

    /* Import into fresh KG */
    KnowledgeGraph kg2;
    kg_init(&kg2);
    int imported = import_brain(&kg2, path);
    assert(imported == 5);
    printf("[PASS] import_brain: %d facts imported\n", imported);
    assert(kg2.count == 5);
    printf("[PASS] Verified 5 facts present in new KG\n");

    /* export_learned */
    int learned = export_learned(&kg, "/tmp/test_learned.haib");
    assert(learned == 5);
    printf("[PASS] export_learned: %d taught facts\n", learned);

    /* Cleanup */
    kg_destroy(&kg);
    kg_destroy(&kg2);
    remove(path);
    remove("/tmp/test_learned.haib");

    printf("=== All export tests passed! ===\n");
    return 0;
}
#endif

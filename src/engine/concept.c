/*
 * concept.c — Semantic Concept Graph Engine
 * CORE intelligence: mmap'd concept graph with inheritance, similarity, relations
 */
#define _GNU_SOURCE
#include "concept.h"
#include <sys/mman.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <unistd.h>
#include <stdlib.h>
#include <string.h>
#include <stdio.h>

/* ─── Helpers ────────────────────────────────────────────────── */
static SemanticCore* g_sort_core = NULL;

static int name_compare(const void* a, const void* b) {
    uint32_t ia = *(const uint32_t*)a, ib = *(const uint32_t*)b;
    const char* na = g_sort_core->string_table + g_sort_core->concepts[ia].name_offset;
    const char* nb = g_sort_core->string_table + g_sort_core->concepts[ib].name_offset;
    return strcmp(na, nb);
}

static uint32_t get_parent(SemanticCore* core, uint32_t id) {
    if (!core->header || id >= core->header->concept_count) return UINT32_MAX;
    uint32_t p = core->concepts[id].parent_id;
    return (p == id) ? UINT32_MAX : p;
}

/* ─── Lifecycle ──────────────────────────────────────────────── */
int semantic_init(SemanticCore* core, const char* filepath) {
    memset(core, 0, sizeof(SemanticCore));
    if (!filepath) return 0;

    int fd = open(filepath, O_RDONLY);
    if (fd < 0) return 0; /* file doesn't exist → empty core is valid */

    struct stat st;
    if (fstat(fd, &st) < 0 || st.st_size < (off_t)sizeof(ConceptFileHeader)) {
        close(fd); return 0;
    }
    void* mapped = mmap(NULL, st.st_size, PROT_READ, MAP_PRIVATE, fd, 0);
    close(fd);
    if (mapped == MAP_FAILED) return -1;

    ConceptFileHeader* hdr = (ConceptFileHeader*)mapped;
    if (hdr->magic != CONCEPT_MAGIC || hdr->version != CONCEPT_VERSION) {
        munmap(mapped, st.st_size); return -1;
    }
    core->mapped_file = mapped;
    core->file_size = st.st_size;
    core->header = hdr;
    core->string_table = (char*)mapped + hdr->string_table_offset;
    core->concepts = (ConceptRecord*)((char*)mapped + hdr->concept_table_offset);
    core->properties = (PropertyRecord*)((char*)mapped + hdr->property_table_offset);
    core->relations = (RelationRecord*)((char*)mapped + hdr->relation_table_offset);
    core->synonyms = (SynonymRecord*)((char*)mapped + hdr->synonym_table_offset);
    return semantic_build_index(core);
}

void semantic_destroy(SemanticCore* core) {
    if (core->mapped_file && core->mapped_file != MAP_FAILED)
        munmap(core->mapped_file, core->file_size);
    free(core->name_index);
    memset(core, 0, sizeof(SemanticCore));
}

/* ─── Lookup ─────────────────────────────────────────────────── */
int semantic_find(SemanticCore* core, const char* name) {
    if (!core->name_index || !core->header || !name) return -1;
    uint32_t lo = 0, hi = core->index_size;
    while (lo < hi) {
        uint32_t mid = lo + (hi - lo) / 2;
        uint32_t cid = core->name_index[mid];
        int cmp = strcmp(name, core->string_table + core->concepts[cid].name_offset);
        if (cmp == 0) { core->lookups++; return (int)cid; }
        if (cmp < 0) hi = mid; else lo = mid + 1;
    }
    core->lookups++;
    return -1;
}

const char* semantic_get_name(SemanticCore* core, uint32_t id) {
    if (!core->header || id >= core->header->concept_count) return NULL;
    return core->string_table + core->concepts[id].name_offset;
}

ConceptRecord* semantic_get_concept(SemanticCore* core, uint32_t id) {
    if (!core->header || id >= core->header->concept_count) return NULL;
    return &core->concepts[id];
}

/* ─── Properties (with Inheritance) ──────────────────────────── */
const char* semantic_get_property(SemanticCore* core, uint32_t id, const char* key) {
    if (!core->header || !key) return NULL;
    uint32_t cur = id;
    for (int depth = 0; depth < INHERIT_DEPTH; depth++) {
        if (cur >= core->header->concept_count) return NULL;
        ConceptRecord* c = &core->concepts[cur];
        PropertyRecord* props = core->properties + c->first_property;
        for (uint16_t i = 0; i < c->property_count; i++) {
            if (strcmp(core->string_table + props[i].key_offset, key) == 0)
                return core->string_table + props[i].value_offset;
        }
        if (c->parent_id == cur) return NULL;
        cur = c->parent_id;
    }
    return NULL;
}

int semantic_get_all_properties(SemanticCore* core, uint32_t id,
                                 PropertyRecord* out, int max_out) {
    if (!core->header || !out || max_out <= 0) return 0;
    int count = 0;
    uint32_t seen_keys[MAX_PROPERTIES * INHERIT_DEPTH];
    int seen_count = 0;
    uint32_t cur = id;

    for (int depth = 0; depth < INHERIT_DEPTH && count < max_out; depth++) {
        if (cur >= core->header->concept_count) break;
        ConceptRecord* c = &core->concepts[cur];
        PropertyRecord* props = core->properties + c->first_property;
        for (uint16_t i = 0; i < c->property_count && count < max_out; i++) {
            int dup = 0;
            for (int s = 0; s < seen_count; s++)
                if (seen_keys[s] == props[i].key_offset) { dup = 1; break; }
            if (dup) continue;
            seen_keys[seen_count++] = props[i].key_offset;
            out[count++] = props[i];
        }
        if (c->parent_id == cur) break;
        cur = c->parent_id;
    }
    return count;
}

/* ─── Relations ──────────────────────────────────────────────── */
int semantic_get_relations(SemanticCore* core, uint32_t id,
                           RelationType type, uint32_t* targets, int max_targets) {
    if (!core->header || id >= core->header->concept_count || !targets) return 0;
    ConceptRecord* c = &core->concepts[id];
    RelationRecord* rels = core->relations + c->first_relation;
    int count = 0;
    for (uint16_t i = 0; i < c->relation_count && count < max_targets; i++)
        if (rels[i].source_id == id && rels[i].relation_type == (uint8_t)type)
            targets[count++] = rels[i].target_id;
    return count;
}

int semantic_are_related(SemanticCore* core, uint32_t a, uint32_t b, RelationType type) {
    if (!core->header || a >= core->header->concept_count || b >= core->header->concept_count)
        return 0;
    ConceptRecord* ca = &core->concepts[a];
    RelationRecord* rels = core->relations + ca->first_relation;
    for (uint16_t i = 0; i < ca->relation_count; i++)
        if (rels[i].source_id == a && rels[i].target_id == b &&
            rels[i].relation_type == (uint8_t)type) return 1;
    /* Transitive for IS_A: a→x→b */
    if (type == REL_IS_A) {
        for (uint16_t i = 0; i < ca->relation_count; i++) {
            if (rels[i].source_id == a && rels[i].relation_type == (uint8_t)REL_IS_A) {
                uint32_t x = rels[i].target_id;
                if (x >= core->header->concept_count) continue;
                ConceptRecord* cx = &core->concepts[x];
                RelationRecord* xr = core->relations + cx->first_relation;
                for (uint16_t j = 0; j < cx->relation_count; j++)
                    if (xr[j].source_id == x && xr[j].target_id == b &&
                        xr[j].relation_type == (uint8_t)REL_IS_A) return 1;
            }
        }
    }
    return 0;
}

/* ─── Semantic Similarity ────────────────────────────────────── */
float semantic_similarity(SemanticCore* core, uint32_t a, uint32_t b) {
    if (!core->header || a >= core->header->concept_count ||
        b >= core->header->concept_count) return 0.0f;
    if (a == b) return 1.0f;

    /* Direct SIMILAR_TO (check both directions) */
    ConceptRecord* ca = &core->concepts[a];
    RelationRecord* rels = core->relations + ca->first_relation;
    for (uint16_t i = 0; i < ca->relation_count; i++)
        if (rels[i].source_id == a && rels[i].target_id == b &&
            rels[i].relation_type == (uint8_t)REL_SIMILAR_TO)
            return (float)rels[i].strength / 255.0f;
    ConceptRecord* cb = &core->concepts[b];
    RelationRecord* br = core->relations + cb->first_relation;
    for (uint16_t i = 0; i < cb->relation_count; i++)
        if (br[i].source_id == b && br[i].target_id == a &&
            br[i].relation_type == (uint8_t)REL_SIMILAR_TO)
            return (float)br[i].strength / 255.0f;

    /* Shared ancestry */
    uint32_t pa = get_parent(core, a), pb = get_parent(core, b);
    if (pa != UINT32_MAX && pa == pb) return 0.7f;
    uint32_t gpa = get_parent(core, pa), gpb = get_parent(core, pb);
    if (gpa != UINT32_MAX && gpa == gpb) return 0.5f;

    /* Same category within 3 hops */
    uint32_t aa[3] = { pa, gpa, get_parent(core, gpa) };
    uint32_t ab[3] = { pb, gpb, get_parent(core, gpb) };
    for (int i = 0; i < 3; i++) {
        if (aa[i] == UINT32_MAX) continue;
        for (int j = 0; j < 3; j++)
            if (aa[i] == ab[j]) return 0.3f;
    }
    return 0.0f;
}

/* ─── Inheritance ────────────────────────────────────────────── */
int semantic_is_a(SemanticCore* core, uint32_t child, uint32_t parent) {
    if (!core->header || child >= core->header->concept_count ||
        parent >= core->header->concept_count) return 0;
    if (child == parent) return 1;
    uint32_t cur = child;
    for (int d = 0; d < INHERIT_DEPTH; d++) {
        uint32_t p = core->concepts[cur].parent_id;
        if (p == cur || p >= core->header->concept_count) return 0;
        if (p == parent) return 1;
        cur = p;
    }
    return 0;
}

int semantic_get_ancestors(SemanticCore* core, uint32_t id, uint32_t* ancestors, int max) {
    if (!core->header || !ancestors || max <= 0 || id >= core->header->concept_count) return 0;
    int count = 0;
    uint32_t cur = id;
    for (int d = 0; d < INHERIT_DEPTH && count < max; d++) {
        uint32_t p = core->concepts[cur].parent_id;
        if (p == cur || p >= core->header->concept_count) break;
        ancestors[count++] = p;
        cur = p;
    }
    return count;
}

/* ─── Synonyms ───────────────────────────────────────────────── */
int semantic_get_synonyms(SemanticCore* core, uint32_t id, uint32_t* syn_ids, int max) {
    if (!core->header || !syn_ids || max <= 0) return 0;
    int count = 0;
    for (uint32_t i = 0; i < core->header->synonym_count && count < max; i++)
        if (core->synonyms[i].concept_id == id)
            syn_ids[count++] = i;
    return count;
}

int semantic_find_by_synonym(SemanticCore* core, const char* word) {
    if (!core->header || !word) return -1;
    int id = semantic_find(core, word);
    if (id >= 0) return id;
    for (uint32_t i = 0; i < core->header->synonym_count; i++)
        if (strcmp(core->string_table + core->synonyms[i].synonym_offset, word) == 0)
            return (int)core->synonyms[i].concept_id;
    return -1;
}

/* ─── Fuzzy Matching ─────────────────────────────────────────── */
int semantic_find_fuzzy(SemanticCore* core, const char* name) {
    if (!core || !core->header || !name || !name[0]) return -1;

    /* 1. Exact match */
    int id = semantic_find(core, name);
    if (id >= 0) return id;

    /* 2. Try without trailing 's' (plural→singular) */
    size_t len = strlen(name);
    if (len > 1 && name[len - 1] == 's') {
        char singular[256];
        if (len - 1 < sizeof(singular)) {
            memcpy(singular, name, len - 1);
            singular[len - 1] = '\0';
            id = semantic_find(core, singular);
            if (id >= 0) return id;
        }
    }

    /* 3. Try lowercase normalized */
    char lower[256];
    size_t i;
    for (i = 0; i < len && i < sizeof(lower) - 1; i++)
        lower[i] = (name[i] >= 'A' && name[i] <= 'Z') ? name[i] + 32 : name[i];
    lower[i] = '\0';
    id = semantic_find(core, lower);
    if (id >= 0) return id;

    /* Also try lowercase + de-pluralized */
    size_t llen = strlen(lower);
    if (llen > 1 && lower[llen - 1] == 's') {
        lower[llen - 1] = '\0';
        id = semantic_find(core, lower);
        if (id >= 0) return id;
        lower[llen - 1] = 's'; /* restore */
    }

    /* 4. Substring match: scan all concepts for one whose name contains the query */
    for (uint32_t ci = 0; ci < core->header->concept_count; ci++) {
        const char* cname = core->string_table + core->concepts[ci].name_offset;
        if (strstr(cname, name) != NULL) return (int)ci;
    }
    /* Also try lowercase substring */
    for (uint32_t ci = 0; ci < core->header->concept_count; ci++) {
        const char* cname = core->string_table + core->concepts[ci].name_offset;
        /* case-insensitive substring: check if lower appears in cname (lowered) */
        const char *p = cname, *q = lower;
        while (*p) {
            const char *pp = p, *qq = q;
            while (*pp && *qq) {
                char cp = (*pp >= 'A' && *pp <= 'Z') ? *pp + 32 : *pp;
                if (cp != *qq) break;
                pp++; qq++;
            }
            if (!*qq) return (int)ci; /* full match of lower within cname */
            p++;
        }
    }

    return -1;
}

/* ─── Index Building ─────────────────────────────────────────── */
int semantic_build_index(SemanticCore* core) {
    if (!core->header || core->header->concept_count == 0) {
        core->name_index = NULL;
        core->index_size = 0;
        return 0;
    }
    uint32_t n = core->header->concept_count;
    core->name_index = malloc(n * sizeof(uint32_t));
    if (!core->name_index) return -1;
    for (uint32_t i = 0; i < n; i++) core->name_index[i] = i;
    g_sort_core = core;
    qsort(core->name_index, n, sizeof(uint32_t), name_compare);
    g_sort_core = NULL;
    core->index_size = n;
    return 0;
}

/* ─── TEST MODE ──────────────────────────────────────────────── */
#ifdef TEST_MODE
#include <assert.h>

static void test_empty_core(void) {
    SemanticCore core;
    assert(semantic_init(&core, "/nonexistent/path/x.bin") == 0);
    assert(core.header == NULL && core.name_index == NULL);
    assert(semantic_find(&core, "anything") == -1);
    assert(semantic_get_name(&core, 0) == NULL);
    assert(semantic_get_concept(&core, 0) == NULL);
    assert(semantic_get_property(&core, 0, "key") == NULL);
    assert(semantic_similarity(&core, 0, 1) == 0.0f);
    assert(semantic_is_a(&core, 0, 1) == 0);
    assert(semantic_find_by_synonym(&core, "word") == -1);
    uint32_t buf[4]; PropertyRecord props[4];
    assert(semantic_get_relations(&core, 0, REL_IS_A, buf, 4) == 0);
    assert(semantic_get_ancestors(&core, 0, buf, 4) == 0);
    assert(semantic_get_synonyms(&core, 0, buf, 4) == 0);
    assert(semantic_are_related(&core, 0, 1, REL_IS_A) == 0);
    assert(semantic_get_all_properties(&core, 0, props, 4) == 0);
    semantic_destroy(&core);
    printf("[PASS] test_empty_core\n");
}

static void test_manual_concepts(void) {
    /* Concepts: "animal"(0), "dog"(1), "cat"(2)
     * dog→parent=animal, cat→parent=animal
     * Properties: animal:"alive"="yes", dog:"sound"="bark"
     * Relations: dog SIMILAR_TO cat (strength 200)
     * Synonyms: "canine" → dog */
    static char strings[] = "animal\0dog\0cat\0alive\0yes\0sound\0bark\0canine\0";
    /* offsets: animal=0 dog=7 cat=11 alive=15 yes=21 sound=25 bark=31 canine=36 */

    static ConceptRecord concepts[3] = {
        { 0, 0, 0, 1, CFLAG_ABSTRACT|CFLAG_CATEGORY, 0, 0, 0 },
        { 7, 0, 1, 1, CFLAG_CONCRETE, 0, 1, 1 },
        { 11, 0, 2, 0, CFLAG_CONCRETE, 1, 1, 1 },
    };
    static PropertyRecord props[3] = {
        { 15, 21, 65535, 0 }, { 25, 31, 65535, 0 }, { 15, 21, 65535, 0 },
    };
    static RelationRecord rels[2] = {
        { 1, 2, REL_SIMILAR_TO, 200, 65535 }, { 2, 1, REL_SIMILAR_TO, 200, 65535 },
    };
    static SynonymRecord syns[1] = { { 1, 36 } };
    static ConceptFileHeader hdr = {
        .magic = CONCEPT_MAGIC, .version = CONCEPT_VERSION,
        .concept_count = 3, .relation_count = 2, .synonym_count = 1,
        .string_table_size = sizeof(strings), .property_table_size = 3,
    };

    SemanticCore core;
    memset(&core, 0, sizeof(core));
    core.header = &hdr; core.string_table = strings;
    core.concepts = concepts; core.properties = props;
    core.relations = rels; core.synonyms = syns;
    assert(semantic_build_index(&core) == 0 && core.index_size == 3);

    /* Lookup */
    assert(semantic_find(&core, "animal") == 0);
    assert(semantic_find(&core, "dog") == 1);
    assert(semantic_find(&core, "cat") == 2);
    assert(semantic_find(&core, "fish") == -1);
    assert(strcmp(semantic_get_name(&core, 0), "animal") == 0);
    assert(semantic_get_concept(&core, 0) != NULL);
    assert(semantic_get_concept(&core, 99) == NULL);

    /* Property with inheritance */
    assert(strcmp(semantic_get_property(&core, 1, "sound"), "bark") == 0);
    assert(strcmp(semantic_get_property(&core, 1, "alive"), "yes") == 0); /* inherited */
    assert(semantic_get_property(&core, 1, "nonexist") == NULL);
    PropertyRecord out_props[8];
    assert(semantic_get_all_properties(&core, 1, out_props, 8) == 2);

    /* Relations */
    uint32_t targets[4];
    assert(semantic_get_relations(&core, 1, REL_SIMILAR_TO, targets, 4) == 1);
    assert(targets[0] == 2);
    assert(semantic_are_related(&core, 1, 2, REL_SIMILAR_TO) == 1);
    assert(semantic_are_related(&core, 1, 2, REL_IS_A) == 0);

    /* Similarity */
    assert(semantic_similarity(&core, 1, 1) == 1.0f);
    float sim = semantic_similarity(&core, 1, 2);
    assert(sim > 0.78f && sim < 0.79f); /* 200/255 */

    /* Inheritance */
    assert(semantic_is_a(&core, 1, 0) == 1);
    assert(semantic_is_a(&core, 2, 0) == 1);
    assert(semantic_is_a(&core, 0, 1) == 0);
    uint32_t ancestors[4];
    assert(semantic_get_ancestors(&core, 1, ancestors, 4) == 1 && ancestors[0] == 0);

    /* Synonyms */
    uint32_t syn_buf[4];
    assert(semantic_get_synonyms(&core, 1, syn_buf, 4) == 1);
    assert(semantic_find_by_synonym(&core, "dog") == 1);
    assert(semantic_find_by_synonym(&core, "canine") == 1);
    assert(semantic_find_by_synonym(&core, "unknown") == -1);

    free(core.name_index);
    printf("[PASS] test_manual_concepts\n");
}

int main(void) {
    printf("=== Semantic Concept Engine Tests ===\n");
    test_empty_core();
    test_manual_concepts();
    printf("=== ALL TESTS PASSED ===\n");
    return 0;
}
#endif /* TEST_MODE */

#ifndef CONCEPT_H
#define CONCEPT_H

#include <stdint.h>
#include <stddef.h>

/*
 * SEMANTIC CORE — Concept Graph Format
 * 
 * Storage: 300MB disk max, 300MB RAM max
 * Design: mmap'd binary file, inheritance-based compression
 * Target: 10M concepts, 50M relations
 *
 * On-disk format:
 *   HEADER (64 bytes)
 *   STRING_TABLE (variable)
 *   CONCEPT_TABLE (fixed records)
 *   PROPERTY_TABLE (variable)
 *   RELATION_TABLE (fixed records)
 *   SYNONYM_TABLE (fixed records)
 */

#define CONCEPT_MAGIC    0x48414953  /* "SIAH" - Semantic Intelligence AI Hybrid */
#define CONCEPT_VERSION  1
#define MAX_PROPERTIES   16         /* Max unique properties per concept */
#define MAX_RELATIONS    32         /* Max relations per concept */
#define MAX_SYNONYMS     8          /* Max synonyms per concept */
#define INHERIT_DEPTH    10         /* Max inheritance chain depth */

/* ─── Relation Types ─────────────────────────────────────────── */
typedef enum {
    REL_IS_A = 0,          /* dog IS_A animal */
    REL_HAS,               /* dog HAS fur */
    REL_PART_OF,           /* wheel PART_OF car */
    REL_SIMILAR_TO,        /* dog SIMILAR_TO wolf */
    REL_OPPOSITE_OF,       /* hot OPPOSITE_OF cold */
    REL_CAUSES,            /* fire CAUSES burn */
    REL_CAUSED_BY,         /* burn CAUSED_BY fire */
    REL_LOCATED_IN,        /* paris LOCATED_IN france */
    REL_CONTAINS,          /* france CONTAINS paris */
    REL_USED_FOR,          /* knife USED_FOR cutting */
    REL_MADE_OF,           /* table MADE_OF wood */
    REL_CAPABLE_OF,        /* bird CAPABLE_OF flying */
    REL_DESIRES,           /* human DESIRES happiness */
    REL_CREATED_BY,        /* linux CREATED_BY torvalds */
    REL_INSTANCE_OF,       /* paris INSTANCE_OF city */
    REL_SYNONYM,           /* big SYNONYM large */
    REL_ANTONYM,           /* big ANTONYM small */
    REL_DERIVED_FROM,      /* happiness DERIVED_FROM happy */
    REL_TEMPORAL_BEFORE,   /* seed TEMPORAL_BEFORE plant */
    REL_TEMPORAL_AFTER,    /* plant TEMPORAL_AFTER seed */
    REL_STRONGER_THAN,     /* excellent STRONGER_THAN good */
    REL_WEAKER_THAN,       /* okay WEAKER_THAN good */
    REL_CUSTOM = 255       /* User-defined */
} RelationType;

/* ─── Concept Flags ──────────────────────────────────────────── */
typedef enum {
    CFLAG_ABSTRACT   = 1 << 0,  /* Can't be instantiated (e.g., "thing") */
    CFLAG_CONCRETE   = 1 << 1,  /* Physical object */
    CFLAG_ACTION     = 1 << 2,  /* Verb/action concept */
    CFLAG_PROPERTY   = 1 << 3,  /* Adjective/property */
    CFLAG_ENTITY     = 1 << 4,  /* Named entity (person, place) */
    CFLAG_CATEGORY   = 1 << 5,  /* Category node (has children) */
    CFLAG_QUANTITY   = 1 << 6,  /* Number/measurement */
    CFLAG_TEMPORAL   = 1 << 7,  /* Time-related */
} ConceptFlags;

/* ─── On-Disk Structures ─────────────────────────────────────── */

typedef struct {
    uint32_t magic;
    uint32_t version;
    uint32_t concept_count;
    uint32_t relation_count;
    uint32_t synonym_count;
    uint32_t string_table_size;    /* bytes */
    uint32_t property_table_size;  /* entries */
    uint64_t string_table_offset;
    uint64_t concept_table_offset;
    uint64_t property_table_offset;
    uint64_t relation_table_offset;
    uint64_t synonym_table_offset;
    uint32_t checksum;
    uint32_t reserved;
} ConceptFileHeader;  /* 64 bytes */

typedef struct {
    uint32_t name_offset;       /* → string table */
    uint32_t parent_id;         /* → parent concept (IS_A, for inheritance) */
    uint32_t first_property;    /* → index into property table */
    uint16_t property_count;    /* unique properties (not inherited) */
    uint16_t flags;             /* ConceptFlags */
    uint32_t first_relation;    /* → index into relation table */
    uint16_t relation_count;
    uint16_t depth;             /* depth in hierarchy (root=0) */
} ConceptRecord;  /* 24 bytes × 10M = 240MB max */

typedef struct {
    uint32_t key_offset;        /* → string table: property name */
    uint32_t value_offset;      /* → string table: property value */
    uint16_t confidence;        /* 0-65535 */
    uint16_t source;            /* 0=builtin, 1=extracted, 2=user */
} PropertyRecord;  /* 12 bytes */

typedef struct {
    uint32_t source_id;         /* concept A */
    uint32_t target_id;         /* concept B */
    uint8_t  relation_type;     /* RelationType enum */
    uint8_t  strength;          /* 0-255 (how strong the relation) */
    uint16_t confidence;        /* 0-65535 */
} RelationRecord;  /* 12 bytes × 50M = 600MB... too big for 300MB */
/* Solution: compress with delta encoding, only store top relations per concept */

typedef struct {
    uint32_t concept_id;        /* which concept */
    uint32_t synonym_offset;    /* → string table */
} SynonymRecord;  /* 8 bytes */

/* ─── In-Memory Runtime Structures ───────────────────────────── */

typedef struct {
    /* File mapping */
    void* mapped_file;          /* mmap'd data */
    size_t file_size;
    
    /* Parsed pointers into mmap'd region */
    ConceptFileHeader* header;
    char* string_table;
    ConceptRecord* concepts;
    PropertyRecord* properties;
    RelationRecord* relations;
    SynonymRecord* synonyms;
    
    /* Runtime index (built on load, lives in RAM) */
    uint32_t* name_index;       /* sorted concept names for binary search */
    uint32_t index_size;
    
    /* Stats */
    uint32_t lookups;
    uint32_t cache_hits;
} SemanticCore;

/* ─── API ────────────────────────────────────────────────────── */

/* Lifecycle */
int semantic_init(SemanticCore* core, const char* filepath);
void semantic_destroy(SemanticCore* core);

/* Lookup */
int semantic_find(SemanticCore* core, const char* name);  /* Returns concept_id or -1 */
const char* semantic_get_name(SemanticCore* core, uint32_t id);
ConceptRecord* semantic_get_concept(SemanticCore* core, uint32_t id);

/* Properties (with inheritance!) */
const char* semantic_get_property(SemanticCore* core, uint32_t id, const char* key);
int semantic_get_all_properties(SemanticCore* core, uint32_t id, 
                                 PropertyRecord* out, int max_out);  /* includes inherited */

/* Relations */
int semantic_get_relations(SemanticCore* core, uint32_t id, 
                           RelationType type, uint32_t* targets, int max_targets);
int semantic_are_related(SemanticCore* core, uint32_t a, uint32_t b, RelationType type);

/* Semantic similarity (graph distance based) */
float semantic_similarity(SemanticCore* core, uint32_t a, uint32_t b);

/* Inheritance */
int semantic_is_a(SemanticCore* core, uint32_t child, uint32_t parent);
int semantic_get_ancestors(SemanticCore* core, uint32_t id, uint32_t* ancestors, int max);

/* Synonyms */
int semantic_get_synonyms(SemanticCore* core, uint32_t id, uint32_t* syn_ids, int max);
int semantic_find_by_synonym(SemanticCore* core, const char* word);  /* find concept even if synonym used */
int semantic_find_fuzzy(SemanticCore* core, const char* name);  /* fuzzy: plural, lowercase, substring */

/* Building (for the compiler) */
int semantic_build_index(SemanticCore* core);  /* Build name_index from loaded data */

#endif /* CONCEPT_H */

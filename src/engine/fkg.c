/*
 * fkg.c — Fractal Knowledge Graph
 * Same concept at 4 zoom levels: child → student → detailed → expert.
 * Adapts explanation depth to user's comprehension level.
 */

#include <string.h>
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <ctype.h>
#include <strings.h>

#define FKG_MAX_LEVELS   4
#define FKG_MAX_TEXT     512
#define FKG_MAX_ENTRIES  10000

/* Zoom levels */
typedef enum {
    FKG_CHILD   = 0,   /* Age 6-10: simple, concrete */
    FKG_STUDENT = 1,   /* Age 11-16: factual, clear */
    FKG_DETAIL  = 2,   /* Adult: comprehensive */
    FKG_EXPERT  = 3,   /* Specialist: technical, precise */
} FKGLevel;

/* A fractal entry: one concept, multiple zoom levels */
typedef struct {
    uint32_t concept_id;
    char     concept_name[64];
    char     text[FKG_MAX_LEVELS][FKG_MAX_TEXT];  /* Different explanation per level */
    uint8_t  levels_filled;  /* Bitmask: which levels have content */
} FKGEntry;

/* User profile for level detection */
typedef struct {
    FKGLevel detected_level;
    uint32_t technical_words_used;   /* Count of technical terms in user's messages */
    uint32_t simple_words_used;
    uint32_t questions_asked;
    uint32_t explicit_level;         /* 0=auto, 1-4=forced by user */
} FKGUserProfile;

/* The fractal knowledge graph */
typedef struct {
    FKGEntry *entries;
    uint32_t  count;
    uint32_t  capacity;
    FKGUserProfile user;
} FKGEngine;

/* ─── Technical word detection ─── */

static const char *TECHNICAL_WORDS[] = {
    "molecular", "quantum", "thermodynamic", "coefficient", "algorithm",
    "polymorphism", "nucleotide", "electromagnetic", "stoichiometry",
    "isomorphic", "eigenvalue", "derivative", "integral", "tensor",
    "entropy", "enthalpy", "catalysis", "ionization", "photon",
    "mitochondria", "ribosome", "genome", "allele", "phenotype",
    "asymptotic", "heuristic", "recursion", "abstraction", "paradigm",
    "topology", "manifold", "morphism", "functor", "cardinality",
    NULL
};

static const char *SIMPLE_MARKERS[] = {
    "explain like", "simple", "easy", "basic", "for kids",
    "what does that mean", "i don't understand", "confused",
    "too complicated", "simpler please", "eli5",
    NULL
};

static const char *EXPERT_MARKERS[] = {
    "specifically", "technically", "in detail", "mechanism",
    "at the molecular level", "quantitatively", "derivation",
    "formally", "rigorously", "be precise", "more detail",
    NULL
};

/* ─── API ─── */

static int fkg_init(FKGEngine *fkg, uint32_t capacity) {
    memset(fkg, 0, sizeof(*fkg));
    fkg->capacity = capacity;
    fkg->entries = calloc(capacity, sizeof(FKGEntry));
    fkg->user.detected_level = FKG_STUDENT;  /* Default */
    return fkg->entries ? 0 : -1;
}

static void fkg_free(FKGEngine *fkg) {
    free(fkg->entries);
    memset(fkg, 0, sizeof(*fkg));
}

/* Add a fractal entry: concept with explanations at different levels */
static int fkg_add(FKGEngine *fkg, uint32_t concept_id, const char *name,
                   const char *child_text, const char *student_text,
                   const char *detail_text, const char *expert_text) {
    if (fkg->count >= fkg->capacity) return -1;

    FKGEntry *entry = &fkg->entries[fkg->count];
    entry->concept_id = concept_id;
    strncpy(entry->concept_name, name, 63);

    if (child_text && child_text[0]) {
        strncpy(entry->text[FKG_CHILD], child_text, FKG_MAX_TEXT - 1);
        entry->levels_filled |= (1 << FKG_CHILD);
    }
    if (student_text && student_text[0]) {
        strncpy(entry->text[FKG_STUDENT], student_text, FKG_MAX_TEXT - 1);
        entry->levels_filled |= (1 << FKG_STUDENT);
    }
    if (detail_text && detail_text[0]) {
        strncpy(entry->text[FKG_DETAIL], detail_text, FKG_MAX_TEXT - 1);
        entry->levels_filled |= (1 << FKG_DETAIL);
    }
    if (expert_text && expert_text[0]) {
        strncpy(entry->text[FKG_EXPERT], expert_text, FKG_MAX_TEXT - 1);
        entry->levels_filled |= (1 << FKG_EXPERT);
    }

    fkg->count++;
    return 0;
}

/* Detect user's level from their message */
static FKGLevel fkg_detect_level(FKGEngine *fkg, const char *user_message) {
    /* Check explicit markers first */
    const char *msg_lower = user_message;  /* Assume pre-lowered or check inline */

    for (int i = 0; SIMPLE_MARKERS[i]; i++) {
        if (strstr(user_message, SIMPLE_MARKERS[i])) {
            fkg->user.detected_level = FKG_CHILD;
            return FKG_CHILD;
        }
    }
    for (int i = 0; EXPERT_MARKERS[i]; i++) {
        if (strstr(user_message, EXPERT_MARKERS[i])) {
            fkg->user.detected_level = FKG_EXPERT;
            return FKG_EXPERT;
        }
    }

    /* Count technical words */
    int tech_count = 0;
    for (int i = 0; TECHNICAL_WORDS[i]; i++) {
        if (strstr(user_message, TECHNICAL_WORDS[i])) tech_count++;
    }
    fkg->user.technical_words_used += tech_count;
    fkg->user.questions_asked++;

    /* Determine level from accumulated evidence */
    float tech_ratio = (float)fkg->user.technical_words_used / (fkg->user.questions_asked + 1);

    FKGLevel level;
    if (tech_ratio > 2.0f) level = FKG_EXPERT;
    else if (tech_ratio > 0.8f) level = FKG_DETAIL;
    else if (tech_ratio > 0.2f) level = FKG_STUDENT;
    else level = FKG_CHILD;

    /* Allow forced level override */
    if (fkg->user.explicit_level > 0) {
        level = (FKGLevel)(fkg->user.explicit_level - 1);
    }

    fkg->user.detected_level = level;
    return level;
}

/* Query: get explanation at appropriate level */
static const char* fkg_query(FKGEngine *fkg, const char *concept_name, FKGLevel level) {
    for (uint32_t i = 0; i < fkg->count; i++) {
        if (strcasecmp(fkg->entries[i].concept_name, concept_name) == 0) {
            FKGEntry *e = &fkg->entries[i];
            /* Try requested level, fallback to nearest available */
            if (e->levels_filled & (1 << level)) {
                return e->text[level];
            }
            /* Fallback: try lower levels first, then higher */
            for (int l = level; l >= 0; l--) {
                if (e->levels_filled & (1 << l)) return e->text[l];
            }
            for (int l = level; l < FKG_MAX_LEVELS; l++) {
                if (e->levels_filled & (1 << l)) return e->text[l];
            }
        }
    }
    return NULL;  /* Concept not in FKG */
}

/* Auto-generate simpler levels from expert text */
static void fkg_auto_simplify(FKGEngine *fkg, uint32_t entry_idx) {
    if (entry_idx >= fkg->count) return;
    FKGEntry *e = &fkg->entries[entry_idx];

    /* If only expert/detail level filled, generate simpler versions */
    const char *source = NULL;
    if (e->text[FKG_EXPERT][0]) source = e->text[FKG_EXPERT];
    else if (e->text[FKG_DETAIL][0]) source = e->text[FKG_DETAIL];
    if (!source) return;

    /* Student level: first 2 sentences */
    if (!(e->levels_filled & (1 << FKG_STUDENT))) {
        const char *end = source;
        int sentences = 0;
        while (*end && sentences < 2) {
            if (*end == '.' || *end == '!' || *end == '?') sentences++;
            end++;
        }
        int len = (int)(end - source);
        if (len > 10 && len < FKG_MAX_TEXT) {
            strncpy(e->text[FKG_STUDENT], source, len);
            e->text[FKG_STUDENT][len] = '\0';
            e->levels_filled |= (1 << FKG_STUDENT);
        }
    }

    /* Child level: first sentence only, simplified */
    if (!(e->levels_filled & (1 << FKG_CHILD))) {
        const char *end = source;
        while (*end && *end != '.' && *end != '!' && *end != '?') end++;
        int len = (int)(end - source);
        if (len > 5 && len < FKG_MAX_TEXT) {
            strncpy(e->text[FKG_CHILD], source, len);
            e->text[FKG_CHILD][len] = '.';
            e->text[FKG_CHILD][len+1] = '\0';
            e->levels_filled |= (1 << FKG_CHILD);
        }
    }
}

/* Set explicit user level (from "/level 1" command) */
static void fkg_set_user_level(FKGEngine *fkg, int level) {
    if (level >= 0 && level <= 4) {
        fkg->user.explicit_level = (uint32_t)level;  /* 0=auto */
    }
}


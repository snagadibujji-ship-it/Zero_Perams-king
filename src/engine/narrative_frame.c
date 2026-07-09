/*
 * narrative_frame.c - Narrative Framing Engine
 * Generates compelling openings and closings for concept explanations.
 * Inspired by quality_maximizer.py (reasoning traces) and
 * deep_message_corpus.py (rich, varied message patterns).
 */
#include "narrative_frame.h"
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <time.h>

/* ─── Helpers ─── */

static const char* article_for(const char* word) {
    if (!word || !word[0]) return "a";
    if (strncmp(word, "uni", 3) == 0 || strncmp(word, "eu", 2) == 0) return "a";
    return (word[0]=='a'||word[0]=='e'||word[0]=='i'||word[0]=='o'||word[0]=='u') ? "an" : "a";
}

static void capitalize_buf(char* s) {
    if (s[0] >= 'a' && s[0] <= 'z') s[0] -= 32;
}

static unsigned int simple_hash(int concept_id, int salt) {
    unsigned int h = (unsigned int)concept_id * 2654435761u + (unsigned int)salt;
    return h;
}

static int pick_variant(int concept_id, int n_options) {
    if (n_options <= 0) return 0;
    return (int)(simple_hash(concept_id, 42) % (unsigned int)n_options);
}

/* Check if a property value is "interesting" (superlative, numeric, temporal) */
static int is_interesting_property(const char* key, const char* value) {
    if (!key || !value) return 0;
    /* created_by relations are always interesting */
    if (strstr(key, "created") || strstr(key, "inventor")) return 2;
    /* numeric values are interesting */
    for (int i = 0; value[i]; i++) {
        if (value[i] >= '0' && value[i] <= '9') return 2;
    }
    /* superlatives / extremes */
    if (strstr(value, "most") || strstr(value, "largest") || strstr(value, "smallest") ||
        strstr(value, "oldest") || strstr(value, "fastest") || strstr(value, "first")) return 2;
    /* temporal markers */
    if (strstr(key, "year") || strstr(key, "date") || strstr(key, "era")) return 1;
    return 0;
}

/* ─── frame_familiarity ─── */

int frame_familiarity(SemanticCore* core, int concept_id) {
    if (!core || concept_id < 0) return 5;

    ConceptRecord* concept = semantic_get_concept(core, (uint32_t)concept_id);
    if (!concept) return 5;

    int rel_count = concept->relation_count;
    int prop_count = concept->property_count;
    int total = rel_count + prop_count;

    if (rel_count >= 5 || total >= 8) return 1;  /* very familiar */
    if (rel_count >= 3 || total >= 5) return 2;  /* somewhat known */
    if (rel_count >= 1 || total >= 2) return 3;  /* less known */
    if (prop_count >= 1)              return 4;  /* obscure but has something */
    return 5;                                     /* unknown */
}

/* ─── frame_opening ─── */

int frame_opening(SemanticCore* core, int concept_id, char* out, int maxlen) {
    if (!core || concept_id < 0 || !out || maxlen < 2) return -1;
    out[0] = '\0';

    const char* name = semantic_get_name(core, (uint32_t)concept_id);
    if (!name) return -1;

    ConceptRecord* concept = semantic_get_concept(core, (uint32_t)concept_id);
    if (!concept) return -1;

    /* Get parent name */
    const char* parent = NULL;
    if (concept->parent_id > 0) {
        parent = semantic_get_name(core, concept->parent_id);
    }
    if (!parent) parent = "concept";

    /* Get an interesting property for color */
    PropertyRecord props[MAX_PROPERTIES];
    int nprops = semantic_get_all_properties(core, (uint32_t)concept_id, props, MAX_PROPERTIES);

    const char* interesting_val = NULL;
    int best_score = 0;
    for (int i = 0; i < nprops; i++) {
        const char* k = core->string_table + props[i].key_offset;
        const char* v = core->string_table + props[i].value_offset;
        int score = is_interesting_property(k, v);
        if (score > best_score) {
            best_score = score;
            interesting_val = v;
        }
    }

    /* Check for created_by relation (always interesting for openings) */
    uint32_t created_targets[4];
    int created_count = semantic_get_relations(core, (uint32_t)concept_id,
                                               REL_CREATED_BY, created_targets, 4);
    const char* creator = NULL;
    if (created_count > 0) {
        creator = semantic_get_name(core, created_targets[0]);
    }

    int familiarity = frame_familiarity(core, concept_id);
    char namecap[128];
    strncpy(namecap, name, sizeof(namecap) - 1);
    namecap[sizeof(namecap) - 1] = '\0';
    capitalize_buf(namecap);

    const char* art = article_for(parent);
    int variant = pick_variant(concept_id, 3);

    if (familiarity <= 1) {
        /* FAMILIAR: rich, confident openings */
        static const char* familiar_adj[] = {"well-known", "common", "familiar", "widely recognized"};
        const char* adj = familiar_adj[pick_variant(concept_id, 4)];

        if (variant == 0) {
            snprintf(out, maxlen, "%s is one of the most %s types of %s.",
                     namecap, adj, parent);
        } else if (variant == 1 && (interesting_val || creator)) {
            if (creator) {
                snprintf(out, maxlen, "%s \u2014 %s %s created by %s.",
                         namecap, art, parent, creator);
            } else {
                snprintf(out, maxlen, "%s \u2014 %s %s that %s.",
                         namecap, art, parent, interesting_val ? interesting_val : "is remarkable");
            }
        } else {
            snprintf(out, maxlen, "Most people are familiar with %s, %s %s.",
                     name, art, parent);
        }
    } else if (familiarity <= 3) {
        /* LESS FAMILIAR: informative, grounding openings */
        if (variant == 0 && interesting_val) {
            snprintf(out, maxlen, "%s is %s %s that %s.",
                     namecap, art, parent, interesting_val);
        } else if (variant == 1) {
            char artcap[8];
            strncpy(artcap, art, sizeof(artcap) - 1);
            artcap[sizeof(artcap) - 1] = '\0';
            capitalize_buf(artcap);
            if (interesting_val) {
                snprintf(out, maxlen, "%s %s, %s is %s.",
                         artcap, parent, name, interesting_val);
            } else {
                snprintf(out, maxlen, "%s is %s %s.", namecap, art, parent);
            }
        } else {
            if (creator) {
                snprintf(out, maxlen, "%s is %s %s created by %s.",
                         namecap, art, parent, creator);
            } else {
                snprintf(out, maxlen, "%s is %s %s.", namecap, art, parent);
            }
        }
    } else {
        /* UNKNOWN/THIN: simple, don't overframe */
        snprintf(out, maxlen, "%s is %s %s.", namecap, art, parent);
    }

    return (int)strlen(out);
}

/* ─── frame_closing ─── */

int frame_closing(SemanticCore* core, int concept_id, int sections_used, char* out, int maxlen) {
    if (!core || concept_id < 0 || !out || maxlen < 2) return -1;
    out[0] = '\0';

    /* No closing for short answers */
    if (sections_used <= 2) return 0;

    const char* name = semantic_get_name(core, (uint32_t)concept_id);
    if (!name) return -1;

    ConceptRecord* concept = semantic_get_concept(core, (uint32_t)concept_id);
    if (!concept) return -1;

    const char* parent = NULL;
    if (concept->parent_id > 0) {
        parent = semantic_get_name(core, concept->parent_id);
    }
    if (!parent) parent = "concept";

    char namecap[128];
    strncpy(namecap, name, sizeof(namecap) - 1);
    namecap[sizeof(namecap) - 1] = '\0';
    capitalize_buf(namecap);

    int variant = pick_variant(concept_id, 4);

    if (sections_used >= 5) {
        /* Rich closing for detailed answers */
        static const char* adj[] = {"fascinating", "remarkable", "versatile", "notable"};
        static const char* tail[] = {
            "many distinctive features", "a wide range of characteristics",
            "numerous noteworthy aspects", "much to explore"
        };
        snprintf(out, maxlen, "Overall, %s is a %s %s with %s.",
                 name, adj[variant], parent, tail[variant]);
    } else {
        /* Moderate closing (3-4 sections) — find context via relations */
        uint32_t ctx_targets[4];
        const char* context = NULL;
        int n = semantic_get_relations(core, (uint32_t)concept_id, REL_LOCATED_IN, ctx_targets, 4);
        if (n > 0) context = semantic_get_name(core, ctx_targets[0]);
        if (!context) {
            n = semantic_get_relations(core, (uint32_t)concept_id, REL_PART_OF, ctx_targets, 4);
            if (n > 0) context = semantic_get_name(core, ctx_targets[0]);
        }

        if (context) {
            switch (variant) {
            case 0: snprintf(out, maxlen, "%s remains an important %s in %s.", namecap, parent, context); break;
            case 1: snprintf(out, maxlen, "%s continues to be a significant %s in %s.", namecap, parent, context); break;
            case 2: snprintf(out, maxlen, "%s plays a notable role as %s %s in %s.", namecap, article_for(parent), parent, context); break;
            default: snprintf(out, maxlen, "In %s, %s stands out as %s %s.", context, name, article_for(parent), parent); break;
            }
        } else {
            switch (variant) {
            case 0: snprintf(out, maxlen, "%s remains an important %s.", namecap, parent); break;
            case 1: snprintf(out, maxlen, "%s is a noteworthy %s worth understanding.", namecap, parent); break;
            case 2: snprintf(out, maxlen, "%s stands as a significant %s.", namecap, parent); break;
            default: snprintf(out, maxlen, "In summary, %s is %s %s of note.", name, article_for(parent), parent); break;
            }
        }
    }

    return (int)strlen(out);
}

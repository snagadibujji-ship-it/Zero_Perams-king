/*
 * discourse.c - Turn multi-fact responses into flowing paragraphs.
 * Inspired by story_engine.py (cause-effect chains) and
 * communication_realism.py (natural flow).
 */

#include "discourse.h"
#include <stdlib.h>
#include <string.h>
#include <stdio.h>

/* ---------- Transition arrays (30+ total) ---------- */

static const char* trans_def_to_property[] = {
    "In terms of characteristics, ",
    "Notably, ",
    "What makes it distinctive is that ",
    "Characteristically, "
};
#define N_DEF_PROP 4

static const char* trans_def_to_physical[] = {
    "Physically, ",
    "In appearance, ",
    "Looking at its features, ",
    "Visually, "
};
#define N_DEF_PHYS 4

static const char* trans_prop_to_capability[] = {
    "This allows it to ",
    "As a result, it can ",
    "These traits enable it to ",
    "Consequently, it is able to "
};
#define N_PROP_CAP 4

static const char* trans_phys_to_capability[] = {
    "With these features, ",
    "These physical traits allow it to ",
    "Thanks to its form, ",
    "This anatomy enables it to "
};
#define N_PHYS_CAP 4

static const char* trans_any_to_purpose[] = {
    "It is primarily used for ",
    "Its main purpose is ",
    "People use it for ",
    "In practice, it serves to ",
    "Its chief function is "
};
#define N_ANY_PURP 5

static const char* trans_any_to_composition[] = {
    "It is composed of ",
    "In terms of composition, ",
    "Structurally, it consists of ",
    "Its makeup includes "
};
#define N_ANY_COMP 4

static const char* trans_any_to_cause[] = {
    "One important effect is that ",
    "Significantly, ",
    "As a consequence, ",
    "This leads to "
};
#define N_ANY_CAUSE 4

static const char* trans_any_to_location[] = {
    "It can be found in ",
    "Geographically, ",
    "In terms of habitat, ",
    "It is typically located in "
};
#define N_ANY_LOC 4

static const char* trans_any_to_history[] = {
    "Historically, ",
    "In terms of origin, ",
    "Its history shows that ",
    "Dating back, "
};
#define N_ANY_HIST 4

static const char* trans_any_to_comparison[] = {
    "Compared to others, ",
    "In contrast, ",
    "Relative to similar things, ",
    "Unlike its counterparts, "
};
#define N_ANY_COMP2 4

/* Generic fallback transitions */
static const char* trans_generic[] = {
    "Additionally, ",
    "Furthermore, ",
    "Moreover, ",
    "Also, "
};
#define N_GENERIC 4

/* ---------- Section openers ---------- */

static const char* opener_definition[] = { "", "Fundamentally, ", "At its core, ", "By definition, " };
#define N_OPEN_DEF 4

static const char* opener_property[] = { "Characteristically, ", "Notably, ", "In terms of traits, ", "" };
#define N_OPEN_PROP 4

static const char* opener_physical[] = { "Physically, ", "In terms of physical features, ", "Visually, ", "" };
#define N_OPEN_PHYS 4

static const char* opener_capability[] = { "Remarkably, ", "In terms of abilities, ", "Impressively, ", "" };
#define N_OPEN_CAP 4

static const char* opener_purpose[] = { "Its primary use is ", "Practically speaking, ", "Functionally, ", "" };
#define N_OPEN_PURP 4

static const char* opener_composition[] = { "Structurally, ", "In composition, ", "", "" };
#define N_OPEN_COMP 4

static const char* opener_location[] = { "Geographically, ", "In terms of location, ", "", "" };
#define N_OPEN_LOC 4

static const char* opener_cause[] = { "Importantly, ", "Significantly, ", "", "" };
#define N_OPEN_CAUSE 4

static const char* opener_history[] = { "Historically, ", "Looking at its origins, ", "", "" };
#define N_OPEN_HIST 4

static const char* opener_comparison[] = { "By comparison, ", "Relative to others, ", "", "" };
#define N_OPEN_CMP 4

/* ---------- Closings ---------- */

static const char* closing_medium_adj[] = { "interesting", "notable", "remarkable" };
#define N_CLOSE_MED 3

static const char* closing_many_adj[] = { "versatile", "complex", "fascinating" };
#define N_CLOSE_MANY 3

/* ---------- Helper: pick random avoiding last ---------- */

static int pick_variant(int count, int *last_used) {
    int choice;
    if (count <= 1) return 0;
    do {
        choice = rand() % count;
    } while (choice == *last_used && count > 1);
    *last_used = choice;
    return choice;
}

/* ---------- Public API ---------- */

const char* discourse_transition(SectionType from, SectionType to) {
    static int last = -1;
    const char** arr;
    int n;

    /* Select array based on from→to pair */
    if (from == SEC_DEFINITION && to == SEC_PROPERTY) {
        arr = trans_def_to_property; n = N_DEF_PROP;
    } else if (from == SEC_DEFINITION && to == SEC_PHYSICAL) {
        arr = trans_def_to_physical; n = N_DEF_PHYS;
    } else if (from == SEC_PROPERTY && to == SEC_CAPABILITY) {
        arr = trans_prop_to_capability; n = N_PROP_CAP;
    } else if (from == SEC_PHYSICAL && to == SEC_CAPABILITY) {
        arr = trans_phys_to_capability; n = N_PHYS_CAP;
    } else if (to == SEC_PURPOSE) {
        arr = trans_any_to_purpose; n = N_ANY_PURP;
    } else if (to == SEC_COMPOSITION) {
        arr = trans_any_to_composition; n = N_ANY_COMP;
    } else if (to == SEC_CAUSE) {
        arr = trans_any_to_cause; n = N_ANY_CAUSE;
    } else if (to == SEC_LOCATION) {
        arr = trans_any_to_location; n = N_ANY_LOC;
    } else if (to == SEC_HISTORY) {
        arr = trans_any_to_history; n = N_ANY_HIST;
    } else if (to == SEC_COMPARISON) {
        arr = trans_any_to_comparison; n = N_ANY_COMP2;
    } else {
        arr = trans_generic; n = N_GENERIC;
    }

    return arr[pick_variant(n, &last)];
}

const char* discourse_subject_ref(const char* concept_name, int sentence_num) {
    static char buf[128];
    int cycle = sentence_num % 5;

    switch (cycle) {
        case 0:
            return concept_name;
        case 1:
            return "It";
        case 2:
            /* "This entity" as generic parent category reference */
            snprintf(buf, sizeof(buf), "This %s", "entity");
            return buf;
        case 3:
            return "It";
        default:
            /* Alternate: even = name, odd = pronoun */
            return (sentence_num % 2 == 0) ? concept_name : "It";
    }
}

const char* discourse_section_opener(SectionType type, const char* concept_name) {
    static int last = -1;
    const char** arr;
    int n;
    (void)concept_name; /* available for future use */

    switch (type) {
        case SEC_DEFINITION:  arr = opener_definition;  n = N_OPEN_DEF;   break;
        case SEC_PROPERTY:    arr = opener_property;    n = N_OPEN_PROP;  break;
        case SEC_PHYSICAL:    arr = opener_physical;    n = N_OPEN_PHYS;  break;
        case SEC_CAPABILITY:  arr = opener_capability;  n = N_OPEN_CAP;   break;
        case SEC_PURPOSE:     arr = opener_purpose;     n = N_OPEN_PURP;  break;
        case SEC_COMPOSITION: arr = opener_composition; n = N_OPEN_COMP;  break;
        case SEC_LOCATION:    arr = opener_location;    n = N_OPEN_LOC;   break;
        case SEC_CAUSE:       arr = opener_cause;       n = N_OPEN_CAUSE; break;
        case SEC_HISTORY:     arr = opener_history;     n = N_OPEN_HIST;  break;
        case SEC_COMPARISON:  arr = opener_comparison;  n = N_OPEN_CMP;   break;
        default:              return "";
    }

    return arr[pick_variant(n, &last)];
}

const char* discourse_closing(const char* concept_name, int fact_count) {
    static char buf[256];
    static int last_med = -1, last_many = -1;

    if (fact_count <= 3) {
        return "";
    } else if (fact_count <= 6) {
        const char* adj = closing_medium_adj[pick_variant(N_CLOSE_MED, &last_med)];
        snprintf(buf, sizeof(buf),
                 "Overall, %s is a %s entity.", concept_name, adj);
        return buf;
    } else {
        const char* adj = closing_many_adj[pick_variant(N_CLOSE_MANY, &last_many)];
        snprintf(buf, sizeof(buf),
                 "In summary, %s is a %s entity with many distinctive characteristics.",
                 concept_name, adj);
        return buf;
    }
}

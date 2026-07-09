#ifndef DISCOURSE_H
#define DISCOURSE_H

typedef enum {
    SEC_DEFINITION,    // IS_A classification
    SEC_PROPERTY,      // characteristics (is X)
    SEC_PHYSICAL,      // physical features (has X)
    SEC_CAPABILITY,    // what it can do
    SEC_PURPOSE,       // what it's used for
    SEC_COMPOSITION,   // what it's made of
    SEC_LOCATION,      // where it is
    SEC_CAUSE,         // what it causes
    SEC_HISTORY,       // origin/creation
    SEC_COMPARISON     // compared to others
} SectionType;

// Get a transition phrase between two section types
const char* discourse_transition(SectionType from, SectionType to);

// Get a varied subject reference (avoid "It" every time)
const char* discourse_subject_ref(const char* concept_name, int sentence_num);

// Get an opening phrase for a section
const char* discourse_section_opener(SectionType type, const char* concept_name);

// Get a closing/synthesis sentence
const char* discourse_closing(const char* concept_name, int fact_count);

#endif

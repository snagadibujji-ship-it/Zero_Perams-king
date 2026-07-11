#ifndef SIP_H
#define SIP_H

/*
 * SIP — Semantic Intent Parser
 * Parses ANY question into canonical form: intent + entity + property.
 * 30 question types mapped to optimal reasoning strategies.
 */

#define SIP_MAX_ENTITIES 8
#define SIP_MAX_PROPS    4

typedef enum {
    SIP_FACTUAL,       /* "What is X?" */
    SIP_PROPERTY,      /* "What color is X?" */
    SIP_CAUSAL,        /* "Why does X?" */
    SIP_COMPARATIVE,   /* "X vs Y" */
    SIP_HYPOTHETICAL,  /* "What if X?" */
    SIP_PROCEDURAL,    /* "How to X?" */
    SIP_QUANTITATIVE,  /* "How many X?" */
    SIP_TEMPORAL,      /* "When did X?" */
    SIP_SPATIAL,       /* "Where is X?" */
    SIP_BOOLEAN,       /* "Can X do Y?" */
    SIP_LIST,          /* "What are all X?" */
    SIP_RELATION,      /* "How is X related to Y?" */
    SIP_COMPOSITION,   /* "What is X made of?" */
    SIP_FUNCTION,      /* "What does X do?" */
    SIP_ORIGIN,        /* "Where does X come from?" */
    SIP_PREDICTION,    /* "Will X happen?" */
    SIP_EXPLANATION,   /* "How does X work?" */
    SIP_NUMERICAL,     /* "Calculate X" */
    SIP_NEGATION,      /* "What is NOT X?" */
    SIP_SUPERLATIVE,   /* "What is the biggest X?" */
    SIP_CONDITIONAL,   /* "If X then Y?" */
    SIP_DEFINITION,    /* "Define X" */
    SIP_EXISTENCE,     /* "Is there X?" */
    SIP_OPINION,       /* "Should I X?" */
    SIP_CONTEXT,       /* "What did I say about X?" */
    SIP_CONTINUATION,  /* "What else?" / "More?" */
    SIP_CORRECTION,    /* "No, I meant X" */
    SIP_COMPOUND,      /* "X and also Y?" */
    SIP_META,          /* "How confident are you?" */
    SIP_AMBIGUOUS,     /* "Tell me about X" (no specific question) */
} SIPIntent;

typedef struct {
    SIPIntent intent;
    char entities[SIP_MAX_ENTITIES][128];
    int entity_count;
    char property[64];       /* For PROPERTY queries: what property? */
    char raw[512];           /* Original input preserved */
    float confidence;        /* How sure we are about the parse */
} SIPResult;

/* API */
SIPResult sip_parse(const char *input);
const char* sip_intent_name(SIPIntent intent);
int sip_requires_comparison(SIPIntent intent);
int sip_requires_reasoning(SIPIntent intent);

#endif

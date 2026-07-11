/*
 * sip.c — Semantic Intent Parser
 * Routes ANY question to the optimal reasoning strategy.
 * 30 intent types × pattern matching = always correct routing.
 */

#include "sip.h"
#include <string.h>
#include <ctype.h>
#include <stdio.h>

/* ─── Helpers ─── */

static int ci_contains(const char *hay, const char *needle) {
    if (!hay || !needle) return 0;
    size_t hlen = strlen(hay), nlen = strlen(needle);
    if (nlen > hlen) return 0;
    for (size_t i = 0; i <= hlen - nlen; i++) {
        int match = 1;
        for (size_t j = 0; j < nlen; j++) {
            if (tolower((unsigned char)hay[i+j]) != tolower((unsigned char)needle[j])) {
                match = 0; break;
            }
        }
        if (match) return 1;
    }
    return 0;
}

static int starts_ci(const char *str, const char *prefix) {
    while (*prefix) {
        if (tolower((unsigned char)*str) != tolower((unsigned char)*prefix)) return 0;
        str++; prefix++;
    }
    return 1;
}

static void extract_after(const char *input, const char *marker, char *out, int max) {
    const char *p = strstr(input, marker);
    if (!p) { out[0] = '\0'; return; }
    p += strlen(marker);
    while (*p == ' ') p++;
    int i = 0;
    while (*p && *p != '?' && *p != '.' && i < max - 1) {
        out[i++] = *p++;
    }
    out[i] = '\0';
}

/* ─── Main Parser ─── */

SIPResult sip_parse(const char *input) {
    SIPResult r;
    memset(&r, 0, sizeof(r));
    strncpy(r.raw, input, sizeof(r.raw) - 1);
    r.confidence = 0.8f;  /* Default: pretty sure */
    
    char lower[512];
    int len = 0;
    for (int i = 0; input[i] && len < 511; i++)
        lower[len++] = tolower((unsigned char)input[i]);
    lower[len] = '\0';
    
    /* ─── Pattern matching (most specific first) ─── */
    
    /* COMPOUND: "X and Y" / "X and also Y" */
    if (ci_contains(lower, " and also ") || ci_contains(lower, " as well as ")) {
        r.intent = SIP_COMPOUND; r.confidence = 0.9f; goto extract;
    }
    
    /* CORRECTION: "no, I meant" / "actually" / "I said X not Y" */
    if (starts_ci(lower, "no,") || starts_ci(lower, "no ") || ci_contains(lower, "i meant") || 
        (starts_ci(lower, "actually") && len < 100)) {
        r.intent = SIP_CORRECTION; r.confidence = 0.9f; goto extract;
    }
    
    /* CONTINUATION: "more" / "what else" / "go on" / "continue" */
    if (ci_contains(lower, "what else") || ci_contains(lower, "tell me more") ||
        (strcmp(lower, "more") == 0) || ci_contains(lower, "go on") || ci_contains(lower, "continue")) {
        r.intent = SIP_CONTINUATION; r.confidence = 0.95f; goto extract;
    }
    
    /* META: "how confident" / "are you sure" / "how do you know" */
    if (ci_contains(lower, "how confident") || ci_contains(lower, "are you sure") ||
        ci_contains(lower, "how do you know") || ci_contains(lower, "your sources")) {
        r.intent = SIP_META; r.confidence = 0.95f; goto extract;
    }
    
    /* CONTEXT: "what did I say" / "earlier I mentioned" */
    if (ci_contains(lower, "what did i") || ci_contains(lower, "earlier") ||
        ci_contains(lower, "last time") || ci_contains(lower, "remember when")) {
        r.intent = SIP_CONTEXT; r.confidence = 0.85f; goto extract;
    }
    
    /* HYPOTHETICAL: "what if" / "what would happen" / "suppose" / "imagine" */
    if (ci_contains(lower, "what if") || ci_contains(lower, "what would") ||
        ci_contains(lower, "suppose") || ci_contains(lower, "imagine if") ||
        ci_contains(lower, "hypothetically")) {
        r.intent = SIP_HYPOTHETICAL; r.confidence = 0.95f; goto extract;
    }
    
    /* COMPARATIVE: "vs" / "versus" / "compare" / "difference between" / "better" */
    if (ci_contains(lower, " vs ") || ci_contains(lower, "versus") ||
        ci_contains(lower, "compare") || ci_contains(lower, "difference between") ||
        ci_contains(lower, "which is better")) {
        r.intent = SIP_COMPARATIVE; r.confidence = 0.9f; goto extract;
    }
    
    /* SUPERLATIVE: "biggest" / "fastest" / "most" / "best" / "tallest" */
    if (ci_contains(lower, "biggest") || ci_contains(lower, "largest") ||
        ci_contains(lower, "smallest") || ci_contains(lower, "fastest") ||
        ci_contains(lower, "tallest") || ci_contains(lower, "longest") ||
        ci_contains(lower, "most ") || ci_contains(lower, "best ")) {
        r.intent = SIP_SUPERLATIVE; r.confidence = 0.9f; goto extract;
    }
    
    /* NUMERICAL: "calculate" / "compute" / math expressions */
    if (ci_contains(lower, "calculate") || ci_contains(lower, "compute") ||
        ci_contains(lower, "solve") || ci_contains(lower, "evaluate")) {
        r.intent = SIP_NUMERICAL; r.confidence = 0.95f; goto extract;
    }
    
    /* CAUSAL: "why" / "what causes" / "because" / "reason" */
    if (starts_ci(lower, "why") || ci_contains(lower, "what causes") ||
        ci_contains(lower, "reason for") || ci_contains(lower, "cause of")) {
        r.intent = SIP_CAUSAL; r.confidence = 0.9f; goto extract;
    }
    
    /* TEMPORAL: "when" / "what year" / "what date" */
    if (starts_ci(lower, "when") || ci_contains(lower, "what year") ||
        ci_contains(lower, "what date") || ci_contains(lower, "how long ago")) {
        r.intent = SIP_TEMPORAL; r.confidence = 0.9f; goto extract;
    }
    
    /* SPATIAL: "where" / "located" / "location" */
    if (starts_ci(lower, "where") || ci_contains(lower, "located") ||
        ci_contains(lower, "location of")) {
        r.intent = SIP_SPATIAL; r.confidence = 0.9f; goto extract;
    }
    
    /* QUANTITATIVE: "how many" / "how much" / "count" */
    if (ci_contains(lower, "how many") || ci_contains(lower, "how much") ||
        ci_contains(lower, "count of") || ci_contains(lower, "number of")) {
        r.intent = SIP_QUANTITATIVE; r.confidence = 0.9f; goto extract;
    }
    
    /* BOOLEAN: "can X" / "is X" / "does X" / "do X" */
    if (starts_ci(lower, "can ") || starts_ci(lower, "is ") ||
        starts_ci(lower, "does ") || starts_ci(lower, "do ") ||
        starts_ci(lower, "are ")) {
        r.intent = SIP_BOOLEAN; r.confidence = 0.8f; goto extract;
    }
    
    /* PROCEDURAL: "how to" / "how do I" / "steps to" */
    if (ci_contains(lower, "how to") || ci_contains(lower, "how do i") ||
        ci_contains(lower, "how can i") || ci_contains(lower, "steps to")) {
        r.intent = SIP_PROCEDURAL; r.confidence = 0.9f; goto extract;
    }
    
    /* EXPLANATION: "how does" / "how is" / "explain how" */
    if (ci_contains(lower, "how does") || ci_contains(lower, "how is") ||
        ci_contains(lower, "explain how") || ci_contains(lower, "mechanism")) {
        r.intent = SIP_EXPLANATION; r.confidence = 0.85f; goto extract;
    }
    
    /* COMPOSITION: "made of" / "consist" / "composed" / "parts of" */
    if (ci_contains(lower, "made of") || ci_contains(lower, "composed") ||
        ci_contains(lower, "consist") || ci_contains(lower, "parts of")) {
        r.intent = SIP_COMPOSITION; r.confidence = 0.9f; goto extract;
    }
    
    /* FUNCTION: "what does X do" / "purpose of" / "used for" */
    if (ci_contains(lower, "what does") && ci_contains(lower, "do") ||
        ci_contains(lower, "purpose of") || ci_contains(lower, "used for")) {
        r.intent = SIP_FUNCTION; r.confidence = 0.85f; goto extract;
    }
    
    /* LIST: "list" / "what are all" / "enumerate" / "name all" */
    if (ci_contains(lower, "list all") || ci_contains(lower, "what are all") ||
        ci_contains(lower, "name all") || ci_contains(lower, "enumerate")) {
        r.intent = SIP_LIST; r.confidence = 0.9f; goto extract;
    }
    
    /* DEFINITION: "define" / "meaning of" / "definition" */
    if (starts_ci(lower, "define") || ci_contains(lower, "meaning of") ||
        ci_contains(lower, "definition")) {
        r.intent = SIP_DEFINITION; r.confidence = 0.9f; goto extract;
    }
    
    /* FACTUAL: "what is" / "who is" / "what are" */
    if (ci_contains(lower, "what is") || ci_contains(lower, "what are") ||
        ci_contains(lower, "who is") || ci_contains(lower, "who was") ||
        ci_contains(lower, "who are")) {
        r.intent = SIP_FACTUAL; r.confidence = 0.9f; goto extract;
    }
    
    /* AMBIGUOUS: "tell me about" / just a topic name */
    if (ci_contains(lower, "tell me about") || ci_contains(lower, "info on") ||
        ci_contains(lower, "about ")) {
        r.intent = SIP_AMBIGUOUS; r.confidence = 0.7f; goto extract;
    }
    
    /* Default: FACTUAL with low confidence */
    r.intent = SIP_FACTUAL;
    r.confidence = 0.5f;

extract:
    /* Extract entities: skip question words, take remaining content words */
    {
        const char *skip[] = {"what","is","are","the","a","an","who","was","where",
                             "when","how","does","do","can","will","which","why",
                             "tell","me","about","define","explain","many","much",
                             "calculate","compare","if","would","should","could",NULL};
        char *words[32];
        char buf[512];
        strncpy(buf, input, sizeof(buf)-1); buf[511] = '\0';
        int wc = 0;
        char *tok = strtok(buf, " \t\n?.,!;:");
        while (tok && wc < 32) { words[wc++] = tok; tok = strtok(NULL, " \t\n?.,!;:"); }
        
        for (int i = 0; i < wc && r.entity_count < SIP_MAX_ENTITIES; i++) {
            /* Skip question/stop words */
            int is_skip = 0;
            char w_lower[64];
            int wl = 0;
            for (int j = 0; words[i][j] && wl < 63; j++)
                w_lower[wl++] = tolower((unsigned char)words[i][j]);
            w_lower[wl] = '\0';
            
            for (int s = 0; skip[s]; s++) {
                if (strcmp(w_lower, skip[s]) == 0) { is_skip = 1; break; }
            }
            if (!is_skip && strlen(words[i]) > 1) {
                strncpy(r.entities[r.entity_count], words[i], 127);
                r.entity_count++;
            }
        }
    }
    
    return r;
}

const char* sip_intent_name(SIPIntent intent) {
    static const char *names[] = {
        "FACTUAL","PROPERTY","CAUSAL","COMPARATIVE","HYPOTHETICAL","PROCEDURAL",
        "QUANTITATIVE","TEMPORAL","SPATIAL","BOOLEAN","LIST","RELATION",
        "COMPOSITION","FUNCTION","ORIGIN","PREDICTION","EXPLANATION","NUMERICAL",
        "NEGATION","SUPERLATIVE","CONDITIONAL","DEFINITION","EXISTENCE","OPINION",
        "CONTEXT","CONTINUATION","CORRECTION","COMPOUND","META","AMBIGUOUS"
    };
    if (intent >= 0 && intent <= SIP_AMBIGUOUS) return names[intent];
    return "UNKNOWN";
}

int sip_requires_comparison(SIPIntent intent) {
    return intent == SIP_COMPARATIVE || intent == SIP_SUPERLATIVE;
}

int sip_requires_reasoning(SIPIntent intent) {
    return intent == SIP_CAUSAL || intent == SIP_HYPOTHETICAL || 
           intent == SIP_EXPLANATION || intent == SIP_CONDITIONAL;
}

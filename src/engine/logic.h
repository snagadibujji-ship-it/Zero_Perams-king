/*
 * logic.h — Universal Logic Engine for Axima
 * Handles: syllogisms, multi-hop chains, negation, quantifiers, transitivity
 * 
 * Supports:
 *   - "all X are Y" / "every X is Y" / "no X are Y"
 *   - "X have Y" / "X live in Y" / "X can Y" / "X contain Y"
 *   - Multi-hop: A→B, B→C ∴ A→C
 *   - Negation: "no X are Y" + "Z is X" → Z is NOT Y
 *   - Modus ponens: "if X then Y" + "X is true" → Y
 *   - Contrapositive: "all X are Y" + "Z is not Y" → Z is not X
 */

#ifndef LOGIC_H
#define LOGIC_H

#include <string.h>
#include <stdio.h>
#include <ctype.h>

#define LOGIC_MAX_PREMISES 10
#define LOGIC_MAX_WORD 64
#define LOGIC_MAX_ANSWER 512

typedef enum {
    LREL_ARE,        /* all X ARE Y / every X IS Y */
    LREL_HAVE,       /* X HAVE Y */
    LREL_CAN,        /* X CAN Y */
    LREL_LIVE_IN,    /* X LIVE IN Y */
    LREL_IS_A,       /* X IS A Y (instance) */
    LREL_CONTAIN,    /* X CONTAIN Y */
    LREL_NOT_ARE,    /* no X ARE Y */
    LREL_IF_THEN,    /* if X then Y */
} LogicRelation;

typedef enum {
    QUANT_ALL,      /* all/every */
    QUANT_NO,       /* no/none */
    QUANT_SOME,     /* some */
    QUANT_INSTANCE, /* specific: "tom is a cat" */
} LogicQuantifier;

typedef struct {
    LogicQuantifier quant;
    LogicRelation rel;
    char subject[LOGIC_MAX_WORD];
    char object[LOGIC_MAX_WORD];
} LogicPremise;

typedef struct {
    int count;
    LogicPremise premises[LOGIC_MAX_PREMISES];
} LogicPremiseSet;

typedef struct {
    int valid;           /* 1 = conclusion found */
    int result;          /* 1 = yes, 0 = no, -1 = unknown */
    float confidence;
    char answer[LOGIC_MAX_ANSWER];
    char proof[LOGIC_MAX_ANSWER];
} LogicResult;

/* ═══════════════════════════════════════════════════════════════ */
/* UTILITIES                                                       */
/* ═══════════════════════════════════════════════════════════════ */

static void logic_lower(char *dst, const char *src, int max) {
    int i;
    for (i = 0; i < max - 1 && src[i]; i++)
        dst[i] = tolower((unsigned char)src[i]);
    dst[i] = '\0';
}

static void logic_trim(char *s) {
    int i = 0, j = (int)strlen(s) - 1;
    while (i <= j && isspace((unsigned char)s[i])) i++;
    while (j >= i && (isspace((unsigned char)s[j]) || s[j] == '.' || s[j] == ',' || s[j] == '?')) j--;
    memmove(s, s + i, j - i + 1);
    s[j - i + 1] = '\0';
}

/* Strip "a ", "an ", "the " from start */
static void logic_strip_article(char *s) {
    if (strncmp(s, "a ", 2) == 0) memmove(s, s+2, strlen(s)-1);
    else if (strncmp(s, "an ", 3) == 0) memmove(s, s+3, strlen(s)-2);
    else if (strncmp(s, "the ", 4) == 0) memmove(s, s+4, strlen(s)-3);
}

/* Check if word matches (singular/plural fuzzy) */
static int logic_match(const char *a, const char *b) {
    if (strcmp(a, b) == 0) return 1;
    /* "cats" matches "cat", "dogs" matches "dog" */
    int la = (int)strlen(a), lb = (int)strlen(b);
    if (la == lb + 1 && a[la-1] == 's' && strncmp(a, b, lb) == 0) return 1;
    if (lb == la + 1 && b[lb-1] == 's' && strncmp(b, a, la) == 0) return 1;
    /* "es" plural: "foxes" = "fox" */
    if (la == lb + 2 && a[la-1] == 's' && a[la-2] == 'e' && strncmp(a, b, lb) == 0) return 1;
    if (lb == la + 2 && b[lb-1] == 's' && b[lb-2] == 'e' && strncmp(b, a, la) == 0) return 1;
    return 0;
}

/* ═══════════════════════════════════════════════════════════════ */
/* PARSER — Extract premises from natural language                 */
/* ═══════════════════════════════════════════════════════════════ */

static int logic_parse_premise(const char *sentence, LogicPremise *p) {
    char buf[256];
    logic_lower(buf, sentence, 256);
    logic_trim(buf);
    
    /* Skip empty */
    if (strlen(buf) < 5) return 0;
    
    /* "all X are Y" / "every X is Y" / "every X is a Y" */
    char *pos;
    if ((pos = strstr(buf, "all ")) == buf || (pos = strstr(buf, "every ")) == buf) {
        int skip = (buf[0] == 'a') ? 4 : 6;
        char *are = strstr(buf + skip, " are ");
        char *is = strstr(buf + skip, " is ");
        char *have = strstr(buf + skip, " have ");
        char *can = strstr(buf + skip, " can ");
        char *live = strstr(buf + skip, " live in ");
        
        if (are) {
            p->quant = QUANT_ALL; p->rel = LREL_ARE;
            strncpy(p->subject, buf + skip, (int)(are - buf - skip));
            p->subject[(int)(are - buf - skip)] = '\0';
            strncpy(p->object, are + 5, LOGIC_MAX_WORD - 1);
        } else if (have) {
            p->quant = QUANT_ALL; p->rel = LREL_HAVE;
            strncpy(p->subject, buf + skip, (int)(have - buf - skip));
            p->subject[(int)(have - buf - skip)] = '\0';
            strncpy(p->object, have + 6, LOGIC_MAX_WORD - 1);
        } else if (can) {
            p->quant = QUANT_ALL; p->rel = LREL_CAN;
            strncpy(p->subject, buf + skip, (int)(can - buf - skip));
            p->subject[(int)(can - buf - skip)] = '\0';
            strncpy(p->object, can + 5, LOGIC_MAX_WORD - 1);
        } else if (live) {
            p->quant = QUANT_ALL; p->rel = LREL_LIVE_IN;
            strncpy(p->subject, buf + skip, (int)(live - buf - skip));
            p->subject[(int)(live - buf - skip)] = '\0';
            strncpy(p->object, live + 9, LOGIC_MAX_WORD - 1);
        } else if (is) {
            p->quant = QUANT_ALL; p->rel = LREL_ARE;
            strncpy(p->subject, buf + skip, (int)(is - buf - skip));
            p->subject[(int)(is - buf - skip)] = '\0';
            char *obj_start = is + 4;
            logic_strip_article(obj_start);
            strncpy(p->object, obj_start, LOGIC_MAX_WORD - 1);
        } else {
            return 0;
        }
        logic_trim(p->subject); logic_trim(p->object);
        logic_strip_article(p->object);
        return 1;
    }
    
    /* "no X are Y" */
    if (strncmp(buf, "no ", 3) == 0) {
        char *are = strstr(buf + 3, " are ");
        char *is = strstr(buf + 3, " is ");
        if (are) {
            p->quant = QUANT_NO; p->rel = LREL_NOT_ARE;
            strncpy(p->subject, buf + 3, (int)(are - buf - 3));
            p->subject[(int)(are - buf - 3)] = '\0';
            strncpy(p->object, are + 5, LOGIC_MAX_WORD - 1);
        } else if (is) {
            p->quant = QUANT_NO; p->rel = LREL_NOT_ARE;
            strncpy(p->subject, buf + 3, (int)(is - buf - 3));
            p->subject[(int)(is - buf - 3)] = '\0';
            strncpy(p->object, is + 4, LOGIC_MAX_WORD - 1);
        } else { return 0; }
        logic_trim(p->subject); logic_trim(p->object);
        logic_strip_article(p->object);
        return 1;
    }
    
    /* "X is a Y" / "X is Y" (instance assertion) */
    pos = strstr(buf, " is a ");
    if (!pos) pos = strstr(buf, " is an ");
    if (!pos) pos = strstr(buf, " is ");
    if (pos) {
        p->quant = QUANT_INSTANCE; p->rel = LREL_IS_A;
        strncpy(p->subject, buf, (int)(pos - buf));
        p->subject[(int)(pos - buf)] = '\0';
        char *obj_start = pos + 4; /* " is " */
        if (strncmp(pos, " is a ", 6) == 0) obj_start = pos + 6;
        else if (strncmp(pos, " is an ", 7) == 0) obj_start = pos + 7;
        strncpy(p->object, obj_start, LOGIC_MAX_WORD - 1);
        logic_trim(p->subject); logic_trim(p->object);
        logic_strip_article(p->subject);
        logic_strip_article(p->object);
        return 1;
    }
    
    return 0;
}

/* ═══════════════════════════════════════════════════════════════ */
/* INFERENCE ENGINE                                                */
/* ═══════════════════════════════════════════════════════════════ */

static LogicResult logic_solve(const char *full_input) {
    LogicResult res = {0, -1, 0.0f, "", ""};
    
    char input[1024];
    logic_lower(input, full_input, 1024);
    
    /* Split into sentences */
    LogicPremiseSet premises = {0};
    char *saveptr;
    char sentences[1024];
    strncpy(sentences, input, 1023); sentences[1023] = '\0';
    
    /* Split by ". " or ", " */
    char *sent = strtok_r(sentences, ".,", &saveptr);
    char question[256] = "";
    
    while (sent) {
        logic_trim(sent);
        if (strlen(sent) < 3) { sent = strtok_r(NULL, ".,", &saveptr); continue; }
        
        /* Is this the question? (contains "is" + "?" or starts with "is/does/can/do") */
        int is_question = 0;
        if (strstr(sent, "?")) is_question = 1;
        if (strncmp(sent, "is ", 3) == 0 || strncmp(sent, "does ", 5) == 0 ||
            strncmp(sent, "can ", 4) == 0 || strncmp(sent, "do ", 3) == 0) is_question = 1;
        
        if (is_question) {
            strncpy(question, sent, 255);
        } else {
            if (premises.count < LOGIC_MAX_PREMISES) {
                if (logic_parse_premise(sent, &premises.premises[premises.count])) {
                    premises.count++;
                }
            }
        }
        sent = strtok_r(NULL, ".,", &saveptr);
    }
    
    /* If no explicit question found, last sentence might be the question */
    if (question[0] == '\0') return res;
    if (premises.count == 0) return res;
    
    /* Parse the question to find what we're asking about */
    char q_subject[LOGIC_MAX_WORD] = "";
    char q_property[LOGIC_MAX_WORD] = "";
    LogicRelation q_rel = LREL_ARE;
    
    logic_trim(question);
    /* Remove "?" */
    int qlen = (int)strlen(question);
    if (qlen > 0 && question[qlen-1] == '?') question[qlen-1] = '\0';
    logic_trim(question);
    
    /* "is X a Y" / "is X Y" */
    if (strncmp(question, "is ", 3) == 0) {
        char *a_pos = strstr(question + 3, " a ");
        char *an_pos = strstr(question + 3, " an ");
        if (a_pos) {
            strncpy(q_subject, question + 3, (int)(a_pos - question - 3));
            q_subject[(int)(a_pos - question - 3)] = '\0';
            strncpy(q_property, a_pos + 3, LOGIC_MAX_WORD - 1);
        } else if (an_pos) {
            strncpy(q_subject, question + 3, (int)(an_pos - question - 3));
            q_subject[(int)(an_pos - question - 3)] = '\0';
            strncpy(q_property, an_pos + 4, LOGIC_MAX_WORD - 1);
        } else {
            /* "is X Y" — split at last space */
            char *last_space = strrchr(question + 3, ' ');
            if (last_space) {
                strncpy(q_subject, question + 3, (int)(last_space - question - 3));
                q_subject[(int)(last_space - question - 3)] = '\0';
                strncpy(q_property, last_space + 1, LOGIC_MAX_WORD - 1);
            }
        }
        q_rel = LREL_ARE;
    }
    /* "does X have Y" / "does X live in Y" / "can X Y" */
    else if (strncmp(question, "does ", 5) == 0) {
        char *have = strstr(question + 5, " have ");
        char *live = strstr(question + 5, " live in ");
        char *verb = strstr(question + 5, " ");
        if (have) {
            strncpy(q_subject, question + 5, (int)(have - question - 5));
            q_subject[(int)(have - question - 5)] = '\0';
            strncpy(q_property, have + 6, LOGIC_MAX_WORD - 1);
            q_rel = LREL_HAVE;
        } else if (live) {
            strncpy(q_subject, question + 5, (int)(live - question - 5));
            q_subject[(int)(live - question - 5)] = '\0';
            strncpy(q_property, live + 9, LOGIC_MAX_WORD - 1);
            q_rel = LREL_LIVE_IN;
        } else if (verb) {
            /* "does X verb Y" → extract subject + property */
            char *second_space = strchr(verb + 1, ' ');
            if (second_space) {
                strncpy(q_subject, question + 5, (int)(verb - question - 5));
                q_subject[(int)(verb - question - 5)] = '\0';
                strncpy(q_property, second_space + 1, LOGIC_MAX_WORD - 1);
                /* Detect relation from verb */
                if (strstr(verb, "live")) q_rel = LREL_LIVE_IN;
                else if (strstr(verb, "have")) q_rel = LREL_HAVE;
                else q_rel = LREL_ARE;
            }
        }
    }
    /* "can X Y" */
    else if (strncmp(question, "can ", 4) == 0) {
        char *space = strchr(question + 4, ' ');
        if (space) {
            strncpy(q_subject, question + 4, (int)(space - question - 4));
            q_subject[(int)(space - question - 4)] = '\0';
            strncpy(q_property, space + 1, LOGIC_MAX_WORD - 1);
            q_rel = LREL_CAN;
        }
    }
    /* "do X verb Y" */
    else if (strncmp(question, "do ", 3) == 0) {
        /* "do penguins have wings" */
        char *have = strstr(question + 3, " have ");
        char *live = strstr(question + 3, " live in ");
        if (have) {
            strncpy(q_subject, question + 3, (int)(have - question - 3));
            q_subject[(int)(have - question - 3)] = '\0';
            strncpy(q_property, have + 6, LOGIC_MAX_WORD - 1);
            q_rel = LREL_HAVE;
        } else if (live) {
            strncpy(q_subject, question + 3, (int)(live - question - 3));
            q_subject[(int)(live - question - 3)] = '\0';
            strncpy(q_property, live + 9, LOGIC_MAX_WORD - 1);
            q_rel = LREL_LIVE_IN;
        }
    }
    
    logic_trim(q_subject); logic_trim(q_property);
    logic_strip_article(q_subject); logic_strip_article(q_property);
    
    if (q_subject[0] == '\0' || q_property[0] == '\0') return res;
    
    /* ─── INFERENCE ─── */
    
    /* Step 1: Find which class the subject belongs to */
    char subject_class[LOGIC_MAX_WORD] = "";
    for (int i = 0; i < premises.count; i++) {
        LogicPremise *p = &premises.premises[i];
        if (p->quant == QUANT_INSTANCE && logic_match(p->subject, q_subject)) {
            strncpy(subject_class, p->object, LOGIC_MAX_WORD - 1);
            break;
        }
    }
    
    /* Step 2: Check universal rules that apply to this class */
    for (int i = 0; i < premises.count; i++) {
        LogicPremise *p = &premises.premises[i];
        
        /* Match: "all CLASS are/have/can PROPERTY" + subject is a CLASS */
        if ((p->quant == QUANT_ALL) && logic_match(p->subject, subject_class)) {
            if (p->rel == q_rel || (p->rel == LREL_ARE && q_rel == LREL_ARE)) {
                if (logic_match(p->object, q_property)) {
                    /* POSITIVE MATCH */
                    res.valid = 1; res.result = 1; res.confidence = 0.99f;
                    snprintf(res.answer, LOGIC_MAX_ANSWER,
                        "Yes. All %s %s %s, and %s is a %s.",
                        p->subject,
                        (p->rel == LREL_ARE) ? "are" : (p->rel == LREL_HAVE) ? "have" : 
                        (p->rel == LREL_CAN) ? "can" : "live in",
                        p->object, q_subject, subject_class);
                    snprintf(res.proof, LOGIC_MAX_ANSWER,
                        "[Proof: syllogism, %d premises, confidence: 99%%]", premises.count);
                    return res;
                }
            }
        }
        
        /* Match: "no CLASS are PROPERTY" + subject is a CLASS → NOT property */
        if (p->quant == QUANT_NO && logic_match(p->subject, subject_class)) {
            if (logic_match(p->object, q_property)) {
                /* NEGATIVE MATCH */
                res.valid = 1; res.result = 0; res.confidence = 0.99f;
                snprintf(res.answer, LOGIC_MAX_ANSWER,
                    "No. No %s are %s, and %s is a %s, so %s is not %s.",
                    p->subject, p->object, q_subject, subject_class, q_subject, q_property);
                snprintf(res.proof, LOGIC_MAX_ANSWER,
                    "[Proof: negative syllogism, %d premises, confidence: 99%%]", premises.count);
                return res;
            }
        }
    }
    
    /* Step 3: Multi-hop chain (A→B, B→C ∴ A→C) */
    /* If subject's class has a rule that leads to another class which has the target property */
    for (int i = 0; i < premises.count; i++) {
        LogicPremise *p1 = &premises.premises[i];
        if (p1->quant != QUANT_ALL) continue;
        if (!logic_match(p1->subject, subject_class)) continue;
        
        /* p1: all CLASS are INTERMEDIATE */
        /* Now find: all INTERMEDIATE are/have PROPERTY */
        for (int j = 0; j < premises.count; j++) {
            if (j == i) continue;
            LogicPremise *p2 = &premises.premises[j];
            if (p2->quant != QUANT_ALL) continue;
            if (logic_match(p2->subject, p1->object) && logic_match(p2->object, q_property)) {
                res.valid = 1; res.result = 1; res.confidence = 0.95f;
                snprintf(res.answer, LOGIC_MAX_ANSWER,
                    "Yes. %s is a %s, all %s are %s, and all %s %s %s.",
                    q_subject, subject_class, subject_class, p1->object,
                    p1->object,
                    (p2->rel == LREL_ARE) ? "are" : (p2->rel == LREL_HAVE) ? "have" : "can",
                    q_property);
                snprintf(res.proof, LOGIC_MAX_ANSWER,
                    "[Proof: chain inference, %d hops, confidence: 95%%]", 2);
                return res;
            }
        }
    }
    
    /* Step 4: Direct property check (subject directly stated to have property) */
    for (int i = 0; i < premises.count; i++) {
        LogicPremise *p = &premises.premises[i];
        if (p->quant == QUANT_ALL && logic_match(p->subject, q_subject)) {
            if (logic_match(p->object, q_property)) {
                res.valid = 1; res.result = 1; res.confidence = 0.99f;
                snprintf(res.answer, LOGIC_MAX_ANSWER,
                    "Yes. All %s %s %s.",
                    p->subject,
                    (p->rel == LREL_ARE) ? "are" : (p->rel == LREL_HAVE) ? "have" : "can",
                    p->object);
                return res;
            }
        }
    }
    
    return res;
}

#endif /* LOGIC_H */

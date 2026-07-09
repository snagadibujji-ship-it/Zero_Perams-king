/*
 * grammar.c - Response generation using generative grammar (templates + slot filling)
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include "grammar.h"
#include "knowledge.h"
#include "memory.h"
#include "parser.h"

/* --- Internal template arrays --- */
static const char *GREETING_TEMPLATES[] = {
    "Hello! How can I help you?",
    "Hey there! What can I do for you?",
    "Hi! Ask me anything.",
    "Hey! What's on your mind?",
    "Welcome back! How can I help?"
};
static const char *FAREWELL_TEMPLATES[] = {
    "Goodbye! Talk to you later.",
    "See you! I'll remember our conversation.",
    "Bye! Come back anytime.",
    "Take care!",
    "Until next time!"
};
/* --- Confidence-grouped query response templates --- */

/* High confidence (>0.8): direct, assertive statements */
static const char *QUERY_HIGH_CONF_TEMPLATES[] = {
    "It's {object}.",
    "{object}, definitely.",
    "That's {object}.",
    "{subject}: {object}.",
    "{object}.",
    "The answer is {object}.",
    "Simple — {object}.",
    "{object}, no question about it.",
    "That would be {object}.",
    "{subject} is {object}, plain and simple.",
};
#define QUERY_HIGH_CONF_COUNT 10

/* Medium confidence (0.5–0.8): hedged, qualified statements */
static const char *QUERY_MED_CONF_TEMPLATES[] = {
    "I believe it's {object}.",
    "From what I know, {object}.",
    "Most likely {object}.",
    "If I recall correctly, {object}.",
    "I'd say {object}.",
    "As far as I know, {object}.",
    "Pretty sure it's {object}.",
};
#define QUERY_MED_CONF_COUNT 7

/* Low confidence (<0.5): uncertain, tentative statements */
static const char *QUERY_LOW_CONF_TEMPLATES[] = {
    "I think it might be {object}.",
    "Not entirely sure, but possibly {object}.",
    "My best guess would be {object}.",
    "I'm not certain, but perhaps {object}.",
    "Take this with a grain of salt: {object}.",
    "Don't quote me on this, but maybe {object}.",
};
#define QUERY_LOW_CONF_COUNT 6

/* No legacy alias needed — confidence-grouped templates are used directly */
static const char *QUERY_NOTFOUND_TEMPLATES[] = {
    "I don't know that yet. Can you teach me?",
    "I don't have that information. Would you like to tell me?",
    "Hmm, I'm not sure. I'd need to learn about that.",
    "That's outside my knowledge right now. Teach me?"
};
static const char *STATEMENT_TEMPLATES[] = {
    "Interesting. Tell me more.",
    "Got it. What else?",
    "I see. Anything else on your mind?",
    "Noted.",
    "I hear you."
};
static const char *CODE_REQUEST_TEMPLATES[] = {
    "I can help with code! Let me work on that...",
    "Code generation coming in Phase 6. For now, I can discuss the approach."
};
static const char *TEACH_TEMPLATES[] = {
    "I'll remember that! Thanks for teaching me.",
    "Stored! I won't forget.",
    "Got it, learned something new!"
};
static const char *UNKNOWN_TEMPLATES[] = {
    "I'm not sure what you mean. Could you rephrase?",
    "Can you say that differently?",
    "I didn't quite catch that."
};

static ResponseStyle current_style = STYLE_CASUAL;

/* --- Helper: fill {subject}, {object}, {predicate} slots in template --- */
static void fill_slots(char *out, size_t max_len, const char *tmpl,
                       const char *subject, const char *object, const char *predicate) {
    size_t pos = 0;
    const char *s = tmpl;
    while (*s && pos < max_len - 1) {
        if (*s == '{') {
            const char *val = NULL;
            int skip = 0;
            if (strncmp(s, "{subject}", 9) == 0) { val = subject; skip = 9; }
            else if (strncmp(s, "{object}", 8) == 0) { val = object; skip = 8; }
            else if (strncmp(s, "{predicate}", 11) == 0) { val = predicate; skip = 11; }
            if (val) {
                size_t vlen = strlen(val);
                if (pos + vlen < max_len - 1) {
                    memcpy(out + pos, val, vlen);
                    /* Capitalize first letter of slot value if at start of sentence */
                    if (pos == 0 && vlen > 0 && out[pos] >= 'a' && out[pos] <= 'z') {
                        out[pos] = out[pos] - 'a' + 'A';
                    }
                    pos += vlen;
                }
                s += skip;
                continue;
            }
        }
        out[pos++] = *s++;
    }
    out[pos] = '\0';
    /* Ensure first character of final output is uppercase */
    if (pos > 0 && out[0] >= 'a' && out[0] <= 'z') {
        out[0] = out[0] - 'a' + 'A';
    }
}

/* --- Public API --- */
int grammar_init(void) {
    srand((unsigned int)time(NULL));
    return 0;
}

int grammar_generate(const ParsedIntent *intent, const Fact *knowledge_results,
                     int kg_result_count, const WorkingMemory *memory, Response *response) {
    (void)memory; /* reserved for future context-aware generation */
    if (!intent || !response) return -1;

    const char **templates = NULL;
    int tcount = 0;
    int answer_found = (kg_result_count > 0);

    switch (intent->intent_type) {
        case INTENT_GREETING:   templates = GREETING_TEMPLATES;    tcount = 5; break;
        case INTENT_FAREWELL:   templates = FAREWELL_TEMPLATES;    tcount = 5; break;
        case INTENT_QUERY:
            if (answer_found) {
                /* Select template group based on knowledge confidence */
                float kg_conf = (kg_result_count > 0 && knowledge_results) ?
                    knowledge_results[0].confidence / 100.0f : 0.9f;
                if (kg_conf > 0.8f) {
                    templates = QUERY_HIGH_CONF_TEMPLATES;
                    tcount = QUERY_HIGH_CONF_COUNT;
                } else if (kg_conf >= 0.5f) {
                    templates = QUERY_MED_CONF_TEMPLATES;
                    tcount = QUERY_MED_CONF_COUNT;
                } else {
                    templates = QUERY_LOW_CONF_TEMPLATES;
                    tcount = QUERY_LOW_CONF_COUNT;
                }
            } else {
                templates = QUERY_NOTFOUND_TEMPLATES;
                tcount = 4;
            }
            break;
        case INTENT_STATEMENT:    templates = STATEMENT_TEMPLATES;    tcount = 5; break;
        case INTENT_CODE_REQUEST: templates = CODE_REQUEST_TEMPLATES; tcount = 2; break;
        case INTENT_TEACH:        templates = TEACH_TEMPLATES;        tcount = 3; break;
        default:                  templates = UNKNOWN_TEMPLATES;      tcount = 3; break;
    }

    /* Pick random template for variety */
    const char *tmpl = templates[rand() % tcount];

    /* Slot values from intent */
    const char *subj = intent->subject[0]   ? intent->subject   : "that";
    const char *obj  = intent->object[0]    ? intent->object    : "something";
    const char *pred = intent->predicate[0] ? intent->predicate : "is";

    /* If object is already a full sentence (contains verb), use directly */
    if (intent->intent_type == INTENT_QUERY && answer_found && intent->object[0]) {
        if (strstr(obj, " is ") || strstr(obj, " has ") || strstr(obj, " can ") ||
            strstr(obj, " are ") || strstr(obj, " was ") || strstr(obj, " located") ||
            strstr(obj, " made ") || strstr(obj, " used ") || strstr(obj, " causes") ||
            strstr(obj, " type of")) {
            /* Already a sentence — capitalize and use directly */
            strncpy(response->text, obj, sizeof(response->text)-1);
            response->text[sizeof(response->text)-1] = '\0';
            /* Trim trailing whitespace and periods */
            size_t len = strlen(response->text);
            while (len > 0 && (response->text[len-1] == ' ' || response->text[len-1] == '.')) {
                response->text[--len] = '\0';
            }
            /* Capitalize first letter */
            if (response->text[0] >= 'a' && response->text[0] <= 'z')
                response->text[0] -= 32;
            /* Add single period at end */
            len = strlen(response->text);
            if (len > 0 && len < sizeof(response->text)-2) {
                response->text[len] = '.';
                response->text[len+1] = '\0';
            }
            response->confidence = 0.9f;
            response->style = current_style;
            return 0;
        }
    }

    fill_slots(response->text, sizeof(response->text), tmpl, subj, obj, pred);

    /* Set confidence */
    if (intent->intent_type == INTENT_QUERY)
        response->confidence = answer_found ? 0.9f : 0.2f;
    else if (intent->intent_type == INTENT_GREETING || intent->intent_type == INTENT_FAREWELL)
        response->confidence = 1.0f;
    else
        response->confidence = 0.7f;

    response->style = current_style;
    return 0;
}

void grammar_set_style(ResponseStyle style) {
    current_style = style;
}

/* --- TEST MODE --- */
#ifdef TEST_MODE
#include <assert.h>

int main(void) {
    printf("=== Grammar Engine Tests ===\n");
    grammar_init();

    /* Test 1: Greeting response is not empty */
    ParsedIntent intent = {0};
    Response resp = {0};
    intent.intent_type = INTENT_GREETING;
    grammar_generate(&intent, NULL, 0, NULL, &resp);
    assert(strlen(resp.text) > 0);
    assert(resp.confidence == 1.0f);
    printf("[PASS] Greeting: \"%s\"\n", resp.text);

    /* Test 2: Query with facts contains the answer */
    memset(&intent, 0, sizeof(intent));
    memset(&resp, 0, sizeof(resp));
    intent.intent_type = INTENT_QUERY;
    strcpy(intent.subject, "Paris");
    strcpy(intent.object, "the capital of France");
    strcpy(intent.predicate, "is");
    Fact dummy = {.confidence = 90};
    grammar_generate(&intent, &dummy, 1, NULL, &resp);
    assert(strlen(resp.text) > 0);
    assert(strstr(resp.text, "capital of France") != NULL);
    assert(resp.confidence > 0.8f);
    printf("[PASS] Query (found): \"%s\"\n", resp.text);

    /* Test 3: Query no answer - contains question or admission */
    memset(&intent, 0, sizeof(intent));
    memset(&resp, 0, sizeof(resp));
    intent.intent_type = INTENT_QUERY;
    strcpy(intent.subject, "unicorns");
    grammar_generate(&intent, NULL, 0, NULL, &resp);
    assert(strlen(resp.text) > 0);
    assert(resp.confidence < 0.5f);
    assert(strstr(resp.text, "?") != NULL || strstr(resp.text, "don't") != NULL ||
           strstr(resp.text, "not sure") != NULL);
    printf("[PASS] Query (not found): \"%s\"\n", resp.text);

    /* Test 4: Unknown response contains question/admission */
    memset(&intent, 0, sizeof(intent));
    memset(&resp, 0, sizeof(resp));
    intent.intent_type = INTENT_UNKNOWN;
    grammar_generate(&intent, NULL, 0, NULL, &resp);
    assert(strlen(resp.text) > 0);
    assert(strstr(resp.text, "?") != NULL);
    printf("[PASS] Unknown: \"%s\"\n", resp.text);

    /* Test 5: Style setting */
    grammar_set_style(STYLE_FORMAL);
    memset(&intent, 0, sizeof(intent));
    memset(&resp, 0, sizeof(resp));
    intent.intent_type = INTENT_STATEMENT;
    grammar_generate(&intent, NULL, 0, NULL, &resp);
    assert(resp.style == STYLE_FORMAL);
    printf("[PASS] Style=FORMAL: \"%s\"\n", resp.text);

    printf("\n=== All grammar tests passed! ===\n");
    return 0;
}
#endif /* TEST_MODE */

#include "parser.h"
#include "tokenizer.h"
#include <string.h>
#include <stdio.h>
#include <ctype.h>

/* Word lists for intent detection */
static const char* greeting_words[] = {
    "hi", "hello", "hey", "greetings", "morning", "evening", "howdy", "hola", NULL
};

static const char* farewell_words[] = {
    "bye", "goodbye", "exit", "quit", "farewell", "cya", "later", NULL
};

static const char* question_words_start[] = {
    "what", "where", "when", "who", "why", "how", "is", "are", "do",
    "does", "can", "could", "would", "will", "shall", "did", NULL
};

static const char* question_words_any[] = {
    "what", "where", "when", "who", "why", "how", NULL
};

static const char* code_words[] = {
    "write", "code", "function", "program", "implement", "create",
    "generate", "build", "script", "class", NULL
};

static const char* teach_words[] = {
    "remember", "learn", "know", "fact", "teach", "store", NULL
};

static int word_in_list(const char* word, const char** list) {
    for (int i = 0; list[i] != NULL; i++) {
        if (strcmp(word, list[i]) == 0) return 1;
    }
    return 0;
}

static int contains_word_from_list(TokenList* tokens, const char** list) {
    for (int i = 0; i < tokens->count; i++) {
        if (tokens->tokens[i].type == TOKEN_WORD) {
            if (word_in_list(tokens->tokens[i].value, list)) return 1;
        }
    }
    return 0;
}

static int ends_with_question_mark(TokenList* tokens) {
    for (int i = tokens->count - 1; i >= 0; i--) {
        if (tokens->tokens[i].type == TOKEN_END) continue;
        if (tokens->tokens[i].type == TOKEN_PUNCTUATION &&
            tokens->tokens[i].value[0] == '?') return 1;
        break;
    }
    return 0;
}

static void extract_subject_object(TokenList* tokens, ParsedIntent* intent) {
    /* Simple extraction: first noun-like word after question word = subject,
       last noun-like word = object. Skip common stop words. */
    static const char* stop_words[] = {
        "the", "a", "an", "is", "are", "of", "in", "on", "at", "to",
        "for", "it", "that", "this", "was", "were", "be", "been", NULL
    };

    int found_subject = 0;
    intent->subject[0] = '\0';
    intent->object[0] = '\0';
    intent->predicate[0] = '\0';

    for (int i = 0; i < tokens->count; i++) {
        Token* t = &tokens->tokens[i];
        if (t->type != TOKEN_WORD) continue;
        if (word_in_list(t->value, stop_words)) continue;
        if (word_in_list(t->value, question_words_start)) continue;
        if (word_in_list(t->value, greeting_words)) continue;
        if (word_in_list(t->value, farewell_words)) continue;

        if (!found_subject) {
            strncpy(intent->subject, t->value, 255);
            intent->subject[255] = '\0';
            found_subject = 1;
        } else {
            /* Last meaningful word becomes object */
            strncpy(intent->object, t->value, 255);
            intent->object[255] = '\0';
        }
    }
}

void parse_intent(TokenList* tokens, ParsedIntent* intent) {
    memset(intent, 0, sizeof(ParsedIntent));
    intent->intent_type = INTENT_UNKNOWN;
    intent->confidence = 0.5f;

    if (tokens->count == 0) return;

    /* Rebuild raw input */
    intent->raw_input[0] = '\0';
    for (int i = 0; i < tokens->count && tokens->tokens[i].type != TOKEN_END; i++) {
        if (i > 0) strncat(intent->raw_input, " ", sizeof(intent->raw_input) - strlen(intent->raw_input) - 1);
        strncat(intent->raw_input, tokens->tokens[i].value, sizeof(intent->raw_input) - strlen(intent->raw_input) - 1);
    }

    Token* first = &tokens->tokens[0];

    /* Check COMMAND first (starts with /) */
    if (first->type == TOKEN_COMMAND) {
        intent->intent_type = INTENT_COMMAND;
        strncpy(intent->subject, first->value, 255);
        intent->confidence = 1.0f;
        return;
    }

    /* Check GREETING */
    if (first->type == TOKEN_WORD && word_in_list(first->value, greeting_words)) {
        intent->intent_type = INTENT_GREETING;
        intent->confidence = 0.95f;
        return;
    }

    /* Check FAREWELL */
    if (first->type == TOKEN_WORD && word_in_list(first->value, farewell_words)) {
        intent->intent_type = INTENT_FAREWELL;
        intent->confidence = 0.95f;
        return;
    }

    /* Check CODE_REQUEST */
    if (contains_word_from_list(tokens, code_words)) {
        intent->intent_type = INTENT_CODE_REQUEST;
        intent->confidence = 0.8f;
        extract_subject_object(tokens, intent);
        return;
    }

    /* Check TEACH */
    if (contains_word_from_list(tokens, teach_words)) {
        intent->intent_type = INTENT_TEACH;
        intent->confidence = 0.75f;
        extract_subject_object(tokens, intent);
        return;
    }

    /* Check QUERY (question words or ends with ?) */
    if ((first->type == TOKEN_WORD && word_in_list(first->value, question_words_start)) ||
        contains_word_from_list(tokens, question_words_any) ||
        ends_with_question_mark(tokens)) {
        intent->intent_type = INTENT_QUERY;
        intent->confidence = 0.85f;
        extract_subject_object(tokens, intent);
        return;
    }

    /* Default: STATEMENT */
    intent->intent_type = INTENT_STATEMENT;
    intent->confidence = 0.6f;
    extract_subject_object(tokens, intent);
}

const char* intent_type_name(IntentType type) {
    switch (type) {
        case INTENT_QUERY:        return "QUERY";
        case INTENT_COMMAND:      return "COMMAND";
        case INTENT_STATEMENT:    return "STATEMENT";
        case INTENT_GREETING:     return "GREETING";
        case INTENT_FAREWELL:     return "FAREWELL";
        case INTENT_TEACH:        return "TEACH";
        case INTENT_CODE_REQUEST: return "CODE_REQUEST";
        case INTENT_AGENT_TASK:   return "AGENT_TASK";
        case INTENT_UNKNOWN:      return "UNKNOWN";
        default:                  return "UNKNOWN";
    }
}

#ifdef TEST_MODE
int main(void) {
    printf("=== Parser Tests ===\n");
    int pass = 0, fail = 0;
    TokenList tokens;
    ParsedIntent intent;

    /* Test 1: Query detection */
    tokenize("What is the capital of France?", &tokens);
    parse_intent(&tokens, &intent);
    if (intent.intent_type == INTENT_QUERY) { printf("PASS: Query detected\n"); pass++; }
    else { printf("FAIL: Expected QUERY, got %s\n", intent_type_name(intent.intent_type)); fail++; }

    /* Test 2: Query subject extraction */
    if (strlen(intent.subject) > 0) { printf("PASS: Subject extracted: '%s'\n", intent.subject); pass++; }
    else { printf("FAIL: No subject extracted\n"); fail++; }

    /* Test 3: Query object extraction */
    if (strlen(intent.object) > 0) { printf("PASS: Object extracted: '%s'\n", intent.object); pass++; }
    else { printf("FAIL: No object extracted\n"); fail++; }

    /* Test 4: Greeting */
    tokenize("Hello there", &tokens);
    parse_intent(&tokens, &intent);
    if (intent.intent_type == INTENT_GREETING) { printf("PASS: Greeting detected\n"); pass++; }
    else { printf("FAIL: Expected GREETING, got %s\n", intent_type_name(intent.intent_type)); fail++; }

    /* Test 5: Command */
    tokenize("/help", &tokens);
    parse_intent(&tokens, &intent);
    if (intent.intent_type == INTENT_COMMAND) { printf("PASS: Command detected\n"); pass++; }
    else { printf("FAIL: Expected COMMAND, got %s\n", intent_type_name(intent.intent_type)); fail++; }

    /* Test 6: Code request */
    tokenize("Write a sort function in Python", &tokens);
    parse_intent(&tokens, &intent);
    if (intent.intent_type == INTENT_CODE_REQUEST) { printf("PASS: Code request detected\n"); pass++; }
    else { printf("FAIL: Expected CODE_REQUEST, got %s\n", intent_type_name(intent.intent_type)); fail++; }

    /* Test 7: Statement */
    tokenize("The sky is blue", &tokens);
    parse_intent(&tokens, &intent);
    if (intent.intent_type == INTENT_STATEMENT) { printf("PASS: Statement detected\n"); pass++; }
    else { printf("FAIL: Expected STATEMENT, got %s\n", intent_type_name(intent.intent_type)); fail++; }

    /* Test 8: Farewell */
    tokenize("goodbye", &tokens);
    parse_intent(&tokens, &intent);
    if (intent.intent_type == INTENT_FAREWELL) { printf("PASS: Farewell detected\n"); pass++; }
    else { printf("FAIL: Expected FAREWELL, got %s\n", intent_type_name(intent.intent_type)); fail++; }

    /* Test 9: Question mark triggers query */
    tokenize("Paris is in France?", &tokens);
    parse_intent(&tokens, &intent);
    if (intent.intent_type == INTENT_QUERY) { printf("PASS: Question mark triggers query\n"); pass++; }
    else { printf("FAIL: Expected QUERY from '?', got %s\n", intent_type_name(intent.intent_type)); fail++; }

    /* Test 10: Teach intent */
    tokenize("Remember that my name is Alex", &tokens);
    parse_intent(&tokens, &intent);
    if (intent.intent_type == INTENT_TEACH) { printf("PASS: Teach intent detected\n"); pass++; }
    else { printf("FAIL: Expected TEACH, got %s\n", intent_type_name(intent.intent_type)); fail++; }

    printf("\n=== Results: %d passed, %d failed ===\n", pass, fail);
    return fail > 0 ? 1 : 0;
}
#endif

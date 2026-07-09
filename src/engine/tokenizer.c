#include "tokenizer.h"
#include <string.h>
#include <ctype.h>
#include <stdio.h>

#define MAX_TOKENS 128

static int is_punctuation(char c) {
    return c == '.' || c == ',' || c == '!' || c == '?' || c == ';' || c == ':';
}

static void lowercase(char *s) {
    for (; *s; ++s) *s = (char)tolower((unsigned char)*s);
}

static void add_token(TokenList *list, TokenType type, const char *val, int len, int pos) {
    if (list->count >= MAX_TOKENS) return;
    Token *t = &list->tokens[list->count];
    t->type = type;
    t->position = pos;
    int n = (len < 255) ? len : 255;
    memcpy(t->value, val, n);
    t->value[n] = '\0';
    if (type == TOKEN_WORD) lowercase(t->value);
    list->count++;
}

int tokenize(const char *input, TokenList *list) {
    if (!input || !list) return -1;
    memset(list, 0, sizeof(TokenList));
    int i = 0, len = (int)strlen(input);

    while (i < len && list->count < MAX_TOKENS) {
        /* skip whitespace */
        while (i < len && isspace((unsigned char)input[i])) i++;
        if (i >= len) break;

        /* quoted string */
        if (input[i] == '"' || input[i] == '\'') {
            char quote = input[i];
            int start = ++i;
            while (i < len && input[i] != quote) i++;
            add_token(list, TOKEN_WORD, &input[start], i - start, start - 1);
            if (i < len) i++; /* skip closing quote */
            continue;
        }

        /* punctuation (single char) */
        if (is_punctuation(input[i])) {
            add_token(list, TOKEN_PUNCTUATION, &input[i], 1, i);
            i++;
            continue;
        }

        /* command (starts with /) */
        if (input[i] == '/') {
            int start = i;
            i++;
            while (i < len && !isspace((unsigned char)input[i]) && !is_punctuation(input[i])) i++;
            add_token(list, TOKEN_COMMAND, &input[start], i - start, start);
            continue;
        }

        /* number (digits, optional decimal) */
        if (isdigit((unsigned char)input[i]) ||
            (input[i] == '-' && i + 1 < len && isdigit((unsigned char)input[i + 1]))) {
            int start = i;
            if (input[i] == '-') i++;
            while (i < len && isdigit((unsigned char)input[i])) i++;
            if (i < len && input[i] == '.' && i + 1 < len && isdigit((unsigned char)input[i + 1])) {
                i++;
                while (i < len && isdigit((unsigned char)input[i])) i++;
            }
            add_token(list, TOKEN_NUMBER, &input[start], i - start, start);
            continue;
        }

        /* word (alphabetic + alphanumeric continuation) */
        if (isalpha((unsigned char)input[i]) || input[i] == '_') {
            int start = i;
            while (i < len && (isalnum((unsigned char)input[i]) || input[i] == '_' || input[i] == '-')) i++;
            add_token(list, TOKEN_WORD, &input[start], i - start, start);
            continue;
        }

        /* unknown: skip character */
        add_token(list, TOKEN_UNKNOWN, &input[i], 1, i);
        i++;
    }

    /* append END token */
    if (list->count < MAX_TOKENS) {
        Token *t = &list->tokens[list->count];
        t->type = TOKEN_END;
        t->value[0] = '\0';
        t->position = i;
        list->count++;
    }
    return list->count;
}

const char *token_type_name(TokenType type) {
    switch (type) {
        case TOKEN_WORD:        return "WORD";
        case TOKEN_NUMBER:      return "NUMBER";
        case TOKEN_PUNCTUATION: return "PUNCTUATION";
        case TOKEN_COMMAND:     return "COMMAND";
        case TOKEN_UNKNOWN:     return "UNKNOWN";
        case TOKEN_END:         return "END";
    }
    return "UNKNOWN";
}

/* ─── TEST MODE ─────────────────────────────────────────────────────── */
#ifdef TEST_MODE

static int tests_passed = 0, tests_total = 0;

static void check(int cond, const char *name) {
    tests_total++;
    if (cond) { printf("  PASS: %s\n", name); tests_passed++; }
    else      { printf("  FAIL: %s\n", name); }
}

int main(void) {
    TokenList tl;

    printf("=== Tokenizer Tests ===\n\n");

    /* Test 1: Basic sentence */
    printf("[1] Basic sentence\n");
    tokenize("Hello world, this is great!", &tl);
    check(tl.tokens[0].type == TOKEN_WORD && strcmp(tl.tokens[0].value, "hello") == 0,
          "first word lowercase");
    check(tl.tokens[1].type == TOKEN_WORD && strcmp(tl.tokens[1].value, "world") == 0,
          "second word");
    check(tl.tokens[2].type == TOKEN_PUNCTUATION && tl.tokens[2].value[0] == ',',
          "comma punctuation");
    check(tl.tokens[6].type == TOKEN_PUNCTUATION && tl.tokens[6].value[0] == '!',
          "exclamation punctuation");
    check(tl.tokens[tl.count - 1].type == TOKEN_END, "ends with END");

    /* Test 2: Command detection */
    printf("[2] Command detection\n");
    tokenize("/help me please", &tl);
    check(tl.tokens[0].type == TOKEN_COMMAND && strcmp(tl.tokens[0].value, "/help") == 0,
          "/help is COMMAND");
    check(tl.tokens[1].type == TOKEN_WORD && strcmp(tl.tokens[1].value, "me") == 0,
          "word after command");

    /* Test 3: Number handling */
    printf("[3] Number handling\n");
    tokenize("I have 42 apples and 3.14 pies", &tl);
    check(tl.tokens[2].type == TOKEN_NUMBER && strcmp(tl.tokens[2].value, "42") == 0,
          "integer 42");
    check(tl.tokens[5].type == TOKEN_NUMBER && strcmp(tl.tokens[5].value, "3.14") == 0,
          "decimal 3.14");

    /* Test 4: Quoted strings */
    printf("[4] Quoted strings\n");
    tokenize("say \"hello world\" now", &tl);
    check(tl.tokens[1].type == TOKEN_WORD && strcmp(tl.tokens[1].value, "hello world") == 0,
          "quoted string as single token");
    check(tl.tokens[2].type == TOKEN_WORD && strcmp(tl.tokens[2].value, "now") == 0,
          "word after quote");

    /* Test 5: Empty input */
    printf("[5] Empty input\n");
    tokenize("", &tl);
    check(tl.count == 1 && tl.tokens[0].type == TOKEN_END, "empty gives only END");
    tokenize("   ", &tl);
    check(tl.count == 1 && tl.tokens[0].type == TOKEN_END, "whitespace gives only END");

    printf("\n=== Results: %d/%d passed ===\n", tests_passed, tests_total);
    return tests_passed == tests_total ? 0 : 1;
}

#endif /* TEST_MODE */

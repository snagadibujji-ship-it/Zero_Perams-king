#ifndef TOKENIZER_H
#define TOKENIZER_H

#include <stdint.h>

typedef enum {
    TOKEN_WORD,
    TOKEN_NUMBER,
    TOKEN_PUNCTUATION,
    TOKEN_COMMAND,
    TOKEN_UNKNOWN,
    TOKEN_END
} TokenType;

typedef struct {
    TokenType type;
    char value[256];
    int position;
} Token;

typedef struct {
    Token tokens[128];
    int count;
} TokenList;

int tokenize(const char *input, TokenList *token_list);
const char *token_type_name(TokenType type);

#endif /* TOKENIZER_H */

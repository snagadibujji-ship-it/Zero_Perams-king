#ifndef PARSER_H
#define PARSER_H

#include "tokenizer.h"

typedef enum {
    INTENT_QUERY,
    INTENT_COMMAND,
    INTENT_STATEMENT,
    INTENT_GREETING,
    INTENT_FAREWELL,
    INTENT_TEACH,
    INTENT_CODE_REQUEST,
    INTENT_AGENT_TASK,
    INTENT_UNKNOWN
} IntentType;

typedef struct {
    IntentType intent_type;
    char subject[256];
    char predicate[256];
    char object[256];
    char raw_input[1024];
    float confidence;
} ParsedIntent;

void parse_intent(TokenList *token_list, ParsedIntent *parsed_intent);
const char* intent_type_name(IntentType type);

#endif /* PARSER_H */

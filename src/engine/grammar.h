#ifndef GRAMMAR_H
#define GRAMMAR_H

#include "parser.h"
#include "knowledge.h"
#include "memory.h"

typedef enum {
    STYLE_CASUAL,
    STYLE_FORMAL,
    STYLE_TECHNICAL,
    STYLE_SIMPLE
} ResponseStyle;

typedef struct {
    char text[2048];
    float confidence;
    ResponseStyle style;
} Response;

int grammar_init(void);
int grammar_generate(const ParsedIntent *intent, const Fact *knowledge_results, int kg_result_count, const WorkingMemory *memory, Response *response);
void grammar_set_style(ResponseStyle style);

#endif /* GRAMMAR_H */

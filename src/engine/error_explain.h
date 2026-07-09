#ifndef ERROR_EXPLAIN_H
#define ERROR_EXPLAIN_H

typedef struct {
    char explanation[512];
    char suggestion[256];
    char category[64];
    int severity;  // 1-5
} ErrorExplanation;

// Explain an error message in human terms
int error_explain(const char* error_text, ErrorExplanation* result);

// Get category name
const char* error_category_name(const char* category);

#endif

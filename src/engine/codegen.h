#ifndef CODEGEN_H
#define CODEGEN_H

typedef enum {
    LANG_PYTHON,
    LANG_C,
    LANG_JAVASCRIPT,
    LANG_BASH,
    LANG_GO,
    LANG_RUST,
    LANG_UNKNOWN
} CodeLanguage;

typedef struct {
    char code[4096];        // Generated code
    CodeLanguage language;  // Target language
    char explanation[512];  // Brief explanation
    int confidence;         // 0-100
} CodeResult;

// Detect language from request
CodeLanguage codegen_detect_language(const char* request);

// Generate code from a natural language description
int codegen_generate(const char* request, CodeLanguage lang, CodeResult* result);

// Get language name string
const char* codegen_language_name(CodeLanguage lang);

#endif

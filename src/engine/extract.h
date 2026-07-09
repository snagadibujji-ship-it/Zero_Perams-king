#ifndef EXTRACT_H
#define EXTRACT_H

#include <stddef.h>

#define MAX_EXTRACT_SUBJECT 128
#define MAX_EXTRACT_VALUE 256

typedef struct {
    char subject[MAX_EXTRACT_SUBJECT];
    char relation[64];
    char object[MAX_EXTRACT_VALUE];
    int confidence;  // 0-100
} ExtractedFact;

typedef struct {
    ExtractedFact* facts;
    int count;
    int capacity;
} ExtractionResult;

// Initialize extraction result buffer
void extract_init(ExtractionResult* result, int initial_capacity);
void extract_free(ExtractionResult* result);

// Extract facts from a single sentence
int extract_sentence(const char* sentence, ExtractionResult* result);

// Extract facts from a block of text (splits into sentences first)
int extract_text(const char* text, ExtractionResult* result);

// Extract facts from a file (line by line)
int extract_file(const char* filepath, ExtractionResult* result);

#endif

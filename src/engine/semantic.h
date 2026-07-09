#ifndef SEMANTIC_H
#define SEMANTIC_H

#define MAX_WORD_LEN 64
#define MAX_SYNONYMS_PER_WORD 8

typedef struct {
    char word[MAX_WORD_LEN];
    char synonyms[MAX_SYNONYMS_PER_WORD][MAX_WORD_LEN];
    int synonym_count;
} SynonymEntry;

typedef struct {
    SynonymEntry* entries;
    int count;
    int capacity;
} SynonymDB;

// Initialize with built-in synonyms
int synonym_init(SynonymDB* db);
void synonym_destroy(SynonymDB* db);

// Find synonyms for a word
int synonym_lookup(SynonymDB* db, const char* word, char results[][MAX_WORD_LEN], int max_results);

// Check if two words are synonyms
int synonym_are_synonyms(SynonymDB* db, const char* a, const char* b);

// Normalize a word (morphology: strip suffixes)
void word_normalize(const char* input, char* output, int max_len);

// Semantic distance (0.0 = same, 1.0 = unrelated)
float word_distance(SynonymDB* db, const char* a, const char* b);

#endif

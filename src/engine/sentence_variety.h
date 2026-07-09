#ifndef SENTENCE_VARIETY_H
#define SENTENCE_VARIETY_H

// Generate an IS_A sentence with variety
int sv_is_a(const char* subject, const char* object, char* out, int maxlen);

// Generate a HAS sentence with variety
int sv_has(const char* subject, const char* property, char* out, int maxlen);

// Generate a CAN/CAPABLE_OF sentence with variety
int sv_can(const char* subject, const char* ability, char* out, int maxlen);

// Generate a USED_FOR sentence with variety
int sv_used_for(const char* subject, const char* purpose, char* out, int maxlen);

// Generate a MADE_OF sentence with variety
int sv_made_of(const char* subject, const char* material, char* out, int maxlen);

// Generate a CAUSES sentence with variety
int sv_causes(const char* subject, const char* effect, char* out, int maxlen);

// Generate a LOCATED_IN sentence with variety
int sv_located_in(const char* subject, const char* location, char* out, int maxlen);

// Generate a list of items with natural English
int sv_list(const char* subject, const char* verb, const char** items, int count, char* out, int maxlen);

// Reset variety tracker (call at start of each response)
void sv_reset(void);

#endif

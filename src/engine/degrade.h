#ifndef DEGRADE_H
#define DEGRADE_H

#include <stddef.h>

typedef enum {
    DEGRADE_FULL = 0,     // All features
    DEGRADE_LIGHT = 1,    // Optimize transparently
    DEGRADE_MODERATE = 2, // Shed non-essential
    DEGRADE_HIGH = 3,     // Essential only
    DEGRADE_SURVIVAL = 4, // Chat only
    DEGRADE_EMERGENCY = 5 // Save and shutdown
} DegradeLevel;

typedef struct {
    DegradeLevel level;
    size_t ram_used_bytes;
    size_t ram_budget_bytes;
    float pressure;        // 0.0-1.0
    int features_disabled;
} DegradeState;

// Initialize with RAM budget
void degrade_init(size_t ram_budget_mb);

// Update current RAM usage and recalculate level
DegradeLevel degrade_update(size_t current_ram_bytes);

// Check if a feature should be active at current level
int degrade_feature_active(const char* feature_name);

// Get current state
DegradeState degrade_get_state(void);

// Format status for display
void degrade_format_status(char* buffer, size_t buflen);

#endif

#include "degrade.h"
#include <stdio.h>
#include <string.h>

typedef struct {
    const char* name;
    DegradeLevel shed_at;  // Level at which this feature is disabled
} FeatureEntry;

static const FeatureEntry feature_table[] = {
    {"self_improve",  DEGRADE_LIGHT},
    {"p2p_sync",     DEGRADE_LIGHT},
    {"voice",        DEGRADE_MODERATE},
    {"multimodal",   DEGRADE_MODERATE},
    {"code_sandbox", DEGRADE_MODERATE},
    {"plugins",      DEGRADE_HIGH},
    {"agent_sub",    DEGRADE_HIGH},
    {"learning",     DEGRADE_SURVIVAL},
    {"codegen",      DEGRADE_SURVIVAL},
};

#define FEATURE_COUNT (sizeof(feature_table) / sizeof(feature_table[0]))

// Never-shed features
static const char* core_features[] = {
    "knowledge", "reasoning", "response", "input"
};
#define CORE_COUNT (sizeof(core_features) / sizeof(core_features[0]))

static DegradeState state = {0};

void degrade_init(size_t ram_budget_mb) {
    state.ram_budget_bytes = ram_budget_mb * 1024 * 1024;
    state.ram_used_bytes = 0;
    state.level = DEGRADE_FULL;
    state.pressure = 0.0f;
    state.features_disabled = 0;
}

DegradeLevel degrade_update(size_t current_ram_bytes) {
    state.ram_used_bytes = current_ram_bytes;
    if (state.ram_budget_bytes == 0) {
        state.pressure = 1.0f;
        state.level = DEGRADE_EMERGENCY;
        return state.level;
    }
    state.pressure = (float)current_ram_bytes / (float)state.ram_budget_bytes;

    if (state.pressure < 0.70f)      state.level = DEGRADE_FULL;
    else if (state.pressure < 0.80f) state.level = DEGRADE_LIGHT;
    else if (state.pressure < 0.90f) state.level = DEGRADE_MODERATE;
    else if (state.pressure < 0.95f) state.level = DEGRADE_HIGH;
    else if (state.pressure < 0.99f) state.level = DEGRADE_SURVIVAL;
    else                             state.level = DEGRADE_EMERGENCY;

    // Count disabled features
    state.features_disabled = 0;
    for (size_t i = 0; i < FEATURE_COUNT; i++) {
        if (state.level >= feature_table[i].shed_at)
            state.features_disabled++;
    }
    return state.level;
}

int degrade_feature_active(const char* feature_name) {
    // Core features are always active
    for (size_t i = 0; i < CORE_COUNT; i++) {
        if (strcmp(feature_name, core_features[i]) == 0)
            return 1;
    }
    // Check feature table
    for (size_t i = 0; i < FEATURE_COUNT; i++) {
        if (strcmp(feature_name, feature_table[i].name) == 0)
            return state.level < feature_table[i].shed_at;
    }
    return 1;  // Unknown features default to active
}

DegradeState degrade_get_state(void) {
    return state;
}

static const char* level_names[] = {
    "FULL", "LIGHT", "MODERATE", "HIGH", "SURVIVAL", "EMERGENCY"
};

void degrade_format_status(char* buffer, size_t buflen) {
    int off = snprintf(buffer, buflen, "[DEGRADE] Level: %s | Pressure: %.1f%% | Disabled: %d/%d",
        level_names[state.level], state.pressure * 100.0f,
        state.features_disabled, (int)FEATURE_COUNT);
    if (off < (int)buflen && state.features_disabled > 0) {
        off += snprintf(buffer + off, buflen - off, " | Shed:");
        for (size_t i = 0; i < FEATURE_COUNT && off < (int)buflen; i++) {
            if (state.level >= feature_table[i].shed_at)
                off += snprintf(buffer + off, buflen - off, " %s", feature_table[i].name);
        }
    }
}

#ifdef TEST_MODE
#include <assert.h>
int main(void) {
    degrade_init(100);  // 100 MB budget
    size_t mb = 1024 * 1024;

    assert(degrade_update(50 * mb) == DEGRADE_FULL);
    assert(degrade_feature_active("self_improve") == 1);

    assert(degrade_update(75 * mb) == DEGRADE_LIGHT);
    assert(degrade_feature_active("self_improve") == 0);
    assert(degrade_feature_active("voice") == 1);

    assert(degrade_update(85 * mb) == DEGRADE_MODERATE);
    assert(degrade_feature_active("voice") == 0);
    assert(degrade_feature_active("plugins") == 1);

    assert(degrade_update(92 * mb) == DEGRADE_HIGH);
    assert(degrade_feature_active("plugins") == 0);
    assert(degrade_feature_active("learning") == 1);

    assert(degrade_update(96 * mb) == DEGRADE_SURVIVAL);
    assert(degrade_feature_active("learning") == 0);
    assert(degrade_feature_active("knowledge") == 1);

    assert(degrade_update(100 * mb) == DEGRADE_EMERGENCY);
    assert(degrade_feature_active("knowledge") == 1);
    assert(degrade_feature_active("reasoning") == 1);

    char buf[256];
    degrade_format_status(buf, sizeof(buf));
    printf("Test passed. Status: %s\n", buf);
    return 0;
}
#endif

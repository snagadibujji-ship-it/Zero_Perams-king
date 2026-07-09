/**
 * personality.c - Phase 10: Adaptive Personality & Mood Detection
 */

#include "personality.h"
#include <stdio.h>
#include <string.h>
#include <ctype.h>

static Personality g_personality = { 0.5f, 0.5f, 0.3f, 0.7f };

static int str_contains_ci(const char *haystack, const char *needle) {
    if (!haystack || !needle) return 0;
    size_t hlen = strlen(haystack);
    size_t nlen = strlen(needle);
    if (nlen > hlen) return 0;
    for (size_t i = 0; i <= hlen - nlen; i++) {
        int match = 1;
        for (size_t j = 0; j < nlen; j++) {
            if (tolower((unsigned char)haystack[i+j]) != tolower((unsigned char)needle[j])) {
                match = 0; break;
            }
        }
        if (match) return 1;
    }
    return 0;
}

void personality_init(void) {
    g_personality.formality = 0.5f;
    g_personality.verbosity = 0.5f;
    g_personality.humor = 0.3f;
    g_personality.empathy = 0.7f;
}

void personality_set(float formality, float verbosity, float humor, float empathy) {
    g_personality.formality = formality;
    g_personality.verbosity = verbosity;
    g_personality.humor = humor;
    g_personality.empathy = empathy;
}

Personality personality_get(void) { return g_personality; }

UserMood mood_detect(const char *text) {
    if (!text) return MOOD_NEUTRAL;

    /* Frustrated keywords */
    static const char *frustrated[] = {
        "ugh", "broken", "won't work", "stupid", "annoying",
        "frustrated", "doesn't work", "hate", "useless", NULL
    };
    for (int i = 0; frustrated[i]; i++) {
        if (str_contains_ci(text, frustrated[i])) return MOOD_FRUSTRATED;
    }

    /* Curious keywords */
    static const char *curious[] = {
        "how does", "what if", "interesting", "curious",
        "wonder", "explain", "why does", NULL
    };
    for (int i = 0; curious[i]; i++) {
        if (str_contains_ci(text, curious[i])) return MOOD_CURIOUS;
    }

    /* Rushed keywords */
    static const char *rushed[] = {
        "quick", "just tell me", "fast", "hurry",
        "short answer", "tldr", "briefly", NULL
    };
    for (int i = 0; rushed[i]; i++) {
        if (str_contains_ci(text, rushed[i])) return MOOD_RUSHED;
    }

    /* Happy keywords */
    static const char *happy[] = {
        "thanks", "great", "awesome", "perfect",
        "love it", "excellent", "nice", NULL
    };
    for (int i = 0; happy[i]; i++) {
        if (str_contains_ci(text, happy[i])) return MOOD_HAPPY;
    }

    /* Confused keywords */
    static const char *confused[] = {
        "confused", "don't understand", "what do you mean",
        "huh", "lost", "unclear", NULL
    };
    for (int i = 0; confused[i]; i++) {
        if (str_contains_ci(text, confused[i])) return MOOD_CONFUSED;
    }

    return MOOD_NEUTRAL;
}

const char *mood_name(UserMood mood) {
    switch (mood) {
        case MOOD_FRUSTRATED: return "frustrated";
        case MOOD_CURIOUS:    return "curious";
        case MOOD_RUSHED:     return "rushed";
        case MOOD_HAPPY:      return "happy";
        case MOOD_CONFUSED:   return "confused";
        default:              return "neutral";
    }
}

void personality_adjust_response(char *response, size_t max_len, UserMood mood) {
    if (!response || max_len == 0) return;
    char prefix[256] = "";
    char suffix[256] = "";

    switch (mood) {
        case MOOD_FRUSTRATED:
            if (g_personality.empathy > 0.5f)
                snprintf(prefix, sizeof(prefix), "I understand the frustration. ");
            break;
        case MOOD_CURIOUS:
            if (g_personality.verbosity > 0.5f)
                snprintf(suffix, sizeof(suffix), " Want me to go deeper on this?");
            break;
        case MOOD_RUSHED:
            /* Trim to first sentence for rushed users */
            {
                char *dot = strchr(response, '.');
                if (dot && (size_t)(dot - response) < max_len - 1) {
                    *(dot + 1) = '\0';
                }
            }
            return;
        case MOOD_HAPPY:
            if (g_personality.humor > 0.5f)
                snprintf(suffix, sizeof(suffix), " Glad I could help!");
            break;
        case MOOD_CONFUSED:
            snprintf(prefix, sizeof(prefix), "Let me clarify: ");
            break;
        default:
            return;
    }

    if (prefix[0] || suffix[0]) {
        char tmp[MAX_RESPONSE_LEN];
        snprintf(tmp, sizeof(tmp), "%s%s%s", prefix, response, suffix);
        strncpy(response, tmp, max_len - 1);
        response[max_len - 1] = '\0';
    }
}

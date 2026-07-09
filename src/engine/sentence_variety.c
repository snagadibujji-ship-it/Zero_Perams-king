#include "sentence_variety.h"
#include <stdio.h>
#include <string.h>
#include <ctype.h>
#include <stdlib.h>
#include <time.h>

/* --- Template arrays --- */

static const char* IS_A_TEMPLATES[] = {
    "%s is %s %s",
    "%s belongs to the %s family",
    "%s is classified as %s %s",
    "%s is a type of %s",
    "As %s %s, %s",
    "%s falls under the category of %s",
};
#define IS_A_COUNT 6

static const char* HAS_TEMPLATES[] = {
    "%s has %s",
    "%s possesses %s",
    "%s is equipped with %s",
    "%s features %s",
    "One notable feature of %s is %s",
    "%s is characterized by %s",
};
#define HAS_COUNT 6

static const char* CAN_TEMPLATES[] = {
    "%s can %s",
    "%s is able to %s",
    "%s is capable of %s",
    "%s has the ability to %s",
    "One remarkable ability of %s is %s",
    "%s is known for being able to %s",
};
#define CAN_COUNT 6

static const char* USED_FOR_TEMPLATES[] = {
    "%s is used for %s",
    "%s is commonly employed for %s",
    "People use %s for %s",
    "The primary purpose of %s is %s",
    "%s serves as a tool for %s",
    "%s is widely used in %s",
};
#define USED_FOR_COUNT 6

static const char* MADE_OF_TEMPLATES[] = {
    "%s is made of %s",
    "%s is composed of %s",
    "%s consists primarily of %s",
    "The main components of %s are %s",
    "%s is constructed from %s",
};
#define MADE_OF_COUNT 5

static const char* CAUSES_TEMPLATES[] = {
    "%s causes %s",
    "%s leads to %s",
    "%s results in %s",
    "%s can produce %s",
    "One effect of %s is %s",
};
#define CAUSES_COUNT 5

static const char* LOCATED_TEMPLATES[] = {
    "%s is located in %s",
    "%s can be found in %s",
    "%s is situated in %s",
    "You can find %s in %s",
    "%s resides in %s",
};
#define LOCATED_COUNT 5

/* --- Variety tracking --- */

enum { T_ISA, T_HAS, T_CAN, T_USED, T_MADE, T_CAUSES, T_LOCATED, T_MAX };
static int last_used[T_MAX] = {-1, -1, -1, -1, -1, -1, -1};
static int seeded = 0;

static void ensure_seed(void) {
    if (!seeded) { srand((unsigned)time(NULL)); seeded = 1; }
}

static int pick(int type, int count) {
    ensure_seed();
    int idx = rand() % count;
    if (count > 1 && idx == last_used[type]) {
        idx = (idx + 1) % count;
    }
    last_used[type] = idx;
    return idx;
}

void sv_reset(void) {
    for (int i = 0; i < T_MAX; i++) last_used[i] = -1;
}

/* --- Helpers --- */

static int is_vowel(char c) {
    c = tolower((unsigned char)c);
    return c == 'a' || c == 'e' || c == 'i' || c == 'o' || c == 'u';
}

/* Write "a"/"an" + word into buf. Returns chars written. */
static int article_word(const char* word, char* buf, int maxlen) {
    const char* art = is_vowel(word[0]) ? "an " : "a ";
    return snprintf(buf, maxlen, "%s%s", art, word);
}

static void capitalize(char* s) {
    if (s && s[0]) s[0] = toupper((unsigned char)s[0]);
}

/* --- Public API --- */

int sv_is_a(const char* subject, const char* object, char* out, int maxlen) {
    int idx = pick(T_ISA, IS_A_COUNT);
    char art_obj[128];
    article_word(object, art_obj, sizeof(art_obj));
    int n = 0;
    switch (idx) {
        case 0: n = snprintf(out, maxlen, IS_A_TEMPLATES[0], subject, is_vowel(object[0]) ? "an" : "a", object); break;
        case 1: n = snprintf(out, maxlen, IS_A_TEMPLATES[1], subject, object); break;
        case 2: n = snprintf(out, maxlen, IS_A_TEMPLATES[2], subject, is_vowel(object[0]) ? "an" : "a", object); break;
        case 3: n = snprintf(out, maxlen, IS_A_TEMPLATES[3], subject, object); break;
        case 4: n = snprintf(out, maxlen, IS_A_TEMPLATES[4], is_vowel(object[0]) ? "an" : "a", object, subject); break;
        case 5: n = snprintf(out, maxlen, IS_A_TEMPLATES[5], subject, object); break;
    }
    capitalize(out);
    return n;
}

int sv_has(const char* subject, const char* property, char* out, int maxlen) {
    int idx = pick(T_HAS, HAS_COUNT);
    int n = snprintf(out, maxlen, HAS_TEMPLATES[idx], subject, property);
    capitalize(out);
    return n;
}

int sv_can(const char* subject, const char* ability, char* out, int maxlen) {
    int idx = pick(T_CAN, CAN_COUNT);
    int n = snprintf(out, maxlen, CAN_TEMPLATES[idx], subject, ability);
    capitalize(out);
    return n;
}

int sv_used_for(const char* subject, const char* purpose, char* out, int maxlen) {
    int idx = pick(T_USED, USED_FOR_COUNT);
    int n = snprintf(out, maxlen, USED_FOR_TEMPLATES[idx], subject, purpose);
    capitalize(out);
    return n;
}

int sv_made_of(const char* subject, const char* material, char* out, int maxlen) {
    int idx = pick(T_MADE, MADE_OF_COUNT);
    int n = snprintf(out, maxlen, MADE_OF_TEMPLATES[idx], subject, material);
    capitalize(out);
    return n;
}

int sv_causes(const char* subject, const char* effect, char* out, int maxlen) {
    int idx = pick(T_CAUSES, CAUSES_COUNT);
    int n = snprintf(out, maxlen, CAUSES_TEMPLATES[idx], subject, effect);
    capitalize(out);
    return n;
}

int sv_located_in(const char* subject, const char* location, char* out, int maxlen) {
    int idx = pick(T_LOCATED, LOCATED_COUNT);
    int n = snprintf(out, maxlen, LOCATED_TEMPLATES[idx], subject, location);
    capitalize(out);
    return n;
}

int sv_list(const char* subject, const char* verb, const char** items, int count, char* out, int maxlen) {
    if (count <= 0) return snprintf(out, maxlen, "%s %s nothing", subject, verb);

    char list_buf[512];
    int pos = 0;

    if (count == 1) {
        pos = snprintf(list_buf, sizeof(list_buf), "%s", items[0]);
    } else if (count == 2) {
        pos = snprintf(list_buf, sizeof(list_buf), "%s and %s", items[0], items[1]);
    } else {
        for (int i = 0; i < count; i++) {
            if (i == count - 1) {
                pos += snprintf(list_buf + pos, sizeof(list_buf) - pos, "and %s", items[i]);
            } else {
                pos += snprintf(list_buf + pos, sizeof(list_buf) - pos, "%s, ", items[i]);
            }
        }
    }

    int n = snprintf(out, maxlen, "%s %s %s", subject, verb, list_buf);
    capitalize(out);
    return n;
}

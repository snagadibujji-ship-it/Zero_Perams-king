/*
 * ast_v.c — Adversarial Self-Tribunal
 * Every answer faces prosecution before delivery.
 * Catches: contradictions, myths, low-confidence speculation delivered as fact.
 */

#include "ast_v.h"
#include "concept.h"
#include <string.h>
#include <stdio.h>
#include <ctype.h>

extern SemanticCore g_semantic_core;

/* ─── Known Myths (commonly believed but false) ─── */
static const char *KNOWN_MYTHS[] = {
    "einstein failed math",
    "great wall visible from space",
    "goldfish memory three seconds",
    "we only use 10 percent of brain",
    "lightning never strikes same place twice",
    "blood is blue inside body",
    "bats are blind",
    "bulls hate red color",
    "sugar causes hyperactivity",
    "cracking knuckles causes arthritis",
    "viking helmets had horns",
    "napoleon was short",
    "tongue has taste zones",
    "chameleons change color to match surroundings",
    "glass is a slow liquid",
    NULL,
};

int ast_is_myth(const char *claim) {
    if (!claim) return 0;
    char lower[512];
    int len = 0;
    for (int i = 0; claim[i] && len < 511; i++)
        lower[len++] = tolower((unsigned char)claim[i]);
    lower[len] = '\0';
    
    for (int i = 0; KNOWN_MYTHS[i]; i++) {
        if (strstr(lower, KNOWN_MYTHS[i])) return 1;
    }
    return 0;
}

/* ─── Prosecution: Find reasons the answer might be WRONG ─── */

static int prosecute(ProofChain *candidate, ASTChallenge *challenges, int max) {
    int count = 0;
    SemanticCore *core = &g_semantic_core;
    
    /* Challenge 1: Low confidence */
    if (candidate->confidence < 0.5f && count < max) {
        ASTChallenge *c = &challenges[count++];
        snprintf(c->challenge, sizeof(c->challenge),
                "Confidence is only %.0f%% — below reliability threshold",
                candidate->confidence * 100);
        c->strength = 0.7f;
        c->upheld = 1;
    }
    
    /* Challenge 2: Not proven */
    if (!candidate->proven && count < max) {
        ASTChallenge *c = &challenges[count++];
        snprintf(c->challenge, sizeof(c->challenge),
                "Answer is not formally proven — speculative derivation");
        c->strength = 0.6f;
        c->upheld = 1;
    }
    
    /* Challenge 3: Myth detection */
    if (ast_is_myth(candidate->answer) && count < max) {
        ASTChallenge *c = &challenges[count++];
        snprintf(c->challenge, sizeof(c->challenge),
                "This matches a known myth — commonly believed but factually incorrect");
        c->strength = 0.95f;
        c->upheld = 1;
    }
    
    /* Challenge 4: Very short chain (might be superficial) */
    if (candidate->step_count <= 1 && candidate->confidence < 0.9f && count < max) {
        ASTChallenge *c = &challenges[count++];
        snprintf(c->challenge, sizeof(c->challenge),
                "Proof chain has only %d step(s) — may be superficial", candidate->step_count);
        c->strength = 0.3f;
        c->upheld = 0;
    }
    
    return count;
}

/* ─── Defense: Counter the prosecution's challenges ─── */

static void defend(ProofChain *candidate, ASTChallenge *challenges, int count) {
    for (int i = 0; i < count; i++) {
        /* Defense against low confidence: if source is direct lookup, confidence is fine */
        if (challenges[i].strength < 0.5f) {
            challenges[i].upheld = 0;  /* Weak challenge dismissed */
        }
        
        /* Defense against "not proven": if confidence > 0.7 from derive, it's acceptable */
        if (candidate->confidence > 0.7f && !candidate->proven) {
            if (strstr(challenges[i].challenge, "not formally proven")) {
                challenges[i].upheld = 0;  /* High-confidence derivation is acceptable */
            }
        }
        
        /* No defense against myth detection — always upheld */
    }
}

/* ─── Judge: Final verdict ─── */

ASTResult ast_evaluate(ProofChain *candidate) {
    ASTResult result;
    memset(&result, 0, sizeof(result));
    result.original = *candidate;
    
    /* Phase 1: Prosecution */
    result.challenge_count = prosecute(candidate, result.challenges, 4);
    
    /* Phase 2: Defense */
    defend(candidate, result.challenges, result.challenge_count);
    
    /* Phase 3: Judgment */
    int upheld_challenges = 0;
    float max_challenge_strength = 0;
    for (int i = 0; i < result.challenge_count; i++) {
        if (result.challenges[i].upheld) {
            upheld_challenges++;
            if (result.challenges[i].strength > max_challenge_strength)
                max_challenge_strength = result.challenges[i].strength;
        }
    }
    
    /* Myth detected → BLOCK */
    if (ast_is_myth(candidate->answer)) {
        result.verdict = VERDICT_BLOCKED;
        result.final_confidence = 0.0f;
        snprintf(result.final_answer, sizeof(result.final_answer),
                "This is a common misconception. The claim is not supported by evidence.");
        snprintf(result.judgment_reason, sizeof(result.judgment_reason),
                "BLOCKED: Known myth detected. Not delivering false information.");
        return result;
    }
    
    /* Strong challenges upheld → UNCERTAIN */
    if (upheld_challenges >= 2 || max_challenge_strength > 0.8f) {
        result.verdict = VERDICT_UNCERTAIN;
        result.final_confidence = candidate->confidence * 0.5f;
        snprintf(result.final_answer, sizeof(result.final_answer),
                "%s (Note: I'm not fully confident in this answer.)", candidate->answer);
        snprintf(result.judgment_reason, sizeof(result.judgment_reason),
                "UNCERTAIN: %d challenges upheld. Answer delivered with caveat.", upheld_challenges);
        return result;
    }
    
    /* Minor challenges only → CONFIRMED with possible revision */
    if (upheld_challenges == 1 && max_challenge_strength < 0.6f) {
        result.verdict = VERDICT_CONFIRMED;
        result.final_confidence = candidate->confidence * 0.9f;
        strncpy(result.final_answer, candidate->answer, sizeof(result.final_answer) - 1);
        snprintf(result.judgment_reason, sizeof(result.judgment_reason),
                "CONFIRMED: Minor challenge noted but answer holds.");
        return result;
    }
    
    /* No challenges or all dismissed → CONFIRMED */
    result.verdict = VERDICT_CONFIRMED;
    result.final_confidence = candidate->confidence;
    strncpy(result.final_answer, candidate->answer, sizeof(result.final_answer) - 1);
    snprintf(result.judgment_reason, sizeof(result.judgment_reason),
            "CONFIRMED: All challenges dismissed. Answer is solid.");
    return result;
}

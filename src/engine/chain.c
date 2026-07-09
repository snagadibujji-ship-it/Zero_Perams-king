/*
 * chain.c — Causal Chain BFS Engine
 *
 * Performs breadth-first search through CAUSES relations in the semantic graph.
 * Confidence decays 0.85 per hop. Max 10 hops.
 * Returns the chain of concept IDs traversed from cause to effect.
 */

#include "derive.h"
#include <string.h>
#include <stdio.h>

extern SemanticCore g_semantic_core;

#define MAX_CHAIN_HOPS  10
#define DECAY_FACTOR    0.85f
#define MAX_BFS_QUEUE   256

/* ─── BFS State ──────────────────────────────────────────────── */

typedef struct {
    uint32_t id;
    int parent_idx;   /* index in visited[] of parent, -1 for root */
    int depth;
    float confidence;
} BFSNode;

/* ─── derive_causal: BFS from cause_id to effect_id ──────────── */

DeriveResult derive_causal(uint32_t cause_id, uint32_t effect_id, int max_hops)
{
    DeriveResult result;
    memset(&result, 0, sizeof(result));
    result.derivation_type = DERIVE_CAUSAL;
    result.confidence = 0.0f;

    SemanticCore *core = &g_semantic_core;

    if (max_hops <= 0 || max_hops > MAX_CHAIN_HOPS)
        max_hops = MAX_CHAIN_HOPS;

    /* BFS queue and visited set */
    BFSNode queue[MAX_BFS_QUEUE];
    int visited_ids[MAX_BFS_QUEUE];
    int queue_head = 0;
    int queue_tail = 0;
    int visited_count = 0;

    /* Seed with cause */
    queue[queue_tail].id = cause_id;
    queue[queue_tail].parent_idx = -1;
    queue[queue_tail].depth = 0;
    queue[queue_tail].confidence = 1.0f;
    queue_tail++;
    visited_ids[visited_count++] = (int)cause_id;

    while (queue_head < queue_tail) {
        BFSNode current = queue[queue_head++];

        /* Check if we reached the target */
        if (current.id == effect_id && current.depth > 0) {
            /* Reconstruct chain by walking parent indices */
            result.confidence = current.confidence;
            result.hops = current.depth;

            /* Walk backwards to build chain */
            uint32_t chain_rev[16];
            int chain_len = 0;
            int idx = queue_head - 1;
            while (idx >= 0 && chain_len < 16) {
                chain_rev[chain_len++] = queue[idx].id;
                idx = queue[idx].parent_idx;
            }

            /* Reverse into result */
            result.chain_len = chain_len;
            for (int i = 0; i < chain_len; i++)
                result.chain[i] = chain_rev[chain_len - 1 - i];

            /* Build explanation */
            const char *cause_name = semantic_get_name(core, cause_id);
            const char *effect_name = semantic_get_name(core, effect_id);
            if (cause_name && effect_name) {
                if (result.chain_len <= 2) {
                    snprintf(result.answer, sizeof(result.answer),
                             "This happens because %s causes %s.",
                             cause_name, effect_name);
                } else {
                    /* Multi-hop: A causes B, which causes C */
                    int written = snprintf(result.answer, sizeof(result.answer),
                                           "This happens because %s causes ", cause_name);
                    for (int i = 1; i < result.chain_len && written < (int)sizeof(result.answer) - 64; i++) {
                        const char *step = semantic_get_name(core, result.chain[i]);
                        if (!step) step = "?";
                        if (i == result.chain_len - 1) {
                            written += snprintf(result.answer + written,
                                                sizeof(result.answer) - (size_t)written,
                                                "%s.", step);
                        } else {
                            written += snprintf(result.answer + written,
                                                sizeof(result.answer) - (size_t)written,
                                                "%s, which causes ", step);
                        }
                    }
                }
            }
            return result;
        }

        /* Don't expand past max hops */
        if (current.depth >= max_hops)
            continue;

        /* Expand: get all CAUSES relations from current node */
        uint32_t targets[MAX_RELATIONS];
        int rel_count = semantic_get_relations(core, current.id, REL_CAUSES, targets, MAX_RELATIONS);

        for (int i = 0; i < rel_count && queue_tail < MAX_BFS_QUEUE; i++) {
            /* Check if already visited */
            int already_visited = 0;
            for (int v = 0; v < visited_count; v++) {
                if (visited_ids[v] == (int)targets[i]) {
                    already_visited = 1;
                    break;
                }
            }
            if (already_visited) continue;

            /* Add to queue */
            queue[queue_tail].id = targets[i];
            queue[queue_tail].parent_idx = queue_head - 1;
            queue[queue_tail].depth = current.depth + 1;
            queue[queue_tail].confidence = current.confidence * DECAY_FACTOR;
            queue_tail++;

            visited_ids[visited_count++] = (int)targets[i];
            if (visited_count >= MAX_BFS_QUEUE) break;
        }
    }

    /* No path found — return low-confidence partial result */
    if (queue_tail > 1) {
        const char *cause_name = semantic_get_name(core, cause_id);
        const char *effect_name = semantic_get_name(core, effect_id);
        if (cause_name && effect_name) {
            snprintf(result.answer, sizeof(result.answer),
                     "No direct causal path found between %s and %s.",
                     cause_name, effect_name);
        }
        result.confidence = 0.1f;
    }

    return result;
}

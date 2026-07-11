/*
 * sokt.c — Self-Organizing Knowledge Topology
 * The knowledge graph physically reorganizes based on access patterns.
 * Hot concepts cluster in cache-friendly zones.
 */

#include "sokt.h"
#include <string.h>
#include <stdio.h>

void sokt_init(SOKTIndex *idx) {
    memset(idx, 0, sizeof(SOKTIndex));
}

void sokt_record_access(SOKTIndex *idx, uint32_t concept_id) {
    idx->current_turn++;
    
    /* Record in last-accessed ring buffer */
    idx->last_accessed[idx->last_idx % 4] = concept_id;
    idx->last_idx++;
    
    /* Co-access: pair with previous accesses */
    for (int i = 0; i < 4; i++) {
        uint32_t prev = idx->last_accessed[i];
        if (prev && prev != concept_id) {
            sokt_record_coaccess(idx, concept_id, prev);
        }
    }
    
    /* Check if already in nuclear zone */
    for (int i = 0; i < idx->nuclear_count; i++) {
        if (idx->nuclear[i].concept_id == concept_id) {
            idx->nuclear[i].access_count++;
            idx->nuclear[i].last_access = idx->current_turn;
            return;
        }
    }
    
    /* Check plasma zone */
    for (int i = 0; i < idx->plasma_count; i++) {
        if (idx->plasma[i].concept_id == concept_id) {
            idx->plasma[i].access_count++;
            idx->plasma[i].last_access = idx->current_turn;
            /* Promote to nuclear if hot enough */
            if (idx->plasma[i].access_count > 5 && idx->nuclear_count < SOKT_NUCLEAR_SIZE) {
                idx->nuclear[idx->nuclear_count++] = idx->plasma[i];
                /* Remove from plasma */
                idx->plasma[i] = idx->plasma[--idx->plasma_count];
            }
            return;
        }
    }
    
    /* New concept — add to plasma */
    if (idx->plasma_count < SOKT_PLASMA_SIZE) {
        SOKTEntry e = {concept_id, 1, idx->current_turn};
        idx->plasma[idx->plasma_count++] = e;
    }
}

void sokt_record_coaccess(SOKTIndex *idx, uint32_t id_a, uint32_t id_b) {
    /* Find or assign matrix slots */
    int slot_a = -1, slot_b = -1;
    
    for (int i = 0; i < idx->coaccess_count; i++) {
        if (idx->coaccess_ids[i] == id_a) slot_a = i;
        if (idx->coaccess_ids[i] == id_b) slot_b = i;
    }
    
    if (slot_a < 0 && idx->coaccess_count < SOKT_COACCESS_DIM) {
        slot_a = idx->coaccess_count;
        idx->coaccess_ids[idx->coaccess_count++] = id_a;
    }
    if (slot_b < 0 && idx->coaccess_count < SOKT_COACCESS_DIM) {
        slot_b = idx->coaccess_count;
        idx->coaccess_ids[idx->coaccess_count++] = id_b;
    }
    
    if (slot_a >= 0 && slot_b >= 0) {
        /* Saturating increment */
        if (idx->coaccess[slot_a][slot_b] < 255) idx->coaccess[slot_a][slot_b]++;
        if (idx->coaccess[slot_b][slot_a] < 255) idx->coaccess[slot_b][slot_a]++;
    }
}

int sokt_is_nuclear(SOKTIndex *idx, uint32_t concept_id) {
    for (int i = 0; i < idx->nuclear_count; i++) {
        if (idx->nuclear[i].concept_id == concept_id) return 1;
    }
    return 0;
}

int sokt_is_plasma(SOKTIndex *idx, uint32_t concept_id) {
    for (int i = 0; i < idx->plasma_count; i++) {
        if (idx->plasma[i].concept_id == concept_id) return 1;
    }
    return 0;
}

void sokt_rebalance(SOKTIndex *idx) {
    /* Demote cold nuclear entries to plasma */
    uint32_t threshold = idx->current_turn > 100 ? idx->current_turn - 100 : 0;
    
    for (int i = idx->nuclear_count - 1; i >= 0; i--) {
        if (idx->nuclear[i].last_access < threshold && idx->nuclear[i].access_count < 3) {
            /* Demote to plasma */
            if (idx->plasma_count < SOKT_PLASMA_SIZE) {
                idx->plasma[idx->plasma_count++] = idx->nuclear[i];
            }
            idx->nuclear[i] = idx->nuclear[--idx->nuclear_count];
        }
    }
    
    /* Promote hot plasma to nuclear */
    for (int i = idx->plasma_count - 1; i >= 0; i--) {
        if (idx->plasma[i].access_count > 10 && idx->nuclear_count < SOKT_NUCLEAR_SIZE) {
            idx->nuclear[idx->nuclear_count++] = idx->plasma[i];
            idx->plasma[i] = idx->plasma[--idx->plasma_count];
        }
    }
    
    /* Decay old access counts (exponential decay) */
    for (int i = 0; i < idx->plasma_count; i++) {
        if (idx->plasma[i].last_access < threshold) {
            idx->plasma[i].access_count = idx->plasma[i].access_count * 3 / 4;
        }
    }
}

void sokt_get_prefetch_hints(SOKTIndex *idx, uint32_t concept_id, uint32_t *hints, int *count) {
    *count = 0;
    
    /* Find this concept in coaccess matrix */
    int slot = -1;
    for (int i = 0; i < idx->coaccess_count; i++) {
        if (idx->coaccess_ids[i] == concept_id) { slot = i; break; }
    }
    
    if (slot < 0) return;
    
    /* Find top-3 co-accessed concepts */
    for (int pass = 0; pass < 3 && *count < 3; pass++) {
        uint8_t max_val = 0;
        int max_idx = -1;
        for (int j = 0; j < idx->coaccess_count; j++) {
            if (j == slot) continue;
            uint8_t val = idx->coaccess[slot][j];
            if (val > max_val) {
                /* Check not already in hints */
                int dup = 0;
                for (int k = 0; k < *count; k++) {
                    if (hints[k] == idx->coaccess_ids[j]) { dup = 1; break; }
                }
                if (!dup) { max_val = val; max_idx = j; }
            }
        }
        if (max_idx >= 0 && max_val > 2) {
            hints[(*count)++] = idx->coaccess_ids[max_idx];
        } else break;
    }
}

void sokt_stats(SOKTIndex *idx) {
    printf("SOKT Topology Stats:\n");
    printf("  Nuclear zone:  %d/%d concepts\n", idx->nuclear_count, SOKT_NUCLEAR_SIZE);
    printf("  Plasma zone:   %d/%d concepts\n", idx->plasma_count, SOKT_PLASMA_SIZE);
    printf("  Co-access dim: %d/%d tracked\n", idx->coaccess_count, SOKT_COACCESS_DIM);
    printf("  Total turns:   %u\n", idx->current_turn);
}

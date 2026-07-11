/*
 * cuq.c — Calibrated Uncertainty Quantification
 * Makes confidence scores MEANINGFUL. Self-adjusts over time.
 * Impossible for LLMs: they have no separate confidence mechanism.
 */

#include "cuq.h"
#include <string.h>
#include <stdio.h>
#include <math.h>

void cuq_init(CUQState *state) {
    memset(state, 0, sizeof(CUQState));
    /* Start with neutral adjustments (1.0 = no change) */
    for (int i = 0; i < CUQ_BINS; i++)
        state->adjustment[i] = 1.0f;
}

float cuq_calibrate(CUQState *state, float raw_confidence) {
    /* Apply learned adjustment to raw confidence */
    if (raw_confidence < 0) raw_confidence = 0;
    if (raw_confidence > 1) raw_confidence = 1;
    
    int bin = (int)(raw_confidence * CUQ_BINS);
    if (bin >= CUQ_BINS) bin = CUQ_BINS - 1;
    
    float adjusted = raw_confidence * state->adjustment[bin];
    if (adjusted > 1.0f) adjusted = 1.0f;
    if (adjusted < 0.0f) adjusted = 0.0f;
    
    return adjusted;
}

void cuq_record_outcome(CUQState *state, float predicted_conf, int was_correct) {
    /* Record a prediction and its outcome */
    state->total_predictions++;
    if (was_correct) state->total_correct++;
    
    int bin = (int)(predicted_conf * CUQ_BINS);
    if (bin >= CUQ_BINS) bin = CUQ_BINS - 1;
    
    state->predictions[bin]++;
    if (was_correct) state->correct[bin]++;
    
    /* Update calibration for this bin */
    if (state->predictions[bin] > 0) {
        state->calibration[bin] = (float)state->correct[bin] / state->predictions[bin];
    }
    
    /* Add to rolling history */
    state->predicted_conf[state->history_pos % CUQ_HISTORY] = predicted_conf;
    state->actual_correct[state->history_pos % CUQ_HISTORY] = was_correct;
    state->history_pos++;
    if (state->history_count < CUQ_HISTORY) state->history_count++;
    
    /* Recompute Brier score */
    float brier_sum = 0;
    int n = state->history_count;
    for (int i = 0; i < n; i++) {
        float diff = state->predicted_conf[i] - (float)state->actual_correct[i];
        brier_sum += diff * diff;
    }
    state->brier_score = n > 0 ? brier_sum / n : 0;
    
    /* Auto-recalibrate every 100 predictions */
    if (state->total_predictions % 100 == 0) {
        cuq_recalibrate(state);
    }
}

void cuq_recalibrate(CUQState *state) {
    /* Adjust confidence factors based on actual vs predicted accuracy */
    for (int i = 0; i < CUQ_BINS; i++) {
        if (state->predictions[i] < 5) continue;  /* Not enough data */
        
        float predicted_avg = (float)(i + 0.5f) / CUQ_BINS;  /* Bin center */
        float actual_accuracy = state->calibration[i];
        
        /* If we predict 80% but only get 60% correct → adjust down */
        if (predicted_avg > 0.01f) {
            state->adjustment[i] = actual_accuracy / predicted_avg;
            /* Clamp to prevent wild swings */
            if (state->adjustment[i] > 1.5f) state->adjustment[i] = 1.5f;
            if (state->adjustment[i] < 0.5f) state->adjustment[i] = 0.5f;
        }
    }
}

float cuq_get_ece(CUQState *state) {
    /* Expected Calibration Error: weighted average of |accuracy - confidence| per bin */
    float ece = 0;
    int total = state->total_predictions;
    if (total == 0) return 0;
    
    for (int i = 0; i < CUQ_BINS; i++) {
        if (state->predictions[i] == 0) continue;
        float bin_conf = (float)(i + 0.5f) / CUQ_BINS;
        float bin_acc = state->calibration[i];
        float weight = (float)state->predictions[i] / total;
        ece += weight * fabsf(bin_acc - bin_conf);
    }
    return ece;
}

float cuq_get_brier(CUQState *state) {
    return state->brier_score;
}

void cuq_stats(CUQState *state, char *buf, int max) {
    int pos = 0;
    pos += snprintf(buf + pos, max - pos, "CUQ Calibration: ECE=%.3f, Brier=%.3f, N=%d\n",
                   cuq_get_ece(state), state->brier_score, state->total_predictions);
    pos += snprintf(buf + pos, max - pos, "Per-bin accuracy:\n");
    for (int i = 0; i < CUQ_BINS; i++) {
        if (state->predictions[i] > 0) {
            pos += snprintf(buf + pos, max - pos, "  %d-%d%%: predicted=%.0f%% actual=%.0f%% (n=%d) adj=%.2f\n",
                           i * 10, (i + 1) * 10,
                           (float)(i + 0.5f) * 10,
                           state->calibration[i] * 100,
                           state->predictions[i],
                           state->adjustment[i]);
        }
    }
}

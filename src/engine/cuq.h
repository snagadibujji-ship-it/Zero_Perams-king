#ifndef CUQ_H
#define CUQ_H

#include <stdint.h>

/*
 * CUQ — Calibrated Uncertainty Quantification
 * When we say "90% confident" we are correct EXACTLY 90% of the time.
 * Self-calibrating: tracks predictions vs outcomes, adjusts automatically.
 */

#define CUQ_BINS 10  /* 10 confidence bins: 0-10%, 10-20%, ... 90-100% */
#define CUQ_HISTORY 1000

typedef struct {
    /* Calibration tracking per bin */
    int predictions[CUQ_BINS];     /* How many predictions in each bin */
    int correct[CUQ_BINS];         /* How many were correct */
    float calibration[CUQ_BINS];   /* Actual accuracy per bin */
    
    /* Running history */
    float predicted_conf[CUQ_HISTORY];
    int actual_correct[CUQ_HISTORY];
    int history_count;
    int history_pos;
    
    /* Adjustment factors */
    float adjustment[CUQ_BINS];    /* Multiply raw confidence by this */
    
    /* Global stats */
    int total_predictions;
    int total_correct;
    float brier_score;             /* Lower = better calibration (0 = perfect) */
    float ece;                     /* Expected Calibration Error */
} CUQState;

/* API */
void cuq_init(CUQState *state);
float cuq_calibrate(CUQState *state, float raw_confidence);  /* Adjust confidence */
void cuq_record_outcome(CUQState *state, float predicted_conf, int was_correct);
void cuq_recalibrate(CUQState *state);  /* Recompute adjustment factors */
float cuq_get_ece(CUQState *state);     /* Expected Calibration Error */
float cuq_get_brier(CUQState *state);   /* Brier score */
void cuq_stats(CUQState *state, char *buf, int max);

#endif

#ifndef METRICS_H
#define METRICS_H

#include <stddef.h>
#include <time.h>

typedef struct {
    // Performance
    double avg_response_ms;
    double total_response_ms;
    int response_count;
    double fastest_ms;
    double slowest_ms;
    
    // Quality  
    int queries_answered;
    int queries_unanswered;  // gaps
    int corrections_received;
    int facts_taught;
    
    // Usage
    int total_messages;
    int commands_executed;
    int agent_tasks_run;
    int agent_tasks_failed;
    
    // System
    time_t start_time;
    size_t peak_memory_bytes;
    int sessions_count;
} Metrics;

void metrics_init(void);
void metrics_record_response(double duration_ms);
void metrics_record_query(int answered);  // 1=answered, 0=gap
void metrics_record_correction(void);
void metrics_record_teach(void);
void metrics_record_command(void);
void metrics_record_agent_task(int success);  // 1=success, 0=fail
void metrics_record_message(void);

Metrics* metrics_get(void);
void metrics_format_dashboard(char* buffer, size_t buflen);
void metrics_reset(void);

#endif

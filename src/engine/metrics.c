#include "metrics.h"
#include <stdio.h>
#include <string.h>
#include <float.h>

static Metrics g_metrics;

void metrics_init(void) {
    memset(&g_metrics, 0, sizeof(Metrics));
    g_metrics.fastest_ms = DBL_MAX;
    g_metrics.slowest_ms = 0.0;
    g_metrics.start_time = time(NULL);
    g_metrics.sessions_count = 1;
}

void metrics_record_response(double duration_ms) {
    g_metrics.response_count++;
    g_metrics.total_response_ms += duration_ms;
    g_metrics.avg_response_ms = g_metrics.total_response_ms / g_metrics.response_count;
    if (duration_ms < g_metrics.fastest_ms) g_metrics.fastest_ms = duration_ms;
    if (duration_ms > g_metrics.slowest_ms) g_metrics.slowest_ms = duration_ms;
}

void metrics_record_query(int answered) {
    if (answered) g_metrics.queries_answered++;
    else g_metrics.queries_unanswered++;
}

void metrics_record_correction(void) { g_metrics.corrections_received++; }
void metrics_record_teach(void) { g_metrics.facts_taught++; }
void metrics_record_command(void) { g_metrics.commands_executed++; }

void metrics_record_agent_task(int success) {
    if (success) g_metrics.agent_tasks_run++;
    else g_metrics.agent_tasks_failed++;
}

void metrics_record_message(void) { g_metrics.total_messages++; }

Metrics* metrics_get(void) { return &g_metrics; }

void metrics_format_dashboard(char* buffer, size_t buflen) {
    time_t now = time(NULL);
    long uptime = (long)difftime(now, g_metrics.start_time);
    int hrs = (int)(uptime / 3600);
    int mins = (int)((uptime % 3600) / 60);
    int secs = (int)(uptime % 60);

    int total_queries = g_metrics.queries_answered + g_metrics.queries_unanswered;
    int pct = total_queries > 0 ? (g_metrics.queries_answered * 100 / total_queries) : 0;

    int total_agent = g_metrics.agent_tasks_run + g_metrics.agent_tasks_failed;

    double fastest = g_metrics.fastest_ms == DBL_MAX ? 0.0 : g_metrics.fastest_ms;

    snprintf(buffer, buflen,
        "\xe2\x94\x8c\xe2\x94\x80 System Dashboard \xe2\x94\x80\xe2\x94\x80\xe2\x94\x80\xe2\x94\x80\xe2\x94\x80\xe2\x94\x80\xe2\x94\x80\xe2\x94\x80\xe2\x94\x80\xe2\x94\x80\xe2\x94\x80\xe2\x94\x80\xe2\x94\x80\xe2\x94\x80\xe2\x94\x80\xe2\x94\x80\xe2\x94\x80\xe2\x94\x80\xe2\x94\x80\xe2\x94\x80\xe2\x94\x80\xe2\x94\x80\xe2\x94\x80\xe2\x94\x90\n"
        "\xe2\x94\x82 Performance:                          \xe2\x94\x82\n"
        "\xe2\x94\x82   Avg response:  %.1f ms             \xe2\x94\x82\n"
        "\xe2\x94\x82   Fastest:       %.1f ms              \xe2\x94\x82\n"
        "\xe2\x94\x82   Slowest:       %.1f ms             \xe2\x94\x82\n"
        "\xe2\x94\x82 Quality:                              \xe2\x94\x82\n"
        "\xe2\x94\x82   Answered: %d/%d (%d%%)              \xe2\x94\x82\n"
        "\xe2\x94\x82   Gaps: %d  Corrections: %d           \xe2\x94\x82\n"
        "\xe2\x94\x82   Facts taught: %d                    \xe2\x94\x82\n"
        "\xe2\x94\x82 Usage:                                \xe2\x94\x82\n"
        "\xe2\x94\x82   Messages: %d  Commands: %d        \xe2\x94\x82\n"
        "\xe2\x94\x82   Agent tasks: %d (%d ok, %d fail)     \xe2\x94\x82\n"
        "\xe2\x94\x82 Uptime: %02d:%02d:%02d                      \xe2\x94\x82\n"
        "\xe2\x94\x94\xe2\x94\x80\xe2\x94\x80\xe2\x94\x80\xe2\x94\x80\xe2\x94\x80\xe2\x94\x80\xe2\x94\x80\xe2\x94\x80\xe2\x94\x80\xe2\x94\x80\xe2\x94\x80\xe2\x94\x80\xe2\x94\x80\xe2\x94\x80\xe2\x94\x80\xe2\x94\x80\xe2\x94\x80\xe2\x94\x80\xe2\x94\x80\xe2\x94\x80\xe2\x94\x80\xe2\x94\x80\xe2\x94\x80\xe2\x94\x80\xe2\x94\x80\xe2\x94\x80\xe2\x94\x80\xe2\x94\x80\xe2\x94\x80\xe2\x94\x80\xe2\x94\x80\xe2\x94\x80\xe2\x94\x80\xe2\x94\x80\xe2\x94\x80\xe2\x94\x80\xe2\x94\x80\xe2\x94\x80\xe2\x94\x80\xe2\x94\x80\xe2\x94\x80\xe2\x94\x98\n",
        g_metrics.avg_response_ms, fastest, g_metrics.slowest_ms,
        g_metrics.queries_answered, total_queries, pct,
        g_metrics.queries_unanswered, g_metrics.corrections_received,
        g_metrics.facts_taught,
        g_metrics.total_messages, g_metrics.commands_executed,
        total_agent, g_metrics.agent_tasks_run, g_metrics.agent_tasks_failed,
        hrs, mins, secs);
}

void metrics_reset(void) {
    time_t start = g_metrics.start_time;
    int sessions = g_metrics.sessions_count;
    memset(&g_metrics, 0, sizeof(Metrics));
    g_metrics.fastest_ms = DBL_MAX;
    g_metrics.start_time = start;
    g_metrics.sessions_count = sessions + 1;
}

/* ─── TEST MODE ─── */
#ifdef TEST_MODE
#include <assert.h>

int main(void) {
    printf("metrics: running tests...\n");

    metrics_init();
    Metrics* m = metrics_get();
    assert(m->response_count == 0);
    assert(m->total_messages == 0);

    // Test response recording
    metrics_record_response(10.0);
    metrics_record_response(20.0);
    assert(m->response_count == 2);
    assert(m->avg_response_ms == 15.0);
    assert(m->fastest_ms == 10.0);
    assert(m->slowest_ms == 20.0);

    // Test query recording
    metrics_record_query(1);
    metrics_record_query(1);
    metrics_record_query(0);
    assert(m->queries_answered == 2);
    assert(m->queries_unanswered == 1);

    // Test other counters
    metrics_record_correction();
    metrics_record_teach();
    metrics_record_command();
    metrics_record_message();
    metrics_record_agent_task(1);
    metrics_record_agent_task(0);
    assert(m->corrections_received == 1);
    assert(m->facts_taught == 1);
    assert(m->commands_executed == 1);
    assert(m->total_messages == 1);
    assert(m->agent_tasks_run == 1);
    assert(m->agent_tasks_failed == 1);

    // Test dashboard format
    char buf[2048];
    metrics_format_dashboard(buf, sizeof(buf));
    assert(strstr(buf, "Dashboard") != NULL);
    assert(strstr(buf, "Performance") != NULL);

    // Test reset
    metrics_reset();
    assert(m->response_count == 0);
    assert(m->total_messages == 0);
    assert(m->sessions_count == 2);

    printf("metrics: all tests passed!\n");
    return 0;
}
#endif

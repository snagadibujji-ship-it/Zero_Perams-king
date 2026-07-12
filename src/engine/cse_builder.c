/* cse_builder.c — Standalone tool to build CSE binary from triples file */
#include "cse.h"
#include <stdio.h>
#include <string.h>

int main(int argc, char **argv) {
    if (argc < 3) {
        fprintf(stderr, "Usage: cse_builder <input.triples> <output.cse>\n");
        fprintf(stderr, "Input format: subject|relation|object|confidence (one per line)\n");
        return 1;
    }

    CSEDatabase db;
    memset(&db, 0, sizeof(db));

    printf("Building CSE database from: %s\n", argv[1]);
    int result = cse_build(&db, argv[1], argv[2]);
    
    if (result < 0) {
        fprintf(stderr, "Error: Failed to build CSE database\n");
        return 1;
    }

    CSEStats stats = cse_stats(&db);
    printf("\n=== CSE Build Complete ===\n");
    printf("  Facts:    %u\n", stats.total_facts);
    printf("  Strings:  %u\n", stats.total_strings);
    printf("  Clusters: %u\n", stats.total_clusters);
    printf("  Hot:      %u facts\n", stats.hot_facts);
    printf("  Warm:     %u facts\n", stats.warm_facts);
    printf("  Memory:   %zu bytes (%.1f KB)\n", stats.memory_bytes, stats.memory_bytes / 1024.0);
    printf("  Output:   %s\n", argv[2]);

    cse_close(&db);
    return 0;
}

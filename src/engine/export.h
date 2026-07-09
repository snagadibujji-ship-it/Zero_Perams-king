#ifndef EXPORT_H
#define EXPORT_H

#include "knowledge.h"

#define EXPORT_MAGIC 0x48414942  // "HAIB" - Hybrid AI Brain
#define EXPORT_VERSION 1

// Export the entire knowledge graph to a portable file
int export_brain(KnowledgeGraph* kg, const char* filepath);

// Import a brain file into the knowledge graph
int import_brain(KnowledgeGraph* kg, const char* filepath);

// Export just learned facts (since last export)
int export_learned(KnowledgeGraph* kg, const char* filepath);

// Get export file info without importing
int export_info(const char* filepath, int* fact_count, int* version);

#endif

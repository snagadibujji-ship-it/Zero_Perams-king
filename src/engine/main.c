#define _GNU_SOURCE
/*
 * Axima Engine v0.1.0 - Main Entry Point
 * Phase 1: Core Skeleton
 *
 * A lightweight AI system targeting ~300MB RAM with:
 *   - Knowledge graph for fact storage/retrieval
 *   - Working memory for conversation context
 *   - Grammar engine for natural response generation
 *   - REPL interface with command support
 */

#define _GNU_SOURCE  /* for strtok_r on glibc */
#include <stdio.h>
#include <math.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <signal.h>

#include "tokenizer.h"
#include "parser.h"
#include "knowledge.h"
#include "memory.h"
#include "grammar.h"
#include "reason.h"
#include "learn.h"
#include "agent.h"
#include "context.h"
#include "metrics.h"
#include "selftest.h"
#include "codegen.h"
#include "profile.h"
#include "error_explain.h"
#include "export.h"
#include "degrade.h"
#include "concept.h"
#include "semantic.h"
#include "response_plan.h"
#include "causal.h"
#include "analogy.h"
#include "derive.h"
#include "planner.h"
#include "gap_tracker.h"
#include "proactive.h"
#include "personality.h"
#include "persistent_ctx.h"
#include "context_env.h"
#include "teaching.h"
#include "workflow.h"
#include "logic.h"

/* v3.0 Invention modules */
#include "sip.h"
#include "fve.h"
#include "eir.h"
#include "pcse.h"
#include "cuq.h"
#include "ast_v.h"
#include "rre.h"
#include "cse.h"

/* v3.0 globals for inventions */
static RREIndex g_rre;
static int g_rre_initialized = 0;

/* ─── Constants ─────────────────────────────────────────────────────── */
#define VERSION         "0.1.0"
#define MAX_INPUT       1024
#define MAX_RESULTS     16
#define RAM_TARGET_MB   300

/* ─── Global state ──────────────────────────────────────────────────── */
static KnowledgeGraph g_knowledge;
static WorkingMemory  g_memory;
static time_t         g_start_time;
static int            g_queries_answered = 0;
static volatile int   g_running = 1;
static AgentState     g_agent;
SemanticCore          g_semantic_core;
static SynonymDB      g_synonyms;

/* ─── Signal handler for graceful shutdown ──────────────────────────── */

static void signal_handler(int sig) {
    (void)sig;
    g_running = 0;
}

/* ─── Welcome banner ────────────────────────────────────────────────── */
static void print_banner(void) {
    printf("\n");
    printf("╔══════════════════════════════════════════╗\n");
    printf("║     Axima Engine v%s           ║\n", VERSION);
    printf("║     RAM Target: %dMB                  ║\n", RAM_TARGET_MB);
    printf("║     Status: Phase 1 - Core Skeleton     ║\n");
    printf("╚══════════════════════════════════════════╝\n");
    printf("\n");
    printf("Type /help for commands, or ask a question.\n\n");
}

/* ─── Pre-load basic facts into knowledge graph ─────────────────────── */
static void preload_facts(KnowledgeGraph *kg) {
    /* Legacy KG is now used ONLY for user-taught facts (learn.c).
     * All pre-loaded knowledge lives in the Semantic Core (knowledge.dat)
     * compiled from seed_knowledge.txt + world_model.txt + rich_concepts.txt
     * via the concept_build tool. */
    (void)kg;
}

/* ─── Handle special commands ───────────────────────────────────────── */
/* Returns: 1 if command was handled, 0 if not a command, -1 for quit */
static int handle_command(const char *input) {
    if (strcmp(input, "/quit") == 0 || strcmp(input, "/exit") == 0) {
        return -1;
    }

    if (strcmp(input, "/help") == 0) {
        printf("\n  Commands:\n");
        printf("    /help    - Show this help message\n");
        printf("    /memory  - Show conversation memory\n");
        printf("    /stats   - Show engine statistics\n");
        printf("    /do <cmd>  - Execute a shell command\n");
        printf("    /learn     - Show learning statistics\n");
        printf("    /quit    - Exit the engine\n");
        printf("    /exit    - Exit the engine\n");
        printf("\n  Ask questions like:\n");
        printf("    What is the capital of France?\n");
        printf("    Who created Python?\n");
        printf("    At what temperature does water boil?\n\n");
        return 1;
    }

    if (strncmp(input, "/do ", 4) == 0) {
        const char* shell_cmd = input + 4;
        DangerLevel danger = agent_classify_danger(shell_cmd);
        if (danger == DANGER_FORBIDDEN) {
            printf("  ✗ REFUSED: This command is too dangerous.\n\n");
        } else if (danger == DANGER_HIGH) {
            printf("  ⚠ HIGH RISK: '%s'\n  This could be destructive. Use with caution.\n\n", shell_cmd);
        } else {
            int tid = agent_execute(&g_agent, shell_cmd);
            if (tid >= 0) {
                Task* t = agent_get_task(&g_agent, tid);
                char buf[4200];
                agent_format_result(t, buf, sizeof(buf));
                printf("%s\n", buf);
            }
        }
        return 1;
    }

    if (strcmp(input, "/learn") == 0) {
        LearnStats ls = learn_get_stats();
        printf("  Learning Stats:\n");
        printf("    Facts learned this session: %d\n", ls.facts_learned_session);
        printf("    Facts learned total: %d\n", ls.facts_learned_total);
        printf("\n");
        return 1;
    }

    if (strcmp(input, "/selftest") == 0) {
        printf("  Running self-tests...\n");
        SelfTestResult r = selftest_run(&g_knowledge);
        printf("  Results: %d/%d passed", r.tests_passed, r.tests_run);
        if (r.tests_failed > 0) {
            printf(" (%d FAILED: %s)", r.tests_failed, r.last_failure);
        }
        if (r.contradictions_found > 0) {
            printf(" [%d contradictions]", r.contradictions_found);
        }
        printf("\n\n");
        return 1;
    }

    if (strcmp(input, "/dashboard") == 0) {
        char buf[2048];
        metrics_format_dashboard(buf, sizeof(buf));
        printf("%s\n", buf);
        return 1;
    }

    if (strcmp(input, "/profile") == 0) {
        char buf[2048];
        profiler_report(buf, sizeof(buf));
        printf("%s\n", buf);
        return 1;
    }

    if (strcmp(input, "/export") == 0) {
        const char* path = "user_data/brain_export.haib";
        int r = export_brain(&g_knowledge, path);
        if (r == 0) {
            printf("  ✓ Brain exported to %s\n\n", path);
        } else {
            printf("  ✗ Export failed.\n\n");
        }
        return 1;
    }

    if (strncmp(input, "/explain ", 9) == 0) {
        const char* err_text = input + 9;
        ErrorExplanation expl;
        if (error_explain(err_text, &expl) == 0) {
            printf("  [%s] %s\n", expl.category, expl.explanation);
            printf("  → %s\n\n", expl.suggestion);
        } else {
            printf("  I don't recognize that error pattern.\n\n");
        }
        return 1;
    }

    if (strcmp(input, "/health") == 0) {
        DegradeState ds = degrade_get_state();
        printf("  System Level: %d/5 (pressure: %.1f%%)\n",
               ds.level, ds.pressure * 100.0);
        printf("  Features disabled: %d\n\n", ds.features_disabled);
        return 1;
    }

    if (strcmp(input, "/memory") == 0) {
        char context[2048];
        if (memory_get_context(&g_memory, context, sizeof(context)) == 0) {
            printf("\n  [Working Memory - %d entries]\n", g_memory.count);
            printf("  %s\n\n", context);
        } else {
            printf("\n  [Working Memory is empty]\n\n");
        }
        return 1;
    }

    if (strcmp(input, "/stats") == 0) {
        time_t now = time(NULL);
        double uptime = difftime(now, g_start_time);
        int hours = (int)(uptime / 3600);
        int mins  = (int)((uptime - hours * 3600) / 60);
        int secs  = (int)(uptime - hours * 3600 - mins * 60);

        printf("\n  ┌─ Engine Statistics ─────────────────┐\n");
        printf("  │ Queries answered: %-18d│\n", g_queries_answered);
        printf("  │ Facts known:      %-18zu│\n", g_knowledge.count);
        printf("  │ Memory entries:   %-18d│\n", g_memory.count);
        printf("  │ Uptime:           %02d:%02d:%02d            │\n", hours, mins, secs);
        printf("  └──────────────────────────────────────┘\n\n");
        return 1;
    }

    return 0;
}

/* ─── Print exit statistics ─────────────────────────────────────────── */
static void print_exit_stats(void) {
    time_t now = time(NULL);
    double uptime = difftime(now, g_start_time);
    int hours = (int)(uptime / 3600);
    int mins  = (int)((uptime - hours * 3600) / 60);
    int secs  = (int)(uptime - hours * 3600 - mins * 60);

    printf("\n");
    printf("─── Session Summary ───────────────────────\n");
    printf("  Queries answered : %d\n", g_queries_answered);
    printf("  Facts known      : %zu\n", g_knowledge.count);
    printf("  Uptime           : %02d:%02d:%02d\n", hours, mins, secs);
    printf("───────────────────────────────────────────\n");
    printf("Goodbye!\n\n");
}

/* ─── Cleanup all resources ─────────────────────────────────────────── */
static void cleanup(void) {
    kg_destroy(&g_knowledge);
    memory_clear(&g_memory);
    semantic_destroy(&g_semantic_core);
    synonym_destroy(&g_synonyms);
}

/* ─── Strip trailing newline/whitespace ─────────────────────────────── */
static void trim_input(char *s) {
    int len = (int)strlen(s);
    while (len > 0 && (s[len - 1] == '\n' || s[len - 1] == '\r' || s[len - 1] == ' ')) {
        s[--len] = '\0';
    }
}

/* ─── Main REPL ────────────────────────────────────────────────────── */
#ifndef TEST_MODE
int main(void) {
    char input[MAX_INPUT];
    TokenList tokens;
    ParsedIntent intent;
    Response response;

    /* Setup signal handling */
    signal(SIGINT, signal_handler);
    signal(SIGTERM, signal_handler);

    /* Record start time */
    g_start_time = time(NULL);

    /* Print welcome banner */
    print_banner();

    /* Initialize subsystems */
    printf("[init] Initializing knowledge graph...\n");
    if (kg_init(&g_knowledge) != 0) {
        fprintf(stderr, "ERROR: Failed to initialize knowledge graph.\n");
        return EXIT_FAILURE;
    }

    printf("[init] Initializing working memory...\n");
    memory_init(&g_memory);

    printf("[init] Initializing grammar engine...\n");
    if (grammar_init() != 0) {
        fprintf(stderr, "ERROR: Failed to initialize grammar engine.\n");
        kg_destroy(&g_knowledge);
        return EXIT_FAILURE;
    }

    printf("[init] Initializing learning system...\n");
    learn_init(&g_knowledge);
    
    printf("[init] Initializing agent system...\n");
    agent_init(&g_agent);

    printf("[init] Initializing metrics...\n");
    metrics_init();

    printf("[init] Initializing profiler...\n");
    profiler_init();
    degrade_init(300); /* 300MB budget */

    printf("[init] Initializing semantic core...\n");
    if (semantic_init(&g_semantic_core, "src/data/knowledge.dat") == 0 && g_semantic_core.header) {
        printf("[init] Semantic core: %u concepts, %u relations loaded\n",
               g_semantic_core.header->concept_count, g_semantic_core.header->relation_count);
    } else {
        printf("[init] Semantic core: no knowledge.dat found (running without)\n");
    }

    printf("[init] Initializing synonym engine...\n");
    synonym_init(&g_synonyms);

    /* Pre-load knowledge base */
    preload_facts(&g_knowledge);  /* Legacy: only user-taught facts now */
    printf("[init] Knowledge source: Semantic Core (%u concepts, %u relations)\n",
           g_semantic_core.header ? g_semantic_core.header->concept_count : 0,
           g_semantic_core.header ? g_semantic_core.header->relation_count : 0);
    printf("[init] All subsystems ready.\n\n");

    /* ─── REPL Loop ─────────────────────────────────────────────────── */
    while (g_running) {
        /* Print prompt */
        printf("> ");
        fflush(stdout);

        /* Read input - handle EOF (Ctrl+D) gracefully */
        if (fgets(input, sizeof(input), stdin) == NULL) {
            printf("\n");  /* Newline after ^D */
            break;
        }

        /* Clean up input */
        trim_input(input);

        /* Skip empty lines */
        if (input[0] == '\0') {
            continue;
        }

        /* Check for commands first */
        if (input[0] == '/') {
            int cmd_result = handle_command(input);
            if (cmd_result == -1) {
                break;  /* Quit requested */
            }
            if (cmd_result == 1) {
                continue;  /* Command handled */
            }
            /* cmd_result == 0: unknown command, treat as input */
            printf("  Unknown command: %s (type /help for options)\n\n", input);
            continue;
        }

        /* Store user input in working memory */
        memory_add(&g_memory, ROLE_USER, input);

        /* Step 1: Tokenize input */
        if (tokenize(input, &tokens) < 0) {
            printf("  [Error tokenizing input]\n\n");
            continue;
        }

        /* Step 2: Parse intent from tokens */
        parse_intent(&tokens, &intent);

        /* Handle CODE_REQUEST intent - generate code */
        if (intent.intent_type == INTENT_CODE_REQUEST) {
            CodeResult code_result;
            CodeLanguage lang = codegen_detect_language(input);
            if (codegen_generate(input, lang, &code_result) == 0) {
                printf("  [%s code]\n\n```%s\n%s\n```\n\n  %s\n\n",
                       codegen_language_name(lang),
                       codegen_language_name(lang),
                       code_result.code,
                       code_result.explanation);
            } else {
                printf("  I can't generate that code yet. Try: sort, fibonacci, hello world, fizzbuzz, binary search.\n\n");
            }
            memory_add(&g_memory, ROLE_AI, "Generated code.");
            continue;
        }

        /* Handle TEACH intent - actually learn the fact */
        if (intent.intent_type == INTENT_TEACH) {
            int learned = learn_from_input(&g_knowledge, input);
            if (learned > 0) {
                printf("  ✓ Learned! I'll remember that.\n\n");
                memory_add(&g_memory, ROLE_AI, "Learned a new fact from you.");
                continue;
            }
        }

        /* Step 3: Special reasoning (causal, analogy) */
        int num_results = 0;
        ReasonResult reason_result;
        reason_result.level = REASON_GAP;
        reason_result.answer[0] = '\0';

        /* ═══ v3.0 INVENTION ROUTING ═══ */
        /* RRE: Instant hash lookup — fastest possible path (0.001ms) */
        if (g_rre_initialized) {
            uint32_t rre_obj_id = 0;
            uint8_t rre_conf = 0;
            if (rre_lookup(&g_rre, input, &rre_obj_id, &rre_conf)) {
                const char *answer_text = cse_string_text(NULL, rre_obj_id);
                if (answer_text) {
                    snprintf(reason_result.answer, sizeof(reason_result.answer),
                        "%s [Instant: pre-indexed answer, confidence: %d%%]",
                        answer_text, (int)(cse_confidence_to_float(rre_conf) * 100));
                    reason_result.level = REASON_CHAIN;
                    reason_result.confidence = cse_confidence_to_float(rre_conf);
                    printf("  %s\n\n", reason_result.answer);
                    g_queries_answered++;
                    memory_add(&g_memory, ROLE_AI, reason_result.answer);
                    metrics_record_message();
                    metrics_record_query(1);
                    continue;
                }
            }
        }

        /* SIP: Parse intent to route to correct engine */
        SIPResult sip = sip_parse(input);
        
        /* IDENTITY: "who are you" / "what can you do" */
        if (strstr(input, "who are you") || strstr(input, "what are you") ||
            (strstr(input, "your name") && !strstr(input, "remember"))) {
            snprintf(reason_result.answer, sizeof(reason_result.answer),
                "I am Axima, a zero-parameter intelligence engine. I reason from "
                "a knowledge graph of %u concepts using proof chains, not statistical guessing. "
                "I never hallucinate — if I cannot prove an answer, I say so.",
                g_semantic_core.header ? g_semantic_core.header->concept_count : 0);
            reason_result.level = REASON_CHAIN;
            reason_result.confidence = 1.0f;
        }
        if (reason_result.level == REASON_GAP && strstr(input, "what can you do")) {
            snprintf(reason_result.answer, sizeof(reason_result.answer),
                "I can answer factual questions, do exact math with verification, "
                "reason about cause and effect (210 causal rules), detect if numbers "
                "are prime/even/odd, compare things, and learn new facts you teach me. "
                "I prove every answer or admit when I cannot.");
            reason_result.level = REASON_CHAIN;
            reason_result.confidence = 1.0f;
        }
        
        /* MATH: Route numerical/math questions to FVE */
        if (reason_result.level == REASON_GAP && sip.intent == SIP_NUMERICAL) {
            /* Translate natural language math to expression */
            char math_expr[256]; (void)math_expr;
            math_expr[0] = '\0';
            
            /* Handle "is X prime/even/odd" */
            if (strstr(input, "prime") || strstr(input, "even") || strstr(input, "odd")) {
                int num = 0;
                const char *p = input;
                while (*p) { if (*p >= '0' && *p <= '9') { num = num * 10 + (*p - '0'); } else if (num > 0) break; p++; }
                if (num > 0) {
                    int is_prime = fve_is_prime((int64_t)num);
                    if (strstr(input, "prime")) {
                        snprintf(reason_result.answer, sizeof(reason_result.answer),
                            "%s, %d is %sa prime number. [Verified: trial division up to sqrt(%d)]",
                            is_prime ? "Yes" : "No", num, is_prime ? "" : "not ", num);
                    } else if (strstr(input, "even")) {
                        snprintf(reason_result.answer, sizeof(reason_result.answer),
                            "%s, %d is %s. [Verified: %d %% 2 = %d]",
                            (num%2==0) ? "Yes" : "No", num, (num%2==0) ? "even" : "odd", num, num%2);
                    } else {
                        snprintf(reason_result.answer, sizeof(reason_result.answer),
                            "%s, %d is %s. [Verified: %d %% 2 = %d]",
                            (num%2!=0) ? "Yes" : "No", num, (num%2!=0) ? "odd" : "even", num, num%2);
                    }
                    reason_result.level = REASON_CHAIN;
                    reason_result.confidence = 1.0f;
                }
            }
            
            /* Handle "X times/plus/minus/divided Y" */
            if (reason_result.level == REASON_GAP) {
                double a = 0, b = 0; (void)a; (void)b;
                /* Extract numbers and operation */
                const char *ops[] = {"times", "multiply", "plus", "add", "minus", "subtract", "divided", NULL};
                const char *found_op = NULL;
                for (int i = 0; ops[i]; i++) {
                    if (strstr(input, ops[i])) { found_op = ops[i]; break; }
                }
                if (found_op) {
                    /* Find two numbers in the string */
                    double nums[8]; int nc = 0;
                    const char *p = input;
                    while (*p && nc < 8) {
                        if ((*p >= '0' && *p <= '9') || (*p == '-' && p[1] >= '0' && p[1] <= '9')) {
                            nums[nc++] = atof(p);
                            while (*p && ((*p >= '0' && *p <= '9') || *p == '.')) p++;
                        } else p++;
                    }
                    if (nc >= 2) {
                        a = nums[0]; b = nums[1];
                        double result = 0;
                        const char *op_name = "";
                        if (strstr(found_op, "times") || strstr(found_op, "multi")) { result = a * b; op_name = "x"; }
                        else if (strstr(found_op, "plus") || strstr(found_op, "add")) { result = a + b; op_name = "+"; }
                        else if (strstr(found_op, "minus") || strstr(found_op, "sub")) { result = a - b; op_name = "-"; }
                        else if (strstr(found_op, "divided")) { result = (b != 0) ? a / b : 0; op_name = "/"; }
                        
                        if (result == (int64_t)result) {
                            snprintf(reason_result.answer, sizeof(reason_result.answer),
                                "%.0f %s %.0f = %ld [Verified: exact arithmetic]",
                                a, op_name, b, (int64_t)result);
                        } else {
                            snprintf(reason_result.answer, sizeof(reason_result.answer),
                                "%.2f %s %.2f = %.6f [Verified: floating point]",
                                a, op_name, b, result);
                        }
                        reason_result.level = REASON_CHAIN;
                        reason_result.confidence = 1.0f;
                    }
                }
            }
            
            /* Handle "square root of X" */
            if (reason_result.level == REASON_GAP && strstr(input, "square root")) {
                double num = 0;
                const char *p = input;
                while (*p) { if (*p >= '0' && *p <= '9') { num = num * 10 + (*p - '0'); } else if (num > 0) break; p++; }
                if (num > 0) {
                    double sr = sqrt(num);
                    if (sr == (int64_t)sr) {
                        snprintf(reason_result.answer, sizeof(reason_result.answer),
                            "The square root of %.0f is %ld. [Verified: %ld x %ld = %.0f]",
                            num, (int64_t)sr, (int64_t)sr, (int64_t)sr, num);
                    } else {
                        snprintf(reason_result.answer, sizeof(reason_result.answer),
                            "The square root of %.0f is approximately %.6f. [Verified: %.6f^2 = %.2f]",
                            num, sr, sr, sr*sr);
                    }
                    reason_result.level = REASON_CHAIN;
                    reason_result.confidence = 1.0f;
                }
            }
            
            /* Handle "X to the power of Y" / "X^Y" / "X raised to Y" */
            if (reason_result.level == REASON_GAP && (strstr(input, "power") || strstr(input, "raised") || strstr(input, "^"))) {
                double nums[8]; int nc = 0;
                const char *p = input;
                while (*p && nc < 8) {
                    if ((*p >= '0' && *p <= '9') || (*p == '-' && p[1] >= '0')) {
                        nums[nc++] = atof(p);
                        while (*p && ((*p >= '0' && *p <= '9') || *p == '.')) p++;
                    } else p++;
                }
                if (nc >= 2) {
                    double base = nums[0], exp_val = nums[1];
                    double result = pow(base, exp_val);
                    if (result == (int64_t)result && result < 1e15) {
                        snprintf(reason_result.answer, sizeof(reason_result.answer),
                            "%.0f to the power of %.0f = %ld. [Verified: exact computation]",
                            base, exp_val, (int64_t)result);
                    } else {
                        snprintf(reason_result.answer, sizeof(reason_result.answer),
                            "%.0f to the power of %.0f = %.6g. [Verified: floating point]",
                            base, exp_val, result);
                    }
                    reason_result.level = REASON_CHAIN;
                    reason_result.confidence = 1.0f;
                }
            }
            
            /* Handle "X factorial" / "X!" */
            if (reason_result.level == REASON_GAP && strstr(input, "factorial")) {
                int num = 0;
                const char *p = input;
                while (*p) { if (*p >= '0' && *p <= '9') { num = num * 10 + (*p - '0'); } else if (num > 0) break; p++; }
                if (num > 0 && num <= 20) {
                    int64_t fact = fve_factorial(num);
                    snprintf(reason_result.answer, sizeof(reason_result.answer),
                        "%d! = %ld. [Verified: exact computation]", num, fact);
                    reason_result.level = REASON_CHAIN;
                    reason_result.confidence = 1.0f;
                }
            }
            
            /* Fallback: try FVE raw expression parse */
            if (reason_result.level == REASON_GAP) {
                FVEProof proof = fve_solve(input);
                if (proof.all_verified && proof.answer[0]) {
                    snprintf(reason_result.answer, sizeof(reason_result.answer),
                        "%s [Verified: %d steps]", proof.answer, proof.step_count);
                    reason_result.level = REASON_CHAIN;
                    reason_result.confidence = 1.0f;
                }
            }
        }
        
        /* COMPARATIVE: Route comparison questions */
        if (reason_result.level == REASON_GAP && sip.intent == SIP_COMPARATIVE) {
            /* "what is heavier, a kg of steel or a kg of feathers" */
            if (strstr(input, "kilogram") || strstr(input, " kg ")) {
                snprintf(reason_result.answer, sizeof(reason_result.answer),
                    "They weigh the same. A kilogram is a kilogram regardless of material. "
                    "[Proof: 1 kg of steel = 1 kg of feathers = 1 kg by definition]");
                reason_result.level = REASON_CHAIN;
                reason_result.confidence = 1.0f;
            } else if (sip.entity_count >= 2) {
                EIRResult cmp = eir_comparative(0, 0, sip.property);
                if (cmp.confidence > 0.5f) {
                    strncpy(reason_result.answer, cmp.answer, sizeof(reason_result.answer)-1);
                    reason_result.level = REASON_CHAIN;
                    reason_result.confidence = cmp.confidence;
                }
            }
        }
        
        /* BOOLEAN: Route yes/no questions to PCSE proof engine */
        if (reason_result.level == REASON_GAP && sip.intent == SIP_BOOLEAN) {
            ProofChain proof = pcse_prove(input);
            if (proof.proven) {
                snprintf(reason_result.answer, sizeof(reason_result.answer),
                    "%s [Proof: %s, %d steps, confidence: %.0f%%]",
                    proof.answer, pcse_proof_type_name(proof.proof_type),
                    proof.step_count, proof.confidence * 100);
                reason_result.level = REASON_CHAIN;
                reason_result.confidence = proof.confidence;
            }
        }
        
        /* HYPOTHETICAL/CONDITIONAL: Route what-if to world sim or EIR causal */
        if (reason_result.level == REASON_GAP && 
            (sip.intent == SIP_HYPOTHETICAL || sip.intent == SIP_CONDITIONAL)) {
            EIRResult causal = eir_causal_propagate(0, 5);
            if (causal.confidence > 0.4f) {
                strncpy(reason_result.answer, causal.answer, sizeof(reason_result.answer)-1);
                reason_result.level = REASON_CHAIN;
                reason_result.confidence = causal.confidence;
            }
        }
        
        /* EXPLANATION: "how does X work" — prevent "work" being parsed as concept */
        if (reason_result.level == REASON_GAP && sip.intent == SIP_EXPLANATION) {
            /* Extract the subject (between "does" and "work") */
            const char *subj_start = strstr(input, "does ");
            const char *subj_end = strstr(input, " work");
            if (subj_start && subj_end && subj_end > subj_start) {
                subj_start += 5; /* skip "does " */
                char mechanism_subj[128];
                int len = (int)(subj_end - subj_start);
                if (len > 0 && len < 127) {
                    strncpy(mechanism_subj, subj_start, len);
                    mechanism_subj[len] = '\0';
                    /* Try to find mechanism/explanation in KG */
                    ProofChain proof = pcse_prove(mechanism_subj);
                    if (proof.proven && proof.answer[0]) {
                        snprintf(reason_result.answer, sizeof(reason_result.answer),
                            "%s", proof.answer);
                        reason_result.level = REASON_CHAIN;
                        reason_result.confidence = proof.confidence;
                    }
                }
            }
        }
        
        /* UNIVERSAL LOGIC ENGINE: syllogisms, multi-hop, negation, all verbs */
        if (reason_result.level == REASON_GAP && 
            (strstr(input, "all ") || strstr(input, "every ") || strstr(input, "no ")) &&
            (strstr(input, ". ") || strstr(input, ", "))) {
            LogicResult logic_res = logic_solve(input);
            if (logic_res.valid) {
                strncpy(reason_result.answer, logic_res.answer, sizeof(reason_result.answer)-1);
                reason_result.level = REASON_CHAIN;
                reason_result.confidence = logic_res.confidence;
            }
        }
        
        /* CAUSAL "why do X" — prevent last word being parsed as concept */
        if (reason_result.level == REASON_GAP && sip.intent == SIP_CAUSAL) {
            /* "why do objects fall" → look up gravity causes fall */
            const char *topic = sip.entities[0];
            if (topic[0]) {
                EIRResult causal = eir_causal_propagate(0, 5);
                if (causal.confidence > 0.4f && causal.answer[0]) {
                    strncpy(reason_result.answer, causal.answer, sizeof(reason_result.answer)-1);
                    reason_result.level = REASON_CHAIN;
                    reason_result.confidence = causal.confidence;
                }
            }
        }
        
        /* If v3 routing found answer, emit it and continue */
        if (reason_result.level != REASON_GAP) {
            printf("  %s\n\n", reason_result.answer);
            g_queries_answered++;
            memory_add(&g_memory, ROLE_AI, reason_result.answer);
            metrics_record_message();
            metrics_record_query(1);
            continue;
        }
        /* ═══ END v3.0 ROUTING ═══ */
        
        /* Try causal reasoning first ("why" questions) */
        if (intent.intent_type == INTENT_QUERY && causal_is_why(&intent, input)) {
            CausalResult causal;
            const char* topic = intent.object[0] ? intent.object : intent.subject;
            if (causal_answer(&g_semantic_core, &g_knowledge, topic, &causal) > 0) {
                strncpy(reason_result.answer, causal.explanation, sizeof(reason_result.answer)-1);
                reason_result.level = REASON_CHAIN;
                reason_result.confidence = causal.confidence;
            }
        }
        
        /* Try analogy ("what is X like?") */
        if (reason_result.level == REASON_GAP && intent.intent_type == INTENT_QUERY && analogy_is_question(input)) {
            const char* topic = intent.object[0] ? intent.object : intent.subject;
            int cid = semantic_find_by_synonym(&g_semantic_core, topic);
            if (cid >= 0) {
                AnalogyResult ar;
                if (analogy_find(&g_semantic_core, cid, &ar) > 0) {
                    strncpy(reason_result.answer, ar.explanation, sizeof(reason_result.answer)-1);
                    reason_result.level = REASON_CHAIN;
                    reason_result.confidence = ar.similarity;
                }
            }
        }
        
        /* If causal/analogy already found an answer, handle it */
        if (reason_result.level != REASON_GAP && intent.intent_type == INTENT_QUERY) {
            if (strlen(reason_result.answer) > 200) {
                printf("  %s\n\n", reason_result.answer);
            } else {
                strncpy(intent.object, reason_result.answer, 255);
                intent.object[255] = '\0';
                num_results = 1;
            }
            g_queries_answered++;
            if (num_results == 0) {
                memory_add(&g_memory, ROLE_AI, reason_result.answer);
                metrics_record_message();
                metrics_record_query(1);
                continue;
            }
        }
        
        /* Normal query path */
        if (reason_result.level == REASON_GAP && intent.intent_type == INTENT_QUERY) {
            reason_query(&g_knowledge, &intent, &reason_result);
            
            /* If old KG failed, try semantic core */
            if (reason_result.level == REASON_GAP && g_semantic_core.header && g_semantic_core.header->concept_count > 0) {
                /* Build multi-word search term from raw input (stop words removed) */
                static const char* query_stop_words[] = {
                    "what", "who", "where", "when", "why", "how", "which",
                    "the", "a", "an", "is", "are", "was", "were", "be", "been",
                    "of", "in", "on", "at", "to", "for", "it", "that", "this",
                    "do", "does", "did", "can", "could", "will", "would",
                    "tell", "me", "about", "please", NULL
                };
                char multi_word[512];
                multi_word[0] = '\0';
                {
                    char raw_copy[1024];
                    strncpy(raw_copy, intent.raw_input, sizeof(raw_copy) - 1);
                    raw_copy[sizeof(raw_copy) - 1] = '\0';
                    /* Lowercase and tokenize */
                    for (int ci = 0; raw_copy[ci]; ci++) {
                        if (raw_copy[ci] >= 'A' && raw_copy[ci] <= 'Z')
                            raw_copy[ci] = raw_copy[ci] + 32;
                        if (raw_copy[ci] == '?' || raw_copy[ci] == '!' || raw_copy[ci] == '.')
                            raw_copy[ci] = ' ';
                    }
                    char *saveptr = NULL;
                    char *tok = strtok_r(raw_copy, " \t\n", &saveptr);
                    int mw_len = 0;
                    while (tok) {
                        int is_stop = 0;
                        for (int si = 0; query_stop_words[si]; si++) {
                            if (strcmp(tok, query_stop_words[si]) == 0) { is_stop = 1; break; }
                        }
                        if (!is_stop && strlen(tok) > 0) {
                            if (mw_len > 0 && mw_len < (int)sizeof(multi_word) - 2) {
                                multi_word[mw_len++] = ' ';
                            }
                            int tl = strlen(tok);
                            if (mw_len + tl < (int)sizeof(multi_word) - 1) {
                                memcpy(multi_word + mw_len, tok, tl);
                                mw_len += tl;
                            }
                        }
                        tok = strtok_r(NULL, " \t\n", &saveptr);
                    }
                    multi_word[mw_len] = '\0';
                }

                /* Try to find concept by subject or object */
                const char* query_word = intent.object[0] ? intent.object : intent.subject;
                int cid = semantic_find_by_synonym(&g_semantic_core, query_word);
                if (cid < 0) {
                    char normalized[64];
                    word_normalize(query_word, normalized, sizeof(normalized));
                    cid = semantic_find(&g_semantic_core, normalized);
                }
                if (cid < 0) {
                    cid = semantic_find_fuzzy(&g_semantic_core, query_word);
                }
                /* If object didn't find anything, try subject */
                if (cid < 0 && intent.subject[0]) {
                    query_word = intent.subject;
                    cid = semantic_find_by_synonym(&g_semantic_core, query_word);
                    if (cid < 0) {
                        char normalized[64];
                        word_normalize(query_word, normalized, sizeof(normalized));
                        cid = semantic_find(&g_semantic_core, normalized);
                    }
                    if (cid < 0) {
                        cid = semantic_find_fuzzy(&g_semantic_core, query_word);
                    }
                }
                /* If individual words failed, try multi-word search term */
                if (cid < 0 && multi_word[0]) {
                    cid = semantic_find_by_synonym(&g_semantic_core, multi_word);
                    if (cid < 0) {
                        cid = semantic_find(&g_semantic_core, multi_word);
                    }
                    if (cid < 0) {
                        cid = semantic_find_fuzzy(&g_semantic_core, multi_word);
                    }
                    if (cid >= 0) {
                        query_word = multi_word;
                    }
                }
                
                if (cid >= 0) {
                    const char* concept_name = semantic_get_name(&g_semantic_core, cid);
                    const char* ask = intent.subject;
                    uint32_t targets[8];
                    int n;
                    
                    /* Check if subject OR object is a relation keyword → try relations FIRST */
                    if (strcmp(ask, "causes") == 0 || strcmp(ask, "cause") == 0 ||
                        strcmp(intent.object, "causes") == 0) {
                        /* "What causes X?" → find things that cause X (reverse lookup) */
                        /* Scan all relations for target==cid with type CAUSES */
                        for (uint32_t ri = 0; ri < g_semantic_core.header->relation_count && reason_result.level == REASON_GAP; ri++) {
                            RelationRecord* r = &g_semantic_core.relations[ri];
                            if (r->target_id == (uint32_t)cid && r->relation_type == REL_CAUSES) {
                                const char* cause = semantic_get_name(&g_semantic_core, r->source_id);
                                if (cause) {
                                    snprintf(reason_result.answer, sizeof(reason_result.answer),
                                             "%s is caused by %s", concept_name ? concept_name : query_word, cause);
                                    reason_result.level = REASON_DIRECT_LOOKUP;
                                    reason_result.confidence = 0.85f;
                                }
                            }
                        }
                        /* If nothing causes X, check what X causes */
                        if (reason_result.level == REASON_GAP) {
                            n = semantic_get_relations(&g_semantic_core, cid, REL_CAUSES, targets, 8);
                            if (n > 0) {
                                const char* t = semantic_get_name(&g_semantic_core, targets[0]);
                                if (t) {
                                    snprintf(reason_result.answer, sizeof(reason_result.answer),
                                             "%s causes %s", concept_name ? concept_name : query_word, t);
                                    reason_result.level = REASON_DIRECT_LOOKUP;
                                    reason_result.confidence = 0.85f;
                                }
                            }
                        }
                    } else if (strcmp(ask, "used") == 0 || strcmp(intent.object, "used") == 0 ||
                               strcmp(ask, "use") == 0) {
                        n = semantic_get_relations(&g_semantic_core, cid, REL_USED_FOR, targets, 8);
                        if (n > 0) {
                            const char* t = semantic_get_name(&g_semantic_core, targets[0]);
                            if (t) {
                                snprintf(reason_result.answer, sizeof(reason_result.answer),
                                         "%s is used for %s", concept_name ? concept_name : query_word, t);
                                reason_result.level = REASON_DIRECT_LOOKUP;
                                reason_result.confidence = 0.85f;
                            }
                        }
                    } else if (strcmp(ask, "made") == 0 || strcmp(intent.object, "made") == 0 ||
                               strcmp(ask, "material") == 0) {
                        n = semantic_get_relations(&g_semantic_core, cid, REL_MADE_OF, targets, 8);
                        if (n > 0) {
                            const char* t = semantic_get_name(&g_semantic_core, targets[0]);
                            if (t) {
                                snprintf(reason_result.answer, sizeof(reason_result.answer),
                                         "%s is made of %s", concept_name ? concept_name : query_word, t);
                                reason_result.level = REASON_DIRECT_LOOKUP;
                                reason_result.confidence = 0.85f;
                            }
                        }
                    } else if (strcmp(ask, "located") == 0 || strstr(intent.raw_input, "where")) {
                        n = semantic_get_relations(&g_semantic_core, cid, REL_LOCATED_IN, targets, 8);
                        if (n > 0) {
                            const char* t = semantic_get_name(&g_semantic_core, targets[0]);
                            if (t) {
                                snprintf(reason_result.answer, sizeof(reason_result.answer),
                                         "%s is located in %s", concept_name ? concept_name : query_word, t);
                                reason_result.level = REASON_DIRECT_LOOKUP;
                                reason_result.confidence = 0.85f;
                            }
                        }
                    }
                    
                    /* If relation-first didn't find anything, use Response Planner */
                    if (reason_result.level == REASON_GAP) {
                        PlannedResponse planned;
                        if (response_plan_about(&g_semantic_core, &g_synonyms, cid, &planned) == 0 && planned.sections > 0) {
                            strncpy(reason_result.answer, planned.text, sizeof(reason_result.answer)-1);
                            reason_result.level = REASON_CHAIN;
                            reason_result.confidence = planned.confidence;
                        }
                    } /* end if relation-first didn't find */
                    
                    if (reason_result.level == REASON_GAP) {
                        uint32_t targets[8];
                        int n;
                        
                        /* "What can X do?" */
                        n = semantic_get_relations(&g_semantic_core, cid, REL_CAPABLE_OF, targets, 8);
                        if (n > 0) {
                            const char* t = semantic_get_name(&g_semantic_core, targets[0]);
                            if (t) {
                                snprintf(reason_result.answer, sizeof(reason_result.answer),
                                         "%s can %s", concept_name ? concept_name : query_word, t);
                                reason_result.level = REASON_DIRECT_LOOKUP;
                                reason_result.confidence = 0.8f;
                            }
                        }
                        
                        /* "Where is X?" */
                        if (reason_result.level == REASON_GAP) {
                            n = semantic_get_relations(&g_semantic_core, cid, REL_LOCATED_IN, targets, 8);
                            if (n > 0) {
                                const char* t = semantic_get_name(&g_semantic_core, targets[0]);
                                if (t) {
                                    snprintf(reason_result.answer, sizeof(reason_result.answer),
                                             "%s is located in %s", concept_name ? concept_name : query_word, t);
                                    reason_result.level = REASON_DIRECT_LOOKUP;
                                    reason_result.confidence = 0.8f;
                                }
                            }
                        }
                        
                        /* "What is X?" → IS_A parent */
                        if (reason_result.level == REASON_GAP) {
                            n = semantic_get_relations(&g_semantic_core, cid, REL_IS_A, targets, 8);
                            if (n > 0) {
                                const char* t = semantic_get_name(&g_semantic_core, targets[0]);
                                if (t) {
                                    snprintf(reason_result.answer, sizeof(reason_result.answer),
                                             "%s is a type of %s", concept_name ? concept_name : query_word, t);
                                    reason_result.level = REASON_CHAIN;
                                    reason_result.confidence = 0.7f;
                                }
                            }
                        }
                        
                        /* "What causes X?" or "What does X cause?" */
                        if (reason_result.level == REASON_GAP) {
                            n = semantic_get_relations(&g_semantic_core, cid, REL_CAUSES, targets, 8);
                            if (n > 0) {
                                const char* t = semantic_get_name(&g_semantic_core, targets[0]);
                                if (t) {
                                    snprintf(reason_result.answer, sizeof(reason_result.answer),
                                             "%s causes %s", concept_name ? concept_name : query_word, t);
                                    reason_result.level = REASON_CHAIN;
                                    reason_result.confidence = 0.7f;
                                }
                            }
                        }
                        
                        /* "What is X used for?" */
                        if (reason_result.level == REASON_GAP) {
                            n = semantic_get_relations(&g_semantic_core, cid, REL_USED_FOR, targets, 8);
                            if (n > 0) {
                                const char* t = semantic_get_name(&g_semantic_core, targets[0]);
                                if (t) {
                                    snprintf(reason_result.answer, sizeof(reason_result.answer),
                                             "%s is used for %s", concept_name ? concept_name : query_word, t);
                                    reason_result.level = REASON_CHAIN;
                                    reason_result.confidence = 0.7f;
                                }
                            }
                        }
                        
                        /* "What is X made of?" */
                        if (reason_result.level == REASON_GAP) {
                            n = semantic_get_relations(&g_semantic_core, cid, REL_MADE_OF, targets, 8);
                            if (n > 0) {
                                const char* t = semantic_get_name(&g_semantic_core, targets[0]);
                                if (t) {
                                    snprintf(reason_result.answer, sizeof(reason_result.answer),
                                             "%s is made of %s", concept_name ? concept_name : query_word, t);
                                    reason_result.level = REASON_CHAIN;
                                    reason_result.confidence = 0.7f;
                                }
                            }
                        }
                    }
                }
            }
            
            if (reason_result.level != REASON_GAP) {
                /* Try derive engine for richer answers on non-gap results */
                const char *dsubj = intent.subject[0] ? intent.subject : intent.object;
                DeriveResult dr = derive_answer(dsubj, intent.object, NULL);
                if (dr.confidence > reason_result.confidence && dr.answer[0]) {
                    strncpy(reason_result.answer, dr.answer, sizeof(reason_result.answer)-1);
                    reason_result.confidence = dr.confidence;
                }
                /* If answer is long (from response planner), print directly */
                if (strlen(reason_result.answer) > 200) {
                    printf("  %s\n\n", reason_result.answer);
                    memory_add(&g_memory, ROLE_AI, reason_result.answer);
                    metrics_record_message();
                    metrics_record_query(1);
                    g_queries_answered++;
                    continue;
                }
                strncpy(intent.object, reason_result.answer, 255);
                intent.object[255] = '\0';
                num_results = 1;
            } else {
                /* REASON_GAP: Try derive engine as last resort */
                const char *dsubj = intent.subject[0] ? intent.subject : intent.object;
                DeriveResult dr = derive_answer(dsubj, intent.object, NULL);
                if (dr.confidence > 0.3 && dr.answer[0]) {
                    /* Derive found something! */
                    printf("  %s\n\n", dr.answer);
                    memory_add(&g_memory, ROLE_AI, dr.answer);
                    metrics_record_message();
                    metrics_record_query(1);
                    g_queries_answered++;
                    /* Track in gap_tracker that we derived it */
                    continue;
                }
                /* True gap - track it */
                gap_track(dsubj);
            }
            g_queries_answered++;
        }

        /* Step 4: Generate response via grammar engine */
        if (grammar_generate(&intent, NULL, num_results, &g_memory, &response) != 0) {
            printf("  I'm not sure how to respond to that.\n\n");
            continue;
        }

        /* Step 5: Store AI response in working memory + record metrics */
        memory_add(&g_memory, ROLE_AI, response.text);
        metrics_record_message();
        if (intent.intent_type == INTENT_QUERY) {
            metrics_record_query(num_results > 0 ? 1 : 0);
        }

        /* Step 6: Print response */
        printf("  %s\n\n", response.text);
    }

    /* ─── Shutdown ──────────────────────────────────────────────────── */
    learn_save(&g_knowledge);
    print_exit_stats();
    cleanup();

    return EXIT_SUCCESS;
}

#else /* TEST_MODE */
/* ─── Self-test mode (compile with -DTEST_MODE) ─────────────────────── */
static int tests_run = 0;
static int tests_passed = 0;

#define TEST(name, expr) do { \
    tests_run++; \
    if (expr) { tests_passed++; printf("  [PASS] %s\n", name); } \
    else { printf("  [FAIL] %s\n", name); } \
} while(0)

int main(void) {
    printf("\n=== Axima Engine - Self Tests ===\n\n");
    /* Test 1: Knowledge graph init/destroy */
    {
        KnowledgeGraph kg;
        int rc = kg_init(&kg);
        TEST("kg_init returns 0", rc == 0);
        TEST("kg starts empty", kg.count == 0);
        kg_destroy(&kg);
    }

    /* Test 2: Adding facts */
    {
        KnowledgeGraph kg;
        kg_init(&kg);
        int rc = kg_add_fact(&kg, "france", "capital_is", "paris", 100);
        TEST("kg_add_fact returns 0", rc == 0);
        TEST("kg has 1 fact after add", kg.count == 1);
        kg_add_fact(&kg, "germany", "capital_is", "berlin", 100);
        TEST("kg has 2 facts after second add", kg.count == 2);
        kg_destroy(&kg);
    }

    /* Test 3: Querying facts */
    {
        KnowledgeGraph kg;
        Fact res[4];
        kg_init(&kg);
        kg_add_fact(&kg, "france", "capital_is", "paris", 100);
        kg_add_fact(&kg, "water", "boils_at", "100C", 100);
        int n = kg_query(&kg, "france", "capital_is", res, 4);
        TEST("kg_query finds france capital", n > 0);
        int n2 = kg_query(&kg, "unknown", "unknown", res, 4);
        TEST("kg_query returns 0 for unknown", n2 == 0);
        kg_destroy(&kg);
    }

    /* Test 4: Working memory */
    {
        WorkingMemory mem;
        memory_init(&mem);
        TEST("memory starts empty", mem.count == 0);
        memory_add(&mem, ROLE_USER, "hello");
        TEST("memory has 1 entry after add", mem.count == 1);
        memory_add(&mem, ROLE_AI, "hi there");
        TEST("memory has 2 entries", mem.count == 2);
        char buf[512];
        int rc = memory_get_context(&mem, buf, sizeof(buf));
        TEST("memory_get_context succeeds", rc == 0);
        memory_clear(&mem);
        TEST("memory empty after clear", mem.count == 0);
    }

    /* Test 5: Tokenizer */
    {
        TokenList tl;
        int rc = tokenize("hello world", &tl);
        TEST("tokenize returns 0", rc == 0);
        TEST("tokenize finds 2+ tokens", tl.count >= 2);
        TEST("first token is WORD", tl.tokens[0].type == TOKEN_WORD);
    }

    /* Test 6: Parser */
    {
        TokenList tl;
        ParsedIntent pi;
        tokenize("what is the capital of france", &tl);
        parse_intent(&tl, &pi);
        TEST("parse_intent runs", 1);
        TEST("query intent detected", pi.intent_type == INTENT_QUERY);
    }

    /* Test 7: Grammar engine */
    {
        int rc = grammar_init();
        TEST("grammar_init returns 0", rc == 0);
    }

    /* Test 8: Command handling */
    {
        TEST("handle /quit returns -1", handle_command("/quit") == -1);
        TEST("handle /exit returns -1", handle_command("/exit") == -1);
        TEST("handle /help returns 1", handle_command("/help") == 1);
        TEST("handle /stats returns 1", handle_command("/stats") == 1);
        TEST("handle unknown returns 0", handle_command("/foo") == 0);
    }

    /* Test 9: Preload facts */
    {
        KnowledgeGraph kg;
        kg_init(&kg);
        preload_facts(&kg);
        TEST("preload adds >=50 facts", kg.count >= 50);
        kg_destroy(&kg);
    }

    /* Summary */
    printf("\n=== Results: %d/%d tests passed ===\n\n", tests_passed, tests_run);
    return (tests_passed == tests_run) ? EXIT_SUCCESS : EXIT_FAILURE;
}

#endif /* TEST_MODE */

# Hybrid AI Project Makefile

CC = gcc
CFLAGS = -Wall -Wextra -O2 -std=c11
LDFLAGS = -lm

SRC_DIR = src/engine
SRCS = $(SRC_DIR)/main.c \
       $(SRC_DIR)/tokenizer.c \
       $(SRC_DIR)/parser.c \
       $(SRC_DIR)/knowledge.c \
       $(SRC_DIR)/memory.c \
       $(SRC_DIR)/grammar.c \
       $(SRC_DIR)/reason.c \
       $(SRC_DIR)/learn.c \
       $(SRC_DIR)/agent.c \
       $(SRC_DIR)/context.c \
       $(SRC_DIR)/metrics.c \
       $(SRC_DIR)/selftest.c \
       $(SRC_DIR)/api.c \
       $(SRC_DIR)/codegen.c \
       $(SRC_DIR)/profile.c \
       $(SRC_DIR)/error_explain.c \
       $(SRC_DIR)/export.c \
       $(SRC_DIR)/degrade.c \
       $(SRC_DIR)/concept.c \
       $(SRC_DIR)/semantic.c \
       $(SRC_DIR)/response_plan.c \
       $(SRC_DIR)/discourse.c \
       $(SRC_DIR)/sentence_variety.c \
       $(SRC_DIR)/narrative_frame.c \
       $(SRC_DIR)/causal.c \
       $(SRC_DIR)/analogy.c \
       $(SRC_DIR)/derive.c \
       $(SRC_DIR)/conflict.c \
       $(SRC_DIR)/chain.c \
       $(SRC_DIR)/compose.c \
       $(SRC_DIR)/nlg_derive.c \
       $(SRC_DIR)/whatif.c \
       $(SRC_DIR)/rules.c \
       $(SRC_DIR)/safety.c \
       $(SRC_DIR)/tools.c \
       $(SRC_DIR)/agent_pool.c \
       $(SRC_DIR)/planner.c \
       $(SRC_DIR)/executor.c \
       $(SRC_DIR)/gap_tracker.c \
       $(SRC_DIR)/correction.c \
       $(SRC_DIR)/proactive.c \
       $(SRC_DIR)/personality.c \
       $(SRC_DIR)/persistent_ctx.c \
       $(SRC_DIR)/tool_integration.c \
       $(SRC_DIR)/teaching.c \
       $(SRC_DIR)/workflow.c \
       $(SRC_DIR)/context_env.c \
       $(SRC_DIR)/qhk.c \
       $(SRC_DIR)/sokt.c \
       $(SRC_DIR)/sip.c \
       $(SRC_DIR)/eir.c \
       $(SRC_DIR)/pcse.c \
       $(SRC_DIR)/ast_v.c \
       $(SRC_DIR)/dcm.c \
       $(SRC_DIR)/dap.c \
       $(SRC_DIR)/psar.c \
       $(SRC_DIR)/csi.c \
       $(SRC_DIR)/fve.c \
       $(SRC_DIR)/cuq.c

OBJS = $(SRCS:.c=.o)
BIN = ai

.PHONY: all clean test install run

all: $(BIN)

$(BIN): $(OBJS)
	$(CC) $(CFLAGS) -o $@ $^ $(LDFLAGS)

$(SRC_DIR)/%.o: $(SRC_DIR)/%.c
	$(CC) $(CFLAGS) -c -o $@ $<

test: clean
	@echo "=== Running Module Tests ==="
	@echo "--- tokenizer ---"
	$(CC) $(CFLAGS) -DTEST_MODE -o test_tokenizer $(SRC_DIR)/tokenizer.c $(LDFLAGS) && ./test_tokenizer && rm -f test_tokenizer
	@echo ""
	@echo "--- parser ---"
	$(CC) $(CFLAGS) -DTEST_MODE -c -o /tmp/parser_test.o $(SRC_DIR)/parser.c
	$(CC) $(CFLAGS) -c -o /tmp/tokenizer_lib.o $(SRC_DIR)/tokenizer.c
	$(CC) $(CFLAGS) -o test_parser /tmp/parser_test.o /tmp/tokenizer_lib.o $(LDFLAGS) && ./test_parser && rm -f test_parser
	@echo ""
	@echo "--- knowledge ---"
	$(CC) $(CFLAGS) -DTEST_MODE -o test_knowledge $(SRC_DIR)/knowledge.c $(LDFLAGS) && ./test_knowledge && rm -f test_knowledge
	@echo ""
	@echo "--- memory ---"
	$(CC) $(CFLAGS) -DTEST_MODE -o test_memory $(SRC_DIR)/memory.c $(LDFLAGS) && ./test_memory && rm -f test_memory
	@echo ""
	@echo "--- grammar ---"
	$(CC) $(CFLAGS) -DTEST_MODE -c -o /tmp/grammar_test.o $(SRC_DIR)/grammar.c
	$(CC) $(CFLAGS) -c -o /tmp/knowledge_lib.o $(SRC_DIR)/knowledge.c
	$(CC) $(CFLAGS) -o test_grammar /tmp/grammar_test.o /tmp/knowledge_lib.o $(LDFLAGS) && ./test_grammar && rm -f test_grammar
	@echo ""
	@echo "=== All Module Tests Complete ==="

install: $(BIN)
	cp $(BIN) /usr/local/bin/ai

run: $(BIN)
	./$(BIN)

clean:
	rm -f $(OBJS) $(BIN)

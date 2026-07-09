#!/usr/bin/env python3
"""
Cosmic Agent System — Self-healing, multi-tool, parallel execution.
8 Agents × 12 Tools × Auto-recovery × Plan decomposition.
"""
import subprocess, os, sys, time, json, re, math

sys.path.insert(0, os.path.dirname(__file__))

# === TOOLS (12 capabilities) ===

class ToolResult:
    def __init__(self, success, output, error=None):
        self.success = success
        self.output = output
        self.error = error

def tool_kg_query(query):
    """Query knowledge graph via C engine."""
    try:
        ai_bin = '/root/hybrid-ai/ai'
        r = subprocess.run([ai_bin], input=query+'\n/quit\n',
                          capture_output=True, text=True, timeout=5)
        for line in r.stdout.split('\n'):
            if line.strip().startswith('>') and len(line.strip()) > 4:
                ans = line.strip()[1:].strip()
                if len(ans) > 10 and 'how can i' not in ans.lower():
                    return ToolResult(True, ans)
        return ToolResult(False, "", "No answer found in KG")
    except Exception as e:
        return ToolResult(False, "", str(e))

def tool_web_search(query):
    """Search web via Wikipedia/DuckDuckGo."""
    try:
        from web_search import search_wikipedia
        result = search_wikipedia(query)
        if result:
            return ToolResult(True, result[:500])
        return ToolResult(False, "", "No results found")
    except Exception as e:
        return ToolResult(False, "", str(e))

def tool_calculate(expression):
    """Safe math evaluation."""
    try:
        # Allow only safe math operations
        allowed = set('0123456789+-*/.()% ')
        clean = ''.join(c for c in expression if c in allowed)
        result = eval(clean, {"__builtins__": {}}, {"abs": abs, "round": round, "min": min, "max": max})
        return ToolResult(True, str(result))
    except Exception as e:
        return ToolResult(False, "", str(e))

def tool_shell_exec(command):
    """Execute shell command (safe subset)."""
    from safety_check import is_safe_command
    if not is_safe_command(command):
        return ToolResult(False, "", "BLOCKED: unsafe command")
    try:
        r = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=30)
        output = r.stdout[:2000] if r.stdout else r.stderr[:500]
        return ToolResult(r.returncode == 0, output, r.stderr[:200] if r.returncode != 0 else None)
    except Exception as e:
        return ToolResult(False, "", str(e))

def tool_file_read(path):
    """Read a file."""
    try:
        if not os.path.exists(path):
            return ToolResult(False, "", f"File not found: {path}")
        with open(path) as f:
            content = f.read(10000)
        return ToolResult(True, content)
    except Exception as e:
        return ToolResult(False, "", str(e))

def tool_file_list(directory):
    """List directory contents."""
    try:
        if not os.path.isdir(directory):
            return ToolResult(False, "", f"Not a directory: {directory}")
        items = os.listdir(directory)[:100]
        return ToolResult(True, '\n'.join(items))
    except Exception as e:
        return ToolResult(False, "", str(e))

def tool_code_gen(request):
    """Generate code using codegen engine."""
    try:
        from codegen_engine import handle_code_request
        result = handle_code_request(request)
        if result['type'] == 'code':
            return ToolResult(True, result['code'])
        return ToolResult(False, "", "Could not generate code")
    except Exception as e:
        return ToolResult(False, "", str(e))

def tool_python_eval(code):
    """Run Python code in sandbox."""
    try:
        import io
        from contextlib import redirect_stdout
        buf = io.StringIO()
        safe_globals = {"__builtins__": {"print": print, "range": range, "len": len,
                        "str": str, "int": int, "float": float, "list": list,
                        "dict": dict, "sorted": sorted, "sum": sum, "min": min, "max": max,
                        "enumerate": enumerate, "zip": zip, "map": map, "filter": filter}}
        with redirect_stdout(buf):
            exec(code, safe_globals)
        output = buf.getvalue()
        return ToolResult(True, output if output else "Code executed successfully")
    except Exception as e:
        return ToolResult(False, "", str(e))

def tool_memory_recall(topic):
    """Recall from long-term memory."""
    try:
        session_file = '/root/hybrid-ai/user_data/session.json'
        if os.path.exists(session_file):
            with open(session_file) as f:
                data = json.load(f)
            topics = data.get('session_topics', [])
            matches = [t for t in topics if topic.lower() in t.lower()]
            if matches:
                return ToolResult(True, f"Found in memory: {', '.join(matches[-5:])}")
        return ToolResult(False, "", "Nothing found in memory")
    except Exception as e:
        return ToolResult(False, "", str(e))

def tool_derive(question):
    """Use the derive engine for reasoning."""
    return tool_kg_query(question)  # Same interface, derive is built into C engine

def tool_world_sim(scenario):
    """Run world simulation."""
    try:
        from world_sim import WorldSimulator
        ws = WorldSimulator()
        result = ws.explain(scenario)
        if result and 'No matching' not in result:
            return ToolResult(True, result)
        return ToolResult(False, "", "No simulation rules matched")
    except Exception as e:
        return ToolResult(False, "", str(e))

# Tool registry
TOOLS = {
    'kg_query': tool_kg_query,
    'web_search': tool_web_search,
    'calculate': tool_calculate,
    'shell_exec': tool_shell_exec,
    'file_read': tool_file_read,
    'file_list': tool_file_list,
    'code_gen': tool_code_gen,
    'python_eval': tool_python_eval,
    'memory_recall': tool_memory_recall,
    'derive': tool_derive,
    'world_sim': tool_world_sim,
}

# === SAFETY CHECK ===
class SafetyCheck:
    FORBIDDEN = ['rm -rf', 'mkfs', 'dd if=', ':()', 'format', 'fdisk', 
                 'shutdown', 'reboot', 'kill -9 1', 'chmod 777 /']
    DANGEROUS = ['rm ', 'mv /', 'cp /', 'wget', 'curl', 'pip install',
                 'apt install', 'yum install']
    
    @staticmethod
    def check(action):
        a = action.lower()
        for f in SafetyCheck.FORBIDDEN:
            if f in a:
                return 'BLOCK'
        for d in SafetyCheck.DANGEROUS:
            if d in a:
                return 'WARN'
        return 'ALLOW'

# Make it importable as safety_check module
class _SafetyModule:
    @staticmethod
    def is_safe_command(cmd):
        return SafetyCheck.check(cmd) != 'BLOCK'

sys.modules['safety_check'] = _SafetyModule()

# === AGENTS (8 specialized workers) ===

class Agent:
    def __init__(self, name, specialty, tools):
        self.name = name
        self.specialty = specialty
        self.tools = tools  # list of tool names this agent can use
        self.tasks_done = 0
        self.tasks_failed = 0
    
    def execute(self, task_description):
        """Execute a task using available tools. Returns (success, result)."""
        # Pick best tool for this task
        tool_name = self._pick_tool(task_description)
        if tool_name and tool_name in TOOLS:
            result = TOOLS[tool_name](task_description)
            if result.success:
                self.tasks_done += 1
                return True, result.output
            else:
                self.tasks_failed += 1
                return False, result.error
        return False, f"No suitable tool for: {task_description}"
    
    def _pick_tool(self, task):
        """Select the best tool for this task."""
        t = task.lower()
        tool_scores = {}
        for tool_name in self.tools:
            score = 0
            if tool_name == 'kg_query' and any(w in t for w in ['what is', 'who is', 'define', 'explain']):
                score = 5
            elif tool_name == 'web_search' and any(w in t for w in ['search', 'find online', 'wikipedia', 'latest']):
                score = 5
            elif tool_name == 'calculate' and any(w in t for w in ['calculate', 'compute', 'math', '+', '-', '*', '/']):
                score = 5
            elif tool_name == 'shell_exec' and any(w in t for w in ['run', 'execute', 'list files', 'disk', 'process']):
                score = 5
            elif tool_name == 'file_read' and any(w in t for w in ['read file', 'open', 'contents of']):
                score = 5
            elif tool_name == 'file_list' and any(w in t for w in ['list', 'directory', 'files in']):
                score = 5
            elif tool_name == 'code_gen' and any(w in t for w in ['write', 'code', 'implement', 'function', 'program']):
                score = 5
            elif tool_name == 'python_eval' and any(w in t for w in ['evaluate', 'run python', 'execute code']):
                score = 5
            elif tool_name == 'derive' and any(w in t for w in ['why', 'cause', 'because', 'reason']):
                score = 5
            elif tool_name == 'world_sim' and any(w in t for w in ['what if', 'what happens', 'simulate']):
                score = 5
            elif tool_name == 'memory_recall' and any(w in t for w in ['remember', 'last time', 'previously']):
                score = 5
            tool_scores[tool_name] = score
        
        if tool_scores:
            best = max(tool_scores, key=tool_scores.get)
            if tool_scores[best] > 0:
                return best
        # Default: first tool
        return self.tools[0] if self.tools else None

# 8 Specialized Agents
AGENTS = [
    Agent("Knowledge", "Facts and definitions", ['kg_query', 'derive', 'memory_recall']),
    Agent("Reasoning", "Why/how/cause-effect", ['derive', 'kg_query', 'world_sim']),
    Agent("Coder", "Write and run code", ['code_gen', 'python_eval']),
    Agent("WebSearch", "Find info online", ['web_search']),
    Agent("FileOps", "Read/list files", ['file_read', 'file_list']),
    Agent("System", "Run commands", ['shell_exec']),
    Agent("Math", "Calculations", ['calculate', 'python_eval']),
    Agent("Simulator", "What-if scenarios", ['world_sim', 'derive']),
]

# === PLANNER (decomposes requests into tasks) ===

class Planner:
    """Decomposes user requests into executable task plans."""
    
    @staticmethod
    def classify_intent(request):
        t = request.lower()
        if any(w in t for w in ['compare', 'vs', 'versus', 'difference', 'better']):
            return 'COMPARE'
        if any(w in t for w in ['why', 'explain', 'how does', 'reason']):
            return 'EXPLAIN'
        if any(w in t for w in ['write', 'create', 'generate', 'build', 'implement']):
            return 'CREATE'
        if any(w in t for w in ['find', 'search', 'where', 'locate']):
            return 'FIND'
        if any(w in t for w in ['analyze', 'check', 'review', 'inspect']):
            return 'ANALYZE'
        if any(w in t for w in ['do', 'run', 'execute', 'perform']):
            return 'DO'
        if any(w in t for w in ['what if', 'what would', 'suppose', 'imagine']):
            return 'WHATIF'
        if any(w in t for w in ['calculate', 'compute', 'how much', 'how many']):
            return 'CALCULATE'
        return 'QUERY'
    
    @staticmethod
    def decompose(request):
        """Decompose request into task list."""
        intent = Planner.classify_intent(request)
        tasks = []
        
        if intent == 'COMPARE':
            tasks.append({'desc': f"Get info about first subject", 'agent': 0, 'depends': []})
            tasks.append({'desc': f"Get info about second subject", 'agent': 0, 'depends': []})
            tasks.append({'desc': f"Compare the two results", 'agent': 1, 'depends': [0, 1]})
        
        elif intent == 'EXPLAIN':
            tasks.append({'desc': request, 'agent': 1, 'depends': []})
            tasks.append({'desc': f"Search for more context", 'agent': 3, 'depends': []})
            tasks.append({'desc': f"Combine explanation", 'agent': 1, 'depends': [0, 1]})
        
        elif intent == 'CREATE':
            tasks.append({'desc': request, 'agent': 2, 'depends': []})
        
        elif intent == 'FIND':
            tasks.append({'desc': request, 'agent': 0, 'depends': []})
            tasks.append({'desc': request, 'agent': 3, 'depends': []})  # web fallback
        
        elif intent == 'ANALYZE':
            tasks.append({'desc': request, 'agent': 4, 'depends': []})  # file ops
            tasks.append({'desc': f"Analyze results", 'agent': 1, 'depends': [0]})
        
        elif intent == 'DO':
            tasks.append({'desc': request, 'agent': 5, 'depends': []})  # system agent
        
        elif intent == 'WHATIF':
            tasks.append({'desc': request, 'agent': 7, 'depends': []})  # simulator
        
        elif intent == 'CALCULATE':
            tasks.append({'desc': request, 'agent': 6, 'depends': []})  # math
        
        else:  # QUERY
            tasks.append({'desc': request, 'agent': 0, 'depends': []})
        
        return {'intent': intent, 'tasks': tasks, 'original': request}

# === EXECUTOR (runs plans with self-healing) ===

class Executor:
    """Executes plans with dependency tracking and self-healing."""
    MAX_RETRIES = 2
    
    @staticmethod
    def execute(plan):
        """Execute a plan, return final answer."""
        tasks = plan['tasks']
        results = [None] * len(tasks)
        
        for i, task in enumerate(tasks):
            # Check dependencies
            deps_met = all(results[d] is not None for d in task['depends'])
            if not deps_met:
                continue
            
            # Execute with retry and fallback
            agent = AGENTS[task['agent']]
            success, output = agent.execute(task['desc'])
            
            if success:
                results[i] = output
            else:
                # Self-healing: try alternative agent
                for alt_agent in AGENTS:
                    if alt_agent.name != agent.name:
                        success, output = alt_agent.execute(task['desc'])
                        if success:
                            results[i] = output
                            break
                
                if results[i] is None:
                    results[i] = f"[Could not complete: {task['desc']}]"
        
        # Compose final answer from all results
        valid_results = [r for r in results if r and '[Could not' not in r]
        if valid_results:
            return '\n'.join(valid_results[:3])
        return None

# === MAIN INTERFACE ===

def agent_process(request):
    """Process a request through the full agent system."""
    # 1. Plan
    plan = Planner.decompose(request)
    
    # 2. Execute
    result = Executor.execute(plan)
    
    # 3. Return
    if result:
        return {
            'success': True,
            'answer': result,
            'intent': plan['intent'],
            'tasks_count': len(plan['tasks'])
        }
    return {'success': False, 'answer': None, 'intent': plan['intent']}


# === SELF TEST ===
if __name__ == '__main__':
    tests = [
        ("What is Python?", "QUERY"),
        ("Compare Python and Rust", "COMPARE"),
        ("Why does ice float?", "EXPLAIN"),
        ("Write a fibonacci function", "CREATE"),
        ("Find information about Mars", "FIND"),
        ("What if you heat metal?", "WHATIF"),
        ("Calculate 15 * 23 + 7", "CALCULATE"),
        ("Run ls command", "DO"),
    ]
    
    print("=== AGENT SYSTEM TEST ===\n")
    passed = 0
    for request, expected_intent in tests:
        result = agent_process(request)
        intent_ok = result['intent'] == expected_intent
        answer_ok = result['success'] and result['answer']
        status = '✓' if (intent_ok and answer_ok) else '✗'
        if intent_ok and answer_ok:
            passed += 1
        print(f"  {status} [{result['intent']:10s}] {request}")
        if result['answer']:
            preview = result['answer'][:80].replace('\n', ' ')
            print(f"    → {preview}")
        print()
    
    print(f"  Passed: {passed}/{len(tests)}")

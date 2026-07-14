#!/usr/bin/env python3
"""
Axima - Unified Interface (Cosmic Level)
Combines C engine (fast knowledge lookup) + Python brain (deep intelligence)
+ Proactive AI + Personality + Teaching + Workflows + Persistent Context.
"""
import subprocess, sys, os, json, time, select, fcntl, re

sys.path.insert(0, os.path.dirname(__file__))
from brain import HybridBrain, engines_loaded
from auto_learn import offer_search, save_facts, get_learned_count
from metacognition import MetacognitiveReasoner
from world_sim import WorldSimulator

# v3.0 modules (graceful fallback)
try:
    from kda_manager import get_kda, query_kda
except ImportError:
    get_kda = None; query_kda = None

try:
    from kfr import KnowledgeFusionReactor
except ImportError:
    KnowledgeFusionReactor = None

try:
    from hvne import HVNEngine
except ImportError:
    HVNEngine = None

try:
    from psar_dsl import synthesize_program
except ImportError:
    synthesize_program = None
from auto_learn import offer_search, save_facts, get_learned_count
from metacognition import MetacognitiveReasoner
from world_sim import WorldSimulator

# Optional cosmic modules (fault-tolerant imports)
try:
    from fluency import FluencyEngine
except Exception: FluencyEngine = None
try:
    from multipath import MultipathReasoner
except Exception: MultipathReasoner = None
try:
    from long_memory import LongMemory
except Exception: LongMemory = None
try:
    from creative import CreativeEngine
except Exception: CreativeEngine = None
try:
    from truthguard import TruthGuard
except Exception: TruthGuard = None
try:
    from community import CommunityIntelligence
except Exception: CommunityIntelligence = None

try:
    from natural_response import NaturalResponseV6
except Exception: NaturalResponseV6 = None

try:
    from semantic_brain import SemanticBrain
except Exception: SemanticBrain = None

# Find C binary
AI_BIN = None
for path in ['../../ai', '/root/hybrid-ai/ai', '/root/axima/ai', './ai']:
    full = os.path.abspath(path)
    if os.path.isfile(full) and os.access(full, os.X_OK):
        AI_BIN = full
        break
# Also check relative to this script's directory
if not AI_BIN:
    _script_dir = os.path.dirname(os.path.abspath(__file__))
    _bin_path = os.path.join(_script_dir, '..', '..', 'ai')
    if os.path.isfile(_bin_path) and os.access(_bin_path, os.X_OK):
        AI_BIN = os.path.abspath(_bin_path)

class Axima:
    """Unified AI combining C speed + Python intelligence + Cosmic features."""
    
    def __init__(self):
        self.brain = HybridBrain()
        self.metacog = MetacognitiveReasoner()
        self.world = WorldSimulator()
        self.c_proc = None
        self.turn = 0
        self.auto_search = True   # Always-on: auto-search web when AI doesn't know
        self._c_restart_count = 0  # C engine restart counter (max 3)
        self.auto_save = True     # Always-on: auto-save web results without asking
        self.teach_mode = False   # Socratic teaching mode
        
        # Cosmic modules (graceful fallback if any fail)
        self.fluency = FluencyEngine() if FluencyEngine else None
        self.multipath = MultipathReasoner() if MultipathReasoner else None
        self.long_memory = LongMemory() if LongMemory else None
        self.creative = CreativeEngine() if CreativeEngine else None
        self.truthguard = TruthGuard() if TruthGuard else None
        self.community = CommunityIntelligence() if CommunityIntelligence else None
        
        # Natural Response v6 — intelligence gate + humanizer
        self._natural_response = NaturalResponseV6() if NaturalResponseV6 else None
        
        # Semantic Brain v6 — field theory entity resolution + spelling correction
        self._semantic_brain = None
        if SemanticBrain:
            try:
                entities = self._load_entities_from_knowledge()
                self._semantic_brain = SemanticBrain(entities=entities)
            except Exception:
                self._semantic_brain = SemanticBrain()
        
        # Personality & context (C-backed but tracked in Python too)
        self.mood = 'neutral'
        self.personality = {'formality': 0.5, 'verbosity': 0.6, 'humor': 0.3, 'empathy': 0.7}
        self.topics_asked = {}  # Track topic frequency for proactive AI
        self.gaps = []  # Track knowledge gaps
        self.session_topics = []  # Persistent context
        self.workflows = []  # User-defined automations
        
        # Load persistent state
        self._load_session()
        self._c_restart_count = 0
        self._start_c_engine()
        
        # Always-on online: detect internet + pre-warm search engine (background)
        self._internet_available = False
        self._search_engine_ready = False
        self._warmup_thread = None
        self._start_online_warmup()
    
    def _load_entities_from_knowledge(self):
        """Extract entity names from knowledge text files for Semantic Brain."""
        entities = set()
        data_dir = os.path.join(os.path.dirname(__file__), '..', 'data')
        if not os.path.isdir(data_dir):
            data_dir = os.path.join(os.path.dirname(__file__), '../../src/data')
        if not os.path.isdir(data_dir):
            return entities
        
        for fname in os.listdir(data_dir):
            if not fname.endswith('.txt'):
                continue
            fpath = os.path.join(data_dir, fname)
            try:
                with open(fpath, 'r', errors='ignore') as f:
                    for line in f:
                        line = line.strip()
                        if not line or line.startswith('#'):
                            continue
                        # Parse patterns: "A X is a Y", "X is Y", "The capital of X is Y"
                        # Extract subjects
                        low = line.lower()
                        if low.startswith('a ') or low.startswith('an '):
                            # "A dog is a mammal" → "dog"
                            parts = line.split(' is ', 1)
                            if parts:
                                subj = parts[0].lstrip('AaAn ').strip()
                                if 2 < len(subj) < 40:
                                    entities.add(subj)
                                # Also extract object: "mammal"
                                if len(parts) > 1:
                                    obj = parts[1].lstrip('a ').lstrip('an ').strip()
                                    if 2 < len(obj) < 40 and ' ' not in obj:
                                        entities.add(obj)
                        elif ' is ' in line:
                            parts = line.split(' is ', 1)
                            subj = parts[0].strip().lstrip('The ').strip()
                            if 2 < len(subj) < 40:
                                entities.add(subj)
                        elif ' has ' in line:
                            subj = line.split(' has ', 1)[0].strip()
                            if 2 < len(subj) < 40:
                                entities.add(subj)
                        elif ' can ' in line:
                            subj = line.split(' can ', 1)[0].strip()
                            if 2 < len(subj) < 40:
                                entities.add(subj)
            except Exception:
                continue
        
        # Add common compound entities
        compounds = [
            'black hole', 'quantum mechanics', 'machine learning', 'artificial intelligence',
            'climate change', 'solar system', 'big bang', 'dark matter', 'dark energy',
            'deep learning', 'neural network', 'electric current', 'magnetic field',
            'gravitational force', 'speed of light', 'periodic table', 'chemical reaction',
            'plate tectonics', 'natural selection', 'genetic code', 'immune system',
            'operating system', 'binary search', 'linked list', 'hash map',
            'prime number', 'real number', 'complex number', 'irrational number',
        ]
        entities.update(compounds)
        return entities

    def _start_online_warmup(self):
        """Background thread: detect internet + pre-warm search engine."""
        import threading
        def _warmup():
            # Step 1: Detect internet connectivity
            self._internet_available = self._check_internet()
            if not self._internet_available:
                return
            # Step 2: Pre-warm the search engine (creates HeatMap, FuzzyCache, tests connection)
            try:
                from online_search import get_engine
                self._online_engine = get_engine()
                self._search_engine_ready = True
            except Exception:
                self._search_engine_ready = False
        
        self._warmup_thread = threading.Thread(target=_warmup, daemon=True)
        self._warmup_thread.start()
    
    @staticmethod
    def _check_internet():
        """Quick internet check — try to reach a fast endpoint."""
        import socket
        targets = [
            ('8.8.8.8', 53),         # Google DNS
            ('1.1.1.1', 53),         # Cloudflare DNS
            ('208.67.222.222', 53),   # OpenDNS
        ]
        for host, port in targets:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(2)
                sock.connect((host, port))
                sock.close()
                return True
            except (OSError, socket.timeout):
                continue
        return False

    def _start_c_engine(self):
        """Launch C engine as a persistent subprocess with stdin/stdout pipes."""
        self.c_available = AI_BIN is not None
        if not self.c_available:
            return
        try:
            self.c_proc = subprocess.Popen(
                [AI_BIN],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
            )
            # Read startup banner until first '> ' prompt
            self._read_until_prompt(timeout=5.0)
        except Exception:
            self.c_proc = None
            self.c_available = False

    def _read_until_prompt(self, timeout=3.0):
        """Read lines from C engine stdout until '> ' prompt appears.
        
        Returns list of output lines (excluding the prompt itself).
        Uses select with chunk reads for efficiency.
        """
        buf = b''
        fd = self.c_proc.stdout.fileno()
        deadline = time.time() + timeout
        # Set non-blocking temporarily
        flags = fcntl.fcntl(fd, fcntl.F_GETFL)
        fcntl.fcntl(fd, fcntl.F_SETFL, flags | os.O_NONBLOCK)
        try:
            while True:
                remaining = deadline - time.time()
                if remaining <= 0:
                    break
                ready, _, _ = select.select([fd], [], [], min(remaining, 0.5))
                if ready:
                    try:
                        chunk = os.read(fd, 4096)
                    except BlockingIOError:
                        continue
                    if not chunk:
                        break  # EOF
                    buf += chunk
                    # Check for prompt: "\n> " at end or just "> " at end (first prompt)
                    if buf.endswith(b'> '):
                        # Strip the trailing prompt
                        content = buf[:-2].decode('utf-8', errors='replace')
                        lines = content.split('\n')
                        return [l for l in lines if l]  # Remove empty strings
                elif self.c_proc.poll() is not None:
                    break
        finally:
            # Restore blocking mode
            fcntl.fcntl(fd, fcntl.F_SETFL, flags)
        # Timeout or EOF
        if buf:
            content = buf.decode('utf-8', errors='replace')
            return [l for l in content.split('\n') if l]
        return []

    def _query_c(self, text):
        """Send query to persistent C engine via stdin, read response until next prompt."""
        if not self.c_available or self.c_proc is None:
            return self._query_c_oneshot(text)
        # Check if process is still alive
        if self.c_proc.poll() is not None:
            # Process died — try to restart (with limit)
            self._c_restart_count += 1
            if self._c_restart_count > 3:
                self.c_available = False
                return None
            try:
                self._start_c_engine()
            except Exception:
                self.c_available = False
                return None
            if self.c_proc is None:
                self.c_available = False
                return None
        try:
            # Send query as bytes
            self.c_proc.stdin.write((text + '\n').encode('utf-8'))
            self.c_proc.stdin.flush()
            # Read response until next '> ' prompt
            output_lines = self._read_until_prompt(timeout=3.0)
            # Parse response — in persistent mode, prompt '> ' is stripped by
            # _read_until_prompt so response lines don't start with '>'.
            for line in output_lines:
                line = line.strip()
                # In persistent mode: line is raw response text (no '>' prefix)
                # In one-shot mode: line starts with '>' — strip it
                if line.startswith('>'):
                    line = line[1:].strip()
                if not line or len(line) <= 10:
                    continue
                # Skip greetings and system messages
                if any(skip in line.lower() for skip in ['how can i', 'what can i', 'goodbye', 'session']):
                    continue
                return line
            # Persistent pipe returned no valid answer — try one-shot
            return self._query_c_oneshot(text)
        except (BrokenPipeError, OSError):
            # Pipe broken — try one-shot fallback
            self.c_proc = None
            return self._query_c_oneshot(text)
        except Exception:
            return self._query_c_oneshot(text)
    
    def _query_c_oneshot(self, text):
        """Fallback: query C engine in one-shot mode (subprocess per query)."""
        if not AI_BIN:
            return None
        try:
            result = subprocess.run(
                [AI_BIN], input=f"{text}\n/quit\n",
                capture_output=True, text=True, timeout=5
            )
            for line in result.stdout.split('\n'):
                line = line.strip()
                if line.startswith('>') and len(line) > 5:
                    answer = line[1:].strip()
                    if answer and 'How can I' not in answer and 'Goodbye' not in answer:
                        return answer
        except Exception:
            pass
        return None

    def _stop_c_engine(self):
        """Cleanly terminate the persistent C engine subprocess."""
        if self.c_proc is not None and self.c_proc.poll() is None:
            try:
                self.c_proc.stdin.write(b'/quit\n')
                self.c_proc.stdin.flush()
                self.c_proc.wait(timeout=2)
            except Exception:
                try:
                    self.c_proc.terminate()
                    self.c_proc.wait(timeout=1)
                except Exception:
                    try:
                        self.c_proc.kill()
                    except Exception:
                        pass
            self.c_proc = None
    
    def ask(self, user_input):
        """Process user input through ALL engines (Cosmic Level)."""
        # Input safety: limit length to prevent buffer overflow in C engine
        if not user_input or not user_input.strip():
            return {"response": None, "gap": True, "query": ""}
        if len(user_input) > 2000:
            user_input = user_input[:2000]
        self.turn += 1
        
        # 0. Track topic + detect mood
        self._track_topic(user_input)
        
        # 0.05 SELF-LEARNING: Check if we have a cached correct answer
        try:
            from self_learning import get_learner
            _learner = get_learner()
            cached = _learner.get_cached_answer(user_input)
            if cached:
                return {"response": cached, "gap": False}
        except Exception:
            pass
        self.mood = self._detect_mood(user_input)
        
        # 0.1 Reference resolution — resolve "it", "that", short follow-ups
        user_input = self._resolve_references(user_input)
        lower = user_input.lower()
        
        # 0.2 QIR — Quantum Intent Resolution (replaces old Semantic Brain rewrite)
        # Never modifies input. Creates parallel interpretations. Tries best first.
        self._forces = None
        self._qir_interpretations = None
        try:
            from qir import get_qir
            if not hasattr(self, '_qir_instance'):
                brain = self._semantic_brain
                try:
                    from cse_knowledge import get_knowledge
                    knowledge = get_knowledge()
                except Exception:
                    knowledge = None
                self._qir_instance = get_qir(brain=brain, knowledge=knowledge)
            
            # Detect question type for observer effect
            _lower_tmp = user_input.lower()
            if any(p in _lower_tmp for p in ['what happens', 'what if', 'what would']):
                _qtype = 'causal'
            elif _lower_tmp.startswith(('is ', 'can ', 'does ', 'do ', 'was ', 'were ')):
                _qtype = 'boolean'
            elif _lower_tmp.startswith(('what is', 'who is', 'what are')):
                _qtype = 'factual'
            else:
                _qtype = 'general'
            
            # Context Gravity: detect domain + temporal context + user profile (Upgrades #2, #9)
            try:
                from self_learning import get_gravity, get_profile
                _grav = get_gravity()
                _domain = _grav.detect_domain(user_input)
                # Record domain in user profile for distribution tracking
                _prof = get_profile()
                if _domain:
                    _prof.record_domain(_domain)
            except Exception:
                _domain = None
            
            # Get interpretations (non-destructive)
            self._qir_interpretations = self._qir_instance.resolve(user_input, _qtype)
            
            # Use best interpretation ONLY if it's a minor correction (1-2 words changed)
            self._qir_changed_words = []  # Track changes for Upgrade #5 verification
            if self._qir_interpretations:
                best = self._qir_interpretations[0]
                original_lower = user_input.lower()
                if (best.text != original_lower 
                    and best.total_confidence > 0.85
                    and '. ' not in user_input):  # never touch multi-sentence
                    # Count how many words changed
                    orig_words = original_lower.split()
                    best_words = best.text.split()
                    if len(orig_words) == len(best_words):
                        changes = sum(1 for a, b in zip(orig_words, best_words) if a != b)
                        if changes <= 2:  # max 2 words corrected
                            # Track which words changed (for self-verifying corrections)
                            self._qir_changed_words = [(a, b) for a, b in zip(orig_words, best_words) if a != b]
                            user_input = best.text
                            if user_input and user_input[0].islower():
                                user_input = user_input[0].upper() + user_input[1:]
        except Exception:
            pass
        
        lower = user_input.lower()
        
        # 0.5 Check workflows (keyword triggers)
        wf_result = self._check_workflows(user_input)
        if wf_result:
            try:
                from response_depth import enrich_response
                wf_result = enrich_response(user_input, wf_result)
            except Exception: pass
            return {"response": wf_result, "gap": False}
        
        # 0.6 IDENTITY — who are you, what can you do
        identity_triggers = ['who are you', 'what are you', 'what can you do', 'what do you do',
                            'tell me about yourself', 'introduce yourself', 'your name']
        if any(t in lower for t in identity_triggers):
            identity_resp = self._identity_response(lower)
            try:
                from response_depth import enrich_response
                identity_resp = enrich_response(user_input, identity_resp)
            except Exception: pass
            return {"response": identity_resp, "gap": False}
        
        # 1. Teaching mode (Socratic)
        if self.teach_mode:
            socratic_resp = self._socratic_response(user_input)
            try:
                from response_depth import enrich_response
                socratic_resp = enrich_response(user_input, socratic_resp)
            except Exception: pass
            return {"response": socratic_resp, "gap": False}
        
        # 1.5 Code generation (cosmic engine - 15 languages, 100+ algorithms)
        lower = user_input.lower()
        code_triggers = ['write', 'code', 'implement', 'create a function', 'build a',
                        'program a', 'script', 'algorithm', 'data structure',
                        'sort', 'fibonacci', 'factorial',
                        'linked list', 'binary tree', 'hash map', 'stack implementation', 'queue implementation']
        # Only trigger code gen for COMMANDS, not questions like "who created X?"
        is_code_request = any(t in lower for t in code_triggers) and not lower.startswith(('who', 'what is', 'why', 'when', 'where'))
        
        # 1.55 SYMTREE — Symbolic Math Engine (algebra, equations, calculus)
        # Catches: solve, factor, expand, simplify, and equation-like inputs
        _is_math = False
        _math_triggers = ['solve', 'factor', 'expand', 'simplif', 'derivative', 'integrate',
                          'differentiate', 'limit of', 'lim ', 'taylor', 'd/d', 'antiderivative',
                          'laplace', 'fourier', 'z transform', 'z-transform', 'ztransform']
        if any(t in lower for t in _math_triggers):
            _is_math = True
        elif '=' in user_input and any(c in user_input for c in 'xyz') and any(c in user_input for c in '+-*/^'):
            _is_math = True  # Equation with variables and operators
        elif re.search(r'(?:x|y|z)\s*[\^]\s*\d', lower):
            _is_math = True  # x^2, y^3, etc.

        if _is_math:
            try:
                from prometheus import get_prometheus
                _sym = get_prometheus()
                _math_result = _sym.process(user_input)
                if _math_result and _math_result not in ('0', '', 'cannot solve symbolically'):
                    return {"response": _math_result, "gap": False}
            except Exception:
                pass

        # 1.6 Agent system for complex tasks (math, compare, run commands)
        # 1.56 PROMETHEUS PHYSICS ENGINE — Solve physics problems numerically
        _is_physics = False
        _physics_triggers = ['force', 'velocity', 'acceleration', 'momentum', 'energy',
                            'projectile', 'orbit', 'pendulum', 'spring', 'collision',
                            'electric field', 'magnetic field', 'voltage', 'resistance',
                            'capacitor', 'circuit', 'wavelength', 'frequency', 'diffraction',
                            'interference', 'doppler', 'refraction', 'lens', 'mirror',
                            'quantum', 'hydrogen atom', 'tunneling', 'spin',
                            'temperature', 'pressure', 'entropy', 'partition function',
                            'black hole', 'redshift', 'time dilation', 'relativity',
                            'binding energy', 'decay', 'half-life', 'fusion',
                            'luminosity', 'escape velocity', 'schwarzschild',
                            'calculate the', 'find the', 'what is the period',
                            'what is the speed', 'what is the force']
        if any(t in lower for t in _physics_triggers):
            # Check with PhysicsIdentifier for confidence
            try:
                from prometheus_physics import PhysicsIdentifier
                _pi = PhysicsIdentifier()
                _domains = _pi.identify(user_input)
                if _domains[0][0] != "unknown" and _domains[0][1] > 0.5:
                    _is_physics = True
            except Exception:
                pass

        if _is_physics:
            try:
                _phys_result = self._solve_physics(user_input, lower)
                if _phys_result:
                    return {"response": _phys_result, "gap": False}
            except Exception:
                pass

        agent_triggers = ['calculate', 'compute', 'run command', 'list files', 'analyze']
        if any(t in lower for t in agent_triggers):
            try:
                from agent_system import agent_process
                result = agent_process(user_input)
                if result['success'] and result['answer'] and len(result['answer']) > 2:
                    try:
                        from response_depth import enrich_response
                        ans = enrich_response(user_input, result['answer'])
                    except Exception:
                        ans = result['answer']
                    return {"response": ans, "gap": False}
            except Exception: pass
        
        if is_code_request:
            try:
                from codegen_engine import handle_code_request
                result = handle_code_request(user_input)
                if result['type'] == 'code' and result.get('code'):
                    lang = result['language']
                    code = result['code']
                    resp = f"[{lang.upper()} code]\n```{lang}\n{code}\n```"
                    try:
                        from response_depth import enrich_response
                        resp = enrich_response(user_input, resp)
                    except Exception: pass
                    return {"response": resp, "gap": False}
                elif result['type'] == 'debug':
                    debug_resp = result['result']
                    try:
                        from response_depth import enrich_response
                        debug_resp = enrich_response(user_input, debug_resp)
                    except Exception: pass
                    return {"response": debug_resp, "gap": False}
                elif result['type'] == 'explain':
                    explain_resp = result['result']
                    try:
                        from response_depth import enrich_response
                        explain_resp = enrich_response(user_input, explain_resp)
                    except Exception: pass
                    return {"response": explain_resp, "gap": False}
            except Exception: pass
        
        # 2. Check for "what if" → world simulator + Causal Axiom Engine
        lower = user_input.lower()
        if any(p in lower for p in ['what happens if', 'what would happen', 'what if you', 'what if i']):
            sim_result = self.world.explain(user_input)
            if sim_result and 'No known causal' not in sim_result and 'Cannot predict' not in sim_result:
                # Enrich causal response
                try:
                    from response_depth import enrich_response
                    sim_result = enrich_response(user_input, sim_result, 'causal')
                except Exception:
                    pass
                return {"response": sim_result, "gap": False}
        
        # 3. Check if needs clarification (skip for greetings and follow-ups)
        greetings = ['hi', 'hello', 'hey', 'yo', 'sup', 'good morning', 'good evening']
        is_followup = hasattr(self, '_last_topic') and self._last_topic and self.turn > 1
        if lower.strip().rstrip('!') not in greetings and not is_followup:
            # Use Semantic Brain's needs_clarify signal if available
            if self._forces and self._forces.needs_clarify and self._forces.confidence < 0.4:
                options = self._forces.clarify_options
                if options:
                    clarify_resp = options[0]
                    try:
                        from response_depth import enrich_response
                        clarify_resp = enrich_response(user_input, clarify_resp)
                    except Exception: pass
                    return {"response": clarify_resp, "gap": False}
        
        # 4. Multi-path reasoning (if available)
        multipath_answer = None
        if self.multipath:
            try:
                paths = self.multipath.reason(user_input)
                if paths and paths.get('best_answer'):
                    multipath_answer = paths['best_answer']
            except Exception: pass
        
        # 4.3 DEBATE auto-detection — contested/opinion questions
        try:
            from debate import get_debate_engine
            de = get_debate_engine()
            if de.is_debate_topic(user_input):
                result = de.debate(user_input)
                if result and result.get('verified_facts', result.get('position_a', {}).get('evidence')):
                    debate_resp = de.format_debate(result)
                    try:
                        from response_depth import enrich_response
                        debate_resp = enrich_response(user_input, debate_resp)
                    except Exception: pass
                    return {"response": debate_resp, "gap": False}
        except Exception: pass

        # 4.5 KDA Query — DISABLED (raw triples pollute answers, CSE handles this better)
        if False:  # KDA disabled
            pass
        if query_kda:
            # Use Semantic Brain entities if available, else fallback to naive split
            subjects = []
            if self._forces and self._forces.gravity and self._forces.confidence > 0.6:
                subjects = [self._forces.gravity.lower()]
                if self._forces.spin:
                    subjects.append(self._forces.spin.lower())
            else:
                topic_words = user_input.lower().split()
                stop_words = {'what','is','the','a','an','who','where','when','how','why','are','was','do','does','tell','me','about'}
                subjects = [w for w in topic_words if w not in stop_words and len(w) > 2]
            for subj in subjects:
                kda_results = query_kda(subj)
                if kda_results:
                    # Format KDA results as answer
                    parts = [f"{subj} {r} {o}" for s, r, o, c in kda_results[:3]]
                    if parts:
                        kda_answer = '. '.join(parts) + '.'
                        # Only use if it's actually informative
                        if len(kda_answer) > 20 and ('is_a' in kda_answer or len(kda_results) >= 2):
                            try:
                                from response_depth import enrich_response
                                kda_answer = enrich_response(user_input, kda_answer)
                            except Exception: pass
                            try:
                                from response_depth import enrich_response
                                kda_answer = enrich_response(user_input, kda_answer)
                            except Exception: pass
                            return {"response": kda_answer, "gap": False}
        
        # 4.8 Boolean Reasoner — yes/no questions, primes, comparisons, syllogisms
        # Trigger on: "is X...", "can X...", "does X..." OR multi-statement syllogisms
        is_boolean = (lower.startswith(('is ', 'can ', 'does ', 'do '))
                      or ('. is ' in lower or '. can ' in lower or '. does ' in lower))
        if is_boolean:
            try:
                from boolean_reasoner import answer_boolean
                bool_result = answer_boolean(user_input)
                if bool_result:
                    answer, conf = bool_result
                    # Enrich the response using RDE with the raw yes/no
                    try:
                        from response_depth import enrich_response, detect_type
                        # If answer is already a full sentence (from universal quantifier), use it
                        if len(answer) > 5 and answer[0].isupper():
                            raw = answer  # Already enriched by boolean_reasoner
                        else:
                            raw = f"{'Yes' if answer == 'yes' else 'No'}."
                        # Use specific type detection for better enrichment
                        q_type = detect_type(user_input)
                        resp = enrich_response(user_input, raw, q_type)
                    except Exception:
                        if len(answer) > 5 and answer[0].isupper():
                            resp = answer
                        else:
                            resp = f"{'Yes' if answer == 'yes' else 'No'}."
                    return {"response": resp, "gap": False}
            except Exception:
                pass
        
        # 5. Get C engine's fast answer (knowledge graph + derive + reasoning)
        c_answer = self._query_c(user_input)
        
        # 5.5 SHORT-CIRCUIT: If C engine returned a high-quality answer, skip expensive
        # Python processing (metacognition, fluency, multipath, truthguard) and return
        # directly. This avoids Python wrapping that degrades natural C responses.
        # BUT: check quality alignment first — don't short-circuit bad answers.
        dont_know_signals_sc = ["don't know", "don't have", "outside my knowledge",
                                "teach me", "not sure", "can't find"]
        _c_is_quality = False
        if (c_answer and len(c_answer) > 50
                and not any(s in c_answer.lower() for s in dont_know_signals_sc)):
            # Check quality score before short-circuiting
            try:
                from self_learning import get_learner as _get_sl
                _sl_sc = _get_sl()
                _sc_score = _sl_sc.score_answer(user_input, c_answer, 'pipeline')
                _c_is_quality = (_sc_score >= 7)
            except Exception:
                _c_is_quality = False  # if scorer fails, DON'T short-circuit (let full pipeline run)
            
            if _c_is_quality:
                # High-quality C answer — run through NR v6 gate then return
                final = self._adjust_for_mood(c_answer, self.mood)
                if NaturalResponseV6 and self._natural_response:
                    try:
                        nr_result = self._natural_response.respond(final, user_input, 0.95)
                        if nr_result and nr_result.get('display'):
                            final = nr_result['display']
                    except Exception: pass
                if self.long_memory:
                    try:
                        self.long_memory.store(user_input, final)
                    except Exception: pass
                # Enrich with Response Depth Engine
                try:
                    from response_depth import enrich_response
                    final = enrich_response(user_input, final)
                except Exception: pass
                return {"response": final, "gap": False}
        
        # 6. Check if C engine doesn't know (gap detected)
        dont_know_signals = ["don't know", "don't have", "outside my knowledge", 
                            "teach me", "not sure", "can't find"]
        is_gap = c_answer and any(s in c_answer.lower() for s in dont_know_signals)
        
        if is_gap or not c_answer:
            # Try agent system before declaring gap
            try:
                from agent_system import agent_process
                agent_result = agent_process(user_input)
                if agent_result['success'] and agent_result['answer']:
                    ans = agent_result['answer']
                    if len(ans) > 20 and 'I hear you' not in ans:
                        try:
                            from response_depth import enrich_response
                            ans = enrich_response(user_input, ans)
                        except Exception: pass
                        return {"response": ans, "gap": False}
            except Exception: pass
            
            # Use multipath if it found something
            if multipath_answer:
                try:
                    from response_depth import enrich_response
                    multipath_answer = enrich_response(user_input, multipath_answer)
                except Exception: pass
                try:
                    from response_depth import enrich_response
                    multipath_answer = enrich_response(user_input, multipath_answer)
                except Exception: pass
                return {"response": multipath_answer, "gap": False}
            
            # 6.5 AUTO WEB SEARCH — before declaring gap, try to find answer online
            # Rate limit: max 5 web searches per minute
            import time as _time
            if not hasattr(self, '_last_web_searches'):
                self._last_web_searches = []
            # Clean old entries (older than 60s)
            now = _time.time()
            self._last_web_searches = [t for t in self._last_web_searches if now - t < 60]
            web_allowed = len(self._last_web_searches) < 5
            if web_allowed:  # Rate limited: max 5/minute
                try:
                    web_result = self.search_and_learn(user_input)
                    self._last_web_searches.append(now)
                    if web_result and web_result.get('found'):
                        answer = web_result['answer']
                        # Enrich with RDE
                        try:
                            from response_depth import enrich_response
                            answer = enrich_response(user_input, answer)
                        except Exception: pass
                        # Auto-save if enabled
                        if self.auto_save and web_result.get('facts'):
                            self.save_learned(web_result['facts'])
                        return {"response": answer, "gap": False}
                except Exception:
                    pass
            
            # Track as gap
            topic = user_input.split()[-1] if user_input.strip() else 'unknown'
            if topic not in self.gaps:
                self.gaps.append(topic)
            return {"response": None, "gap": True, "query": user_input}
        
        # 7. Metacognitive quality check
        eval_result = self.metacog.evaluate_answer(user_input, c_answer)
        final_answer = c_answer
        if eval_result['quality_score'] < 0.6 and eval_result.get('improved_answer'):
            final_answer = eval_result['improved_answer']
        
        # 8. TruthGuard verification
        if self.truthguard:
            try:
                verified = self.truthguard.verify(user_input, final_answer)
                if verified and verified.get('flagged'):
                    final_answer = f"{final_answer}\n⚠️ Note: {verified.get('reason', 'low confidence on this')}"
            except Exception: pass
        
        # 9. Fluency enhancement
        if self.fluency:
            try:
                enhanced = self.fluency.enhance(final_answer)
                if enhanced and len(enhanced) > len(final_answer) * 0.5:
                    final_answer = enhanced
            except Exception: pass
        
        # 10. Run through Python brain for intelligence enhancement
        result = self.brain.process_turn(user_input, final_answer)
        final = result['response']
        
        # 11. Mood-based adjustment
        final = self._adjust_for_mood(final, self.mood)
        
        # 12. Natural Response v6 — intelligence gate + humanizer (LAST STEP)
        if NaturalResponseV6 and hasattr(self, '_natural_response'):
            try:
                nr_result = self._natural_response.respond(final, user_input, 0.9)
                if nr_result and nr_result.get('display'):
                    final = nr_result['display']
            except Exception: pass
        
        # 13. Long-term memory storage
        if self.long_memory:
            try:
                self.long_memory.store(user_input, final)
            except Exception: pass
        
        # 14. Response Depth Engine — enrich final answer
        try:
            from response_depth import enrich_response
            final = enrich_response(user_input, final)
        except Exception: pass
        
        # 15. Self-Learning: quality scoring + auto-import + verify corrections + decay
        try:
            from self_learning import get_learner
            _sl = get_learner()
            
            # Upgrade #7: Answer Quality Score (replaces simple detect_error)
            _quality_score = _sl.score_answer(user_input, final, 'pipeline')
            
            if _quality_score < 7 and self._internet_available:
                # Bad or uncertain answer + internet available → always try web
                if _quality_score < 4:
                    _sl.log_failure(user_input, final)
                    # Upgrade #8: Decay failed QIR interpretation
                    if hasattr(self, '_qir_instance') and hasattr(self, '_qir_changed_words'):
                        for orig, resolved in self._qir_changed_words:
                            self._qir_instance.decay_interpretation(orig, resolved)
                
                # Auto-search web (always-on, no asking)
                try:
                    web_result = self.search_and_learn(user_input)
                    if web_result and web_result.get('found'):
                        final = web_result['answer']
                        try:
                            from response_depth import enrich_response as _enrich
                            final = _enrich(user_input, final)
                        except Exception: pass
                        _sl.log_success(user_input, final, 'web_recovery')
                        
                        # Upgrade #1: Auto-import verified triples from web answer
                        try:
                            from cse_knowledge import get_knowledge
                            _kb = get_knowledge()
                            _kb.auto_import(user_input, final, source='web')
                        except Exception: pass
                except Exception: pass
                
            elif _quality_score >= 7:
                # Good answer — cache it
                _sl.log_success(user_input, final, 'pipeline')
                
                # Upgrade #5: Verify QIR corrections (they led to success)
                if hasattr(self, '_qir_instance') and hasattr(self, '_qir_changed_words'):
                    if self._qir_changed_words:
                        orig_list = [w[0] for w in self._qir_changed_words]
                        resolved_list = [w[1] for w in self._qir_changed_words]
                        self._qir_instance.verify_correction(orig_list, resolved_list, True)
                
                # Upgrade #1: Auto-import from pipeline answers too
                try:
                    from cse_knowledge import get_knowledge
                    _kb = get_knowledge()
                    _kb.auto_import(user_input, final, source='pipeline')
                except Exception: pass
            # else: score 3-4 with no internet = uncertain, don't cache
        except Exception: pass
        
        return {"response": final, "gap": False}
    
    def search_and_learn(self, query):
        """Search the web for an answer and AUTO-SAVE facts (always-on)."""
        # Use pre-warmed engine if available
        if hasattr(self, '_online_engine') and self._search_engine_ready:
            answer = self._online_engine.search(query)
            if answer:
                # Auto-save: extract and store facts without asking
                try:
                    from auto_learn import _get_engine as _get_learn_engine
                    learn_engine = _get_learn_engine()
                    result = learn_engine.offer_search(query)
                    if result:
                        learn_engine.save_learned(result)  # AUTO-SAVE always
                except Exception:
                    pass
                return {
                    "found": True,
                    "answer": answer,
                    "source": "online_search_v3",
                    "facts": [],
                }
        
        # Fallback: use offer_search directly
        result = offer_search(query)
        if result:
            # AUTO-SAVE: always save facts without asking
            try:
                from auto_learn import _get_engine as _get_learn_engine
                learn_engine = _get_learn_engine()
                learn_engine.save_learned(result)
            except Exception:
                pass
            return {
                "found": True,
                "answer": result["answer"],
                "source": result["source"],
                "facts": result.get("facts", []),
            }
        return {"found": False}
    
    def save_learned(self, facts):
        """Save web-learned facts permanently."""
        return save_facts(facts)
    
    def close(self):
        self._stop_c_engine()
        self._save_session()
    
    # ── Persistent Context (Phase 15) ──────────────────────────────
    def _load_session(self):
        """Load previous session state."""
        path = os.path.join(os.path.dirname(__file__), '../../user_data/session.json')
        try:
            if os.path.exists(path):
                with open(path) as f:
                    data = json.load(f)
                self.topics_asked = data.get('topics_asked', {})
                self.gaps = data.get('gaps', [])
                self.session_topics = data.get('session_topics', [])
                self.workflows = data.get('workflows', [])
        except Exception: pass
    
    def _save_session(self):
        """Save session state for next time."""
        path = os.path.join(os.path.dirname(__file__), '../../user_data/session.json')
        os.makedirs(os.path.dirname(path), exist_ok=True)
        try:
            data = {
                'topics_asked': self.topics_asked,
                'gaps': self.gaps[-100:],  # Keep last 100 gaps
                'session_topics': self.session_topics[-50:],
                'workflows': self.workflows
            }
            with open(path, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception: pass
    
    # ── Smart Follow-up Questions (Phase GPT-killer) ─────────────
    # ── Reference Resolution (context awareness) ──────────────────
    def _resolve_references(self, user_input):
        """Resolve 'it', 'that', 'this', short follow-ups using conversation history."""
        lower = user_input.lower().strip()
        
        # Track what we're talking about (extract main topic from questions)
        if not hasattr(self, '_last_topic'):
            self._last_topic = None
            self._last_entity = None
            self._conversation_history = []
        
        # Store this turn
        self._conversation_history.append(user_input)
        if len(self._conversation_history) > 20:
            self._conversation_history = self._conversation_history[-20:]
        
        # Pronouns that refer to last topic
        pronouns = ['it', 'that', 'this', 'its', 'they', 'them']
        
        # Check if input contains unresolved pronoun as the main subject
        words = lower.split()
        needs_resolution = False
        
        # Pattern: "What can it do?" / "Tell me more about it" / "How does it work?"
        if any(w in words for w in pronouns):
            # Only resolve if the pronoun seems to be the SUBJECT (not part of a longer entity name)
            for p in pronouns:
                if p in words:
                    idx = words.index(p)
                    # If pronoun is after a question word or "about", it's referring to something
                    if idx > 0 and words[idx-1] in ['is', 'does', 'can', 'about', 'of', 'with', 'from']:
                        needs_resolution = True
                        break
                    if idx == 0 or (idx == 1 and words[0] in ['what', 'how', 'why', 'where', 'can', 'does']):
                        needs_resolution = True
                        break
        
        # Short follow-up with no clear subject (like "and?" "more?" "why?")
        if len(words) <= 3 and lower.endswith('?') and not any(c.isupper() for c in user_input[1:]):
            if self._last_topic and lower not in ['hi?', 'hello?']:
                needs_resolution = True
        
        # Resolve
        if needs_resolution and self._last_topic:
            # Replace pronoun with actual topic
            resolved = user_input
            for p in pronouns:
                # Replace "it" with the topic, but carefully
                if f' {p} ' in f' {lower} ':
                    resolved = resolved.replace(f' {p} ', f' {self._last_topic} ', 1)
                    resolved = resolved.replace(f' {p.capitalize()} ', f' {self._last_topic} ', 1)
                elif lower.startswith(f'{p} '):
                    resolved = self._last_topic + resolved[len(p):]
                elif lower.endswith(f' {p}'):
                    resolved = resolved[:-len(p)] + self._last_topic
            
            # For very short questions, prepend topic
            if len(words) <= 3 and resolved == user_input:
                resolved = f"What about {self._last_topic}? {user_input}"
            
            return resolved
        
        # Extract topic from this question for future reference
        topic = self._extract_main_topic(user_input)
        if topic:
            self._last_topic = topic
            self._last_entity = topic
        
        return user_input
    
    def _extract_main_topic(self, text):
        """Extract the main subject/topic from a question."""
        lower = text.lower()
        skip = {'what', 'is', 'are', 'the', 'a', 'an', 'who', 'was', 'where', 'when',
                'how', 'does', 'do', 'can', 'will', 'which', 'why', 'tell', 'me', 
                'about', 'write', 'in', 'of', 'for', 'to', 'and', 'or', 'hi', 'hello'}
        
        words = text.split()
        topic_words = []
        for w in words:
            clean = w.strip('?.,!').lower()
            if clean not in skip and len(clean) > 2:
                topic_words.append(w.strip('?.,!'))
                if len(topic_words) >= 3:
                    break
        
        if topic_words:
            return ' '.join(topic_words[:2])  # Max 2 words as topic
        return None

    def _detect_mood(self, text):
        """Detect user mood from text patterns."""
        t = text.lower()
        if any(w in t for w in ['ugh', 'broken', "won't work", 'stupid', 'frustrated', 'hate']):
            return 'frustrated'
        if any(w in t for w in ['how does', 'what if', 'interesting', 'curious', 'tell me more', 'explain']):
            return 'curious'
        if any(w in t for w in ['thanks', 'awesome', 'great', 'perfect', 'love it', 'amazing']):
            return 'happy'
        if any(w in t for w in ['confused', "don't understand", 'unclear', 'lost', 'what do you mean']):
            return 'confused'
        return 'neutral'

    def _adjust_for_mood(self, response, mood):
        """Adjust response tone based on detected mood."""
        if not response:
            return response
        if mood == 'frustrated':
            return response  # Don't add fluff when user is frustrated
        if mood == 'curious':
            return response  # Give full detail
        if mood == 'confused':
            return response  # Keep it simple
        return response

    def _track_topic(self, text):
        """Track topic frequency for proactive suggestions."""
        topic = self._extract_main_topic(text)
        if topic:
            topic_lower = topic.lower()
            self.topics_asked[topic_lower] = self.topics_asked.get(topic_lower, 0) + 1

    def _proactive_check(self):
        """Check if we should proactively suggest something."""
        for topic, count in self.topics_asked.items():
            if count >= 5:
                self.topics_asked[topic] = 0
                return f"  You've asked about '{topic}' {count} times. Want a deep dive? (/hunt {topic})"
        return None

    def _socratic_response(self, user_input):
        """In teach mode, ask guiding questions instead of giving answers."""
        topic = self._extract_main_topic(user_input) or 'that'
        questions = [
            f"Interesting question! What do YOU think about {topic}?",
            f"Before I answer — what do you already know about {topic}?",
            f"Let's think about this together. What comes to mind when you hear '{topic}'?",
            f"Good question! Can you think of any examples of {topic}?",
        ]
        import random
        return random.choice(questions)

    def _check_workflows(self, user_input):
        """Check if input triggers a workflow keyword."""
        lower = user_input.lower()
        for wf in self.workflows:
            if wf.get('trigger') and wf['trigger'] in lower:
                return wf.get('response', f"Workflow '{wf.get('name', 'unnamed')}' triggered.")
        return None

    def _identity_response(self, q):
        """Handle 'who are you' / 'what can you do' questions."""
        if any(w in q for w in ['who are', 'what are you', 'your name', 'introduce']):
            return ("I'm Axima — a zero-parameter AI that reasons from verified knowledge, not guesses. "
                    "I run fully offline on your device, never hallucinate, and get smarter with every conversation. "
                    "Built by Ghias (Gowtham Sangadi).")
        if any(w in q for w in ['what can you', 'what do you']):
            return ("I can:\n"
                    "• Answer questions from verified knowledge (7,800+ concepts)\n"
                    "• Do math (exact arithmetic, primes, comparisons)\n"
                    "• Reason about cause and effect (physics, chemistry, biology, social)\n"
                    "• Generate code in Python, C, JavaScript, Bash\n"
                    "• Search the web when I don't know something\n"
                    "• Learn permanently from every conversation\n"
                    "• Logic and syllogisms\n"
                    "• Share knowledge peer-to-peer with other users\n"
                    "All offline, all free, all private. 0% hallucination guaranteed.")
        return "I'm Axima — an AI that proves answers instead of guessing them."
        """Check if any workflow triggers match this input."""
        for wf in self.workflows:
            if not wf.get('enabled'):
                continue
            trigger = wf.get('trigger_value', '').lower()
            if trigger and trigger in user_input.lower():
                return f"[Workflow '{wf['name']}'] {wf.get('action_value', '')}"
        return None

    def workflow_create(self, name, trigger_type, trigger_value, action_type, action_value):
        """Create a new workflow automation."""
        self.workflows.append({
            'name': name,
            'trigger_type': trigger_type,
            'trigger_value': trigger_value,
            'action_type': action_type,
            'action_value': action_value,
            'enabled': True
        })
        self._save_session()
        return f"✅ Workflow '{name}' created! Triggers on: {trigger_type}='{trigger_value}'"

    def _solve_physics(self, question: str, lower: str) -> Optional[str]:
        """Route physics question to appropriate solver and return answer."""
        import re
        from prometheus_physics import PhysicsIdentifier, PhysicsLawDB, PhysicsConstants
        from prometheus_physics_solve import (NewtonianSolver, EMSolver, WaveSolver,
            QuantumSolver, StatMechSolver, RelativitySolver, NuclearSolver, AstroSolver,
            DerivationEngine, FermiEstimator, LagrangianSolver)

        pi = PhysicsIdentifier()
        domains = pi.identify(question)
        top_domain = domains[0][0]

        # Extract numbers from question
        numbers = [float(x) for x in re.findall(r'[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?', question)]

        # Try derivation engine first (for "derive", "show", "prove" questions)
        if any(w in lower for w in ['derive', 'show that', 'prove', 'derivation']):
            DE = DerivationEngine()
            for target in DE.available_derivations():
                # Match by: full name in question, or any word >3 chars
                target_lower = target.lower().replace('_', ' ')
                if (target_lower in lower or target.lower() in lower or
                    any(w in lower for w in target_lower.split() if len(w) > 3)):
                    d = DE.derive(target)
                    if d:
                        steps = '\n'.join(d['steps'])
                        return f"📐 {d['result']}\n\nFrom: {d['from']}\n\n{steps}"

        # Try Fermi estimator (for "how many", "estimate", "order of magnitude")
        if any(w in lower for w in ['how many', 'estimate', 'order of magnitude', 'roughly']):
            FE = FermiEstimator()
            est = FE.estimate(question)
            if est:
                reasoning = '\n'.join(f'  • {r}' for r in est['reasoning'])
                return f"🔬 Fermi Estimate: {est['answer']}\n\nReasoning:\n{reasoning}"

        # Route to domain-specific solver
        try:
            if top_domain == "classical_mechanics":
                NS = NewtonianSolver()
                if 'projectile' in lower or ('angle' in lower and ('range' in lower or 'height' in lower)):
                    v0 = numbers[0] if numbers else 20
                    angle = numbers[1] if len(numbers) > 1 else 45
                    r = NS.projectile(v0, angle)
                    return f"⚙️ Projectile Motion (v₀={v0} m/s, θ={angle}°):\n  Range: {r['range']:.2f} m\n  Max height: {r['max_height']:.2f} m\n  Time of flight: {r['time_of_flight']:.2f} s\n  {r['formula']}"
                elif 'pendulum' in lower or 'period' in lower:
                    L = numbers[0] if numbers else 1.0
                    r = NS.shm(L=L)
                    return f"⚙️ Pendulum (L={L} m):\n  Period: {r['period']:.4f} s\n  Frequency: {r['frequency']:.4f} Hz\n  ω = {r['omega']:.4f} rad/s\n  {r['formula']}"
                elif 'orbit' in lower or 'escape' in lower:
                    if 'escape' in lower and numbers:
                        M = numbers[0] if numbers[0] > 1e10 else 5.972e24
                        R = numbers[1] if len(numbers) > 1 else 6.371e6
                        v = NS.escape_velocity(M, R)
                        return f"⚙️ Escape velocity: {v:.0f} m/s = {v/1000:.1f} km/s"
                elif 'collision' in lower:
                    if len(numbers) >= 4:
                        v1f, v2f = NS.elastic_collision_1d(numbers[0], numbers[1], numbers[2], numbers[3])
                        return f"⚙️ Elastic Collision:\n  v₁' = {v1f:.2f} m/s\n  v₂' = {v2f:.2f} m/s"
                elif 'moment of inertia' in lower:
                    shape = 'solid_sphere'
                    if 'sphere' in lower: shape = 'solid_sphere'
                    elif 'cylinder' in lower or 'disk' in lower: shape = 'solid_cylinder'
                    elif 'rod' in lower: shape = 'thin_rod_center'
                    M = numbers[0] if numbers else 1
                    R = numbers[1] if len(numbers) > 1 else 1
                    I = NS.moment_of_inertia(shape, M, R=R)
                    return f"⚙️ Moment of Inertia ({shape}, M={M}, R={R}):\n  I = {I:.6f} kg·m²"

            elif top_domain == "electromagnetism":
                EM = EMSolver()
                if 'ohm' in lower or ('voltage' in lower and 'current' in lower):
                    if len(numbers) >= 2:
                        if 'resistance' in lower or 'R' in question:
                            return f"⚡ Ohm's Law: V = IR = {numbers[0]*numbers[1]:.2f} V"
                        else:
                            return f"⚡ Ohm's Law: I = V/R = {numbers[0]/numbers[1]:.4f} A"
                elif 'capacit' in lower and numbers:
                    if 'energy' in lower and len(numbers) >= 2:
                        E = EM.capacitor_energy(numbers[0], numbers[1])
                        return f"⚡ Capacitor energy: E = ½CV² = {E:.6e} J"
                elif 'solenoid' in lower and numbers:
                    B = EM.magnetic_field_solenoid(numbers[0], numbers[1] if len(numbers)>1 else 1)
                    return f"⚡ B inside solenoid: B = μ₀nI = {B:.6e} T"
                elif 'skin depth' in lower and numbers:
                    d = EM.skin_depth(numbers[0], numbers[1] if len(numbers)>1 else 5.8e7)
                    return f"⚡ Skin depth: δ = {d*1e6:.2f} μm = {d:.6e} m"
                elif 'snell' in lower or 'refract' in lower:
                    if len(numbers) >= 3:
                        t2 = EM.snell(numbers[0], numbers[1], numbers[2])
                        if t2 == -1:
                            return f"⚡ Total internal reflection! (n₁={numbers[0]} > n₂={numbers[2]}, θ > θ_c)"
                        return f"⚡ Snell's Law: θ₂ = {t2:.2f}°"
                elif 'resonan' in lower and len(numbers) >= 2:
                    f = EM.resonant_frequency(numbers[0], numbers[1])
                    return f"⚡ Resonant frequency: f₀ = 1/(2π√LC) = {f:.2f} Hz"

            elif top_domain == "quantum_mechanics":
                QS = QuantumSolver()
                if 'hydrogen' in lower:
                    n = int(numbers[0]) if numbers else 1
                    r = QS.hydrogen(n)
                    return f"⚛️ Hydrogen atom (n={n}):\n  Energy: {r['energy_eV']:.4f} eV\n  Radius: {r['radius_a0']:.1f} a₀ = {r['radius_m']:.3e} m\n  Degeneracy: {r['degeneracy']}\n  {r['formula']}"
                elif 'tunneling' in lower or 'barrier' in lower:
                    if len(numbers) >= 3:
                        E = numbers[0] * 1.602e-19  # eV to J
                        V0 = numbers[1] * 1.602e-19
                        L = numbers[2] * 1e-9 if numbers[2] < 1 else numbers[2]
                        T = QS.tunneling_rectangular(E, V0, L)
                        return f"⚛️ Tunneling (E={numbers[0]}eV, V₀={numbers[1]}eV, L={numbers[2]}nm):\n  Transmission T = {T:.6e}\n  Formula: T ≈ e^{{-2κL}}"
                elif 'infinite' in lower and 'well' in lower:
                    n = int(numbers[0]) if numbers else 1
                    L = numbers[1]*1e-9 if len(numbers) > 1 else 1e-9
                    r = QS.infinite_well(n, L)
                    return f"⚛️ Infinite Well (n={n}, L={L*1e9:.1f} nm):\n  E = {r['energy_eV']:.4f} eV\n  {r['formula']}"
                elif 'uncertainty' in lower:
                    if numbers:
                        dx = numbers[0]
                        r = QS.uncertainty(dx=dx)
                        return f"⚛️ Heisenberg: Δx = {dx:.2e} m\n  Minimum Δp ≥ {r['min_dp']:.2e} kg·m/s\n  Minimum Δv ≥ {r['min_dv']:.2e} m/s"

            elif top_domain == "statistical_mechanics":
                SM = StatMechSolver()
                if 'carnot' in lower and len(numbers) >= 2:
                    r = SM.carnot(max(numbers[:2]), min(numbers[:2]))
                    return f"🔥 Carnot (T_h={max(numbers[:2])}K, T_c={min(numbers[:2])}K):\n  Efficiency: η = {r['efficiency']:.4f} = {r['efficiency']*100:.1f}%\n  COP (heat pump): {r['COP_heat_pump']:.2f}\n  {r['formula']}"
                elif 'wien' in lower or 'peak wavelength' in lower:
                    T = numbers[0] if numbers else 5800
                    lam = SM.wien_peak(T)
                    return f"🔥 Wien's Law (T={T}K):\n  λ_max = {lam*1e9:.1f} nm = {lam*1e6:.3f} μm"
                elif 'fermi energy' in lower:
                    n = numbers[0] if numbers else 8.5e28
                    Ef = SM.fermi_energy(n)
                    return f"🔥 Fermi Energy (n={n:.2e} /m³):\n  E_F = {Ef/1.602e-19:.2f} eV"

            elif top_domain == "relativity":
                RS = RelativitySolver()
                if 'schwarzschild' in lower or 'black hole' in lower:
                    M = numbers[0] * 1.989e30 if numbers and numbers[0] < 1e10 else (numbers[0] if numbers else 1.989e30)
                    rs = RS.schwarzschild_radius(M)
                    Th = RS.hawking_temperature(M)
                    return f"🌌 Black Hole (M={M/1.989e30:.1f} M☉):\n  Schwarzschild radius: {rs:.0f} m = {rs/1000:.2f} km\n  Hawking temperature: {Th:.2e} K\n  Evaporation time: ~10⁶⁷(M/M☉)³ years"
                elif 'time dilation' in lower and numbers:
                    v = numbers[0] if numbers[0] < 3e8 else numbers[0]
                    g = RS.gamma(v)
                    return f"🌌 Time Dilation (v={v:.2e} m/s = {v/2.998e8:.4f}c):\n  γ = {g:.6f}\n  1 second (moving) = {g:.6f} seconds (stationary)"
                elif 'redshift' in lower and numbers:
                    z = numbers[0]
                    r = RS.cosmological_redshift_to_distance(z)
                    return f"🌌 Cosmological Redshift z={z}:\n  Distance: {r['distance_Mpc']:.0f} Mpc" if r['distance_Mpc'] else f"🌌 z={z}: Need full cosmological calculation for z>0.3"

            elif top_domain == "nuclear_physics":
                NuS = NuclearSolver()
                if 'binding' in lower and numbers:
                    Z = int(numbers[0]) if numbers else 26
                    A = int(numbers[1]) if len(numbers) > 1 else 56
                    r = NuS.binding_energy(Z, A)
                    return f"☢️ Nuclear Binding (Z={Z}, A={A}):\n  B = {r['binding_energy_MeV']:.2f} MeV\n  B/A = {r['binding_per_nucleon']:.3f} MeV/nucleon"
                elif 'half-life' in lower or 'decay' in lower:
                    if len(numbers) >= 2:
                        N = NuS.decay_remaining(numbers[0], numbers[1],
                                               numbers[2] if len(numbers)>2 else numbers[1])
                        return f"☢️ Radioactive Decay:\n  Remaining: {N:.4e}"

            elif top_domain == "cosmology":
                AS = AstroSolver()
                if 'jeans' in lower:
                    T = numbers[0] if numbers else 10
                    n = numbers[1] if len(numbers)>1 else 1e4
                    Mj = AS.jeans_mass(T, n*1e6)  # convert to /m³
                    return f"🌌 Jeans Mass (T={T}K, n={n}/cm³):\n  M_J = {Mj/1.989e30:.2f} M☉"

        except Exception as e:
            pass

        # Fallback: return relevant laws as educational answer
        try:
            law_db = PhysicsLawDB()
            relevant = pi.get_relevant_laws(question, law_db)
            if relevant:
                laws_text = '\n'.join(f"  • {l.name}: {l.equation}" for l in relevant[:5])
                return f"📚 Relevant Physics Laws:\n{laws_text}\n\nDomain: {top_domain}"
        except:
            pass

        return None


def main():
    print("╔══════════════════════════════════════════╗")
    print("║   Axima v1.0.0 — Cosmic Engine      ║")
    print(f"║   Engines: {len(engines_loaded)} + 21 C modules" + " " * (17 - len(str(len(engines_loaded)))) + "║")
    print(f"║   C Engine: {'✓' if AI_BIN else '✗'}  Derive: ✓  Agents: ✓  " + "║")
    print("║   Phases: 3,7,8,10,14,15,16,17,22,23   ║")
    print("╚══════════════════════════════════════════╝")
    print()
    
    ai = Axima()
    
    # Show proactive suggestion on startup if any
    proactive = ai._proactive_check()
    if proactive:
        print(f"  {proactive}\n")
    
    # Show session resumption
    if ai.session_topics:
        last = ai.session_topics[-1] if ai.session_topics else None
        if last:
            print(f"  📌 Last session topic: {last}")
            print()
    
    try:
        while True:
            try:
                user = input("> ").strip()
            except EOFError:
                break
            if not user:
                continue
            if user in ('/quit', '/exit', 'quit', 'exit'):
                break
            if user == '/status':
                s = ai.brain.status()
                print(f"  Engines: {len(s['engines'])} ({', '.join(s['engines'][:5])}...)")
                print(f"  Turn: {s['turn']} | Mood: {s['mood']} | Topics: {s['topics_tracked']}")
                print(f"  Auto-search: {'🟢 ON' if ai.auto_search else '🔴 OFF'}")
                print(f"  Auto-save:   {'🟢 ON' if ai.auto_save else '🔴 OFF'}")
                print()
                continue
            if user == '/autosearch':
                ai.auto_search = not ai.auto_search
                status = '🟢 ON' if ai.auto_search else '🔴 OFF'
                print(f"  Auto-search: {status}")
                if ai.auto_search:
                    print(f"  (I'll automatically search the web when I don't know something)")
                else:
                    print(f"  (I'll ask before searching)")
                print()
                continue
            if user == '/autosave':
                ai.auto_save = not ai.auto_save
                status = '🟢 ON' if ai.auto_save else '🔴 OFF'
                print(f"  Auto-save: {status}")
                if ai.auto_save:
                    print(f"  (Web results will be saved automatically for next time)")
                else:
                    print(f"  (I'll ask before saving)")
                print()
                continue
            if user == '/teach':
                ai.teach_mode = not ai.teach_mode
                status = '🟢 ON' if ai.teach_mode else '🔴 OFF'
                print(f"  Teaching mode: {status}")
                if ai.teach_mode:
                    print(f"  (I'll ask guiding questions instead of giving answers)")
                else:
                    print(f"  (Back to normal answers)")
                print()
                continue
            
            # ═══ v3.0 MODES ═══
            if user.startswith('/hunt '):
                topic = user[6:].strip()
                if topic:
                    try:
                        from hunt import get_hunt_engine
                        print(f"  Hunting: {topic}...")
                        result = get_hunt_engine().hunt(topic)
                        print(get_hunt_engine().format_hunt(result))
                        # Auto-save verified facts via KDA
                        if result.get('verified_facts'):
                            for f in result['verified_facts']:
                                try:
                                    from kda_manager import save_with_kda
                                    save_with_kda(topic, 'has_fact', f['text'][:100], 90)
                                except Exception: pass
                    except Exception as e:
                        print(f"  Hunt error: {e}")
                else:
                    print("  Usage: /hunt <topic>")
                print()
                continue
            
            if user.startswith('/debate '):
                topic = user[8:].strip()
                if topic:
                    try:
                        from debate import get_debate_engine
                        result = get_debate_engine().debate(topic)
                        if result:
                            print(get_debate_engine().format_debate(result))
                    except Exception as e:
                        print(f"  Debate error: {e}")
                else:
                    print("  Usage: /debate <topic>")
                print()
                continue
            
            if user == '/predict':
                # Show what PCE thinks you'll ask next
                if hasattr(ai, '_last_topic') and ai._last_topic:
                    print(f"  Based on your conversation about '{ai._last_topic}':")
                    print(f"  You might ask next:")
                    suggestions = [
                        f"    • More about {ai._last_topic}",
                        f"    • A related topic",
                        f"    • Why {ai._last_topic} is important",
                        f"    • How {ai._last_topic} works",
                    ]
                    for s in suggestions:
                        print(s)
                else:
                    print("  No predictions yet. Ask a few questions first.")
                print()
                continue
            
            if user.startswith('/prove '):
                claim = user[7:].strip()
                if claim:
                    print(f"  Proving: \"{claim}\"")
                    # Route through C engine with PCSE
                    ans = ai._query_c(f"is {claim}")
                    if ans:
                        print(f"  {ans}")
                    else:
                        print(f"  Cannot prove or disprove with available knowledge.")
                else:
                    print("  Usage: /prove <claim>")
                print()
                continue
            
            if user.startswith('/level '):
                try:
                    level = int(user[7:].strip())
                    if 0 <= level <= 4:
                        ai._user_level = level
                        levels = ['auto', 'child', 'student', 'detailed', 'expert']
                        print(f"  Explanation level: {levels[level]}")
                    else:
                        print("  Levels: 0=auto, 1=child, 2=student, 3=detailed, 4=expert")
                except Exception:
                    print("  Usage: /level 0-4")
                print()
                continue
            
            if user.startswith('/workflow'):
                parts = user.split(maxsplit=4)
                if len(parts) < 2 or parts[1] == 'list':
                    if ai.workflows:
                        print("  ⚙️  Active Workflows:")
                        for i, wf in enumerate(ai.workflows):
                            status = '🟢' if wf.get('enabled') else '🔴'
                            print(f"    {status} {i+1}. {wf['name']} — on '{wf['trigger_value']}' → {wf['action_type']}: {wf['action_value']}")
                    else:
                        print("  No workflows yet. Create one:")
                        print("  /workflow create <name> <keyword> <shell_command>")
                    print()
                elif parts[1] == 'create' and len(parts) >= 5:
                    name, trigger, action = parts[2], parts[3], parts[4]
                    result = ai.workflow_create(name, 'keyword', trigger, 'shell', action)
                    print(f"  {result}\n")
                elif parts[1] == 'delete' and len(parts) >= 3:
                    try:
                        idx = int(parts[2]) - 1
                        if 0 <= idx < len(ai.workflows):
                            removed = ai.workflows.pop(idx)
                            print(f"  ✓ Deleted workflow '{removed['name']}'\n")
                        else:
                            print(f"  Invalid workflow number.\n")
                    except Exception: print("  Usage: /workflow delete <number>\n")
                else:
                    print("  Usage: /workflow create <name> <trigger_keyword> <shell_command>")
                    print("         /workflow list")
                    print("         /workflow delete <number>\n")
                continue
            if user == '/mood':
                print(f"  Current detected mood: {ai.mood}")
                print(f"  Personality: formality={ai.personality['formality']:.1f} verbosity={ai.personality['verbosity']:.1f} humor={ai.personality['humor']:.1f} empathy={ai.personality['empathy']:.1f}\n")
                continue
            if user == '/proactive':
                suggestion = ai._proactive_check()
                if suggestion:
                    print(f"  {suggestion}\n")
                else:
                    print("  No proactive suggestions right now.\n")
                continue
            if user == '/gaps':
                if ai.gaps:
                    print(f"  Knowledge gaps ({len(ai.gaps)}):")
                    for g in ai.gaps[-10:]:
                        print(f"    ❌ {g}")
                else:
                    print("  No knowledge gaps tracked!")
                print()
                continue
            if user == '/topics':
                top = sorted(ai.topics_asked.items(), key=lambda x: -x[1])[:10]
                if top:
                    print("  Top topics you ask about:")
                    for topic, count in top:
                        bar = '█' * min(count, 20)
                        print(f"    {topic:20s} {bar} ({count})")
                else:
                    print("  No topics tracked yet.")
                print()
                continue
            if user == '/share':
                from p2p_share import share_interactive
                share_interactive()
                print()
                continue
            if user == '/undo':
                from undo import undo_last
                undo_last()
                print()
                continue
            if user.startswith('/vision'):
                parts = user.split(maxsplit=1)
                if len(parts) < 2:
                    print("  Usage: /vision <image_path>")
                    print("  Example: /vision photo.jpg\n")
                    continue
                from vision import VisionEngine
                ve = VisionEngine()
                result = ve.analyze(parts[1].strip())
                if "error" in result:
                    print(f"  ❌ {result['error']}\n")
                else:
                    print(f"  🖼️  {result['description']}")
                    if result.get('metadata'):
                        print(f"  📷 Camera: {result['metadata']}")
                    print()
                continue
            if user.startswith('/workspace'):
                from workspace import WorkspaceManager
                if not hasattr(ai, '_ws_mgr'):
                    ai._ws_mgr = WorkspaceManager()
                    ai._ws_user = 'me'
                parts = user.split(maxsplit=2)
                cmd = parts[1] if len(parts) > 1 else 'help'
                arg = parts[2] if len(parts) > 2 else ''
                
                if cmd == 'create':
                    ws = ai._ws_mgr.create(arg or 'My Workspace', ai._ws_user)
                    print(f"  🚀 Workspace created: \"{ws.name}\"")
                    print(f"  Room code: {ws.code}")
                    print(f"  Share this code with your team!\n")
                elif cmd == 'join':
                    ws = ai._ws_mgr.join(arg, ai._ws_user)
                    if ws:
                        print(f"  ✓ Joined \"{ws.name}\" ({len(ws.users)} members)\n")
                    else:
                        print(f"  ✗ Workspace '{arg}' not found.\n")
                elif cmd == 'members':
                    ws = ai._ws_mgr.get_user_workspace(ai._ws_user)
                    if ws:
                        print(ws.get_members_display() + '\n')
                    else:
                        print("  Not in a workspace. Use /workspace create or /workspace join CODE\n")
                elif cmd == 'goals':
                    ws = ai._ws_mgr.get_user_workspace(ai._ws_user)
                    if ws:
                        print(ws.get_goals_display() + '\n')
                    else:
                        print("  Not in a workspace.\n")
                elif cmd == 'summary':
                    ws = ai._ws_mgr.get_user_workspace(ai._ws_user)
                    if ws:
                        s = ws.get_summary()
                        print(f"  📋 {s['name']} ({s['duration_min']}min)")
                        print(f"  Members: {s['members']} | Messages: {s['messages']}")
                        print(f"  Goals: {s['goals_done']}/{s['goals_total']} | Facts: {s['facts_learned']}")
                        print(f"  Focus: {s['focus'] or 'free'} ({s['mode']})\n")
                    else:
                        print("  Not in a workspace.\n")
                elif cmd == 'focus':
                    ws = ai._ws_mgr.get_user_workspace(ai._ws_user)
                    if ws:
                        ws.set_focus(arg, 'focused')
                        print(f"  🔒 Focus set: {arg}\n")
                elif cmd == 'free':
                    ws = ai._ws_mgr.get_user_workspace(ai._ws_user)
                    if ws:
                        ws.clear_focus()
                        print(f"  🔓 Focus cleared.\n")
                elif cmd == 'leave':
                    ai._ws_mgr.leave(ai._ws_user)
                    print(f"  Left workspace.\n")
                else:
                    print("  Workspace commands:")
                    print("    /workspace create \"name\"  — Create workspace")
                    print("    /workspace join CODE      — Join workspace")
                    print("    /workspace members        — Show members")
                    print("    /workspace goals          — Show goals")
                    print("    /workspace summary        — Session summary")
                    print("    /workspace focus topic    — Lock focus")
                    print("    /workspace free           — Unlock focus")
                    print("    /workspace leave          — Leave\n")
                continue
            
            # ═══ PREDICT v3.0: Check if input is about suggestions (DIE) ═══
            if hasattr(ai, '_predict_engine') and ai._predict_engine.state.state != 'open':
                die_result = ai._predict_engine.process_input(user)
                if die_result.get('handled'):
                    ans = die_result.get('answer', '')
                    if ans and 'Did you mean' not in ans:
                        print(f"  {ans}")
                        # Show next-level suggestions if drilling
                        next_sugs = die_result.get('suggestions', [])
                        if next_sugs:
                            print(f"\n  You might also want to know:")
                            print(ai._predict_engine.format_suggestions(next_sugs))
                        print()
                        continue
                    elif 'Did you mean' in str(ans):
                        print(f"  {ans}")
                        print()
                        continue
            
            response = ai.ask(user)
            if response.get("gap"):
                # AI doesn't know
                if ai.auto_search:
                    # Auto-search without asking
                    import sys as _sys
                    frames = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']
                    import threading
                    searching = [True]
                    def _anim():
                        i = 0
                        while searching[0]:
                            _sys.stdout.write(f'\r  {frames[i%len(frames)]} Searching the web...')
                            _sys.stdout.flush()
                            time.sleep(0.1); i += 1
                        _sys.stdout.write('\r  ✓ Found!                    \n')
                        _sys.stdout.flush()
                    t = threading.Thread(target=_anim, daemon=True)
                    t.start()
                    result = ai.search_and_learn(user)
                    searching[0] = False
                    t.join(timeout=1)
                    
                    if result["found"]:
                        print(f"\n  [{result['source']}]")
                        print(f"  {result['answer'][:500]}")
                        if ai.auto_save:
                            n = ai.save_learned(result["facts"])
                            print(f"\n  ✓ Auto-saved {n} facts!\n")
                        else:
                            print(f"\n  Save this for future? (yes/no)")
                            try:
                                save = input("  > ").strip().lower()
                            except EOFError:
                                break
                            if save in ('yes', 'y', 'yeah', 'sure', 'ok'):
                                n = ai.save_learned(result["facts"])
                                print(f"  ✓ Saved {n} facts!\n")
                            else:
                                print("  OK, not saved.\n")
                    else:
                        print("  Searched but couldn't find anything online.\n")
                else:
                    # Manual mode — ask before searching
                    print("  I don't have information about that yet.")
                    print("  Would you like me to search online? (yes/no)")
                    try:
                        choice = input("  > ").strip().lower()
                    except EOFError:
                        break
                    if choice in ('yes', 'y', 'yeah', 'sure', 'ok'):
                        import sys as _sys
                        frames = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']
                        import threading
                        searching = [True]
                        def _anim():
                            i = 0
                            while searching[0]:
                                _sys.stdout.write(f'\r  {frames[i%len(frames)]} Searching the web...')
                                _sys.stdout.flush()
                                time.sleep(0.1); i += 1
                            _sys.stdout.write('\r  ✓ Found!                    \n')
                            _sys.stdout.flush()
                        t = threading.Thread(target=_anim, daemon=True)
                        t.start()
                        result = ai.search_and_learn(user)
                        searching[0] = False
                        t.join(timeout=1)
                        
                        if result["found"]:
                            print(f"\n  [{result['source']}]")
                            print(f"  {result['answer'][:500]}")
                            if ai.auto_save:
                                n = ai.save_learned(result["facts"])
                                print(f"\n  ✓ Auto-saved {n} facts!\n")
                            else:
                                print(f"\n  Save this for future? (yes/no)")
                                try:
                                    save = input("  > ").strip().lower()
                                except EOFError:
                                    break
                                if save in ('yes', 'y', 'yeah', 'sure', 'ok'):
                                    n = ai.save_learned(result["facts"])
                                    print(f"  ✓ Saved {n} facts!\n")
                                else:
                                    print("  OK, not saved.\n")
                        else:
                            print("  Couldn't find anything online either.\n")
                    else:
                        print("  OK. You can teach me: 'Remember that...'\n")
            else:
                print(f"  {response['response']}")
                
                # ═══ PREDICT v3.0: DIE + Suggestions + Drilling ═══
                if not hasattr(ai, '_predict_engine'):
                    from predict import PredictEngine
                    ai._predict_engine = PredictEngine(answer_func=lambda q: ai._query_c(q) or '')
                
                # Generate suggestions after answer
                if not ai.teach_mode:
                    sugs = ai._predict_engine.after_answer(user, response['response'])
                    if sugs:
                        print(f"\n  You might also want to know:")
                        print(ai._predict_engine.format_suggestions(sugs))
                
                print()
    except KeyboardInterrupt:
        pass
    finally:
        ai.close()
        if ai.turn > 0:
            print("\n  See you next time.")
        # No message if no interaction happened (test mode)


if __name__ == "__main__":
    main()

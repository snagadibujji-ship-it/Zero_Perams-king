#!/usr/bin/env python3
"""
Hybrid AI - Unified Interface (Cosmic Level)
Combines C engine (fast knowledge lookup) + Python brain (deep intelligence)
+ Proactive AI + Personality + Teaching + Workflows + Persistent Context.
"""
import subprocess, sys, os, json, time, select, fcntl

sys.path.insert(0, os.path.dirname(__file__))
from brain import HybridBrain, engines_loaded
from auto_learn import offer_search, save_facts, get_learned_count
from metacognition import MetacognitiveReasoner
from world_sim import WorldSimulator

# Optional cosmic modules (fault-tolerant imports)
try:
    from fluency import FluencyEngine
except: FluencyEngine = None
try:
    from multipath import MultipathReasoner
except: MultipathReasoner = None
try:
    from long_memory import LongMemory
except: LongMemory = None
try:
    from creative import CreativeEngine
except: CreativeEngine = None
try:
    from truthguard import TruthGuard
except: TruthGuard = None
try:
    from community import CommunityIntelligence
except: CommunityIntelligence = None

# Find C binary
AI_BIN = None
for path in ['../../ai', '/root/hybrid-ai/ai']:
    if os.path.isfile(path) and os.access(path, os.X_OK):
        AI_BIN = os.path.abspath(path)
        break

class HybridAI:
    """Unified AI combining C speed + Python intelligence + Cosmic features."""
    
    def __init__(self):
        self.brain = HybridBrain()
        self.metacog = MetacognitiveReasoner()
        self.world = WorldSimulator()
        self.c_proc = None
        self.turn = 0
        self.auto_search = False  # Auto-search web when AI doesn't know
        self.auto_save = False    # Auto-save web results without asking
        self.teach_mode = False   # Socratic teaching mode
        
        # Cosmic modules (graceful fallback if any fail)
        self.fluency = FluencyEngine() if FluencyEngine else None
        self.multipath = MultipathReasoner() if MultipathReasoner else None
        self.long_memory = LongMemory() if LongMemory else None
        self.creative = CreativeEngine() if CreativeEngine else None
        self.truthguard = TruthGuard() if TruthGuard else None
        self.community = CommunityIntelligence() if CommunityIntelligence else None
        
        # Personality & context (C-backed but tracked in Python too)
        self.mood = 'neutral'
        self.personality = {'formality': 0.5, 'verbosity': 0.6, 'humor': 0.3, 'empathy': 0.7}
        self.topics_asked = {}  # Track topic frequency for proactive AI
        self.gaps = []  # Track knowledge gaps
        self.session_topics = []  # Persistent context
        self.workflows = []  # User-defined automations
        
        # Load persistent state
        self._load_session()
        self._start_c_engine()
    
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
            return None
        # Check if process is still alive
        if self.c_proc.poll() is not None:
            # Process died — try to restart once
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
            return None
        except (BrokenPipeError, OSError):
            # Pipe broken — mark as unavailable
            self.c_proc = None
            self.c_available = False
            return None
        except Exception:
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
        self.turn += 1
        
        # 0. Track topic + detect mood
        self._track_topic(user_input)
        self.mood = self._detect_mood(user_input)
        
        # 0.5 Check workflows (keyword triggers)
        wf_result = self._check_workflows(user_input)
        if wf_result:
            return {"response": wf_result, "gap": False}
        
        # 1. Teaching mode (Socratic)
        if self.teach_mode:
            return {"response": self._socratic_response(user_input), "gap": False}
        
        # 1.5 Code generation (cosmic engine - 15 languages, 100+ algorithms)
        lower = user_input.lower()
        code_triggers = ['write', 'code', 'implement', 'create a function', 'build a',
                        'program', 'script', 'algorithm', 'data structure',
                        'sort', 'search', 'fibonacci', 'factorial', 'server',
                        'linked list', 'binary tree', 'hash', 'graph', 'stack', 'queue']
        
        # 1.6 Agent system for complex tasks (math, compare, run commands)
        agent_triggers = ['calculate', 'compute', 'compare', 'vs', 'versus',
                         'run command', 'execute', 'list files', 'analyze']
        if any(t in lower for t in agent_triggers):
            try:
                from agent_system import agent_process
                result = agent_process(user_input)
                if result['success'] and result['answer'] and len(result['answer']) > 2:
                    return {"response": result['answer'], "gap": False}
            except: pass
        
        if any(t in lower for t in code_triggers):
            try:
                from codegen_engine import handle_code_request
                result = handle_code_request(user_input)
                if result['type'] == 'code' and result.get('code'):
                    lang = result['language']
                    code = result['code']
                    resp = f"[{lang.upper()} code]\n```{lang}\n{code}\n```"
                    return {"response": resp, "gap": False}
                elif result['type'] == 'debug':
                    return {"response": result['result'], "gap": False}
                elif result['type'] == 'explain':
                    return {"response": result['result'], "gap": False}
            except: pass
        
        # 2. Check for "what if" → world simulator
        lower = user_input.lower()
        if any(p in lower for p in ['what happens if', 'what would happen', 'what if you', 'what if i']):
            sim_result = self.world.explain(user_input)
            if sim_result and 'No matching rules' not in sim_result:
                return {"response": sim_result, "gap": False}
        
        # 3. Check if needs clarification
        should_clarify, clarification = self.metacog.should_ask_clarification(user_input)
        if should_clarify:
            return {"response": clarification, "gap": False}
        
        # 4. Multi-path reasoning (if available)
        multipath_answer = None
        if self.multipath:
            try:
                paths = self.multipath.reason(user_input)
                if paths and paths.get('best_answer'):
                    multipath_answer = paths['best_answer']
            except: pass
        
        # 5. Get C engine's fast answer (knowledge graph + derive + reasoning)
        c_answer = self._query_c(user_input)
        
        # 5.5 SHORT-CIRCUIT: If C engine returned a high-quality answer, skip expensive
        # Python processing (metacognition, fluency, multipath, truthguard) and return
        # directly. This avoids Python wrapping that degrades natural C responses.
        dont_know_signals_sc = ["don't know", "don't have", "outside my knowledge",
                                "teach me", "not sure", "can't find"]
        if (c_answer and len(c_answer) > 50
                and not any(s in c_answer.lower() for s in dont_know_signals_sc)):
            # High-quality C answer — return directly with mood adjustment only
            final = self._adjust_for_mood(c_answer, self.mood)
            if self.long_memory:
                try:
                    self.long_memory.store(user_input, final)
                except: pass
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
                        return {"response": f"[Agent: {agent_result['intent']}] {ans}", "gap": False}
            except: pass
            
            # Use multipath if it found something
            if multipath_answer:
                return {"response": multipath_answer, "gap": False}
            
            # Track as gap
            topic = user_input.split()[-1] if user_input.split() else user_input
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
            except: pass
        
        # 9. Fluency enhancement
        if self.fluency:
            try:
                enhanced = self.fluency.enhance(final_answer)
                if enhanced and len(enhanced) > len(final_answer) * 0.5:
                    final_answer = enhanced
            except: pass
        
        # 10. Run through Python brain for intelligence enhancement
        result = self.brain.process_turn(user_input, final_answer)
        final = result['response']
        
        # 11. Mood-based adjustment
        final = self._adjust_for_mood(final, self.mood)
        
        # 12. Long-term memory storage
        if self.long_memory:
            try:
                self.long_memory.store(user_input, final)
            except: pass
        
        return {"response": final, "gap": False}
    
    def search_and_learn(self, query):
        """Search the web for an answer and offer to save."""
        result = offer_search(query)
        if result:
            return {
                "found": True,
                "answer": result["answer"],
                "source": result["source"],
                "facts": result["facts"],
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
        except: pass
    
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
        except: pass
    
    # ── Smart Follow-up Questions (Phase GPT-killer) ─────────────
    def _generate_followups(self, question, answer):
        """Generate 2-3 smart follow-up questions based on the topic."""
        q = question.lower()
        followups = []
        
        # Extract the main topic
        topic = None
        for word in question.split():
            w = word.strip('?.,!').lower()
            if len(w) > 3 and w not in ('what', 'where', 'when', 'which', 'that', 
                'this', 'about', 'does', 'have', 'with', 'from', 'they', 'there',
                'their', 'would', 'could', 'should', 'write', 'explain', 'tell'):
                topic = w
                break
        
        if not topic:
            return ""
        
        # Generate contextual follow-ups based on question type
        if 'what is' in q or 'what are' in q:
            followups = [
                f"How does {topic} work in practice?",
                f"What are the main types of {topic}?",
                f"Where is {topic} used most?",
            ]
        elif 'how' in q:
            followups = [
                f"What are the advantages of this approach?",
                f"Are there alternatives to {topic}?",
                f"What problems can occur with {topic}?",
            ]
        elif 'why' in q:
            followups = [
                f"What would happen without {topic}?",
                f"When was this first discovered?",
                f"How does this affect daily life?",
            ]
        elif 'who' in q:
            followups = [
                f"What else did they contribute?",
                f"Who were their contemporaries?",
                f"How did their work change the field?",
            ]
        elif 'capital' in q or 'country' in q or 'located' in q:
            followups = [
                f"What is {topic} known for?",
                f"What is the population of {topic}?",
                f"What language do they speak in {topic}?",
            ]
        elif any(w in q for w in ['cause', 'happen', 'effect']):
            followups = [
                f"Can this be prevented?",
                f"What are the long-term effects?",
                f"How common is this?",
            ]
        else:
            followups = [
                f"Would you like to know more about {topic}?",
                f"How is {topic} related to other concepts?",
            ]
        
        # Return 2 questions max, cleanly formatted
        selected = followups[:2]
        return "\n  → " + "\n  → ".join(selected)
    def _detect_mood(self, text):
        """Detect user mood from text patterns."""
        t = text.lower()
        if any(w in t for w in ['ugh', 'broken', "won't work", 'stupid', 'frustrated', 'hate']):
            return 'frustrated'
        if any(w in t for w in ['how does', 'what if', 'interesting', 'curious', 'tell me more', 'explain']):
            return 'curious'
        if any(w in t for w in ['quick', 'just', 'fast', 'hurry', 'briefly']):
            return 'rushed'
        if any(w in t for w in ['thanks', 'perfect', 'awesome', 'great', 'love it', '!']):
            return 'happy'
        if any(w in t for w in ["don't understand", 'confused', 'what?', 'huh', 'lost']):
            return 'confused'
        return 'neutral'
    
    def _adjust_for_mood(self, response, mood):
        """Adjust response based on detected mood."""
        if not response:
            return response
        if mood == 'frustrated':
            response = response.split('.')[0] + '.' if len(response) > 200 else response
        elif mood == 'rushed':
            sentences = response.split('. ')
            response = '. '.join(sentences[:2]) + '.' if len(sentences) > 2 else response
        elif mood == 'curious' and len(response) < 100:
            response += " Would you like me to go deeper on this topic?"
        return response
    
    # ── Proactive AI (Phase 14) ───────────────────────────────────
    def _track_topic(self, text):
        """Track topic frequency for proactive suggestions."""
        words = text.lower().split()
        for w in words:
            if len(w) > 3 and w not in ('what', 'where', 'when', 'that', 'this', 'about', 'does', 'have', 'with'):
                self.topics_asked[w] = self.topics_asked.get(w, 0) + 1
        # Track session topic
        if words:
            topic = ' '.join(w for w in words[:5] if len(w) > 3)
            if topic and topic not in self.session_topics[-5:]:
                self.session_topics.append(topic)
    
    def _proactive_check(self):
        """Check if we should proactively suggest something."""
        # If any topic asked 5+ times → suggest deep dive
        for topic, count in self.topics_asked.items():
            if count >= 5:
                self.topics_asked[topic] = 0  # Reset after suggesting
                return f"💡 I notice you've asked about '{topic}' many times. Want me to do a deep search and build comprehensive knowledge on it?"
        # If 3+ recent gaps → offer to auto-learn
        if len(self.gaps) >= 3:
            recent = self.gaps[-3:]
            self.gaps = self.gaps[:-3]
            topics = ', '.join(recent)
            return f"💡 I couldn't answer these recently: {topics}. Want me to search and learn them all?"
        return None
    
    # ── Teaching Mode (Phase 17) ──────────────────────────────────
    def _socratic_response(self, question):
        """Instead of answering, ask a guiding question (Socratic method)."""
        q = question.lower()
        if 'what is' in q:
            topic = q.replace('what is', '').replace('a ', '').replace('an ', '').strip().rstrip('?')
            return f"Good question! Before I tell you, let me ask: what do you already know about {topic}? Any guesses?"
        if 'how' in q:
            return f"Let's think about this step by step. What's the first thing that needs to happen?"
        if 'why' in q:
            return f"Think about what causes lead to this effect. What do you think might be the reason?"
        return f"Interesting! What's your intuition telling you? Let's work through it together."
    
    # ── Workflow Automation (Phase 22) ─────────────────────────────
    def _check_workflows(self, text):
        """Check if any workflow keyword triggers fire."""
        t = text.lower()
        for wf in self.workflows:
            if wf.get('enabled') and wf.get('trigger_type') == 'keyword':
                if wf['trigger_value'].lower() in t:
                    return self._execute_workflow(wf)
        return None
    
    def _execute_workflow(self, wf):
        """Execute a workflow action."""
        if wf['action_type'] == 'shell':
            try:
                r = subprocess.run(wf['action_value'], shell=True, capture_output=True, text=True, timeout=10)
                return f"⚙️ Workflow '{wf['name']}' executed:\n{r.stdout[:500]}"
            except Exception as e:
                return f"⚙️ Workflow '{wf['name']}' failed: {e}"
        elif wf['action_type'] == 'notify':
            return f"🔔 Reminder: {wf['action_value']}"
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


def main():
    print("╔══════════════════════════════════════════╗")
    print("║   Hybrid AI v1.0.0 — Cosmic Engine      ║")
    print(f"║   Engines: {len(engines_loaded)} + 21 C modules" + " " * (17 - len(str(len(engines_loaded)))) + "║")
    print(f"║   C Engine: {'✓' if AI_BIN else '✗'}  Derive: ✓  Agents: ✓  " + "║")
    print("║   Phases: 3,7,8,10,14,15,16,17,22,23   ║")
    print("╚══════════════════════════════════════════╝")
    print()
    
    ai = HybridAI()
    
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
                    except: print("  Usage: /workflow delete <number>\n")
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
                # Smart follow-up suggestions (not every time - every 3rd turn)
                if ai.turn % 3 == 0 and not ai.teach_mode:
                    followups = ai._generate_followups(user, response['response'])
                    if followups:
                        print(followups)
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

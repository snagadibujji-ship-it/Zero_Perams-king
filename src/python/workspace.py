import socket, threading, json, time, os, sys, random, string

class User:
    def __init__(self, name, role='member'):
        self.name = name
        self.role = role  # owner/admin/member/viewer
        self.status = 'active'  # active/away/focused/offline
        self.last_seen = time.time()
        self.expertise = []  # topics they know about
        self.goals_completed = 0

class Message:
    def __init__(self, sender, text, channel='general', target=None, priority='normal'):
        self.sender = sender
        self.text = text
        self.channel = channel  # general/research/code/random/ai-answers
        self.target = target  # None=all, '@name'=DM, '@everyone'=broadcast
        self.priority = priority  # silent/normal/urgent
        self.timestamp = time.time()
        self.reactions = []

class Goal:
    def __init__(self, title, assigned_to=None, depends_on=None):
        self.id = ''.join(random.choices(string.ascii_lowercase, k=4))
        self.title = title
        self.assigned_to = assigned_to
        self.depends_on = depends_on  # goal ID that must complete first
        self.status = 'pending'  # pending/in_progress/complete/blocked
        self.progress = 0  # 0-100
        self.created = time.time()
        self.completed_at = None

class Workspace:
    def __init__(self, name, owner):
        self.name = name
        self.code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        self.owner = owner
        self.users = {owner: User(owner, 'owner')}
        self.messages = []  # all messages
        self.goals = []  # task list
        self.knowledge = []  # shared facts learned
        self.focus_topic = None  # None = free mode
        self.focus_mode = 'free'  # free/focused/sprint/brainstorm/review
        self.sprint_end = None  # timestamp when sprint ends
        self.created = time.time()
        self.channels = ['general', 'research', 'code', 'random', 'ai-answers']
    
    def join(self, username, role='member'):
        self.users[username] = User(username, role)
        self.add_message('system', f'{username} joined the workspace', 'general')
        return True
    
    def leave(self, username):
        if username in self.users:
            del self.users[username]
            self.add_message('system', f'{username} left', 'general')
    
    def add_message(self, sender, text, channel='general', target=None, priority='normal'):
        msg = Message(sender, text, channel, target, priority)
        self.messages.append(msg)
        return msg
    
    def get_messages(self, username, channel=None, limit=20):
        """Get messages visible to this user."""
        visible = []
        for m in reversed(self.messages):
            # DM filtering
            if m.target and m.target != '@everyone':
                if m.target != f'@{username}' and m.sender != username:
                    continue
            # Channel filtering
            if channel and m.channel != channel:
                continue
            visible.append(m)
            if len(visible) >= limit:
                break
        return list(reversed(visible))
    
    def add_goal(self, title, assigned_to=None, depends_on=None):
        goal = Goal(title, assigned_to, depends_on)
        # Check if blocked
        if depends_on:
            dep = self.get_goal(depends_on)
            if dep and dep.status != 'complete':
                goal.status = 'blocked'
        self.goals.append(goal)
        self.add_message('system', f'Goal added: "{title}" → @{assigned_to or "unassigned"}', 'general', priority='silent')
        return goal
    
    def complete_goal(self, goal_id, by_user):
        goal = self.get_goal(goal_id)
        if goal:
            goal.status = 'complete'
            goal.progress = 100
            goal.completed_at = time.time()
            # Unblock dependents
            for g in self.goals:
                if g.depends_on == goal_id and g.status == 'blocked':
                    g.status = 'pending'
            # Notify
            self.add_message('system', f'🎉 @{by_user} completed: "{goal.title}"', 'general', target='@everyone', priority='normal')
            return True
        return False
    
    def get_goal(self, goal_id):
        for g in self.goals:
            if g.id == goal_id:
                return g
        return None
    
    def set_focus(self, topic, mode='focused'):
        self.focus_topic = topic
        self.focus_mode = mode
        self.add_message('system', f'🔒 Focus: {topic} (mode: {mode})', 'general')
    
    def clear_focus(self):
        self.focus_topic = None
        self.focus_mode = 'free'
        self.add_message('system', '🔓 Focus cleared — free mode', 'general')
    
    def is_on_topic(self, text):
        """Check if message is on the focused topic."""
        if not self.focus_topic or self.focus_mode == 'free':
            return True
        topic_words = set(self.focus_topic.lower().split())
        text_lower = text.lower()
        
        # Direct match
        if any(w in text_lower for w in topic_words):
            return True
        
        # Related words expansion (common associations)
        related = {
            'quantum': ['qubit', 'qubits', 'superposition', 'entanglement', 'decoherence', 'hadamard'],
            'computing': ['algorithm', 'computer', 'code', 'program', 'software', 'cpu', 'gpu'],
            'machine': ['model', 'training', 'neural', 'ai', 'deep', 'learning'],
            'learning': ['train', 'dataset', 'model', 'neural', 'epoch', 'gradient'],
            'programming': ['code', 'function', 'variable', 'debug', 'compile', 'syntax'],
            'science': ['experiment', 'hypothesis', 'research', 'theory', 'data'],
            'math': ['equation', 'formula', 'calculate', 'algebra', 'geometry'],
            'biology': ['cell', 'dna', 'gene', 'protein', 'organism', 'evolution'],
            'physics': ['force', 'energy', 'mass', 'velocity', 'gravity', 'particle'],
            'chemistry': ['element', 'compound', 'reaction', 'molecule', 'atom'],
        }
        for topic_word in topic_words:
            if topic_word in related:
                if any(rw in text_lower for rw in related[topic_word]):
                    return True
        
        return False
    
    def add_knowledge(self, fact, source_user):
        self.knowledge.append({'fact': fact, 'from': source_user, 'time': time.time()})
        self.add_message('ai', f'📌 New fact: {fact[:80]}', 'ai-answers', priority='silent')
    
    def get_summary(self):
        elapsed = time.time() - self.created
        mins = int(elapsed / 60)
        done = sum(1 for g in self.goals if g.status == 'complete')
        total = len(self.goals)
        return {
            'name': self.name,
            'duration_min': mins,
            'members': len(self.users),
            'messages': len(self.messages),
            'goals_done': done,
            'goals_total': total,
            'facts_learned': len(self.knowledge),
            'focus': self.focus_topic,
            'mode': self.focus_mode,
        }
    
    def get_members_display(self):
        icons = {'active': '🟢', 'away': '🟡', 'focused': '🔵', 'offline': '🔴'}
        lines = []
        for name, user in self.users.items():
            icon = icons.get(user.status, '⚪')
            role_badge = f' [{user.role}]' if user.role != 'member' else ''
            lines.append(f'  {icon} {name}{role_badge}')
        return '\n'.join(lines)
    
    def get_goals_display(self):
        lines = []
        for g in self.goals:
            icon = {'pending': '□', 'in_progress': '◐', 'complete': '✓', 'blocked': '⊘'}[g.status]
            assigned = f' @{g.assigned_to}' if g.assigned_to else ''
            lines.append(f'  {icon} {g.title}{assigned} [{g.status}]')
        return '\n'.join(lines) if lines else '  No goals yet.'


# === Workspace Manager (handles multiple workspaces) ===
class WorkspaceManager:
    def __init__(self):
        self.workspaces = {}  # code -> Workspace
        self.user_workspace = {}  # username -> code
    
    def create(self, name, owner):
        ws = Workspace(name, owner)
        self.workspaces[ws.code] = ws
        self.user_workspace[owner] = ws.code
        return ws
    
    def join(self, code, username):
        if code in self.workspaces:
            self.workspaces[code].join(username)
            self.user_workspace[username] = code
            return self.workspaces[code]
        return None
    
    def get_user_workspace(self, username):
        code = self.user_workspace.get(username)
        if code and code in self.workspaces:
            return self.workspaces[code]
        return None
    
    def leave(self, username):
        code = self.user_workspace.get(username)
        if code and code in self.workspaces:
            self.workspaces[code].leave(username)
            del self.user_workspace[username]


# === TEST / DEMO ===
if __name__ == '__main__':
    print('=== WORKSPACE MODE — SIMULATION ===')
    print()
    
    mgr = WorkspaceManager()
    
    # Alice creates workspace
    ws = mgr.create('Build AI Model', 'alice')
    print(f'Workspace created: "{ws.name}" (code: {ws.code})')
    
    # Bob and Carol join
    mgr.join(ws.code, 'bob')
    mgr.join(ws.code, 'carol')
    print(f'Members: {list(ws.users.keys())}')
    
    # Add goals
    g1 = ws.add_goal('Research transformers', 'carol')
    g2 = ws.add_goal('Find datasets', 'bob')
    g3 = ws.add_goal('Write training code', 'alice', depends_on=g1.id)
    print(f'\nGoals:')
    print(ws.get_goals_display())
    
    # Set focus
    ws.set_focus('machine learning', 'focused')
    print(f'\nFocus: {ws.focus_topic} ({ws.focus_mode})')
    
    # Check on-topic
    assert ws.is_on_topic('How does machine learning work?') == True
    assert ws.is_on_topic('What should I eat for dinner?') == False
    print('On-topic detection: ✓')
    
    # Chat
    ws.add_message('bob', 'Found ImageNet dataset!', 'research')
    ws.add_message('carol', '@alice check this paper', 'general', target='@alice')
    ws.add_message('alice', 'thanks!', 'general')
    
    # Bob completes his goal
    ws.complete_goal(g2.id, 'bob')
    print(f'\nAfter Bob completes:')
    print(ws.get_goals_display())
    
    # Carol completes → unblocks Alice
    ws.complete_goal(g1.id, 'carol')
    print(f'\nAfter Carol completes (unblocks Alice):')
    print(ws.get_goals_display())
    
    # Add shared knowledge
    ws.add_knowledge('Transformers use self-attention mechanism', 'carol')
    ws.add_knowledge('ImageNet has 14 million images', 'bob')
    
    # Summary
    print(f'\nSummary: {ws.get_summary()}')
    
    # DM visibility
    alice_msgs = ws.get_messages('alice', 'general')
    bob_msgs = ws.get_messages('bob', 'general')
    # Carol's DM to alice should be visible to alice but not bob
    carol_dm = [m for m in alice_msgs if m.target == '@alice']
    bob_sees_dm = [m for m in bob_msgs if m.target == '@alice']
    assert len(carol_dm) >= 1
    assert len(bob_sees_dm) == 0
    print('DM privacy: ✓')
    
    print(f'\nMembers:')
    print(ws.get_members_display())
    
    print('\n✅ ALL WORKSPACE TESTS PASSED!')

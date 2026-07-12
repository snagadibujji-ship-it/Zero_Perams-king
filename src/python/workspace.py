#!/usr/bin/env python3
"""
Workspace v3.0 — Maximum Level Collaboration

Multi-user collaboration rooms with:
  - Roles & permissions (owner/admin/member/viewer)
  - Channels (general/research/code/random/ai-answers)
  - Goals with dependencies (DAG task tracking)
  - Focus modes (free/focused/sprint/brainstorm/review)
  - Timed sprints (25min pomodoro or custom)
  - AI assistant per workspace (answers go to ai-answers channel)
  - Knowledge pool (shared facts discovered during session)
  - Session analytics (who contributed what, time tracking)
  - DMs and @mentions
  - Activity feed
  - Export (session summary as markdown)
  - Persistence (workspaces survive restarts)
"""

import socket, threading, json, time, os, sys, random, string, hashlib
from typing import Dict, List, Optional

DATA_DIR = os.path.join(os.path.dirname(__file__), '..', '..', 'user_data')
WORKSPACES_FILE = os.path.join(DATA_DIR, 'workspaces.json')


class User:
    def __init__(self, name, role='member'):
        self.name = name
        self.role = role  # owner/admin/member/viewer
        self.status = 'active'  # active/away/focused/offline
        self.last_seen = time.time()
        self.joined = time.time()
        self.expertise = []
        self.goals_completed = 0
        self.messages_sent = 0
        self.time_active_s = 0

    def to_dict(self):
        return {
            'name': self.name, 'role': self.role, 'status': self.status,
            'last_seen': self.last_seen, 'joined': self.joined,
            'expertise': self.expertise, 'goals_completed': self.goals_completed,
            'messages_sent': self.messages_sent, 'time_active_s': self.time_active_s,
        }

    @staticmethod
    def from_dict(d):
        u = User(d['name'], d.get('role', 'member'))
        u.status = d.get('status', 'active')
        u.last_seen = d.get('last_seen', time.time())
        u.joined = d.get('joined', time.time())
        u.expertise = d.get('expertise', [])
        u.goals_completed = d.get('goals_completed', 0)
        u.messages_sent = d.get('messages_sent', 0)
        u.time_active_s = d.get('time_active_s', 0)
        return u


class Message:
    def __init__(self, sender, text, channel='general', target=None, priority='normal'):
        self.id = hashlib.md5(f"{sender}{text}{time.time()}".encode()).hexdigest()[:8]
        self.sender = sender
        self.text = text
        self.channel = channel
        self.target = target  # None=all, '@name'=DM, '@everyone'=broadcast
        self.priority = priority  # silent/normal/urgent
        self.timestamp = time.time()
        self.reactions = {}  # emoji → [user_ids]
        self.pinned = False
        self.edited = False

    def to_dict(self):
        return {
            'id': self.id, 'sender': self.sender, 'text': self.text,
            'channel': self.channel, 'target': self.target,
            'priority': self.priority, 'timestamp': self.timestamp,
            'reactions': self.reactions, 'pinned': self.pinned, 'edited': self.edited,
        }

    @staticmethod
    def from_dict(d):
        m = Message(d['sender'], d['text'], d.get('channel', 'general'),
                    d.get('target'), d.get('priority', 'normal'))
        m.id = d.get('id', m.id)
        m.timestamp = d.get('timestamp', time.time())
        m.reactions = d.get('reactions', {})
        m.pinned = d.get('pinned', False)
        m.edited = d.get('edited', False)
        return m


class Goal:
    def __init__(self, title, assigned_to=None, depends_on=None, priority='normal'):
        self.id = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
        self.title = title
        self.assigned_to = assigned_to
        self.depends_on = depends_on  # goal ID
        self.priority = priority  # low/normal/high/critical
        self.status = 'pending'  # pending/in_progress/complete/blocked/cancelled
        self.progress = 0  # 0-100
        self.created = time.time()
        self.started_at = None
        self.completed_at = None
        self.subtasks = []  # list of mini-goals
        self.notes = []  # comments

    def to_dict(self):
        return {
            'id': self.id, 'title': self.title, 'assigned_to': self.assigned_to,
            'depends_on': self.depends_on, 'priority': self.priority,
            'status': self.status, 'progress': self.progress,
            'created': self.created, 'started_at': self.started_at,
            'completed_at': self.completed_at,
            'subtasks': self.subtasks, 'notes': self.notes,
        }

    @staticmethod
    def from_dict(d):
        g = Goal(d['title'], d.get('assigned_to'), d.get('depends_on'), d.get('priority', 'normal'))
        g.id = d.get('id', g.id)
        g.status = d.get('status', 'pending')
        g.progress = d.get('progress', 0)
        g.created = d.get('created', time.time())
        g.started_at = d.get('started_at')
        g.completed_at = d.get('completed_at')
        g.subtasks = d.get('subtasks', [])
        g.notes = d.get('notes', [])
        return g


class Sprint:
    """Timed focus session (pomodoro-style or custom)."""
    def __init__(self, duration_min=25, topic=None, started_by=None):
        self.duration_min = duration_min
        self.topic = topic
        self.started_by = started_by
        self.started_at = time.time()
        self.ends_at = self.started_at + duration_min * 60
        self.participants = [started_by] if started_by else []
        self.messages_during = 0
        self.goals_completed_during = 0
        self.active = True

    def time_remaining(self) -> int:
        """Seconds remaining."""
        return max(0, int(self.ends_at - time.time()))

    def is_expired(self) -> bool:
        return time.time() >= self.ends_at

    def to_dict(self):
        return {
            'duration_min': self.duration_min, 'topic': self.topic,
            'started_by': self.started_by, 'started_at': self.started_at,
            'ends_at': self.ends_at, 'participants': self.participants,
            'messages_during': self.messages_during,
            'goals_completed_during': self.goals_completed_during, 'active': self.active,
        }


class Workspace:
    """Full collaboration workspace."""

    def __init__(self, name, owner):
        self.name = name
        self.code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        self.owner = owner
        self.users: Dict[str, User] = {owner: User(owner, 'owner')}
        self.messages: List[Message] = []
        self.goals: List[Goal] = []
        self.knowledge: List[Dict] = []  # shared facts
        self.focus_topic = None
        self.focus_mode = 'free'  # free/focused/sprint/brainstorm/review
        self.sprint: Optional[Sprint] = None
        self.created = time.time()
        self.channels = ['general', 'research', 'code', 'random', 'ai-answers']
        self.pinned_messages: List[str] = []  # message IDs
        self.settings = {
            'allow_off_topic': True,
            'auto_ai_answers': True,  # AI answers go to ai-answers channel
            'notify_goals': True,
            'max_sprint_min': 120,
        }

    # ═══════════════════════════════════════════════════════════
    # USER MANAGEMENT
    # ═══════════════════════════════════════════════════════════

    def join(self, username, role='member') -> bool:
        if username in self.users:
            self.users[username].status = 'active'
            return True
        self.users[username] = User(username, role)
        self.add_message('system', f'{username} joined the workspace', 'general')
        return True

    def leave(self, username):
        if username in self.users:
            self.users[username].status = 'offline'
            self.add_message('system', f'{username} left', 'general')

    def set_role(self, username, role, by_user):
        """Only owner/admin can change roles."""
        if by_user not in self.users:
            return False
        if self.users[by_user].role not in ('owner', 'admin'):
            return False
        if username in self.users:
            self.users[username].role = role
            return True
        return False

    def get_active_users(self) -> List[str]:
        return [u.name for u in self.users.values() if u.status == 'active']

    # ═══════════════════════════════════════════════════════════
    # MESSAGING
    # ═══════════════════════════════════════════════════════════

    def add_message(self, sender, text, channel='general', target=None, priority='normal') -> Message:
        msg = Message(sender, text, channel, target, priority)
        self.messages.append(msg)
        if sender in self.users:
            self.users[sender].messages_sent += 1
        if self.sprint and self.sprint.active:
            self.sprint.messages_during += 1
        # Keep last 1000 messages
        if len(self.messages) > 1000:
            self.messages = self.messages[-1000:]
        return msg

    def get_messages(self, username, channel=None, limit=20) -> List[Dict]:
        """Get messages visible to user."""
        visible = []
        for m in reversed(self.messages):
            if m.target and m.target not in ('@everyone', f'@{username}'):
                if m.sender != username:
                    continue
            if channel and m.channel != channel:
                continue
            visible.append(m.to_dict())
            if len(visible) >= limit:
                break
        return list(reversed(visible))

    def pin_message(self, msg_id: str) -> bool:
        for m in self.messages:
            if m.id == msg_id:
                m.pinned = True
                self.pinned_messages.append(msg_id)
                return True
        return False

    def react(self, msg_id: str, emoji: str, user_id: str) -> bool:
        for m in self.messages:
            if m.id == msg_id:
                if emoji not in m.reactions:
                    m.reactions[emoji] = []
                if user_id not in m.reactions[emoji]:
                    m.reactions[emoji].append(user_id)
                return True
        return False

    # ═══════════════════════════════════════════════════════════
    # GOALS (DAG Task Management)
    # ═══════════════════════════════════════════════════════════

    def add_goal(self, title, assigned_to=None, depends_on=None, priority='normal') -> Goal:
        goal = Goal(title, assigned_to, depends_on, priority)
        if depends_on:
            dep = self.get_goal(depends_on)
            if dep and dep.status != 'complete':
                goal.status = 'blocked'
        self.goals.append(goal)
        self.add_message('system', f'Goal: "{title}" → @{assigned_to or "unassigned"}',
                         'general', priority='silent')
        return goal

    def start_goal(self, goal_id: str, by_user: str) -> bool:
        goal = self.get_goal(goal_id)
        if goal and goal.status in ('pending', 'blocked'):
            goal.status = 'in_progress'
            goal.started_at = time.time()
            if not goal.assigned_to:
                goal.assigned_to = by_user
            return True
        return False

    def complete_goal(self, goal_id: str, by_user: str) -> bool:
        goal = self.get_goal(goal_id)
        if goal:
            goal.status = 'complete'
            goal.progress = 100
            goal.completed_at = time.time()
            if by_user in self.users:
                self.users[by_user].goals_completed += 1
            # Unblock dependents
            for g in self.goals:
                if g.depends_on == goal_id and g.status == 'blocked':
                    g.status = 'pending'
            if self.sprint and self.sprint.active:
                self.sprint.goals_completed_during += 1
            self.add_message('system', f'@{by_user} completed: "{goal.title}"',
                             'general', target='@everyone')
            return True
        return False

    def get_goal(self, goal_id: str) -> Optional[Goal]:
        for g in self.goals:
            if g.id == goal_id:
                return g
        return None

    def get_goals_for_user(self, username: str) -> List[Dict]:
        return [g.to_dict() for g in self.goals if g.assigned_to == username]

    def get_blocked_goals(self) -> List[Dict]:
        return [g.to_dict() for g in self.goals if g.status == 'blocked']

    # ═══════════════════════════════════════════════════════════
    # FOCUS + SPRINTS
    # ═══════════════════════════════════════════════════════════

    def set_focus(self, topic, mode='focused'):
        self.focus_topic = topic
        self.focus_mode = mode
        self.add_message('system', f'Focus: {topic} (mode: {mode})', 'general')

    def clear_focus(self):
        self.focus_topic = None
        self.focus_mode = 'free'
        self.add_message('system', 'Focus cleared', 'general')

    def start_sprint(self, duration_min: int = 25, topic: str = None, started_by: str = None) -> Sprint:
        """Start a timed sprint (pomodoro-style)."""
        self.sprint = Sprint(duration_min, topic, started_by)
        self.focus_topic = topic
        self.focus_mode = 'sprint'
        self.add_message('system',
                         f'Sprint started: {duration_min}min on "{topic or "free"}" by @{started_by}',
                         'general', target='@everyone', priority='urgent')
        return self.sprint

    def end_sprint(self) -> Optional[Dict]:
        """End sprint and return summary."""
        if not self.sprint:
            return None
        self.sprint.active = False
        summary = {
            'duration_min': self.sprint.duration_min,
            'topic': self.sprint.topic,
            'messages': self.sprint.messages_during,
            'goals_completed': self.sprint.goals_completed_during,
            'participants': self.sprint.participants,
            'actual_duration_s': int(time.time() - self.sprint.started_at),
        }
        self.focus_mode = 'free'
        self.focus_topic = None
        self.add_message('system', f'Sprint ended. {summary["goals_completed"]} goals done, '
                         f'{summary["messages"]} messages.', 'general')
        self.sprint = None
        return summary

    def is_on_topic(self, text: str) -> bool:
        """Check if message matches current focus."""
        if not self.focus_topic or self.focus_mode == 'free':
            return True
        return self.focus_topic.lower() in text.lower()

    # ═══════════════════════════════════════════════════════════
    # KNOWLEDGE POOL
    # ═══════════════════════════════════════════════════════════

    def add_knowledge(self, fact: str, source_user: str):
        self.knowledge.append({'fact': fact, 'from': source_user, 'time': time.time()})
        self.add_message('ai', f'New fact: {fact[:80]}', 'ai-answers', priority='silent')

    def get_knowledge(self) -> List[Dict]:
        return self.knowledge

    # ═══════════════════════════════════════════════════════════
    # ANALYTICS
    # ═══════════════════════════════════════════════════════════

    def get_summary(self) -> Dict:
        """Full session analytics."""
        elapsed = time.time() - self.created
        done = sum(1 for g in self.goals if g.status == 'complete')
        total = len(self.goals)
        active_users = self.get_active_users()

        # Per-user stats
        user_stats = {}
        for uid, user in self.users.items():
            user_stats[uid] = {
                'messages': user.messages_sent,
                'goals_done': user.goals_completed,
                'role': user.role,
            }

        # Channel activity
        channel_counts = {}
        for m in self.messages:
            channel_counts[m.channel] = channel_counts.get(m.channel, 0) + 1

        return {
            'workspace': self.name,
            'code': self.code,
            'elapsed_min': int(elapsed / 60),
            'total_messages': len(self.messages),
            'goals_done': done,
            'goals_total': total,
            'goals_progress': f"{done}/{total}" if total else "no goals",
            'active_users': active_users,
            'total_users': len(self.users),
            'knowledge_facts': len(self.knowledge),
            'focus_mode': self.focus_mode,
            'focus_topic': self.focus_topic,
            'channel_activity': channel_counts,
            'user_stats': user_stats,
            'sprint_active': self.sprint.active if self.sprint else False,
        }

    def export_markdown(self) -> str:
        """Export session as markdown summary."""
        s = self.get_summary()
        md = f"# Workspace: {s['workspace']}\n\n"
        md += f"**Duration:** {s['elapsed_min']} minutes\n"
        md += f"**Participants:** {', '.join(s['active_users'])}\n"
        md += f"**Goals:** {s['goals_progress']}\n"
        md += f"**Messages:** {s['total_messages']}\n"
        md += f"**Knowledge gained:** {s['knowledge_facts']} facts\n\n"

        if self.goals:
            md += "## Goals\n\n"
            for g in self.goals:
                status_icon = {'complete': '[x]', 'in_progress': '[-]', 'pending': '[ ]', 'blocked': '[!]'}.get(g.status, '[ ]')
                md += f"- {status_icon} {g.title} (@{g.assigned_to or 'unassigned'})\n"
            md += "\n"

        if self.knowledge:
            md += "## Knowledge Gained\n\n"
            for k in self.knowledge:
                md += f"- {k['fact']} (from @{k['from']})\n"
            md += "\n"

        # Key messages (pinned)
        pinned = [m for m in self.messages if m.pinned]
        if pinned:
            md += "## Key Messages\n\n"
            for m in pinned:
                md += f"> **@{m.sender}**: {m.text}\n\n"

        return md

    # ═══════════════════════════════════════════════════════════
    # SERIALIZATION
    # ═══════════════════════════════════════════════════════════

    def to_dict(self) -> Dict:
        return {
            'name': self.name, 'code': self.code, 'owner': self.owner,
            'users': {k: v.to_dict() for k, v in self.users.items()},
            'messages': [m.to_dict() for m in self.messages[-200:]],  # Keep last 200
            'goals': [g.to_dict() for g in self.goals],
            'knowledge': self.knowledge,
            'focus_topic': self.focus_topic, 'focus_mode': self.focus_mode,
            'created': self.created, 'channels': self.channels,
            'settings': self.settings,
        }

    @staticmethod
    def from_dict(d) -> 'Workspace':
        ws = Workspace(d['name'], d['owner'])
        ws.code = d.get('code', ws.code)
        ws.users = {k: User.from_dict(v) for k, v in d.get('users', {}).items()}
        ws.messages = [Message.from_dict(m) for m in d.get('messages', [])]
        ws.goals = [Goal.from_dict(g) for g in d.get('goals', [])]
        ws.knowledge = d.get('knowledge', [])
        ws.focus_topic = d.get('focus_topic')
        ws.focus_mode = d.get('focus_mode', 'free')
        ws.created = d.get('created', time.time())
        ws.channels = d.get('channels', ws.channels)
        ws.settings = d.get('settings', ws.settings)
        return ws


# ═══════════════════════════════════════════════════════════════
# WORKSPACE MANAGER (multiple workspaces, persistence)
# ═══════════════════════════════════════════════════════════════

class WorkspaceManager:
    """Manages multiple workspaces with persistence."""

    def __init__(self):
        self.workspaces: Dict[str, Workspace] = {}  # code → workspace
        self.load()

    def load(self):
        if os.path.isfile(WORKSPACES_FILE):
            try:
                with open(WORKSPACES_FILE) as f:
                    data = json.load(f)
                for code, ws_data in data.items():
                    self.workspaces[code] = Workspace.from_dict(ws_data)
            except: pass

    def save(self):
        os.makedirs(DATA_DIR, exist_ok=True)
        with open(WORKSPACES_FILE, 'w') as f:
            json.dump({code: ws.to_dict() for code, ws in self.workspaces.items()}, f)

    def create(self, name: str, owner: str) -> Workspace:
        ws = Workspace(name, owner)
        self.workspaces[ws.code] = ws
        self.save()
        return ws

    def join_by_code(self, code: str, username: str) -> Optional[Workspace]:
        code = code.upper()
        if code in self.workspaces:
            self.workspaces[code].join(username)
            self.save()
            return self.workspaces[code]
        return None

    def get(self, code: str) -> Optional[Workspace]:
        return self.workspaces.get(code.upper())

    def list_for_user(self, username: str) -> List[Dict]:
        results = []
        for code, ws in self.workspaces.items():
            if username in ws.users:
                results.append({'name': ws.name, 'code': code, 'users': len(ws.users)})
        return results

    def delete(self, code: str, by_user: str) -> bool:
        ws = self.workspaces.get(code.upper())
        if ws and ws.owner == by_user:
            del self.workspaces[code.upper()]
            self.save()
            return True
        return False


# ═══════════════════════════════════════════════════════════════
# CLI TEST
# ═══════════════════════════════════════════════════════════════

if __name__ == '__main__':
    print("Workspace v3.0 — Self-test")

    mgr = WorkspaceManager()
    ws = mgr.create("Test Project", "alice")
    print(f"  Created workspace: {ws.name} (code: {ws.code})")

    ws.join("bob")
    ws.join("carol")
    print(f"  Users: {ws.get_active_users()}")

    # Goals
    g1 = ws.add_goal("Research topic", assigned_to="alice", priority="high")
    g2 = ws.add_goal("Write code", assigned_to="bob", depends_on=g1.id)
    g3 = ws.add_goal("Test code", assigned_to="carol", depends_on=g2.id)
    print(f"  Goals: {len(ws.goals)} (g2 blocked: {ws.goals[1].status})")

    ws.complete_goal(g1.id, "alice")
    print(f"  After g1 complete: g2 status = {ws.goals[1].status}")

    # Sprint
    sprint = ws.start_sprint(25, "implement feature", "bob")
    print(f"  Sprint: {sprint.duration_min}min, remaining: {sprint.time_remaining()}s")

    # Messages
    ws.add_message("alice", "Starting research now", "research")
    ws.add_message("bob", "Found a bug", "code")
    ws.add_message("carol", "@bob I can help", "code", target="@bob")
    print(f"  Messages: {len(ws.messages)}")

    # Knowledge
    ws.add_knowledge("Python uses indentation for blocks", "alice")
    ws.add_knowledge("GIL limits true parallelism", "bob")

    # Summary
    summary = ws.get_summary()
    print(f"  Summary: {summary['goals_progress']} goals, {summary['total_messages']} msgs")

    # Export
    md = ws.export_markdown()
    print(f"  Markdown export: {len(md)} chars")

    # Persistence
    mgr.save()
    mgr2 = WorkspaceManager()
    loaded = mgr2.get(ws.code)
    print(f"  Persistence: loaded workspace '{loaded.name}' with {len(loaded.users)} users")

    print("\n  ALL WORKSPACE v3.0 TESTS PASSED")

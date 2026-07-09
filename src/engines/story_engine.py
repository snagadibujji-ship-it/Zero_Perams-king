"""
Story Engine — Wave 2
======================
Manages cause-effect chains, task continuity, and context.

When a breakdown happens → next 5-15 events are ALL about fixing it.
When a person starts a task → they finish it before switching.
Night time → no social events, only monitoring and sleepy messages.
"""
import random
from typing import List, Dict, Optional


class StoryEngine:
    """Manages ongoing stories and task continuity."""
    
    def __init__(self, rng: random.Random):
        self.rng = rng
        self.active_story = None  # Current running story
        self.story_events_remaining = 0
        self.task_lock = None  # Current task category lock
        self.task_events_remaining = 0
    
    def should_override_category(self, hour: int) -> Optional[str]:
        """Check if a story or task lock should override random category selection.
        
        Returns:
            Category to force, or None to let random selection happen.
        """
        # If there's an active story, force its events
        if self.active_story and self.story_events_remaining > 0:
            self.story_events_remaining -= 1
            event = self.active_story["events"][0]
            self.active_story["events"] = self.active_story["events"][1:]
            if not self.active_story["events"]:
                self.active_story = None
            return event
        
        # If there's a task lock, keep same category
        if self.task_lock and self.task_events_remaining > 0:
            self.task_events_remaining -= 1
            if self.task_events_remaining <= 0:
                self.task_lock = None
            return self.task_lock
        
        # Night time override — NO social events between 0-5am
        if 0 <= hour < 5:
            return self.rng.choice([
                "routine_monitoring", "routine_monitoring", "routine_monitoring",
                "night_shift_special", "equipment_sounds", "daily_ops",
            ])
        
        return None
    
    def trigger_story(self, trigger_type: str):
        """Start a cause-effect story chain based on a trigger event."""
        stories = {
            "breakdown": {
                "events": ["maintenance", "maintenance", "maintenance", 
                          "daily_ops", "maintenance", "quality"],
                "description": "Equipment breakdown → diagnosis → repair → test"
            },
            "quality_reject": {
                "events": ["quality", "quality", "mistakes_failures",
                          "daily_ops", "quality"],
                "description": "Batch rejected → investigation → rework"
            },
            "safety_incident": {
                "events": ["safety_accidents", "safety_accidents", "leadership",
                          "documentation", "workforce"],
                "description": "Incident → response → investigation → report"
            },
            "visitor_arrival": {
                "events": ["visitor_external", "daily_ops", "visitor_external",
                          "documentation"],
                "description": "Visitor comes → tour → questions → leave"
            },
            "delivery_arrived": {
                "events": ["supply_chain", "supply_chain", "daily_ops",
                          "documentation"],
                "description": "Truck arrives → unloading → checking → storing"
            },
            "shift_start": {
                "events": ["commute_arrival", "commute_arrival", "shift_handover",
                          "shift_handover", "daily_ops", "routine_monitoring"],
                "description": "People arrive → change clothes → briefing → start"
            },
            "lunch_time": {
                "events": ["canteen_food", "canteen_food", "human_relations",
                          "human_relations", "personal_life"],
                "description": "Lunch break → eat → chat → personal stuff"
            },
            "end_of_shift": {
                "events": ["shift_handover", "documentation", "shift_handover",
                          "commute_arrival"],
                "description": "Handover notes → log entry → brief incoming → leave"
            },
        }
        
        if trigger_type in stories:
            story = stories[trigger_type]
            self.active_story = {
                "type": trigger_type,
                "events": story["events"].copy(),
                "description": story["description"],
            }
            self.story_events_remaining = len(story["events"])
    
    def lock_task(self, category: str, duration: int = None):
        """Lock the person into a task category for multiple events."""
        if duration is None:
            duration = self.rng.randint(2, 5)
        self.task_lock = category
        self.task_events_remaining = duration
    
    def check_triggers(self, category: str, subtype: str, hour: int):
        """Check if current event should trigger a story chain."""
        # Don't trigger if already in a story
        if self.active_story:
            return
        
        # Breakdown triggers repair chain
        if subtype in ("breakdown_repair", "electrical_fault") or "breakdown" in subtype:
            if self.rng.random() < 0.7:
                self.trigger_story("breakdown")
        
        # Quality reject triggers investigation
        elif subtype in ("rejection_report", "nonconformance_raised", "production_rejected_batch"):
            if self.rng.random() < 0.5:
                self.trigger_story("quality_reject")
        
        # Safety incident triggers response chain
        elif category == "safety_accidents":
            if self.rng.random() < 0.8:
                self.trigger_story("safety_incident")
        
        # Time-based triggers
        if hour == 6 and self.rng.random() < 0.3:
            self.trigger_story("shift_start")
        elif hour == 12 and self.rng.random() < 0.4:
            self.trigger_story("lunch_time")
        elif hour == 14 and self.rng.random() < 0.2:
            self.trigger_story("shift_start")  # Afternoon shift
        elif hour == 17 and self.rng.random() < 0.3:
            self.trigger_story("end_of_shift")
        
        # Random delivery (once per day chance)
        if category == "supply_chain" and "received" in subtype:
            if self.rng.random() < 0.4:
                self.trigger_story("delivery_arrived")
        
        # If not in a story, sometimes lock into current task
        if self.task_lock is None and self.rng.random() < 0.3:
            if category in ("maintenance", "quality", "daily_ops", "documentation"):
                self.lock_task(category, self.rng.randint(2, 4))


class NightFilter:
    """Filters events to be appropriate for time of day."""
    
    # Categories that should NEVER appear at certain times
    NIGHT_BANNED = {
        "canteen_food",       # Canteen IS closed at 3am (but food sharing is in human_relations)
        "learning_training",  # No training at night
        "leadership",         # No meetings at 3am
        "visitor_external",   # No visitors at night
        "customer_sales",     # No customers at 3am
        "competition",        # Not discussed at night
        "holidays_breaks",    # Not relevant at 3am
        "innovation",         # No brainstorming at 3am
        "commute_arrival",    # Nobody arriving at 3am
        "regulation",         # No inspections at night
        "expansion",          # No planning at night
        "mergers_acquisitions",  # Not at night
    }
    
    # Categories ALLOWED at night — workers ARE human, they chat!
    NIGHT_ALLOWED = {
        "routine_monitoring",    # Main job at night
        "daily_ops",             # Work continues
        "equipment_sounds",      # Things sound louder at night
        "night_shift_special",   # Sleepy, bored, ghost stories
        "maintenance",           # Planned shutdowns often at night
        "safety_accidents",      # Accidents can happen anytime
        "crisis",                # Crisis can happen anytime
        "human_relations",       # Workers DO chat at night to stay awake!
        "gossip_rumors",         # Actually MORE gossip (less supervision)
        "personal_life",         # Call family, share worries
        "documentation",         # Log entries happen anytime
        "workforce",             # Attendance, shift swaps
    }
    
    DAY_PEAK_CATEGORIES = {
        "commute_arrival": (5, 8),      # Only 5am-8am
        "canteen_food": (11, 14),       # Only 11am-2pm (lunch) + 7-9pm (dinner)
        "leadership": (8, 17),          # Only office hours
        "visitor_external": (9, 17),    # Only business hours
        "customer_sales": (8, 18),      # Only business hours
        "learning_training": (7, 16),   # Only work hours
    }
    
    @classmethod
    def is_allowed(cls, category: str, hour: int) -> bool:
        """Check if a category is appropriate for this hour."""
        # Night time (0-5am)
        if 0 <= hour < 5:
            if category in cls.NIGHT_BANNED:
                return False
        
        # Check time-restricted categories
        if category in cls.DAY_PEAK_CATEGORIES:
            start, end = cls.DAY_PEAK_CATEGORIES[category]
            if not (start <= hour <= end):
                # Special case: canteen also allowed at dinner time
                if category == "canteen_food" and 19 <= hour <= 21:
                    return True
                return False
        
        return True
    
    @classmethod
    def get_night_replacement(cls, rng) -> str:
        """Get an appropriate night-time category.
        
        Night workers DO socialize — they're bored and lonely!
        But no canteen, no meetings, no visitors.
        """
        night_choices = [
            "routine_monitoring", "routine_monitoring", "routine_monitoring",
            "daily_ops", "daily_ops", "daily_ops",
            "equipment_sounds", "equipment_sounds",
            "night_shift_special", "night_shift_special", "night_shift_special",
            "maintenance", "maintenance",
            "human_relations", "human_relations",  # YES they chat at night!
            "gossip_rumors",  # Less supervision = more gossip
            "personal_life",  # Calling family, sharing worries
            "documentation",  # Log entries
        ]
        return rng.choice(night_choices)

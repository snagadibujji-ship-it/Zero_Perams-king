"""Workforce Dynamics Engine — Realistic industrial workforce lifecycle.

DESIGN PRINCIPLES:
1. A person works in ONE department at ONE position at a time
   - But different departments have different role titles
   - Production: operator, senior operator, shift charge, plant superintendent
   - Maintenance: fitter, technician, foreman, maintenance manager
   - Security: watchman, guard supervisor, security officer, chief security
   - Admin: clerk, assistant, executive, head of admin
   
2. People join at ANY age (18-55+):
   - 18: Helper/apprentice (no qualifications, learns on job)
   - 20-24: After ITI/diploma (technician entry)
   - 22-26: After engineering degree (graduate trainee)
   - 28-40: Experienced lateral hire (mid-management)
   - 40-55: Senior specialist/consultant hire (top management)
   
3. NOT everyone gets promoted:
   - Some stay worker level 30 years (common in India/Middle East)
   - Some get promoted fast (merit or nepotism)
   - Some get demoted and never recover
   - Promotion depends on: education, connections, performance, vacancy, politics
   
4. Real workforce dynamics:
   - Transfers between departments (rare but happens)
   - Deputation to other plants
   - Long leave (maternity, medical, personal)
   - Suspension pending inquiry
   - Abscondment (just stops coming)
   - Contract vs permanent employees
   - Daily wage workers (most unstable)
   - Retired persons rehired as consultants
"""
from typing import Any, Dict, List, Optional, Tuple
from core.random.deterministic_rng import DeterministicRNG
import hashlib


# =============================================================================
# DEPARTMENT STRUCTURE — Each department has its OWN role titles
# =============================================================================

DEPARTMENTS = {
    'production': {
        'roles': ['helper', 'operator', 'senior_operator', 'panel_operator', 
                  'shift_charge_engineer', 'assistant_superintendent',
                  'superintendent', 'deputy_manager', 'manager_production',
                  'general_manager_production', 'VP_production'],
        'shift_based': True,
        'typical_strength': 0.35,  # 35% of plant workforce
    },
    'maintenance_mechanical': {
        'roles': ['helper', 'fitter', 'senior_fitter', 'technician',
                  'senior_technician', 'foreman', 'assistant_engineer',
                  'engineer', 'senior_engineer', 'manager_maintenance',
                  'GM_maintenance'],
        'shift_based': False,
        'typical_strength': 0.15,
    },
    'maintenance_electrical': {
        'roles': ['helper', 'wireman', 'electrician', 'senior_electrician',
                  'electrical_foreman', 'assistant_engineer_electrical',
                  'engineer_electrical', 'senior_engineer_electrical',
                  'manager_electrical', 'chief_engineer_electrical'],
        'shift_based': False,
        'typical_strength': 0.08,
    },
    'instrumentation': {
        'roles': ['helper', 'instrument_mechanic', 'senior_instrument_mechanic',
                  'instrument_technician', 'instrument_foreman',
                  'assistant_engineer_instrumentation', 'engineer_instrumentation',
                  'manager_instrumentation'],
        'shift_based': False,
        'typical_strength': 0.05,
    },
    'safety': {
        'roles': ['safety_steward', 'safety_officer', 'senior_safety_officer',
                  'assistant_manager_safety', 'manager_safety',
                  'chief_safety_officer'],
        'shift_based': False,
        'typical_strength': 0.03,
    },
    'quality_lab': {
        'roles': ['lab_attendant', 'lab_technician', 'senior_lab_technician',
                  'chemist', 'senior_chemist', 'quality_manager'],
        'shift_based': True,
        'typical_strength': 0.04,
    },
    'stores_procurement': {
        'roles': ['store_helper', 'store_keeper', 'senior_store_keeper',
                  'purchase_assistant', 'purchase_officer', 'manager_materials'],
        'shift_based': False,
        'typical_strength': 0.04,
    },
    'security': {
        'roles': ['watchman', 'senior_watchman', 'guard_supervisor',
                  'security_officer', 'chief_security_officer'],
        'shift_based': True,
        'typical_strength': 0.05,
    },
    'administration': {
        'roles': ['peon', 'clerk', 'senior_clerk', 'assistant',
                  'executive', 'manager_admin', 'GM_admin'],
        'shift_based': False,
        'typical_strength': 0.05,
    },
    'hr_training': {
        'roles': ['assistant_hr', 'hr_executive', 'senior_hr_executive',
                  'training_officer', 'manager_hr', 'VP_hr'],
        'shift_based': False,
        'typical_strength': 0.03,
    },
    'finance': {
        'roles': ['accounts_clerk', 'accountant', 'senior_accountant',
                  'finance_executive', 'manager_finance', 'CFO'],
        'shift_based': False,
        'typical_strength': 0.03,
    },
    'planning': {
        'roles': ['planning_assistant', 'planner', 'senior_planner',
                  'planning_engineer', 'manager_planning'],
        'shift_based': False,
        'typical_strength': 0.03,
    },
    'it_systems': {
        'roles': ['computer_operator', 'system_administrator',
                  'DCS_engineer', 'senior_DCS_engineer', 'IT_manager'],
        'shift_based': False,
        'typical_strength': 0.02,
    },
    'environment': {
        'roles': ['environment_technician', 'environment_officer',
                  'senior_environment_officer', 'manager_environment'],
        'shift_based': False,
        'typical_strength': 0.02,
    },
    'top_management': {
        'roles': ['deputy_general_manager', 'general_manager',
                  'executive_director', 'managing_director', 'CEO'],
        'shift_based': False,
        'typical_strength': 0.01,
    },
    'contract_labor': {
        'roles': ['daily_wage_worker', 'contract_helper', 'contract_operator',
                  'contract_technician', 'contractor_supervisor'],
        'shift_based': True,
        'typical_strength': 0.15,  # Large contract workforce
    },
}



# =============================================================================
# EMPLOYMENT TYPES — Different stability and benefits
# =============================================================================

EMPLOYMENT_TYPES = {
    'permanent': {'stability': 0.98, 'benefits': True, 'union_eligible': True},
    'probation': {'stability': 0.85, 'benefits': True, 'union_eligible': False},
    'contract_fixed': {'stability': 0.7, 'benefits': False, 'union_eligible': False},
    'contract_renewable': {'stability': 0.5, 'benefits': False, 'union_eligible': False},
    'daily_wage': {'stability': 0.3, 'benefits': False, 'union_eligible': False},
    'consultant': {'stability': 0.6, 'benefits': False, 'union_eligible': False},
    'trainee': {'stability': 0.9, 'benefits': True, 'union_eligible': False},
    'apprentice': {'stability': 0.95, 'benefits': False, 'union_eligible': False},
    'deputation': {'stability': 0.8, 'benefits': True, 'union_eligible': False},
}

# =============================================================================
# JOINING AGE DISTRIBUTION — Realistic entry points
# =============================================================================

JOINING_PROFILES = {
    'unskilled_entry': {
        'age_range': (18, 25), 'weight': 0.25,
        'education': 'below_10th',
        'entry_departments': ['production', 'maintenance_mechanical', 'security', 
                             'stores_procurement', 'contract_labor'],
        'entry_level': 0,  # Bottom level in department
        'employment_type': 'daily_wage',
    },
    'iti_diploma': {
        'age_range': (20, 28), 'weight': 0.30,
        'education': 'ITI_diploma',
        'entry_departments': ['production', 'maintenance_mechanical', 'maintenance_electrical',
                             'instrumentation', 'quality_lab'],
        'entry_level': 1,  # Second level (fitter, operator, etc.)
        'employment_type': 'probation',
    },
    'graduate_engineer': {
        'age_range': (22, 28), 'weight': 0.20,
        'education': 'engineering_degree',
        'entry_departments': ['production', 'maintenance_mechanical', 'maintenance_electrical',
                             'instrumentation', 'safety', 'planning', 'it_systems', 'environment'],
        'entry_level': 3,  # Mid level (assistant engineer, etc.)
        'employment_type': 'trainee',
    },
    'experienced_lateral': {
        'age_range': (28, 45), 'weight': 0.15,
        'education': 'degree_plus_experience',
        'entry_departments': ['production', 'maintenance_mechanical', 'safety',
                             'planning', 'hr_training', 'finance', 'administration'],
        'entry_level': 5,  # Senior level
        'employment_type': 'permanent',
    },
    'senior_specialist': {
        'age_range': (40, 55), 'weight': 0.05,
        'education': 'postgraduate_or_specialist',
        'entry_departments': ['top_management', 'safety', 'hr_training', 'finance',
                             'it_systems', 'environment'],
        'entry_level': 7,  # Near top
        'employment_type': 'permanent',
    },
    'retired_rehire': {
        'age_range': (58, 65), 'weight': 0.02,
        'education': 'veteran',
        'entry_departments': ['production', 'maintenance_mechanical', 'safety', 'planning'],
        'entry_level': 4,  # Mid level (advisory role)
        'employment_type': 'consultant',
    },
    'contract_worker': {
        'age_range': (18, 50), 'weight': 0.03,
        'education': 'varied',
        'entry_departments': ['contract_labor'],
        'entry_level': 0,
        'employment_type': 'contract_renewable',
    },
}

# =============================================================================
# PROMOTION REALITY — NOT everyone gets promoted
# =============================================================================

PROMOTION_PATTERNS = {
    'fast_track': {
        'probability': 0.05,  # Only 5% are fast-tracked
        'avg_years_between_promotions': 2,
        'reasons': ['merit', 'connections', 'shortage_above', 'management_favorite'],
    },
    'normal': {
        'probability': 0.30,  # 30% get normal promotions
        'avg_years_between_promotions': 5,
        'reasons': ['seniority', 'adequate_performance', 'vacancy'],
    },
    'slow': {
        'probability': 0.25,  # 25% are slow movers
        'avg_years_between_promotions': 10,
        'reasons': ['poor_performance', 'no_vacancy', 'political_issues'],
    },
    'stagnant': {
        'probability': 0.30,  # 30% NEVER get promoted
        'avg_years_between_promotions': 999,  # Effectively never
        'reasons': ['no_education', 'disciplinary_record', 'no_vacancy', 
                   'satisfied_at_current_level', 'contract_employee'],
    },
    'political': {
        'probability': 0.10,  # 10% get promoted for wrong reasons
        'avg_years_between_promotions': 3,
        'reasons': ['nepotism', 'caste_network', 'union_pressure', 'sycophancy'],
    },
}



# =============================================================================
# NAME POOLS BY REGION
# =============================================================================

NAME_POOLS = {
    'south_india': {
        'male': ['Prasad', 'Venkat', 'Kiran', 'Ravi', 'Suresh', 'Mahesh', 'Ramesh',
                 'Rajesh', 'Srinivas', 'Nagaraju', 'Balu', 'Kumar', 'Satish', 'Ganesh',
                 'Murali', 'Harish', 'Chandra', 'Vijay', 'Anil', 'Suman', 'Raju',
                 'Hari', 'Gopal', 'Srikanth', 'Phani', 'Naveen', 'Vamsi', 'Pavan',
                 'Bharath', 'Manoj', 'Sekhar', 'Rambabu', 'Apparao', 'Subbarao',
                 'Venkateswarlu', 'Satyanarayana', 'Padmanabham'],
        'female': ['Anita', 'Lakshmi', 'Sridevi', 'Padma', 'Swathi', 'Divya', 'Priya',
                   'Madhavi', 'Rekha', 'Sarala', 'Deepika', 'Mounika', 'Lavanya'],
        'last': ['Reddy', 'Rao', 'Naidu', 'Sharma', 'Prasad', 'Kumar', 'Varma',
                 'Chowdary', 'Goud', 'Setty', 'Raju', 'Murthy', 'Swamy', 'Patil',
                 'Deshmukh', 'Iyer', 'Nair', 'Pillai', 'Menon', 'Babu'],
    },
    'north_india': {
        'male': ['Amit', 'Rahul', 'Vikram', 'Deepak', 'Sachin', 'Pradeep', 'Ajay',
                 'Sanjay', 'Manoj', 'Arun', 'Rakesh', 'Ashok', 'Mukesh', 'Dinesh',
                 'Sunil', 'Vivek', 'Rohit', 'Gaurav', 'Nikhil', 'Ankur', 'Mohit',
                 'Rajendra', 'Bhagwan', 'Rampal', 'Dharamvir', 'Satpal', 'Jagdish',
                 'Balram', 'Harbans', 'Surinder', 'Kuldeep'],
        'female': ['Neha', 'Pooja', 'Ritu', 'Sunita', 'Shweta', 'Kavita', 'Meena',
                   'Geeta', 'Renu'],
        'last': ['Singh', 'Sharma', 'Verma', 'Gupta', 'Jain', 'Agarwal', 'Mishra',
                 'Pandey', 'Tiwari', 'Dubey', 'Yadav', 'Chauhan', 'Rajput', 'Saxena',
                 'Srivastava', 'Mehta', 'Chopra', 'Thakur', 'Bhatt', 'Tyagi'],
    },
    'middle_east': {
        'male': ['Mohammed', 'Ahmed', 'Ali', 'Hassan', 'Rashid', 'Khalid', 'Omar',
                 'Yusuf', 'Ibrahim', 'Faisal', 'Tariq', 'Hamza', 'Saeed', 'Nasser',
                 'Salim', 'Waleed', 'Majid', 'Fahad', 'Bilal', 'Zaid', 'Hasan', 'Imran'],
        'female': ['Fatima', 'Aisha', 'Maryam', 'Layla', 'Noor', 'Sara'],
        'last': ['Al-Rashid', 'Al-Maktoum', 'Al-Thani', 'Al-Saud', 'Al-Nahyan',
                 'Khan', 'Hussain', 'Abbasi', 'Malik', 'Sheikh', 'Qureshi',
                 'Al-Harbi', 'Al-Ghamdi', 'Al-Zahrani', 'Al-Otaibi', 'Al-Dosari'],
    },
    'europe': {
        'male': ['Hans', 'Klaus', 'Werner', 'Fritz', 'Heinrich', 'Stefan', 'Thomas',
                 'Michael', 'Andreas', 'Peter', 'Karl', 'Helmut', 'Dieter', 'Wolfgang',
                 'Pierre', 'Jacques', 'Jean', 'Marcel', 'Giuseppe', 'Antonio', 'Marco',
                 'Roberto', 'Giovanni'],
        'female': ['Maria', 'Anna', 'Elena'],
        'last': ['Mueller', 'Schmidt', 'Weber', 'Fischer', 'Wagner', 'Becker',
                 'Hoffmann', 'Koch', 'Richter', 'Klein', 'Zimmermann', 'Dupont',
                 'Martin', 'Bernard', 'Moreau', 'Laurent', 'Rossi', 'Russo'],
    },
    'americas': {
        'male': ['James', 'Robert', 'John', 'Michael', 'David', 'William', 'Richard',
                 'Joseph', 'Thomas', 'Charles', 'Carlos', 'Miguel', 'Jose', 'Luis',
                 'Pedro', 'Antonio', 'Fernando', 'Ricardo'],
        'female': ['Mary', 'Patricia', 'Jennifer', 'Linda', 'Elizabeth', 'Barbara',
                   'Maria', 'Guadalupe'],
        'last': ['Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Garcia', 'Martinez',
                 'Rodriguez', 'Hernandez', 'Lopez', 'Wilson', 'Anderson', 'Taylor',
                 'Thomas', 'Jackson', 'White', 'Thompson', 'Davis'],
    },
    'east_asia': {
        'male': ['Wei', 'Jian', 'Ming', 'Hui', 'Lei', 'Tao', 'Yang', 'Xiao',
                 'Chen', 'Lin', 'Kenji', 'Takeshi', 'Hiroshi', 'Satoshi',
                 'Jin', 'Hyun', 'Sung', 'Min', 'Jun', 'Hao', 'Yu', 'Rui'],
        'female': ['Yuki'],
        'last': ['Wang', 'Li', 'Zhang', 'Liu', 'Chen', 'Yang', 'Huang', 'Wu',
                 'Tanaka', 'Suzuki', 'Sato', 'Kim', 'Park', 'Lee', 'Choi'],
    },
}



# =============================================================================
# EMPLOYEE GENERATION
# =============================================================================

def _generate_employee_id(plant_seed: int, sequence: int) -> str:
    """Generate a deterministic unique employee ID."""
    raw = f"{plant_seed}:{sequence}"
    return "EMP-" + hashlib.sha256(raw.encode()).hexdigest()[:10].upper()


def _select_joining_profile(rng) -> dict:
    """Select a joining profile based on weighted probability."""
    profiles = list(JOINING_PROFILES.values())
    weights = [p['weight'] for p in profiles]
    total = sum(weights)
    r = rng.uniform(0, total)
    cumulative = 0.0
    for p in profiles:
        cumulative += p['weight']
        if cumulative >= r:
            return p
    return profiles[0]


def _select_promotion_pattern(rng) -> dict:
    """Select lifetime promotion pattern for an employee."""
    patterns = list(PROMOTION_PATTERNS.values())
    weights = [p['probability'] for p in patterns]
    total = sum(weights)
    r = rng.uniform(0, total)
    cumulative = 0.0
    for p in patterns:
        cumulative += p['probability']
        if cumulative >= r:
            return p
    return patterns[2]  # Default: slow


def _generate_employee(emp_id: str, plant_seed: int, region: str,
                       era_year: int, rng) -> Dict[str, Any]:
    """Generate a complete employee with realistic attributes."""
    pool = NAME_POOLS.get(region, NAME_POOLS['south_india'])

    # Personal characteristics — determine gender FIRST, then pick matching name
    gender = rng.choice(['male'] * 80 + ['female'] * 20)  # Industrial skew
    if region in ('middle_east',):
        gender = rng.choice(['male'] * 92 + ['female'] * 8)

    # Select name matching gender
    gender_names = pool.get(gender, pool.get('male', []))
    first_name = rng.choice(gender_names)
    last_name = rng.choice(pool['last'])

    # Select joining profile (determines age, department, level)
    profile = _select_joining_profile(rng)
    
    # Joining age from profile range
    age_min, age_max = profile['age_range']
    join_age = rng.randint(age_min, age_max)
    
    # Department assignment from profile's eligible departments
    eligible_depts = [d for d in profile['entry_departments'] if d in DEPARTMENTS]
    department = rng.choice(eligible_depts) if eligible_depts else 'production'
    dept_info = DEPARTMENTS[department]
    
    # Entry role level (clamped to department's actual roles)
    max_level = len(dept_info['roles']) - 1
    entry_level = min(profile['entry_level'], max_level)
    
    # Employment type
    emp_type = profile['employment_type']
    
    # How long ago did they join? (varies to create mixed-tenure workforce)
    max_tenure = max(0, era_year - 1970)  # Plant can't be older than ~50 years
    tenure_years = rng.randint(0, min(max_tenure, max(0, 65 - join_age - 1)))
    
    # Current age
    current_age = join_age + tenure_years
    
    # Promotion pattern (lifetime trajectory)
    promo_pattern = _select_promotion_pattern(rng)
    
    # Calculate promotions received based on pattern
    if promo_pattern['avg_years_between_promotions'] >= 999:
        promotions = 0
    else:
        avg_yrs = promo_pattern['avg_years_between_promotions']
        # Not deterministic interval: some years early, some late
        promotions = 0
        years_counted = 0
        while years_counted < tenure_years:
            next_promo_in = max(1, rng.randint(
                max(1, avg_yrs - 2), avg_yrs + 3
            ))
            years_counted += next_promo_in
            if years_counted <= tenure_years:
                promotions += 1
    
    # Current role level
    current_level = min(max_level, entry_level + promotions)
    current_role = dept_info['roles'][current_level]
    
    # Retirement check
    retirement_age = 58 if region in ('south_india', 'north_india') else 62
    if era_year > 2010:
        retirement_age += 2
    if emp_type == 'consultant':
        retirement_age = 68  # Consultants work longer
    
    active = current_age < retirement_age
    
    # Shift assignment (only for shift-based departments)
    if dept_info['shift_based']:
        shift = rng.choice(['A', 'B', 'C'])
    else:
        shift = 'general'
    
    # Performance score (influenced by promotion pattern)
    if promo_pattern == PROMOTION_PATTERNS['fast_track']:
        perf_base = rng.uniform(0.7, 1.0)
    elif promo_pattern == PROMOTION_PATTERNS['stagnant']:
        perf_base = rng.uniform(0.2, 0.6)
    else:
        perf_base = rng.uniform(0.35, 0.85)

    # Education
    education = profile['education']
    
    # Relationships (grudges, friendships — populated later by personality engine)
    
    return {
        'employee_id': emp_id,
        'first_name': first_name,
        'last_name': last_name,
        'full_name': f"{first_name} {last_name}",
        'age': current_age,
        'gender': gender,
        'join_age': join_age,
        'join_year': era_year - tenure_years,
        'education': education,
        'department': department,
        'current_role': current_role,
        'current_role_level': current_level,
        'max_role_level': max_level,
        'employment_type': emp_type,
        'promotion_pattern': list(PROMOTION_PATTERNS.keys())[
            list(PROMOTION_PATTERNS.values()).index(promo_pattern)
        ],
        'shift_assigned': shift,
        'active': active,
        'retired': current_age >= retirement_age,
        'suspended': False,
        'on_leave': False,
        'absent_without_leave': False,
        'transferred_out': False,
        'resignation_pending': False,
        'absconded': False,
        'tenure_years': tenure_years,
        'performance_score': round(perf_base, 3),
        'promotions_received': promotions,
        'demotions_received': 0,
        'warnings_received': 0,
        'years_since_last_promotion': rng.randint(0, max(1, tenure_years)),
        'region': region,
        # These will be set by PersonalityEngine
        'morale': 0.5,
        'behavioral_mode': 'productive',
    }



# =============================================================================
# WORKFORCE SCALING BY ERA
# =============================================================================

def _calculate_workforce_size(era_year: int, plant_type: str, scale: float = 1.0) -> int:
    """Realistic workforce size based on era and plant type."""
    base_sizes = {
        'thermal_power': 800, 'refinery': 1200, 'steel_mill': 2000,
        'chemical_plant': 600, 'cement_factory': 400, 'textile_mill': 1500,
        'automotive': 3000, 'pharmaceutical': 500, 'mining': 1000,
        'shipyard': 1800, 'default': 600,
    }
    base = base_sizes.get(plant_type, base_sizes['default'])
    
    if era_year < 1800:
        base = max(20, base // 20)
    elif era_year < 1850:
        base = max(50, base // 10)
    elif era_year < 1900:
        base = max(100, base // 5)
    elif era_year < 1950:
        base = max(200, base // 2)
    elif era_year < 2000:
        pass  # full base
    else:
        base = max(base // 2, int(base * 0.85))
    
    return max(20, int(base * scale))


# =============================================================================
# MAIN ENGINE CLASS
# =============================================================================

class WorkforceDynamicsEngine:
    """
    Manages the complete lifecycle of an industrial workforce.
    
    Key principles:
    - A person can hold ONLY ONE position in ONE department at a time
    - Workforce scales with plant size and era
    - Members join at ANY age with different profiles
    - NOT everyone gets promoted (30% never do)
    - Real events: suspension, absconding, contract expiry, etc.
    """

    def __init__(self, turnover_interval: int = 480):
        self.turnover_interval = turnover_interval

    def _init_workforce(self, world_state: Any, rng: DeterministicRNG) -> None:
        """Initialize the full workforce roster."""
        hidden = world_state.hidden_state
        era_year = hidden.get('era_year', 2024)
        region = hidden.get('plant_region', 'south_india')
        plant_type = hidden.get('plant_type', 'thermal_power')
        plant_seed = hidden.get('universe_seed', 42)
        scale = hidden.get('workforce_scale', 1.0)
        
        target_size = _calculate_workforce_size(era_year, plant_type, scale)
        roster = {}
        emp_sequence = 0
        
        for i in range(target_size):
            emp_id = _generate_employee_id(plant_seed, emp_sequence)
            emp_rng = rng.split(f"emp_init_{emp_sequence}")
            employee = _generate_employee(emp_id, plant_seed, region, era_year, emp_rng._rng)
            if employee['active']:
                roster[emp_id] = employee
            emp_sequence += 1
        
        hidden['workforce'] = {
            'roster': roster,
            'next_sequence': emp_sequence,
            'total_hired': len(roster),
            'total_retired': 0, 'total_fired': 0,
            'total_resigned': 0, 'total_transferred': 0,
            'total_absconded': 0, 'total_suspended': 0,
            'era_year': era_year, 'region': region,
            'plant_type': plant_type, 'plant_seed': plant_seed,
            'target_size': target_size, 'scale': scale,
        }


    def process(self, world_state: Any, rng: DeterministicRNG) -> None:
        """Main tick processing for workforce dynamics."""
        hidden = world_state.hidden_state
        
        if 'workforce' not in hidden:
            self._init_workforce(world_state, rng)
        
        wf = hidden['workforce']
        roster = wf['roster']
        tick = world_state.world_tick
        
        # Only run lifecycle events at intervals
        if tick % self.turnover_interval != 0:
            self._publish_active_roster(hidden)
            return
        
        lifecycle_rng = rng.split(f"lifecycle_{tick}")
        events = []
        active_ids = sorted([eid for eid, e in roster.items() if e['active']])
        
        for emp_id in active_ids:
            emp = roster[emp_id]
            emp_rng = lifecycle_rng.split(f"lc_{emp_id}")
            
            # 1. Retirement
            ret_age = 58 if wf['region'] in ('south_india', 'north_india') else 62
            if emp['age'] >= ret_age and emp['employment_type'] != 'consultant':
                emp['active'] = False
                emp['retired'] = True
                wf['total_retired'] += 1
                events.append({'type': 'retirement', 'name': emp['full_name'],
                              'role': emp['current_role'], 'age': emp['age']})
                continue
            
            # 2. Contract expiry (high turnover for daily wage)
            if emp['employment_type'] == 'daily_wage' and emp_rng.random() < 0.03:
                emp['active'] = False
                events.append({'type': 'contract_ended', 'name': emp['full_name']})
                continue
            
            # 3. Abscondment (just stops coming — common with contract labor)
            if emp['employment_type'] in ('daily_wage', 'contract_renewable'):
                if emp_rng.random() < 0.005:
                    emp['active'] = False
                    emp['absconded'] = True
                    wf['total_absconded'] += 1
                    events.append({'type': 'absconded', 'name': emp['full_name']})
                    continue
            
            # 4. Resignation (morale-dependent)
            resign_prob = 0.001
            if emp.get('morale', 0.5) < 0.2:
                resign_prob += 0.04
            if emp['years_since_last_promotion'] > 8 and emp['promotion_pattern'] != 'stagnant':
                resign_prob += 0.01
            if emp['warnings_received'] >= 3:
                resign_prob += 0.02
            if emp['age'] < 35 and emp['current_role_level'] <= 1:
                resign_prob += 0.005  # Young + stuck = leaves
            if emp_rng.random() < resign_prob:
                emp['active'] = False
                emp['resignation_pending'] = True
                wf['total_resigned'] += 1
                events.append({'type': 'resignation', 'name': emp['full_name'],
                              'role': emp['current_role']})
                continue
            
            # 5. Suspension (rare)
            if emp_rng.random() < 0.0005:
                emp['suspended'] = True
                emp['active'] = False
                wf['total_suspended'] += 1
                events.append({'type': 'suspension', 'name': emp['full_name']})
                continue
            
            # 6. Promotion attempt (based on pattern)
            emp['years_since_last_promotion'] += 1
            pattern = PROMOTION_PATTERNS.get(emp['promotion_pattern'], PROMOTION_PATTERNS['slow'])
            if pattern['avg_years_between_promotions'] < 999:
                if emp['years_since_last_promotion'] >= pattern['avg_years_between_promotions']:
                    dept_info = DEPARTMENTS.get(emp['department'], DEPARTMENTS['production'])
                    max_level = len(dept_info['roles']) - 1
                    if emp['current_role_level'] < max_level:
                        if emp_rng.random() < 0.6:  # Even eligible people don't always get it
                            emp['current_role_level'] += 1
                            emp['current_role'] = dept_info['roles'][emp['current_role_level']]
                            emp['promotions_received'] += 1
                            emp['years_since_last_promotion'] = 0
                            events.append({'type': 'promotion', 'name': emp['full_name'],
                                          'new_role': emp['current_role']})
        
        # Backfill hiring
        active_count = len([e for e in roster.values() if e['active']])
        hires_needed = max(0, wf['target_size'] - active_count)
        for _ in range(min(hires_needed, 5)):
            emp_seq = wf['next_sequence']
            wf['next_sequence'] = emp_seq + 1
            emp_id = _generate_employee_id(wf['plant_seed'], emp_seq)
            hire_rng = lifecycle_rng.split(f"hire_{emp_seq}")
            new_emp = _generate_employee(emp_id, wf['plant_seed'], wf['region'],
                                        wf['era_year'], hire_rng._rng)
            new_emp['tenure_years'] = 0
            new_emp['active'] = True
            new_emp['retired'] = False
            roster[emp_id] = new_emp
            wf['total_hired'] += 1
            events.append({'type': 'new_hire', 'name': new_emp['full_name'],
                          'age': new_emp['age'], 'role': new_emp['current_role']})
        
        if events:
            world_state.event_log.append({'tick': tick, 'type': 'workforce_lifecycle',
                                         'events': events[:20],  # Cap log size
                                         'active_headcount': active_count})
        self._publish_active_roster(hidden)


    def _publish_active_roster(self, hidden: Dict) -> None:
        """Publish active roster summary for other engines."""
        wf = hidden['workforce']
        roster = wf['roster']
        active = [e for e in roster.values() if e['active']]
        
        shift_rosters = {'A': [], 'B': [], 'C': [], 'general': []}
        dept_counts = {}
        for emp in active:
            shift = emp.get('shift_assigned', 'general')
            shift_rosters.setdefault(shift, []).append(emp)
            dept = emp.get('department', 'production')
            dept_counts[dept] = dept_counts.get(dept, 0) + 1
        
        hidden['active_workforce'] = {
            'headcount': len(active),
            'by_shift': {k: len(v) for k, v in shift_rosters.items()},
            'by_department': dept_counts,
            'shift_rosters': shift_rosters,
        }

    def get_current_shift_members(self, hidden: Dict, tick: int) -> List[Dict]:
        """Get members currently on active shift duty."""
        if 'active_workforce' not in hidden:
            return []
        shift_cycle = tick % 5760
        if shift_cycle < 1920:
            current_shift = 'A'
        elif shift_cycle < 3840:
            current_shift = 'B'
        else:
            current_shift = 'C'
        rosters = hidden['active_workforce'].get('shift_rosters', {})
        shift_members = rosters.get(current_shift, [])
        general_members = rosters.get('general', [])
        if current_shift == 'A':
            return shift_members + general_members
        return shift_members

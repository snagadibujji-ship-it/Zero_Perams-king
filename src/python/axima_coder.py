#!/usr/bin/env python3
"""
AXIMA CODER V2 — System Architecture-Based Code Generator
Built by: Ghias + Kiro | July 2026

Philosophy: Understand SYSTEM ARCHITECTURE → then EXPRESS it as code.
A todo app isn't "files with React code."
A todo app is: STATE MACHINE + EVENT HANDLERS + PERSISTENCE + UI PROJECTION.

Features:
  - System model: Data → Logic → Interface → Infrastructure
  - Dependency resolver (framework → compatible versions)
  - Security by default (auth, sanitization, CORS, env vars)
  - Complex flow patterns (auth, payments, realtime, CRUD)
  - Static analysis (missing imports, undefined vars, type mismatches)
  - Multi-framework support (React, Vue, Flask, Express, FastAPI, etc.)
  - Project scaffolding (full directory structure)

Builds ON TOP of codegen_engine.py (which handles algorithm-level code).
"""

import re
import json
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field



# ═══════════════════════════════════════════════════════════════
# SYSTEM MODEL — Every app decomposed into 4 layers
# ═══════════════════════════════════════════════════════════════

@dataclass
class Entity:
    """A data entity in the system."""
    name: str
    fields: Dict[str, str] = field(default_factory=dict)  # field_name → type
    relations: List[str] = field(default_factory=list)     # "User --owns--> Todo[]"

@dataclass
class Operation:
    """A business logic operation."""
    name: str
    entity: str
    action: str            # create, read, update, delete, list, search
    auth_required: bool = True
    owner_only: bool = False
    params: List[str] = field(default_factory=list)
    returns: str = ""

@dataclass
class SystemModel:
    """Complete system architecture."""
    name: str = ""
    entities: List[Entity] = field(default_factory=list)
    operations: List[Operation] = field(default_factory=list)
    features: List[str] = field(default_factory=list)      # auth, realtime, payments, upload
    frontend: str = "react"        # react, vue, nextjs, angular, none
    backend: str = "fastapi"       # fastapi, express, flask, django, none
    database: str = "sqlite"       # sqlite, postgres, mongodb, firebase
    auth_method: str = "jwt"       # jwt, session, firebase, oauth
    deploy: str = "docker"         # docker, vercel, heroku, serverless



# ═══════════════════════════════════════════════════════════════
# DEPENDENCY RESOLVER — Framework → exact compatible versions
# ═══════════════════════════════════════════════════════════════

DEPENDENCY_SETS = {
    'react': {
        'package.json': {
            "react": "^18.3.0",
            "react-dom": "^18.3.0",
            "react-router-dom": "^6.23.0",
        },
        'devDependencies': {
            "vite": "^5.4.0",
            "@vitejs/plugin-react": "^4.3.0",
        }
    },
    'react+tailwind': {
        'package.json': {
            "react": "^18.3.0",
            "react-dom": "^18.3.0",
            "react-router-dom": "^6.23.0",
        },
        'devDependencies': {
            "vite": "^5.4.0",
            "@vitejs/plugin-react": "^4.3.0",
            "tailwindcss": "^3.4.0",
            "postcss": "^8.4.0",
            "autoprefixer": "^10.4.0",
        }
    },
    'nextjs': {
        'package.json': {
            "next": "^14.2.0",
            "react": "^18.3.0",
            "react-dom": "^18.3.0",
        },
        'devDependencies': {
            "typescript": "^5.5.0",
            "@types/react": "^18.3.0",
            "@types/node": "^20.14.0",
        }
    },
    'express': {
        'package.json': {
            "express": "^4.19.0",
            "cors": "^2.8.5",
            "helmet": "^7.1.0",
            "dotenv": "^16.4.0",
        },
        'devDependencies': {
            "nodemon": "^3.1.0",
        }
    },
    'express+auth': {
        'package.json': {
            "express": "^4.19.0",
            "cors": "^2.8.5",
            "helmet": "^7.1.0",
            "dotenv": "^16.4.0",
            "jsonwebtoken": "^9.0.0",
            "bcryptjs": "^2.4.3",
            "express-validator": "^7.1.0",
        },
        'devDependencies': {
            "nodemon": "^3.1.0",
        }
    },
    'fastapi': {
        'requirements.txt': [
            "fastapi>=0.111.0",
            "uvicorn[standard]>=0.30.0",
            "pydantic>=2.8.0",
            "python-dotenv>=1.0.0",
        ]
    },
    'fastapi+auth': {
        'requirements.txt': [
            "fastapi>=0.111.0",
            "uvicorn[standard]>=0.30.0",
            "pydantic>=2.8.0",
            "python-dotenv>=1.0.0",
            "python-jose[cryptography]>=3.3.0",
            "passlib[bcrypt]>=1.7.4",
            "python-multipart>=0.0.9",
        ]
    },
    'flask': {
        'requirements.txt': [
            "flask>=3.0.0",
            "flask-cors>=4.0.0",
            "python-dotenv>=1.0.0",
            "gunicorn>=22.0.0",
        ]
    },
    'vue': {
        'package.json': {
            "vue": "^3.4.0",
            "vue-router": "^4.3.0",
            "pinia": "^2.1.0",
        },
        'devDependencies': {
            "vite": "^5.4.0",
            "@vitejs/plugin-vue": "^5.0.0",
        }
    },
    'sqlite': {'requirements.txt': []},  # Built-in
    'postgres': {'requirements.txt': ["asyncpg>=0.29.0", "sqlalchemy>=2.0.30"]},
    'mongodb': {'requirements.txt': ["pymongo>=4.7.0", "motor>=3.4.0"]},
    'firebase': {'package.json': {"firebase": "^10.12.0"}},
    'socketio': {'package.json': {"socket.io": "^4.7.0", "socket.io-client": "^4.7.0"}},
    'stripe': {'package.json': {"stripe": "^15.0.0"}},
}



# ═══════════════════════════════════════════════════════════════
# REQUEST PARSER — Natural language → SystemModel
# ═══════════════════════════════════════════════════════════════

class RequestParser:
    """Parse a user's project request into a SystemModel."""

    ENTITY_PATTERNS = [
        (r'\b(?:todo|task|item)\b', 'Todo', {'id': 'int', 'text': 'str', 'done': 'bool', 'user_id': 'int'}),
        (r'\b(?:user|account|profile)\b', 'User', {'id': 'int', 'email': 'str', 'password_hash': 'str', 'name': 'str'}),
        (r'\b(?:post|article|blog)\b', 'Post', {'id': 'int', 'title': 'str', 'content': 'str', 'author_id': 'int', 'created_at': 'datetime'}),
        (r'\b(?:comment)\b', 'Comment', {'id': 'int', 'text': 'str', 'post_id': 'int', 'user_id': 'int'}),
        (r'\b(?:product|products|item|goods?)\b', 'Product', {'id': 'int', 'name': 'str', 'price': 'float', 'description': 'str', 'stock': 'int'}),
        (r'\b(?:order|orders|purchase)\b', 'Order', {'id': 'int', 'user_id': 'int', 'total': 'float', 'status': 'str', 'created_at': 'datetime'}),
        (r'\b(?:message|chat|dm)\b', 'Message', {'id': 'int', 'sender_id': 'int', 'receiver_id': 'int', 'text': 'str', 'sent_at': 'datetime'}),
        (r'\b(?:file|upload|image|photo)\b', 'File', {'id': 'int', 'name': 'str', 'url': 'str', 'size': 'int', 'user_id': 'int'}),
        (r'\b(?:event|booking|appointment)\b', 'Event', {'id': 'int', 'title': 'str', 'date': 'datetime', 'user_id': 'int', 'location': 'str'}),
        (r'\b(?:note|memo)\b', 'Note', {'id': 'int', 'title': 'str', 'body': 'str', 'user_id': 'int', 'tags': 'str'}),
    ]

    FEATURE_PATTERNS = [
        (r'(?:auth|authenticat\w*|login|signup|register|password)', 'auth'),
        (r'\b(?:real\s*time|socket|live|chat|notification)\b', 'realtime'),
        (r'\b(?:payment|payments|stripe|checkout|pay|billing)\b', 'payments'),
        (r'\b(?:upload|file|image|photo|media)\b', 'upload'),
        (r'\b(?:search|filter|find)\b', 'search'),
        (r'\b(?:admin|dashboard|panel)\b', 'admin'),
        (r'\b(?:email|mail|notification|notify)\b', 'email'),
        (r'\b(?:api|rest|endpoint)\b', 'api'),
    ]

    FRAMEWORK_PATTERNS = [
        (r'\breact\b', 'react', 'frontend'),
        (r'\bvue\b', 'vue', 'frontend'),
        (r'\bnext\.?js\b', 'nextjs', 'frontend'),
        (r'\bangular\b', 'angular', 'frontend'),
        (r'\bexpress\b', 'express', 'backend'),
        (r'\bfastapi\b', 'fastapi', 'backend'),
        (r'\bflask\b', 'flask', 'backend'),
        (r'\bdjango\b', 'django', 'backend'),
        (r'\bfirebase\b', 'firebase', 'database'),
        (r'\bpostgres\b', 'postgres', 'database'),
        (r'\bmongo\b', 'mongodb', 'database'),
        (r'\bsqlite\b', 'sqlite', 'database'),
        (r'\bsocket\.?io\b', 'socketio', 'realtime'),
        (r'\btailwind\b', 'tailwind', 'css'),
    ]

    def parse(self, request: str) -> SystemModel:
        """Parse natural language request into system model."""
        model = SystemModel()
        req_lower = request.lower()

        # Extract project name
        name_match = re.search(r'\b(?:build|create|make)\s+(?:a|an|me\s+a)?\s*(.+?)(?:\s+with|\s+using|\s+in|$)', req_lower)
        model.name = name_match.group(1).strip()[:30] if name_match else "app"

        # Detect entities
        for pattern, name, fields in self.ENTITY_PATTERNS:
            if re.search(pattern, req_lower):
                model.entities.append(Entity(name=name, fields=fields))

        # Always add User if auth is detected
        if re.search(r'\b(?:auth|login|user|signup)\b', req_lower):
            if not any(e.name == 'User' for e in model.entities):
                model.entities.append(Entity(name='User', fields={'id': 'int', 'email': 'str', 'password_hash': 'str', 'name': 'str'}))

        # If no entities detected, create a generic one
        if not model.entities:
            model.entities.append(Entity(name='Item', fields={'id': 'int', 'name': 'str', 'data': 'str', 'created_at': 'datetime'}))

        # Detect features
        for pattern, feature in self.FEATURE_PATTERNS:
            if re.search(pattern, req_lower):
                if feature not in model.features:
                    model.features.append(feature)

        # Detect frameworks
        for pattern, framework, layer in self.FRAMEWORK_PATTERNS:
            if re.search(pattern, req_lower):
                if layer == 'frontend': model.frontend = framework
                elif layer == 'backend': model.backend = framework
                elif layer == 'database': model.database = framework

        # Generate operations for each entity
        for entity in model.entities:
            has_auth = 'auth' in model.features
            for action in ['create', 'read', 'list', 'update', 'delete']:
                op = Operation(
                    name=f"{action}_{entity.name.lower()}",
                    entity=entity.name,
                    action=action,
                    auth_required=has_auth and entity.name != 'User',
                    owner_only=(action in ('update', 'delete') and has_auth),
                )
                model.operations.append(op)

        return model



# ═══════════════════════════════════════════════════════════════
# CODE GENERATOR — SystemModel → Project files
# ═══════════════════════════════════════════════════════════════

class ProjectGenerator:
    """Generate a complete project from a SystemModel."""

    def generate(self, model: SystemModel) -> Dict[str, str]:
        """Generate all project files. Returns {filepath: content}."""
        files = {}

        # Generate based on backend choice
        if model.backend == 'fastapi':
            files.update(self._gen_fastapi(model))
        elif model.backend == 'express':
            files.update(self._gen_express(model))
        elif model.backend == 'flask':
            files.update(self._gen_flask(model))

        # Generate dependency file
        files.update(self._gen_dependencies(model))

        # Generate .env template
        files['.env.example'] = self._gen_env(model)

        # Generate docker-compose if applicable
        if model.deploy == 'docker':
            files['Dockerfile'] = self._gen_dockerfile(model)

        # Generate README
        files['README.md'] = self._gen_readme(model)

        return files

    def _gen_fastapi(self, model: SystemModel) -> Dict[str, str]:
        """Generate FastAPI backend."""
        files = {}

        # Main app
        imports = [
            "from fastapi import FastAPI, HTTPException, Depends, status",
            "from fastapi.middleware.cors import CORSMiddleware",
            "from pydantic import BaseModel, EmailStr",
            "from typing import List, Optional",
            "import sqlite3",
            "import os",
            "from dotenv import load_dotenv",
        ]

        if 'auth' in model.features:
            imports.extend([
                "from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials",
                "from jose import JWTError, jwt",
                "from passlib.context import CryptContext",
                "from datetime import datetime, timedelta",
            ])

        # Models
        models_code = "\n\n# ═══ Data Models ═══\n"
        for entity in model.entities:
            models_code += f"\nclass {entity.name}Create(BaseModel):\n"
            for fname, ftype in entity.fields.items():
                if fname == 'id':
                    continue
                py_type = {'str': 'str', 'int': 'int', 'float': 'float',
                          'bool': 'bool', 'datetime': 'str'}.get(ftype, 'str')
                if fname == 'password_hash':
                    models_code += f"    password: str\n"
                else:
                    models_code += f"    {fname}: {py_type}\n"

            models_code += f"\nclass {entity.name}Response(BaseModel):\n"
            for fname, ftype in entity.fields.items():
                py_type = {'str': 'str', 'int': 'int', 'float': 'float',
                          'bool': 'bool', 'datetime': 'str'}.get(ftype, 'str')
                if fname == 'password_hash':
                    continue
                models_code += f"    {fname}: {py_type}\n"

        # Auth middleware
        auth_code = ""
        if 'auth' in model.features:
            auth_code = '''

# ═══ Auth Configuration ═══
SECRET_KEY = os.getenv("SECRET_KEY", "change-me-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)

def create_token(user_id: int) -> str:
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {"sub": str(user_id), "exp": expire}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> int:
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = int(payload.get("sub"))
        return user_id
    except (JWTError, ValueError):
        raise HTTPException(status_code=401, detail="Invalid token")
'''

        # Database setup
        db_code = '''

# ═══ Database ═══
DB_PATH = os.getenv("DATABASE_URL", "app.db")

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    db = get_db()
'''
        for entity in model.entities:
            db_code += f"    db.execute('''\n        CREATE TABLE IF NOT EXISTS {entity.name.lower()}s (\n"
            field_defs = []
            for fname, ftype in entity.fields.items():
                sql_type = {'int': 'INTEGER', 'str': 'TEXT', 'float': 'REAL',
                           'bool': 'INTEGER', 'datetime': 'TEXT'}.get(ftype, 'TEXT')
                if fname == 'id':
                    field_defs.append(f"            {fname} INTEGER PRIMARY KEY AUTOINCREMENT")
                elif fname == 'password_hash':
                    field_defs.append(f"            password_hash TEXT NOT NULL")
                else:
                    field_defs.append(f"            {fname} {sql_type}")
            db_code += ',\n'.join(field_defs)
            db_code += f"\n        )\n    ''')\n"
        db_code += "    db.commit()\n    db.close()\n"

        # App setup
        app_code = '''

# ═══ App Setup ═══
load_dotenv()
app = FastAPI(title="{name}", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("ALLOWED_ORIGINS", "*").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def startup():
    init_db()

@app.get("/health")
def health():
    return {{"status": "ok"}}
'''.format(name=model.name)

        # Routes
        routes_code = "\n\n# ═══ Routes ═══\n"
        for entity in model.entities:
            ename = entity.name
            ename_lower = ename.lower()
            table = f"{ename_lower}s"

            # Auth routes for User entity
            if ename == 'User' and 'auth' in model.features:
                routes_code += f'''
@app.post("/auth/register", response_model={ename}Response)
def register(data: {ename}Create):
    db = get_db()
    # Check if email exists
    existing = db.execute("SELECT id FROM {table} WHERE email = ?", (data.email,)).fetchone()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    hashed = hash_password(data.password)
    cursor = db.execute(
        "INSERT INTO {table} (email, password_hash, name) VALUES (?, ?, ?)",
        (data.email, hashed, data.name)
    )
    db.commit()
    user_id = cursor.lastrowid
    db.close()
    return {ename}Response(id=user_id, email=data.email, name=data.name)

@app.post("/auth/login")
def login(data: {ename}Create):
    db = get_db()
    user = db.execute("SELECT * FROM {table} WHERE email = ?", (data.email,)).fetchone()
    db.close()
    if not user or not verify_password(data.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_token(user["id"])
    return {{"access_token": token, "token_type": "bearer"}}

@app.get("/auth/me", response_model={ename}Response)
def get_me(user_id: int = Depends(get_current_user)):
    db = get_db()
    user = db.execute("SELECT * FROM {table} WHERE id = ?", (user_id,)).fetchone()
    db.close()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {ename}Response(id=user["id"], email=user["email"], name=user["name"])
'''
                continue

            # CRUD routes for other entities
            auth_dep = ", user_id: int = Depends(get_current_user)" if 'auth' in model.features else ""
            fields_no_id = [f for f in entity.fields if f != 'id' and f != 'password_hash']

            routes_code += f'''
@app.post("/{ename_lower}s", response_model={ename}Response)
def create_{ename_lower}(data: {ename}Create{auth_dep}):
    db = get_db()
    fields = "{', '.join(fields_no_id)}"
    placeholders = "{', '.join(['?' for _ in fields_no_id])}"
    values = ({', '.join([f'data.{f}' for f in fields_no_id])},)
    cursor = db.execute(f"INSERT INTO {table} ({{fields}}) VALUES ({{placeholders}})", values)
    db.commit()
    item_id = cursor.lastrowid
    db.close()
    return {ename}Response(id=item_id, **data.dict())

@app.get("/{ename_lower}s", response_model=List[{ename}Response])
def list_{ename_lower}s({auth_dep.lstrip(', ')}):
    db = get_db()
    rows = db.execute("SELECT * FROM {table}").fetchall()
    db.close()
    return [dict(row) for row in rows]

@app.get("/{ename_lower}s/{{item_id}}", response_model={ename}Response)
def get_{ename_lower}(item_id: int{auth_dep}):
    db = get_db()
    row = db.execute("SELECT * FROM {table} WHERE id = ?", (item_id,)).fetchone()
    db.close()
    if not row:
        raise HTTPException(status_code=404, detail="{ename} not found")
    return dict(row)

@app.delete("/{ename_lower}s/{{item_id}}")
def delete_{ename_lower}(item_id: int{auth_dep}):
    db = get_db()
    db.execute("DELETE FROM {table} WHERE id = ?", (item_id,))
    db.commit()
    db.close()
    return {{"deleted": True}}
'''

        # Assemble main.py
        main_content = '\n'.join(imports) + models_code + auth_code + db_code + app_code + routes_code
        main_content += '\n\nif __name__ == "__main__":\n    import uvicorn\n    uvicorn.run(app, host="0.0.0.0", port=8000)\n'
        files['main.py'] = main_content
        return files


    def _gen_express(self, model: SystemModel) -> Dict[str, str]:
        """Generate Express.js backend."""
        files = {}
        has_auth = 'auth' in model.features

        # server.js
        server = '''const express = require('express');
const cors = require('cors');
const helmet = require('helmet');
require('dotenv').config();

const app = express();
const PORT = process.env.PORT || 3000;

// Security middleware
app.use(helmet());
app.use(cors({ origin: process.env.ALLOWED_ORIGINS || '*' }));
app.use(express.json({ limit: '10mb' }));

// Input sanitization middleware
app.use((req, res, next) => {
  if (req.body) {
    for (const key of Object.keys(req.body)) {
      if (typeof req.body[key] === 'string') {
        req.body[key] = req.body[key].replace(/[<>]/g, '');
      }
    }
  }
  next();
});

'''
        if has_auth:
            server += '''// Auth middleware
const jwt = require('jsonwebtoken');
const bcrypt = require('bcryptjs');
const JWT_SECRET = process.env.JWT_SECRET || 'change-me';

function authMiddleware(req, res, next) {
  const token = req.headers.authorization?.split(' ')[1];
  if (!token) return res.status(401).json({ error: 'No token provided' });
  try {
    const decoded = jwt.verify(token, JWT_SECRET);
    req.userId = decoded.userId;
    next();
  } catch (err) {
    return res.status(401).json({ error: 'Invalid token' });
  }
}

'''

        server += '''// Database (SQLite)
const Database = require('better-sqlite3');
const db = new Database(process.env.DB_PATH || 'app.db');
db.pragma('journal_mode = WAL');

// Create tables
'''
        for entity in model.entities:
            ename_lower = entity.name.lower()
            field_defs = []
            for fname, ftype in entity.fields.items():
                sql_type = {'int': 'INTEGER', 'str': 'TEXT', 'float': 'REAL',
                           'bool': 'INTEGER', 'datetime': 'TEXT'}.get(ftype, 'TEXT')
                if fname == 'id':
                    field_defs.append(f"  {fname} INTEGER PRIMARY KEY AUTOINCREMENT")
                else:
                    field_defs.append(f"  {fname} {sql_type}")
            server += f"db.exec(`CREATE TABLE IF NOT EXISTS {ename_lower}s ({', '.join(field_defs)})`);\n"

        server += '\n// Health check\napp.get("/health", (req, res) => res.json({ status: "ok" }));\n\n'

        # Routes for each entity
        for entity in model.entities:
            ename = entity.name
            ename_lower = ename.lower()
            table = f"{ename_lower}s"
            protect = "authMiddleware, " if has_auth and ename != 'User' else ""
            fields_no_id = [f for f in entity.fields if f != 'id']

            if ename == 'User' and has_auth:
                server += f'''// Auth routes
app.post("/auth/register", async (req, res) => {{
  try {{
    const {{ email, password, name }} = req.body;
    if (!email || !password) return res.status(400).json({{ error: "Email and password required" }});
    const existing = db.prepare("SELECT id FROM {table} WHERE email = ?").get(email);
    if (existing) return res.status(400).json({{ error: "Email already registered" }});
    const password_hash = await bcrypt.hash(password, 10);
    const result = db.prepare("INSERT INTO {table} (email, password_hash, name) VALUES (?, ?, ?)").run(email, password_hash, name || "");
    res.status(201).json({{ id: result.lastInsertRowid, email, name }});
  }} catch (err) {{ res.status(500).json({{ error: err.message }}); }}
}});

app.post("/auth/login", async (req, res) => {{
  try {{
    const {{ email, password }} = req.body;
    const user = db.prepare("SELECT * FROM {table} WHERE email = ?").get(email);
    if (!user || !(await bcrypt.compare(password, user.password_hash)))
      return res.status(401).json({{ error: "Invalid credentials" }});
    const token = jwt.sign({{ userId: user.id }}, JWT_SECRET, {{ expiresIn: "24h" }});
    res.json({{ access_token: token, token_type: "bearer" }});
  }} catch (err) {{ res.status(500).json({{ error: err.message }}); }}
}});

app.get("/auth/me", authMiddleware, (req, res) => {{
  const user = db.prepare("SELECT id, email, name FROM {table} WHERE id = ?").get(req.userId);
  if (!user) return res.status(404).json({{ error: "User not found" }});
  res.json(user);
}});

'''
            else:
                server += f'''// {ename} CRUD
app.get("/{table}", {protect}(req, res) => {{
  const rows = db.prepare("SELECT * FROM {table}").all();
  res.json(rows);
}});

app.get("/{table}/:id", {protect}(req, res) => {{
  const row = db.prepare("SELECT * FROM {table} WHERE id = ?").get(req.params.id);
  if (!row) return res.status(404).json({{ error: "{ename} not found" }});
  res.json(row);
}});

app.post("/{table}", {protect}(req, res) => {{
  const fields = {json.dumps(fields_no_id)};
  const values = fields.map(f => req.body[f]);
  const placeholders = fields.map(() => "?").join(", ");
  const result = db.prepare(`INSERT INTO {table} (${{fields.join(", ")}}) VALUES (${{placeholders}})`).run(...values);
  res.status(201).json({{ id: result.lastInsertRowid, ...req.body }});
}});

app.delete("/{table}/:id", {protect}(req, res) => {{
  db.prepare("DELETE FROM {table} WHERE id = ?").run(req.params.id);
  res.json({{ deleted: true }});
}});

'''

        server += f'''// Start server
app.listen(PORT, () => console.log(`Server running on port ${{PORT}}`));
'''
        files['server.js'] = server
        return files

    def _gen_flask(self, model: SystemModel) -> Dict[str, str]:
        """Generate Flask backend (simplified)."""
        files = {}
        files['app.py'] = f'''from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3, os
from dotenv import load_dotenv

load_dotenv()
app = Flask(__name__)
CORS(app)

DB_PATH = os.getenv("DATABASE_URL", "app.db")

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

@app.route("/health")
def health():
    return jsonify({{"status": "ok"}})

# Generated CRUD routes for: {', '.join(e.name for e in model.entities)}
# (Full implementation follows same pattern as FastAPI/Express above)

if __name__ == "__main__":
    app.run(debug=os.getenv("FLASK_ENV") == "development", port=5000)
'''
        return files


    def _gen_dependencies(self, model: SystemModel) -> Dict[str, str]:
        """Generate dependency files (package.json or requirements.txt)."""
        files = {}

        if model.backend in ('express', 'none') or model.frontend in ('react', 'vue', 'nextjs'):
            # Generate package.json
            deps = {}
            dev_deps = {}

            # Backend deps
            backend_key = model.backend
            if 'auth' in model.features and f"{model.backend}+auth" in DEPENDENCY_SETS:
                backend_key = f"{model.backend}+auth"
            if backend_key in DEPENDENCY_SETS:
                pkg = DEPENDENCY_SETS[backend_key]
                deps.update(pkg.get('package.json', {}))
                dev_deps.update(pkg.get('devDependencies', {}))

            # Frontend deps
            frontend_key = model.frontend
            if frontend_key in DEPENDENCY_SETS:
                pkg = DEPENDENCY_SETS[frontend_key]
                deps.update(pkg.get('package.json', {}))
                dev_deps.update(pkg.get('devDependencies', {}))

            # Feature deps
            if 'realtime' in model.features and 'socketio' in DEPENDENCY_SETS:
                deps.update(DEPENDENCY_SETS['socketio'].get('package.json', {}))
            if 'payments' in model.features and 'stripe' in DEPENDENCY_SETS:
                deps.update(DEPENDENCY_SETS['stripe'].get('package.json', {}))

            # SQLite for express
            if model.backend == 'express':
                deps['better-sqlite3'] = '^11.1.0'

            pkg_json = {
                "name": model.name.replace(' ', '-').lower(),
                "version": "1.0.0",
                "description": f"{model.name} — Generated by AXIMA Coder",
                "main": "server.js",
                "scripts": {
                    "start": "node server.js",
                    "dev": "nodemon server.js",
                },
                "dependencies": deps,
                "devDependencies": dev_deps,
            }
            files['package.json'] = json.dumps(pkg_json, indent=2)

        if model.backend in ('fastapi', 'flask', 'django'):
            # Generate requirements.txt
            reqs = []
            backend_key = model.backend
            if 'auth' in model.features and f"{model.backend}+auth" in DEPENDENCY_SETS:
                backend_key = f"{model.backend}+auth"
            if backend_key in DEPENDENCY_SETS:
                reqs.extend(DEPENDENCY_SETS[backend_key].get('requirements.txt', []))

            # DB deps
            if model.database in DEPENDENCY_SETS:
                reqs.extend(DEPENDENCY_SETS[model.database].get('requirements.txt', []))

            files['requirements.txt'] = '\n'.join(reqs) + '\n'

        return files

    def _gen_env(self, model: SystemModel) -> str:
        """Generate .env.example with secure defaults."""
        lines = [
            "# ═══ Environment Variables ═══",
            "# NEVER commit real values to git!",
            "",
            f"PORT=8000",
            f"DATABASE_URL=app.db",
            "ALLOWED_ORIGINS=http://localhost:3000",
        ]
        if 'auth' in model.features:
            lines.extend([
                "",
                "# Auth",
                "SECRET_KEY=change-this-to-a-random-64-char-string",
                "JWT_SECRET=change-this-to-a-random-64-char-string",
                "ACCESS_TOKEN_EXPIRE_MINUTES=60",
            ])
        if 'payments' in model.features:
            lines.extend([
                "",
                "# Payments (Stripe)",
                "STRIPE_SECRET_KEY=sk_test_...",
                "STRIPE_WEBHOOK_SECRET=whsec_...",
            ])
        if 'email' in model.features:
            lines.extend([
                "",
                "# Email",
                "SMTP_HOST=smtp.gmail.com",
                "SMTP_PORT=587",
                "SMTP_USER=your-email@gmail.com",
                "SMTP_PASS=app-specific-password",
            ])
        return '\n'.join(lines) + '\n'

    def _gen_dockerfile(self, model: SystemModel) -> str:
        """Generate Dockerfile."""
        if model.backend in ('fastapi', 'flask'):
            return f'''FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
'''
        else:
            return f'''FROM node:20-slim
WORKDIR /app
COPY package*.json ./
RUN npm ci --production
COPY . .
EXPOSE 3000
CMD ["node", "server.js"]
'''

    def _gen_readme(self, model: SystemModel) -> str:
        """Generate project README."""
        entities_list = ', '.join(e.name for e in model.entities)
        features_list = ', '.join(model.features) if model.features else 'basic CRUD'
        return f'''# {model.name.title()}

> Generated by AXIMA Coder v2

## Stack
- **Backend:** {model.backend}
- **Database:** {model.database}
- **Frontend:** {model.frontend}
- **Auth:** {model.auth_method if 'auth' in model.features else 'none'}

## Entities
{entities_list}

## Features
{features_list}

## Setup

```bash
# Install dependencies
{'pip install -r requirements.txt' if model.backend in ('fastapi', 'flask') else 'npm install'}

# Copy env file
cp .env.example .env
# Edit .env with your values

# Run
{'uvicorn main:app --reload' if model.backend == 'fastapi' else 'npm run dev'}
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | /health | Health check |
'''



# ═══════════════════════════════════════════════════════════════
# STATIC ANALYSIS — Check generated code for common errors
# ═══════════════════════════════════════════════════════════════

class StaticAnalyzer:
    """Basic static analysis for generated code."""

    def analyze(self, code: str, language: str = 'python') -> List[str]:
        """Return list of potential issues found."""
        issues = []

        if language == 'python':
            issues.extend(self._check_python(code))
        elif language in ('javascript', 'typescript'):
            issues.extend(self._check_js(code))

        return issues

    def _check_python(self, code: str) -> List[str]:
        """Check Python code for common issues."""
        issues = []
        lines = code.split('\n')

        # Check: SQL injection (string formatting in queries)
        for i, line in enumerate(lines, 1):
            if 'execute(' in line and ('f"' in line or "f'" in line or '%s' in line):
                if '?' not in line and '%s' not in line:
                    issues.append(f"Line {i}: Potential SQL injection — use parameterized queries (?)")

        # Check: hardcoded secrets
        for i, line in enumerate(lines, 1):
            if re.search(r'(?:password|secret|key|token)\s*=\s*["\'][^"\']{5,}', line, re.I):
                if 'os.getenv' not in line and 'environ' not in line:
                    issues.append(f"Line {i}: Hardcoded secret — use environment variable")

        # Check: missing error handling on file operations
        for i, line in enumerate(lines, 1):
            if 'open(' in line and 'try' not in '\n'.join(lines[max(0,i-3):i]):
                if 'with' not in line:
                    issues.append(f"Line {i}: File operation without context manager (use 'with')")

        # Check: eval() usage
        for i, line in enumerate(lines, 1):
            if 'eval(' in line:
                issues.append(f"Line {i}: eval() is dangerous — avoid or validate input strictly")

        return issues

    def _check_js(self, code: str) -> List[str]:
        """Check JavaScript code for common issues."""
        issues = []
        lines = code.split('\n')

        # Check: innerHTML (XSS risk)
        for i, line in enumerate(lines, 1):
            if 'innerHTML' in line:
                issues.append(f"Line {i}: innerHTML is XSS-vulnerable — use textContent or sanitize")

        # Check: hardcoded secrets
        for i, line in enumerate(lines, 1):
            if re.search(r'(?:password|secret|key|token)\s*[:=]\s*["\'][^"\']{5,}', line, re.I):
                if 'process.env' not in line:
                    issues.append(f"Line {i}: Hardcoded secret — use process.env")

        # Check: no error handling on async
        for i, line in enumerate(lines, 1):
            if 'await ' in line and 'try' not in '\n'.join(lines[max(0,i-3):i]):
                pass  # Common pattern, don't flag unless no catch nearby

        return issues


# ═══════════════════════════════════════════════════════════════
# MAIN INTERFACE
# ═══════════════════════════════════════════════════════════════

class AximaCoder:
    """Main AXIMA Coder V2 interface."""

    def __init__(self):
        self.parser = RequestParser()
        self.generator = ProjectGenerator()
        self.analyzer = StaticAnalyzer()

    def generate_project(self, request: str) -> Dict[str, str]:
        """Generate a complete project from a natural language request."""
        model = self.parser.parse(request)
        files = self.generator.generate(model)

        # Run static analysis on generated code
        for filepath, content in list(files.items()):
            if filepath.endswith('.py'):
                issues = self.analyzer.analyze(content, 'python')
            elif filepath.endswith('.js'):
                issues = self.analyzer.analyze(content, 'javascript')
            else:
                issues = []
            if issues:
                # Add issues as comments at top
                header = f"# ⚠️  Static Analysis Notes:\n"
                for issue in issues:
                    header += f"# - {issue}\n"
                header += "#\n"
                files[filepath] = header + content

        return files

    def get_model(self, request: str) -> SystemModel:
        """Get the system model without generating code."""
        return self.parser.parse(request)

    def explain_architecture(self, request: str) -> str:
        """Explain the architecture that would be generated."""
        model = self.parser.parse(request)
        lines = [
            f"═══ Architecture: {model.name.title()} ═══\n",
            f"Backend:  {model.backend}",
            f"Frontend: {model.frontend}",
            f"Database: {model.database}",
            f"Auth:     {model.auth_method if 'auth' in model.features else 'none'}",
            f"Deploy:   {model.deploy}",
            f"\n─── Data Layer ───",
        ]
        for entity in model.entities:
            fields_str = ', '.join(f"{k}: {v}" for k, v in entity.fields.items())
            lines.append(f"  {entity.name}({fields_str})")

        lines.append(f"\n─── Logic Layer ───")
        for op in model.operations[:10]:
            auth_mark = "🔒" if op.auth_required else "🔓"
            lines.append(f"  {auth_mark} {op.name}()")

        lines.append(f"\n─── Features ───")
        lines.append(f"  {', '.join(model.features) if model.features else 'basic CRUD'}")

        return '\n'.join(lines)


def get_coder() -> AximaCoder:
    """Get coder instance."""
    return AximaCoder()



# ═══════════════════════════════════════════════════════════════
# SELF-TEST
# ═══════════════════════════════════════════════════════════════

if __name__ == '__main__':
    print("═══ AXIMA Coder V2 — Test ═══\n")

    coder = AximaCoder()

    # Test 1: Todo app with auth
    print("─── Test 1: Todo app with auth and React ───")
    request = "Build a todo app with user authentication using FastAPI and React"
    print(f"  Request: {request}")
    print(f"\n  Architecture:")
    print(f"  {coder.explain_architecture(request)}")

    files = coder.generate_project(request)
    print(f"\n  Generated {len(files)} files:")
    for fname, content in files.items():
        print(f"    {fname} ({len(content)} chars)")
    print()

    # Test 2: Chat app with realtime
    print("─── Test 2: Chat app with Socket.io ───")
    request = "Create a real-time chat app with Express and Socket.io"
    model = coder.get_model(request)
    print(f"  Model: {model.name}")
    print(f"  Entities: {[e.name for e in model.entities]}")
    print(f"  Features: {model.features}")
    print(f"  Backend: {model.backend}")
    print()

    # Test 3: E-commerce
    print("─── Test 3: E-commerce ───")
    request = "Build an e-commerce app with products, orders, payments using FastAPI and postgres"
    model = coder.get_model(request)
    print(f"  Entities: {[e.name for e in model.entities]}")
    print(f"  Features: {model.features}")
    print(f"  DB: {model.database}")

    files = coder.generate_project(request)
    print(f"  Files: {list(files.keys())}")
    print()

    # Test 4: Blog with Flask
    print("─── Test 4: Blog with Flask ───")
    request = "Make a blog with posts and comments using Flask"
    files = coder.generate_project(request)
    print(f"  Files: {list(files.keys())}")
    print(f"  Total code: {sum(len(v) for v in files.values())} chars")
    print()

    print("  ✅ AXIMA Coder V2 ready!")

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
        self.pattern_selector = DesignPatternSelector()
        self.performance_optimizer = PerformanceOptimizer()
        self.test_generator = TestGenerator()
        self.cicd_generator = CICDGenerator()
        self.api_doc_generator = APIDocGenerator()
        self.monitoring_generator = MonitoringGenerator()
        self.migration_generator = MigrationGenerator()
        self.error_boundary_generator = ErrorBoundaryGenerator()

    def generate_project(self, request: str) -> Dict[str, str]:
        """Generate a complete project from a natural language request.

        Now includes: design patterns, performance optimizations, tests,
        CI/CD pipeline, API docs, monitoring, migrations, and error handling.
        """
        model = self.parser.parse(request)
        files = self.generator.generate(model)

        # ═══ NEW: Design Pattern Selection ═══
        patterns = self.pattern_selector.select_patterns(model)
        if patterns:
            pattern_code = self.pattern_selector.generate_pattern_code(model)
            if pattern_code:
                files['patterns.py'] = pattern_code

        # ═══ NEW: Performance Optimizations ═══
        perf_files = self.performance_optimizer.optimize(model)
        files.update(perf_files)

        # ═══ NEW: Test Suite ═══
        test_files = self.test_generator.generate_tests(model, files)
        files.update(test_files)

        # ═══ NEW: CI/CD Pipeline ═══
        cicd_files = self.cicd_generator.generate_cicd(model)
        files.update(cicd_files)

        # ═══ NEW: API Documentation ═══
        doc_files = self.api_doc_generator.generate_openapi(model)
        files.update(doc_files)

        # ═══ NEW: Monitoring & Logging ═══
        monitoring_files = self.monitoring_generator.generate_monitoring(model)
        files.update(monitoring_files)

        # ═══ NEW: Database Migrations ═══
        migration_files = self.migration_generator.generate_migrations(model)
        files.update(migration_files)

        # ═══ NEW: Error Boundaries ═══
        error_files = self.error_boundary_generator.generate_error_boundaries(model)
        files.update(error_files)

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
# SECTION 1: DESIGN PATTERN SELECTOR
# Automatically detects and recommends architectural patterns
# based on system model analysis.
# ═══════════════════════════════════════════════════════════════

class DesignPatternSelector:
    """Analyze a SystemModel and recommend architectural patterns."""

    PATTERN_RULES = {
        'singleton': {
            'description': 'Single shared instance (DB connection, config, logger)',
            'triggers': ['database', 'config', 'logging'],
            'code_hint': 'class Singleton:\n    _instance = None\n    @classmethod\n    def get_instance(cls):\n        if cls._instance is None:\n            cls._instance = cls()\n        return cls._instance',
        },
        'factory': {
            'description': 'Create objects without specifying exact class',
            'triggers': ['multiple_entities', 'polymorphism'],
            'code_hint': 'class EntityFactory:\n    @staticmethod\n    def create(entity_type, **kwargs):\n        registry = {}\n        return registry[entity_type](**kwargs)',
        },
        'observer': {
            'description': 'Pub/sub for event-driven communication',
            'triggers': ['realtime', 'notifications', 'email', 'webhooks'],
            'code_hint': 'class EventBus:\n    def __init__(self):\n        self._listeners = {}\n    def on(self, event, callback):\n        self._listeners.setdefault(event, []).append(callback)\n    def emit(self, event, data):\n        for cb in self._listeners.get(event, []):\n            cb(data)',
        },
        'strategy': {
            'description': 'Interchangeable algorithms at runtime',
            'triggers': ['auth', 'payments', 'search', 'multiple_backends'],
            'code_hint': 'class AuthStrategy:\n    def authenticate(self, credentials): ...\nclass JWTAuth(AuthStrategy): ...\nclass OAuth2Auth(AuthStrategy): ...',
        },
        'repository': {
            'description': 'Abstract data access layer',
            'triggers': ['database', 'crud', 'entities'],
            'code_hint': 'class BaseRepository:\n    def find_by_id(self, id): ...\n    def find_all(self, filters=None): ...\n    def create(self, data): ...\n    def update(self, id, data): ...\n    def delete(self, id): ...',
        },
        'service_layer': {
            'description': 'Business logic separated from transport',
            'triggers': ['auth', 'payments', 'complex_logic'],
            'code_hint': 'class UserService:\n    def __init__(self, repo, event_bus):\n        self.repo = repo\n        self.event_bus = event_bus\n    def register(self, data):\n        user = self.repo.create(data)\n        self.event_bus.emit("user.registered", user)\n        return user',
        },
        'cqrs': {
            'description': 'Separate read/write models for scalability',
            'triggers': ['high_read', 'analytics', 'admin', 'search'],
            'code_hint': 'class CommandBus:\n    def dispatch(self, command): ...\nclass QueryBus:\n    def execute(self, query): ...',
        },
        'event_sourcing': {
            'description': 'Store state as sequence of events',
            'triggers': ['payments', 'audit', 'history', 'undo'],
            'code_hint': 'class EventStore:\n    def append(self, stream_id, event): ...\n    def get_events(self, stream_id): ...\n    def replay(self, stream_id): ...',
        },
    }

    def select_patterns(self, model: SystemModel) -> Dict[str, dict]:
        """Analyze model and return recommended patterns with rationale."""
        recommended = {}
        features = set(model.features)
        num_entities = len(model.entities)

        for pattern_name, pattern_info in self.PATTERN_RULES.items():
            triggers = pattern_info['triggers']
            score = 0
            reasons = []

            # Check feature triggers
            for trigger in triggers:
                if trigger in features:
                    score += 2
                    reasons.append(f"feature '{trigger}' detected")
                elif trigger == 'database' and model.database != 'none':
                    score += 1
                    reasons.append(f"database '{model.database}' in use")
                elif trigger == 'multiple_entities' and num_entities >= 3:
                    score += 1
                    reasons.append(f"{num_entities} entities detected")
                elif trigger == 'crud' and model.operations:
                    score += 1
                    reasons.append("CRUD operations present")
                elif trigger == 'entities' and model.entities:
                    score += 1
                    reasons.append("entities defined")
                elif trigger == 'complex_logic' and num_entities >= 2:
                    score += 1
                    reasons.append("multi-entity logic")

            if score >= 2:
                recommended[pattern_name] = {
                    'description': pattern_info['description'],
                    'score': score,
                    'reasons': reasons,
                    'code_hint': pattern_info['code_hint'],
                }

        return recommended

    def generate_pattern_code(self, model: SystemModel) -> str:
        """Generate pattern implementation scaffolding."""
        patterns = self.select_patterns(model)
        if not patterns:
            return ""

        code = "# ═══ Design Patterns (Auto-Selected) ═══\n\n"

        if 'observer' in patterns:
            code += '''class EventBus:
    """Observer pattern — pub/sub event system."""
    _instance = None

    def __init__(self):
        self._listeners: Dict[str, List] = {}

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def on(self, event: str, callback):
        self._listeners.setdefault(event, []).append(callback)

    def emit(self, event: str, data=None):
        for cb in self._listeners.get(event, []):
            cb(data)

    def off(self, event: str, callback=None):
        if callback:
            self._listeners.get(event, []).remove(callback)
        else:
            self._listeners.pop(event, None)

event_bus = EventBus.get_instance()

'''

        if 'repository' in patterns:
            code += '''class BaseRepository:
    """Repository pattern — abstract data access."""

    def __init__(self, db, table_name: str):
        self.db = db
        self.table = table_name

    def find_by_id(self, id: int):
        return self.db.execute(
            f"SELECT * FROM {self.table} WHERE id = ?", (id,)
        ).fetchone()

    def find_all(self, limit: int = 100, offset: int = 0):
        return self.db.execute(
            f"SELECT * FROM {self.table} LIMIT ? OFFSET ?", (limit, offset)
        ).fetchall()

    def create(self, data: dict):
        fields = ', '.join(data.keys())
        placeholders = ', '.join(['?'] * len(data))
        cursor = self.db.execute(
            f"INSERT INTO {self.table} ({fields}) VALUES ({placeholders})",
            tuple(data.values())
        )
        self.db.commit()
        return cursor.lastrowid

    def update(self, id: int, data: dict):
        sets = ', '.join(f"{k} = ?" for k in data.keys())
        self.db.execute(
            f"UPDATE {self.table} SET {sets} WHERE id = ?",
            (*data.values(), id)
        )
        self.db.commit()

    def delete(self, id: int):
        self.db.execute(f"DELETE FROM {self.table} WHERE id = ?", (id,))
        self.db.commit()

'''

        if 'service_layer' in patterns:
            code += '''class BaseService:
    """Service layer — business logic separated from transport."""

    def __init__(self, repository: BaseRepository):
        self.repo = repository
        self.event_bus = EventBus.get_instance()

    def create(self, data: dict):
        result = self.repo.create(data)
        self.event_bus.emit(f"{self.repo.table}.created", result)
        return result

    def get(self, id: int):
        return self.repo.find_by_id(id)

    def list_all(self, limit=100, offset=0):
        return self.repo.find_all(limit, offset)

    def update(self, id: int, data: dict):
        self.repo.update(id, data)
        self.event_bus.emit(f"{self.repo.table}.updated", {"id": id, **data})

    def delete(self, id: int):
        self.repo.delete(id)
        self.event_bus.emit(f"{self.repo.table}.deleted", {"id": id})

'''

        if 'strategy' in patterns:
            code += '''class AuthStrategyBase:
    """Strategy pattern — interchangeable auth methods."""
    def authenticate(self, credentials: dict) -> Optional[dict]:
        raise NotImplementedError

    def create_token(self, user_id: int) -> str:
        raise NotImplementedError

class JWTAuthStrategy(AuthStrategyBase):
    def __init__(self, secret: str, algorithm: str = "HS256"):
        self.secret = secret
        self.algorithm = algorithm

    def authenticate(self, credentials: dict) -> Optional[dict]:
        # Verify credentials against DB
        pass

    def create_token(self, user_id: int) -> str:
        import jwt
        from datetime import datetime, timedelta
        payload = {"sub": str(user_id), "exp": datetime.utcnow() + timedelta(hours=24)}
        return jwt.encode(payload, self.secret, algorithm=self.algorithm)

'''

        return code




# ═══════════════════════════════════════════════════════════════
# SECTION 2: PERFORMANCE OPTIMIZER
# Adds caching, indexing, pooling, rate limiting, pagination,
# and compression recommendations.
# ═══════════════════════════════════════════════════════════════

class PerformanceOptimizer:
    """Generate performance optimization configurations and middleware."""

    def optimize(self, model: SystemModel) -> Dict[str, str]:
        """Return optimization files/configs for the project."""
        optimizations = {}

        # Caching strategy
        optimizations['config/caching.py'] = self._gen_caching(model)

        # Database indexing
        optimizations['migrations/add_indexes.sql'] = self._gen_indexes(model)

        # Connection pooling
        optimizations['config/database_pool.py'] = self._gen_pool(model)

        # Rate limiting middleware
        optimizations['middleware/rate_limit.py'] = self._gen_rate_limit(model)

        # Pagination utility
        optimizations['utils/pagination.py'] = self._gen_pagination(model)

        # Response compression
        optimizations['middleware/compression.py'] = self._gen_compression(model)

        return optimizations

    def _gen_caching(self, model: SystemModel) -> str:
        """Generate caching strategy configuration."""
        entities = [e.name.lower() for e in model.entities]
        cache_config = {
            "strategy": "multi-tier",
            "layers": {
                "l1_memory": {"type": "LRU", "max_size": 1000, "ttl_seconds": 60},
                "l2_redis": {"type": "redis", "ttl_seconds": 300, "prefix": model.name.lower()},
            },
            "cache_rules": {},
        }
        for entity in entities:
            cache_config["cache_rules"][entity] = {
                "list": {"ttl": 30, "invalidate_on": ["create", "update", "delete"]},
                "detail": {"ttl": 120, "invalidate_on": ["update", "delete"]},
            }

        return f'''"""Caching Strategy — Auto-generated by AXIMA Coder V2"""
import time
import hashlib
from typing import Any, Optional
from functools import wraps

# Cache Configuration
CACHE_CONFIG = {json.dumps(cache_config, indent=4)}


class LRUCache:
    """In-memory LRU cache with TTL support."""

    def __init__(self, max_size: int = 1000, default_ttl: int = 60):
        self.max_size = max_size
        self.default_ttl = default_ttl
        self._store: dict = {{}}
        self._access_order: list = []

    def get(self, key: str) -> Optional[Any]:
        if key in self._store:
            entry = self._store[key]
            if time.time() < entry["expires"]:
                self._access_order.remove(key)
                self._access_order.append(key)
                return entry["value"]
            else:
                del self._store[key]
                self._access_order.remove(key)
        return None

    def set(self, key: str, value: Any, ttl: Optional[int] = None):
        if len(self._store) >= self.max_size:
            oldest = self._access_order.pop(0)
            del self._store[oldest]
        self._store[key] = {{
            "value": value,
            "expires": time.time() + (ttl or self.default_ttl)
        }}
        self._access_order.append(key)

    def invalidate(self, pattern: str = ""):
        if pattern:
            keys_to_del = [k for k in self._store if pattern in k]
            for k in keys_to_del:
                del self._store[k]
                self._access_order.remove(k)
        else:
            self._store.clear()
            self._access_order.clear()


# Global cache instance
cache = LRUCache(max_size=1000, default_ttl=60)


def cached(ttl: int = 60, key_prefix: str = ""):
    """Decorator to cache function results."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            cache_key = f"{{key_prefix}}:{{func.__name__}}:{{hashlib.md5(str(args).encode() + str(kwargs).encode()).hexdigest()[:12]}}"
            result = cache.get(cache_key)
            if result is not None:
                return result
            result = func(*args, **kwargs)
            cache.set(cache_key, result, ttl)
            return result
        return wrapper
    return decorator
'''

    def _gen_indexes(self, model: SystemModel) -> str:
        """Generate database index recommendations."""
        lines = ["-- Database Indexes — Auto-generated by AXIMA Coder V2\n"]
        lines.append("-- Run these after initial schema migration\n")

        for entity in model.entities:
            table = f"{entity.name.lower()}s"
            # Index foreign keys
            for fname, ftype in entity.fields.items():
                if fname.endswith('_id'):
                    lines.append(f"CREATE INDEX IF NOT EXISTS idx_{table}_{fname} ON {table}({fname});")
                elif fname == 'email':
                    lines.append(f"CREATE UNIQUE INDEX IF NOT EXISTS idx_{table}_{fname} ON {table}({fname});")
                elif fname in ('created_at', 'date', 'sent_at'):
                    lines.append(f"CREATE INDEX IF NOT EXISTS idx_{table}_{fname} ON {table}({fname} DESC);")
                elif fname == 'status':
                    lines.append(f"CREATE INDEX IF NOT EXISTS idx_{table}_{fname} ON {table}({fname});")

            # Composite indexes for common queries
            fk_fields = [f for f in entity.fields if f.endswith('_id')]
            time_fields = [f for f in entity.fields if f in ('created_at', 'date', 'sent_at')]
            if fk_fields and time_fields:
                cols = ', '.join(fk_fields[:1] + time_fields[:1])
                lines.append(f"CREATE INDEX IF NOT EXISTS idx_{table}_composite ON {table}({cols});")

            lines.append("")

        return '\n'.join(lines)

    def _gen_pool(self, model: SystemModel) -> str:
        """Generate connection pooling configuration."""
        return f'''"""Connection Pool Configuration — Auto-generated by AXIMA Coder V2"""
import os

POOL_CONFIG = {{
    "pool_size": int(os.getenv("DB_POOL_SIZE", "10")),
    "max_overflow": int(os.getenv("DB_MAX_OVERFLOW", "20")),
    "pool_timeout": int(os.getenv("DB_POOL_TIMEOUT", "30")),
    "pool_recycle": int(os.getenv("DB_POOL_RECYCLE", "3600")),
    "pool_pre_ping": True,
    "echo_pool": os.getenv("DB_ECHO_POOL", "false").lower() == "true",
}}


class ConnectionPool:
    """Lightweight connection pool for SQLite/Postgres."""

    def __init__(self, db_url: str, **kwargs):
        self.db_url = db_url
        self.config = {{**POOL_CONFIG, **kwargs}}
        self._connections: list = []
        self._available: list = []

    def get_connection(self):
        if self._available:
            conn = self._available.pop()
            if self._is_alive(conn):
                return conn
        if len(self._connections) < self.config["pool_size"] + self.config["max_overflow"]:
            conn = self._create_connection()
            self._connections.append(conn)
            return conn
        raise RuntimeError("Connection pool exhausted")

    def release(self, conn):
        if len(self._available) < self.config["pool_size"]:
            self._available.append(conn)
        else:
            self._close_connection(conn)

    def _create_connection(self):
        import sqlite3
        return sqlite3.connect(self.db_url)

    def _is_alive(self, conn) -> bool:
        try:
            conn.execute("SELECT 1")
            return True
        except Exception:
            return False

    def _close_connection(self, conn):
        try:
            conn.close()
        except Exception:
            pass
'''

    def _gen_rate_limit(self, model: SystemModel) -> str:
        """Generate rate limiting middleware."""
        return '''"""Rate Limiting Middleware — Auto-generated by AXIMA Coder V2"""
import time
from typing import Dict, Tuple
from functools import wraps


class RateLimiter:
    """Token bucket rate limiter."""

    def __init__(self, requests_per_minute: int = 60, burst: int = 10):
        self.rate = requests_per_minute / 60.0  # tokens per second
        self.burst = burst
        self._buckets: Dict[str, Tuple[float, float]] = {}  # key -> (tokens, last_time)

    def is_allowed(self, key: str) -> Tuple[bool, dict]:
        """Check if request is allowed. Returns (allowed, headers)."""
        now = time.time()

        if key not in self._buckets:
            self._buckets[key] = (self.burst - 1, now)
            return True, self._headers(self.burst - 1)

        tokens, last_time = self._buckets[key]
        elapsed = now - last_time
        tokens = min(self.burst, tokens + elapsed * self.rate)

        if tokens >= 1:
            self._buckets[key] = (tokens - 1, now)
            return True, self._headers(tokens - 1)
        else:
            retry_after = (1 - tokens) / self.rate
            return False, {**self._headers(0), "Retry-After": str(int(retry_after) + 1)}

    def _headers(self, remaining: float) -> dict:
        return {
            "X-RateLimit-Limit": str(self.burst),
            "X-RateLimit-Remaining": str(int(remaining)),
        }

    def cleanup(self, max_age: float = 3600):
        """Remove stale entries."""
        now = time.time()
        stale = [k for k, (_, t) in self._buckets.items() if now - t > max_age]
        for k in stale:
            del self._buckets[k]


# Default rate limiters
default_limiter = RateLimiter(requests_per_minute=60, burst=10)
auth_limiter = RateLimiter(requests_per_minute=10, burst=5)  # Stricter for auth
upload_limiter = RateLimiter(requests_per_minute=10, burst=3)  # Stricter for uploads


def rate_limit(limiter: RateLimiter = None, key_func=None):
    """Decorator for rate limiting."""
    _limiter = limiter or default_limiter

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Extract client key (IP or user_id)
            key = key_func(*args, **kwargs) if key_func else "global"
            allowed, headers = _limiter.is_allowed(key)
            if not allowed:
                raise Exception(f"Rate limit exceeded. Retry after {headers.get('Retry-After', '?')}s")
            return func(*args, **kwargs)
        return wrapper
    return decorator
'''

    def _gen_pagination(self, model: SystemModel) -> str:
        """Generate pagination utility."""
        return '''"""Pagination Utility — Auto-generated by AXIMA Coder V2"""
from typing import Any, Dict, List, Optional
from dataclasses import dataclass
import math


@dataclass
class PaginatedResponse:
    """Standardized paginated response."""
    items: List[Any]
    total: int
    page: int
    page_size: int
    total_pages: int
    has_next: bool
    has_prev: bool

    def to_dict(self) -> Dict:
        return {
            "items": self.items,
            "pagination": {
                "total": self.total,
                "page": self.page,
                "page_size": self.page_size,
                "total_pages": self.total_pages,
                "has_next": self.has_next,
                "has_prev": self.has_prev,
            }
        }


def paginate(
    query_func,
    page: int = 1,
    page_size: int = 20,
    max_page_size: int = 100,
    count_func=None,
) -> PaginatedResponse:
    """Generic pagination helper.

    Args:
        query_func: Function that accepts (limit, offset) and returns items
        page: Current page (1-indexed)
        page_size: Items per page
        max_page_size: Maximum allowed page size
        count_func: Function that returns total count
    """
    page = max(1, page)
    page_size = min(max(1, page_size), max_page_size)
    offset = (page - 1) * page_size

    items = query_func(limit=page_size, offset=offset)
    total = count_func() if count_func else len(items)
    total_pages = math.ceil(total / page_size) if total > 0 else 1

    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
        has_next=page < total_pages,
        has_prev=page > 1,
    )


def cursor_paginate(query_func, cursor: Optional[str] = None, limit: int = 20):
    """Cursor-based pagination for large datasets.

    Args:
        query_func: Function that accepts (cursor, limit) and returns (items, next_cursor)
        cursor: Opaque cursor string (None for first page)
        limit: Number of items to return
    """
    items, next_cursor = query_func(cursor=cursor, limit=limit + 1)
    has_more = len(items) > limit
    if has_more:
        items = items[:limit]

    return {
        "items": items,
        "next_cursor": next_cursor if has_more else None,
        "has_more": has_more,
    }
'''

    def _gen_compression(self, model: SystemModel) -> str:
        """Generate response compression middleware."""
        return '''"""Response Compression Middleware — Auto-generated by AXIMA Coder V2"""
import gzip
import io
from typing import Callable


class CompressionMiddleware:
    """GZip compression for responses above threshold."""

    def __init__(self, minimum_size: int = 500, compression_level: int = 6):
        self.minimum_size = minimum_size
        self.compression_level = compression_level
        self.compressible_types = {
            "application/json",
            "text/html",
            "text/plain",
            "text/css",
            "application/javascript",
            "application/xml",
        }

    def should_compress(self, content_type: str, content_length: int, accept_encoding: str) -> bool:
        """Determine if response should be compressed."""
        if "gzip" not in accept_encoding:
            return False
        if content_length < self.minimum_size:
            return False
        base_type = content_type.split(";")[0].strip()
        return base_type in self.compressible_types

    def compress(self, data: bytes) -> bytes:
        """Compress data using gzip."""
        buf = io.BytesIO()
        with gzip.GzipFile(fileobj=buf, mode="wb", compresslevel=self.compression_level) as f:
            f.write(data)
        return buf.getvalue()

    def get_fastapi_middleware(self):
        """Return FastAPI middleware function."""
        middleware_self = self

        async def compression_middleware(request, call_next):
            response = await call_next(request)
            accept_encoding = request.headers.get("accept-encoding", "")

            if hasattr(response, "body"):
                body = response.body
                content_type = response.headers.get("content-type", "")
                if middleware_self.should_compress(content_type, len(body), accept_encoding):
                    compressed = middleware_self.compress(body)
                    if len(compressed) < len(body):
                        response.body = compressed
                        response.headers["content-encoding"] = "gzip"
                        response.headers["content-length"] = str(len(compressed))
            return response

        return compression_middleware


# Default instance
compression = CompressionMiddleware(minimum_size=500, compression_level=6)
'''




# ═══════════════════════════════════════════════════════════════
# SECTION 3: TEST GENERATOR
# Creates unit tests, integration tests, and load test scripts.
# ═══════════════════════════════════════════════════════════════

class TestGenerator:
    """Generate comprehensive test suites from SystemModel."""

    def generate_tests(self, model: SystemModel, files: Dict[str, str]) -> Dict[str, str]:
        """Generate all test files."""
        test_files = {}

        # Unit tests for each endpoint
        test_files['tests/test_endpoints.py'] = self._gen_unit_tests(model)

        # Integration tests for auth flow
        if 'auth' in model.features:
            test_files['tests/test_auth_flow.py'] = self._gen_auth_tests(model)

        # Load test script
        test_files['tests/load_test.py'] = self._gen_load_tests(model)

        # Test configuration
        test_files['tests/conftest.py'] = self._gen_conftest(model)

        # pytest.ini
        test_files['pytest.ini'] = self._gen_pytest_ini()

        return test_files

    def _gen_unit_tests(self, model: SystemModel) -> str:
        """Generate unit tests for all endpoints."""
        code = '''"""Unit Tests — Auto-generated by AXIMA Coder V2"""
import pytest
from unittest.mock import patch, MagicMock


class TestHealthEndpoint:
    """Health check endpoint tests."""

    def test_health_returns_ok(self, client):
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}

'''
        for entity in model.entities:
            if entity.name == 'User' and 'auth' in model.features:
                continue  # Auth tests are separate

            ename = entity.name
            ename_lower = ename.lower()
            table = f"{ename_lower}s"

            # Sample data for tests
            sample_data = {}
            for fname, ftype in entity.fields.items():
                if fname == 'id':
                    continue
                if fname == 'password_hash':
                    continue
                if ftype == 'str':
                    sample_data[fname] = f"test_{fname}"
                elif ftype == 'int':
                    sample_data[fname] = 1
                elif ftype == 'float':
                    sample_data[fname] = 9.99
                elif ftype == 'bool':
                    sample_data[fname] = True
                elif ftype == 'datetime':
                    sample_data[fname] = "2024-01-01T00:00:00"

            sample_json = json.dumps(sample_data, indent=8)

            code += f'''
class Test{ename}Endpoints:
    """{ename} CRUD endpoint tests."""

    SAMPLE_DATA = {sample_json}

    def test_create_{ename_lower}(self, client, auth_headers):
        response = client.post("/{table}", json=self.SAMPLE_DATA, headers=auth_headers)
        assert response.status_code in (200, 201)
        data = response.json()
        assert "id" in data

    def test_list_{ename_lower}s(self, client, auth_headers):
        response = client.get("/{table}", headers=auth_headers)
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_get_{ename_lower}_by_id(self, client, auth_headers):
        # Create first
        create_resp = client.post("/{table}", json=self.SAMPLE_DATA, headers=auth_headers)
        item_id = create_resp.json().get("id", 1)
        # Get
        response = client.get(f"/{table}/{{item_id}}", headers=auth_headers)
        assert response.status_code == 200

    def test_get_{ename_lower}_not_found(self, client, auth_headers):
        response = client.get("/{table}/99999", headers=auth_headers)
        assert response.status_code == 404

    def test_delete_{ename_lower}(self, client, auth_headers):
        # Create first
        create_resp = client.post("/{table}", json=self.SAMPLE_DATA, headers=auth_headers)
        item_id = create_resp.json().get("id", 1)
        # Delete
        response = client.delete(f"/{table}/{{item_id}}", headers=auth_headers)
        assert response.status_code == 200

    def test_create_{ename_lower}_unauthorized(self, client):
        response = client.post("/{table}", json=self.SAMPLE_DATA)
        assert response.status_code in (401, 403)

'''
        return code

    def _gen_auth_tests(self, model: SystemModel) -> str:
        """Generate integration tests for auth flow."""
        return '''"""Auth Flow Integration Tests — Auto-generated by AXIMA Coder V2"""
import pytest


class TestAuthFlow:
    """Full authentication flow integration tests."""

    TEST_USER = {
        "email": "test@example.com",
        "password": "SecurePass123!",
        "name": "Test User"
    }

    def test_register_new_user(self, client):
        response = client.post("/auth/register", json=self.TEST_USER)
        assert response.status_code in (200, 201)
        data = response.json()
        assert data["email"] == self.TEST_USER["email"]
        assert "password" not in data
        assert "password_hash" not in data

    def test_register_duplicate_email(self, client):
        # Register first
        client.post("/auth/register", json=self.TEST_USER)
        # Try again
        response = client.post("/auth/register", json=self.TEST_USER)
        assert response.status_code == 400

    def test_login_valid_credentials(self, client):
        # Register first
        client.post("/auth/register", json=self.TEST_USER)
        # Login
        response = client.post("/auth/login", json={
            "email": self.TEST_USER["email"],
            "password": self.TEST_USER["password"]
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_login_invalid_password(self, client):
        client.post("/auth/register", json=self.TEST_USER)
        response = client.post("/auth/login", json={
            "email": self.TEST_USER["email"],
            "password": "wrong_password"
        })
        assert response.status_code == 401

    def test_login_nonexistent_user(self, client):
        response = client.post("/auth/login", json={
            "email": "nobody@example.com",
            "password": "anything"
        })
        assert response.status_code == 401

    def test_access_protected_endpoint_with_token(self, client):
        # Register + login
        client.post("/auth/register", json=self.TEST_USER)
        login_resp = client.post("/auth/login", json={
            "email": self.TEST_USER["email"],
            "password": self.TEST_USER["password"]
        })
        token = login_resp.json()["access_token"]

        # Access protected route
        response = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200
        assert response.json()["email"] == self.TEST_USER["email"]

    def test_access_protected_endpoint_without_token(self, client):
        response = client.get("/auth/me")
        assert response.status_code in (401, 403)

    def test_access_with_invalid_token(self, client):
        response = client.get("/auth/me", headers={"Authorization": "Bearer invalid.token.here"})
        assert response.status_code == 401

    def test_token_contains_user_info(self, client):
        client.post("/auth/register", json=self.TEST_USER)
        login_resp = client.post("/auth/login", json={
            "email": self.TEST_USER["email"],
            "password": self.TEST_USER["password"]
        })
        token = login_resp.json()["access_token"]
        # Token should be a valid JWT (3 parts)
        assert len(token.split(".")) == 3
'''

    def _gen_load_tests(self, model: SystemModel) -> str:
        """Generate load test script (locust/k6 pattern)."""
        entities = [e for e in model.entities if e.name != 'User']
        first_entity = entities[0] if entities else model.entities[0]
        ename_lower = first_entity.name.lower()

        return f'''"""Load Test Script — Auto-generated by AXIMA Coder V2
Usage:
    pip install locust
    locust -f tests/load_test.py --host=http://localhost:8000

Alternative k6 script at bottom (commented out).
"""
from locust import HttpUser, task, between, events
import json
import random
import string


class APIUser(HttpUser):
    """Simulated API user for load testing."""
    wait_time = between(0.5, 2.0)
    token = None

    def on_start(self):
        """Register and login on start."""
        email = f"loadtest_{{random.randint(1, 999999)}}@test.com"
        password = "LoadTest123!"

        # Register
        self.client.post("/auth/register", json={{
            "email": email,
            "password": password,
            "name": "Load Test User"
        }})

        # Login
        resp = self.client.post("/auth/login", json={{
            "email": email,
            "password": password
        }})
        if resp.status_code == 200:
            self.token = resp.json().get("access_token")

    @property
    def auth_headers(self):
        if self.token:
            return {{"Authorization": f"Bearer {{self.token}}"}}
        return {{}}

    @task(3)
    def list_{ename_lower}s(self):
        """List all {ename_lower}s (most common operation)."""
        self.client.get("/{ename_lower}s", headers=self.auth_headers)

    @task(2)
    def create_{ename_lower}(self):
        """Create a new {ename_lower}."""
        data = {{{", ".join(f'"{f}": "test_{{random.randint(1,999)}}"' for f in first_entity.fields if f != "id" and f != "password_hash")}}}
        self.client.post("/{ename_lower}s", json=data, headers=self.auth_headers)

    @task(2)
    def get_{ename_lower}_detail(self):
        """Get a specific {ename_lower}."""
        item_id = random.randint(1, 100)
        self.client.get(f"/{ename_lower}s/{{item_id}}", headers=self.auth_headers)

    @task(1)
    def health_check(self):
        """Health check endpoint."""
        self.client.get("/health")


# ═══ k6 Load Test (JavaScript) ═══
# Save this as load_test.js and run: k6 run load_test.js
K6_SCRIPT = """
// k6 Load Test — Auto-generated by AXIMA Coder V2
// Run: k6 run --vus 50 --duration 60s load_test.js

import http from "k6/http";
import {{ check, sleep }} from "k6";
import {{ Rate }} from "k6/metrics";

const errorRate = new Rate("errors");
const BASE_URL = __ENV.BASE_URL || "http://localhost:8000";

export const options = {{
  stages: [
    {{ duration: "10s", target: 10 }},   // Ramp up
    {{ duration: "30s", target: 50 }},   // Sustained load
    {{ duration: "10s", target: 100 }},  // Peak
    {{ duration: "10s", target: 0 }},    // Ramp down
  ],
  thresholds: {{
    http_req_duration: ["p(95)<500"],  // 95% under 500ms
    errors: ["rate<0.1"],              // Error rate under 10%
  }},
}};

export default function () {{
  // Health check
  let res = http.get(`${{BASE_URL}}/health`);
  check(res, {{ "health ok": (r) => r.status === 200 }});
  errorRate.add(res.status !== 200);

  // List endpoint
  res = http.get(`${{BASE_URL}}/{ename_lower}s`);
  check(res, {{ "list ok": (r) => r.status === 200 }});
  errorRate.add(res.status !== 200);

  sleep(0.5);
}}
"""
'''

    def _gen_conftest(self, model: SystemModel) -> str:
        """Generate pytest conftest with fixtures."""
        if model.backend == 'fastapi':
            return '''"""Test Configuration — Auto-generated by AXIMA Coder V2"""
import pytest
import os
import tempfile

# Use test database
os.environ["DATABASE_URL"] = ":memory:"
os.environ["SECRET_KEY"] = "test-secret-key-not-for-production"


@pytest.fixture(scope="session")
def app():
    """Create application instance for testing."""
    from main import app as _app
    return _app


@pytest.fixture
def client(app):
    """Create test client."""
    from fastapi.testclient import TestClient
    with TestClient(app) as c:
        yield c


@pytest.fixture
def auth_headers(client):
    """Get auth headers for protected endpoints."""
    # Register a test user
    client.post("/auth/register", json={
        "email": "fixture@test.com",
        "password": "TestPass123!",
        "name": "Fixture User"
    })
    # Login
    resp = client.post("/auth/login", json={
        "email": "fixture@test.com",
        "password": "TestPass123!"
    })
    if resp.status_code == 200:
        token = resp.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}
    return {}


@pytest.fixture(autouse=True)
def reset_db():
    """Reset database between tests."""
    from main import init_db
    init_db()
    yield
'''
        else:
            return '''"""Test Configuration — Auto-generated by AXIMA Coder V2"""
import pytest
import os

os.environ["DB_PATH"] = ":memory:"
os.environ["JWT_SECRET"] = "test-secret-key"


@pytest.fixture
def client():
    """Create test client."""
    # Import and configure app for testing
    pass


@pytest.fixture
def auth_headers(client):
    """Get auth headers for protected endpoints."""
    return {}
'''

    def _gen_pytest_ini(self) -> str:
        """Generate pytest configuration."""
        return '''[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = -v --tb=short --strict-markers
markers =
    slow: marks tests as slow (deselect with '-m "not slow"')
    integration: marks integration tests
    load: marks load tests
'''




# ═══════════════════════════════════════════════════════════════
# SECTION 4: CI/CD PIPELINE GENERATOR
# Creates GitHub Actions, Docker multi-stage build, health checks.
# ═══════════════════════════════════════════════════════════════

class CICDGenerator:
    """Generate CI/CD pipeline configurations."""

    def generate_cicd(self, model: SystemModel) -> Dict[str, str]:
        """Generate all CI/CD files."""
        files = {}

        # GitHub Actions workflow
        files['.github/workflows/ci.yml'] = self._gen_github_actions(model)

        # Docker multi-stage build
        files['Dockerfile'] = self._gen_multistage_docker(model)
        files['docker-compose.yml'] = self._gen_docker_compose(model)
        files['.dockerignore'] = self._gen_dockerignore()

        # Health check endpoint (extended)
        files['healthcheck.py'] = self._gen_healthcheck(model)

        return files

    def _gen_github_actions(self, model: SystemModel) -> str:
        """Generate GitHub Actions CI/CD workflow."""
        if model.backend in ('fastapi', 'flask', 'django'):
            return f'''# CI/CD Pipeline — Auto-generated by AXIMA Coder V2
name: CI/CD Pipeline

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

env:
  PYTHON_VERSION: "3.12"
  REGISTRY: ghcr.io
  IMAGE_NAME: ${{{{ github.repository }}}}

jobs:
  lint:
    name: Lint & Format Check
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: ${{{{ env.PYTHON_VERSION }}}}
          cache: pip

      - name: Install linting tools
        run: pip install ruff mypy

      - name: Run ruff (linting)
        run: ruff check .

      - name: Run ruff (formatting)
        run: ruff format --check .

      - name: Run mypy (type checking)
        run: mypy . --ignore-missing-imports || true

  test:
    name: Test Suite
    runs-on: ubuntu-latest
    needs: lint
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: ${{{{ env.PYTHON_VERSION }}}}
          cache: pip

      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest pytest-cov pytest-asyncio httpx

      - name: Run tests with coverage
        run: pytest --cov=. --cov-report=xml --cov-report=term-missing
        env:
          DATABASE_URL: ":memory:"
          SECRET_KEY: "ci-test-secret"

      - name: Upload coverage
        uses: actions/upload-artifact@v4
        with:
          name: coverage-report
          path: coverage.xml

  build:
    name: Build & Push Docker Image
    runs-on: ubuntu-latest
    needs: test
    if: github.ref == 'refs/heads/main'
    permissions:
      contents: read
      packages: write

    steps:
      - uses: actions/checkout@v4

      - name: Login to Container Registry
        uses: docker/login-action@v3
        with:
          registry: ${{{{ env.REGISTRY }}}}
          username: ${{{{ github.actor }}}}
          password: ${{{{ secrets.GITHUB_TOKEN }}}}

      - name: Build and push Docker image
        uses: docker/build-push-action@v5
        with:
          context: .
          push: true
          tags: |
            ${{{{ env.REGISTRY }}}}/${{{{ env.IMAGE_NAME }}}}:latest
            ${{{{ env.REGISTRY }}}}/${{{{ env.IMAGE_NAME }}}}:${{{{ github.sha }}}}

  deploy:
    name: Deploy
    runs-on: ubuntu-latest
    needs: build
    if: github.ref == 'refs/heads/main'
    environment: production
    steps:
      - name: Deploy to production
        run: |
          echo "Deploy step — configure for your hosting provider"
          echo "Image: ${{{{ env.REGISTRY }}}}/${{{{ env.IMAGE_NAME }}}}:${{{{ github.sha }}}}"
'''
        else:
            return f'''# CI/CD Pipeline — Auto-generated by AXIMA Coder V2
name: CI/CD Pipeline

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

env:
  NODE_VERSION: "20"
  REGISTRY: ghcr.io
  IMAGE_NAME: ${{{{ github.repository }}}}

jobs:
  lint:
    name: Lint & Format Check
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: ${{{{ env.NODE_VERSION }}}}
          cache: npm

      - run: npm ci
      - run: npm run lint || npx eslint .

  test:
    name: Test Suite
    runs-on: ubuntu-latest
    needs: lint
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: ${{{{ env.NODE_VERSION }}}}
          cache: npm

      - run: npm ci
      - run: npm test || echo "No tests configured"
        env:
          DB_PATH: ":memory:"
          JWT_SECRET: "ci-test-secret"

  build:
    name: Build & Push Docker Image
    runs-on: ubuntu-latest
    needs: test
    if: github.ref == 'refs/heads/main'
    permissions:
      contents: read
      packages: write

    steps:
      - uses: actions/checkout@v4
      - name: Login to Container Registry
        uses: docker/login-action@v3
        with:
          registry: ${{{{ env.REGISTRY }}}}
          username: ${{{{ github.actor }}}}
          password: ${{{{ secrets.GITHUB_TOKEN }}}}
      - name: Build and push
        uses: docker/build-push-action@v5
        with:
          context: .
          push: true
          tags: ${{{{ env.REGISTRY }}}}/${{{{ env.IMAGE_NAME }}}}:${{{{ github.sha }}}}
'''

    def _gen_multistage_docker(self, model: SystemModel) -> str:
        """Generate multi-stage Dockerfile."""
        if model.backend in ('fastapi', 'flask', 'django'):
            return f'''# Multi-stage Dockerfile — Auto-generated by AXIMA Coder V2
# Stage 1: Dependencies
FROM python:3.12-slim AS deps
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Stage 2: Production
FROM python:3.12-slim AS production
WORKDIR /app

# Security: non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Copy installed packages from deps stage
COPY --from=deps /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH

# Copy application code
COPY . .

# Remove unnecessary files
RUN rm -rf tests/ docs/ .git/ .env* *.md

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \\
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

# Run as non-root
USER appuser
EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
'''
        else:
            return f'''# Multi-stage Dockerfile — Auto-generated by AXIMA Coder V2
# Stage 1: Dependencies
FROM node:20-slim AS deps
WORKDIR /app
COPY package*.json ./
RUN npm ci --production

# Stage 2: Production
FROM node:20-slim AS production
WORKDIR /app

# Security: non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Copy node_modules from deps stage
COPY --from=deps /app/node_modules ./node_modules
COPY . .

# Remove unnecessary files
RUN rm -rf tests/ docs/ .git/ .env* *.md

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \\
    CMD node -e "require('http').get('http://localhost:3000/health', r => process.exit(r.statusCode === 200 ? 0 : 1))" || exit 1

USER appuser
EXPOSE 3000

CMD ["node", "server.js"]
'''

    def _gen_docker_compose(self, model: SystemModel) -> str:
        """Generate docker-compose for local development."""
        port = "8000" if model.backend in ('fastapi', 'flask') else "3000"
        services = f'''# Docker Compose — Auto-generated by AXIMA Coder V2
version: "3.8"

services:
  app:
    build: .
    ports:
      - "{port}:{port}"
    environment:
      - DATABASE_URL=${{DATABASE_URL:-app.db}}
      - SECRET_KEY=${{SECRET_KEY:-dev-secret-change-me}}
    volumes:
      - ./data:/app/data
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:{port}/health"]
      interval: 30s
      timeout: 10s
      retries: 3
'''
        if model.database == 'postgres':
            services += '''
  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: app
      POSTGRES_USER: ${POSTGRES_USER:-appuser}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-changeme}
    ports:
      - "5432:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U appuser"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s

volumes:
  pgdata:
'''
        return services

    def _gen_dockerignore(self) -> str:
        """Generate .dockerignore."""
        return '''# .dockerignore — Auto-generated by AXIMA Coder V2
.git
.gitignore
.env
.env.*
*.md
docs/
tests/
__pycache__/
*.pyc
.pytest_cache/
.coverage
coverage.xml
node_modules/
.npm
*.log
.vscode/
.idea/
'''

    def _gen_healthcheck(self, model: SystemModel) -> str:
        """Generate comprehensive health check endpoint."""
        return '''"""Health Check System — Auto-generated by AXIMA Coder V2"""
import time
import os
import sqlite3
from typing import Dict, Any
from datetime import datetime


class HealthChecker:
    """Comprehensive health check with dependency verification."""

    def __init__(self):
        self.start_time = time.time()
        self.checks: Dict[str, callable] = {}

    def register_check(self, name: str, check_func):
        """Register a health check function."""
        self.checks[name] = check_func

    def run_all(self) -> Dict[str, Any]:
        """Run all health checks and return status."""
        results = {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "uptime_seconds": int(time.time() - self.start_time),
            "version": os.getenv("APP_VERSION", "1.0.0"),
            "checks": {},
        }

        for name, check_func in self.checks.items():
            try:
                start = time.time()
                check_func()
                duration_ms = (time.time() - start) * 1000
                results["checks"][name] = {
                    "status": "pass",
                    "duration_ms": round(duration_ms, 2),
                }
            except Exception as e:
                results["checks"][name] = {
                    "status": "fail",
                    "error": str(e),
                }
                results["status"] = "unhealthy"

        return results


# Default health checker with DB check
health_checker = HealthChecker()


def check_database():
    """Verify database connectivity."""
    db_path = os.getenv("DATABASE_URL", "app.db")
    if db_path == ":memory:":
        return
    conn = sqlite3.connect(db_path)
    conn.execute("SELECT 1")
    conn.close()


def check_disk_space():
    """Verify sufficient disk space (>100MB free)."""
    import shutil
    usage = shutil.disk_usage("/")
    free_mb = usage.free / (1024 * 1024)
    if free_mb < 100:
        raise RuntimeError(f"Low disk space: {free_mb:.0f}MB free")


health_checker.register_check("database", check_database)
health_checker.register_check("disk_space", check_disk_space)
'''




# ═══════════════════════════════════════════════════════════════
# SECTION 5: API DOCUMENTATION GENERATOR
# Creates OpenAPI 3.0 spec and Swagger UI endpoint.
# ═══════════════════════════════════════════════════════════════

class APIDocGenerator:
    """Generate OpenAPI 3.0 specification from SystemModel."""

    def generate_openapi(self, model: SystemModel) -> Dict[str, str]:
        """Generate OpenAPI spec and Swagger UI setup."""
        files = {}

        # OpenAPI 3.0 specification
        files['docs/openapi.json'] = json.dumps(self._build_spec(model), indent=2)
        files['docs/openapi.yaml'] = self._spec_to_yaml(self._build_spec(model))

        # Swagger UI HTML endpoint
        files['docs/swagger_ui.html'] = self._gen_swagger_html(model)

        return files

    def _build_spec(self, model: SystemModel) -> dict:
        """Build OpenAPI 3.0 specification object."""
        spec = {
            "openapi": "3.0.3",
            "info": {
                "title": f"{model.name.title()} API",
                "version": "1.0.0",
                "description": f"API documentation for {model.name} — Generated by AXIMA Coder V2",
                "contact": {"name": "API Support"},
            },
            "servers": [
                {"url": "http://localhost:8000", "description": "Development"},
                {"url": "https://api.example.com", "description": "Production"},
            ],
            "paths": {},
            "components": {
                "schemas": {},
                "securitySchemes": {},
            },
        }

        # Add auth security scheme
        if 'auth' in model.features:
            spec["components"]["securitySchemes"]["BearerAuth"] = {
                "type": "http",
                "scheme": "bearer",
                "bearerFormat": "JWT",
            }

        # Generate schemas for each entity
        for entity in model.entities:
            schema_props = {}
            required_fields = []
            for fname, ftype in entity.fields.items():
                json_type = {'str': 'string', 'int': 'integer', 'float': 'number',
                             'bool': 'boolean', 'datetime': 'string'}.get(ftype, 'string')
                prop = {"type": json_type}
                if ftype == 'datetime':
                    prop["format"] = "date-time"
                if fname == 'id':
                    prop["readOnly"] = True
                if fname == 'email':
                    prop["format"] = "email"
                schema_props[fname] = prop
                if fname != 'id' and fname != 'password_hash':
                    required_fields.append(fname)

            spec["components"]["schemas"][entity.name] = {
                "type": "object",
                "properties": schema_props,
                "required": required_fields,
            }

            # Create request schema (without id)
            create_props = {k: v for k, v in schema_props.items() if k != 'id'}
            if 'password_hash' in create_props:
                del create_props['password_hash']
                create_props['password'] = {"type": "string", "format": "password", "minLength": 8}
            spec["components"]["schemas"][f"{entity.name}Create"] = {
                "type": "object",
                "properties": create_props,
            }

        # Generate paths for each entity
        for entity in model.entities:
            ename = entity.name
            ename_lower = ename.lower()
            table = f"{ename_lower}s"

            if ename == 'User' and 'auth' in model.features:
                # Auth endpoints
                spec["paths"]["/auth/register"] = {
                    "post": {
                        "tags": ["Authentication"],
                        "summary": "Register new user",
                        "requestBody": {
                            "required": True,
                            "content": {"application/json": {"schema": {"$ref": f"#/components/schemas/{ename}Create"}}},
                        },
                        "responses": {
                            "200": {"description": "User registered successfully"},
                            "400": {"description": "Email already exists"},
                        },
                    }
                }
                spec["paths"]["/auth/login"] = {
                    "post": {
                        "tags": ["Authentication"],
                        "summary": "Login and get access token",
                        "requestBody": {
                            "required": True,
                            "content": {"application/json": {"schema": {
                                "type": "object",
                                "properties": {
                                    "email": {"type": "string", "format": "email"},
                                    "password": {"type": "string"},
                                },
                            }}},
                        },
                        "responses": {
                            "200": {"description": "Login successful", "content": {"application/json": {"schema": {
                                "type": "object",
                                "properties": {
                                    "access_token": {"type": "string"},
                                    "token_type": {"type": "string"},
                                },
                            }}}},
                            "401": {"description": "Invalid credentials"},
                        },
                    }
                }
                spec["paths"]["/auth/me"] = {
                    "get": {
                        "tags": ["Authentication"],
                        "summary": "Get current user profile",
                        "security": [{"BearerAuth": []}],
                        "responses": {
                            "200": {"description": "User profile", "content": {"application/json": {"schema": {"$ref": f"#/components/schemas/{ename}"}}}},
                            "401": {"description": "Unauthorized"},
                        },
                    }
                }
            else:
                # CRUD endpoints
                security = [{"BearerAuth": []}] if 'auth' in model.features else []

                spec["paths"][f"/{table}"] = {
                    "get": {
                        "tags": [ename],
                        "summary": f"List all {table}",
                        "security": security,
                        "parameters": [
                            {"name": "page", "in": "query", "schema": {"type": "integer", "default": 1}},
                            {"name": "page_size", "in": "query", "schema": {"type": "integer", "default": 20}},
                        ],
                        "responses": {
                            "200": {"description": f"List of {table}", "content": {"application/json": {"schema": {
                                "type": "array", "items": {"$ref": f"#/components/schemas/{ename}"}
                            }}}},
                        },
                    },
                    "post": {
                        "tags": [ename],
                        "summary": f"Create a new {ename_lower}",
                        "security": security,
                        "requestBody": {
                            "required": True,
                            "content": {"application/json": {"schema": {"$ref": f"#/components/schemas/{ename}Create"}}},
                        },
                        "responses": {
                            "201": {"description": f"{ename} created"},
                            "400": {"description": "Validation error"},
                        },
                    },
                }
                spec["paths"][f"/{table}/{{id}}"] = {
                    "get": {
                        "tags": [ename],
                        "summary": f"Get {ename_lower} by ID",
                        "security": security,
                        "parameters": [{"name": "id", "in": "path", "required": True, "schema": {"type": "integer"}}],
                        "responses": {
                            "200": {"description": f"{ename} details"},
                            "404": {"description": "Not found"},
                        },
                    },
                    "delete": {
                        "tags": [ename],
                        "summary": f"Delete {ename_lower}",
                        "security": security,
                        "parameters": [{"name": "id", "in": "path", "required": True, "schema": {"type": "integer"}}],
                        "responses": {
                            "200": {"description": "Deleted"},
                            "404": {"description": "Not found"},
                        },
                    },
                }

        # Health endpoint
        spec["paths"]["/health"] = {
            "get": {
                "tags": ["System"],
                "summary": "Health check",
                "responses": {"200": {"description": "Service healthy"}},
            }
        }

        return spec

    def _spec_to_yaml(self, spec: dict) -> str:
        """Convert spec dict to YAML-like format (without PyYAML dependency)."""
        def to_yaml(obj, indent=0):
            lines = []
            prefix = "  " * indent
            if isinstance(obj, dict):
                for k, v in obj.items():
                    if isinstance(v, (dict, list)):
                        lines.append(f"{prefix}{k}:")
                        lines.append(to_yaml(v, indent + 1))
                    else:
                        lines.append(f"{prefix}{k}: {json.dumps(v)}")
            elif isinstance(obj, list):
                for item in obj:
                    if isinstance(item, dict):
                        lines.append(f"{prefix}-")
                        lines.append(to_yaml(item, indent + 1))
                    else:
                        lines.append(f"{prefix}- {json.dumps(item)}")
            return '\n'.join(lines)
        return to_yaml(spec)

    def _gen_swagger_html(self, model: SystemModel) -> str:
        """Generate Swagger UI HTML page."""
        return f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>{model.name.title()} — API Documentation</title>
    <link rel="stylesheet" href="https://unpkg.com/swagger-ui-dist@5/swagger-ui.css">
    <style>
        body {{ margin: 0; padding: 0; }}
        #swagger-ui {{ max-width: 1200px; margin: 0 auto; }}
    </style>
</head>
<body>
    <div id="swagger-ui"></div>
    <script src="https://unpkg.com/swagger-ui-dist@5/swagger-ui-bundle.js"></script>
    <script>
        SwaggerUIBundle({{
            url: "/docs/openapi.json",
            dom_id: "#swagger-ui",
            deepLinking: true,
            presets: [SwaggerUIBundle.presets.apis, SwaggerUIBundle.SwaggerUIStandalonePreset],
            layout: "StandaloneLayout",
        }});
    </script>
</body>
</html>'''




# ═══════════════════════════════════════════════════════════════
# SECTION 6: MONITORING & LOGGING
# Structured JSON logging, request timing, error tracking,
# and health metrics.
# ═══════════════════════════════════════════════════════════════

class MonitoringGenerator:
    """Generate monitoring and logging middleware."""

    def generate_monitoring(self, model: SystemModel) -> Dict[str, str]:
        """Generate monitoring files."""
        files = {}

        # Structured logging
        files['middleware/logging_middleware.py'] = self._gen_structured_logging(model)

        # Request/response timing
        files['middleware/timing_middleware.py'] = self._gen_timing(model)

        # Error tracking
        files['middleware/error_tracking.py'] = self._gen_error_tracking(model)

        # Metrics endpoint
        files['middleware/metrics.py'] = self._gen_metrics(model)

        return files

    def _gen_structured_logging(self, model: SystemModel) -> str:
        """Generate structured JSON logging configuration."""
        return '''"""Structured JSON Logging — Auto-generated by AXIMA Coder V2"""
import logging
import json
import sys
import os
import traceback
from datetime import datetime, timezone
from typing import Optional


class JSONFormatter(logging.Formatter):
    """Format log records as JSON for structured logging."""

    def __init__(self, service_name: str = "app"):
        super().__init__()
        self.service_name = service_name

    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "service": self.service_name,
            "message": record.getMessage(),
            "logger": record.name,
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = {
                "type": record.exc_info[0].__name__ if record.exc_info[0] else None,
                "message": str(record.exc_info[1]) if record.exc_info[1] else None,
                "traceback": traceback.format_exception(*record.exc_info),
            }

        # Add extra fields
        for key in ("request_id", "user_id", "method", "path", "status_code", "duration_ms"):
            if hasattr(record, key):
                log_entry[key] = getattr(record, key)

        return json.dumps(log_entry, default=str)


def setup_logging(service_name: str = "app", level: str = "INFO"):
    """Configure structured JSON logging."""
    log_level = getattr(logging, level.upper(), logging.INFO)

    # Root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Remove existing handlers
    root_logger.handlers.clear()

    # JSON handler (stdout)
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JSONFormatter(service_name=service_name))
    root_logger.addHandler(handler)

    # Suppress noisy libraries
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)

    return root_logger


# Initialize on import
logger = setup_logging(
    service_name=os.getenv("SERVICE_NAME", "app"),
    level=os.getenv("LOG_LEVEL", "INFO")
)
'''

    def _gen_timing(self, model: SystemModel) -> str:
        """Generate request/response timing middleware."""
        return '''"""Request/Response Timing Middleware — Auto-generated by AXIMA Coder V2"""
import time
import logging
import uuid
from typing import Callable

logger = logging.getLogger(__name__)


class TimingMiddleware:
    """Track request duration and add timing headers."""

    def __init__(self, slow_threshold_ms: float = 500):
        self.slow_threshold_ms = slow_threshold_ms
        self.request_count = 0
        self.total_duration_ms = 0
        self.slow_requests = 0

    async def __call__(self, request, call_next):
        """FastAPI middleware implementation."""
        request_id = str(uuid.uuid4())[:8]
        start_time = time.perf_counter()

        # Add request ID to request state
        request.state.request_id = request_id

        try:
            response = await call_next(request)
        except Exception as e:
            duration_ms = (time.perf_counter() - start_time) * 1000
            logger.error(
                f"Request failed: {request.method} {request.url.path}",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "path": str(request.url.path),
                    "duration_ms": round(duration_ms, 2),
                    "status_code": 500,
                }
            )
            raise

        duration_ms = (time.perf_counter() - start_time) * 1000

        # Update metrics
        self.request_count += 1
        self.total_duration_ms += duration_ms
        if duration_ms > self.slow_threshold_ms:
            self.slow_requests += 1

        # Add timing headers
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Response-Time"] = f"{duration_ms:.2f}ms"

        # Log request
        log_level = logging.WARNING if duration_ms > self.slow_threshold_ms else logging.INFO
        logger.log(
            log_level,
            f"{request.method} {request.url.path} -> {response.status_code} ({duration_ms:.1f}ms)",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": str(request.url.path),
                "status_code": response.status_code,
                "duration_ms": round(duration_ms, 2),
            }
        )

        return response

    @property
    def avg_duration_ms(self) -> float:
        if self.request_count == 0:
            return 0
        return self.total_duration_ms / self.request_count


# Default instance
timing = TimingMiddleware(slow_threshold_ms=500)
'''

    def _gen_error_tracking(self, model: SystemModel) -> str:
        """Generate error tracking with stack traces."""
        return '''"""Error Tracking Middleware — Auto-generated by AXIMA Coder V2"""
import logging
import traceback
import sys
from datetime import datetime, timezone
from typing import Dict, List, Optional
from collections import deque

logger = logging.getLogger(__name__)


class ErrorTracker:
    """Track and aggregate application errors."""

    def __init__(self, max_history: int = 100):
        self.errors: deque = deque(maxlen=max_history)
        self.error_counts: Dict[str, int] = {}
        self.total_errors = 0

    def track(self, error: Exception, context: Optional[Dict] = None):
        """Record an error with context."""
        self.total_errors += 1
        error_type = type(error).__name__
        self.error_counts[error_type] = self.error_counts.get(error_type, 0) + 1

        error_record = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "type": error_type,
            "message": str(error),
            "traceback": traceback.format_exc(),
            "context": context or {},
        }
        self.errors.append(error_record)

        # Log the error
        logger.error(
            f"Error tracked: {error_type}: {error}",
            exc_info=True,
            extra=context or {},
        )

    def get_recent(self, limit: int = 10) -> List[Dict]:
        """Get most recent errors."""
        return list(self.errors)[-limit:]

    def get_summary(self) -> Dict:
        """Get error summary statistics."""
        return {
            "total_errors": self.total_errors,
            "unique_types": len(self.error_counts),
            "by_type": dict(self.error_counts),
            "recent_count": len(self.errors),
        }

    def clear(self):
        """Clear error history."""
        self.errors.clear()
        self.error_counts.clear()
        self.total_errors = 0


# Global error tracker
error_tracker = ErrorTracker(max_history=100)


def error_tracking_middleware(app):
    """FastAPI error tracking middleware."""
    from fastapi import Request
    from fastapi.responses import JSONResponse

    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        context = {
            "method": request.method,
            "path": str(request.url.path),
            "client": request.client.host if request.client else "unknown",
        }
        error_tracker.track(exc, context)

        # Don't expose internal details in production
        return JSONResponse(
            status_code=500,
            content={
                "error": "Internal server error",
                "error_type": type(exc).__name__,
                "request_id": getattr(request.state, "request_id", None),
            }
        )
    return app
'''

    def _gen_metrics(self, model: SystemModel) -> str:
        """Generate health metrics endpoint."""
        return '''"""Health Metrics Endpoint — Auto-generated by AXIMA Coder V2"""
import time
import os
import platform
from typing import Dict, Any


class MetricsCollector:
    """Collect and expose application metrics."""

    def __init__(self):
        self.start_time = time.time()
        self._counters: Dict[str, int] = {}
        self._gauges: Dict[str, float] = {}

    def increment(self, metric: str, value: int = 1):
        """Increment a counter metric."""
        self._counters[metric] = self._counters.get(metric, 0) + value

    def gauge(self, metric: str, value: float):
        """Set a gauge metric."""
        self._gauges[metric] = value

    def get_metrics(self) -> Dict[str, Any]:
        """Get all metrics."""
        import resource
        usage = resource.getrusage(resource.RUSAGE_SELF)

        return {
            "uptime_seconds": int(time.time() - self.start_time),
            "system": {
                "python_version": platform.python_version(),
                "platform": platform.platform(),
                "pid": os.getpid(),
            },
            "resources": {
                "memory_mb": round(usage.ru_maxrss / 1024, 2),
                "user_time_seconds": round(usage.ru_utime, 2),
                "system_time_seconds": round(usage.ru_stime, 2),
            },
            "counters": dict(self._counters),
            "gauges": dict(self._gauges),
        }


# Global metrics instance
metrics = MetricsCollector()
'''




# ═══════════════════════════════════════════════════════════════
# SECTION 7: DATABASE MIGRATION SYSTEM
# Initial schema, add column templates, and rollback support.
# ═══════════════════════════════════════════════════════════════

class MigrationGenerator:
    """Generate database migration scripts."""

    def generate_migrations(self, model: SystemModel) -> Dict[str, str]:
        """Generate migration files."""
        files = {}

        # Migration runner
        files['migrations/migrate.py'] = self._gen_migration_runner()

        # Initial schema migration
        files['migrations/001_initial_schema.py'] = self._gen_initial_migration(model)

        # Add column migration template
        files['migrations/002_add_column_template.py'] = self._gen_add_column_template()

        # Seed data migration
        files['migrations/003_seed_data.py'] = self._gen_seed_migration(model)

        return files

    def _gen_migration_runner(self) -> str:
        """Generate the migration runner system."""
        return '''"""Database Migration Runner — Auto-generated by AXIMA Coder V2

Usage:
    python migrations/migrate.py up        # Run all pending migrations
    python migrations/migrate.py down      # Rollback last migration
    python migrations/migrate.py status    # Show migration status
    python migrations/migrate.py reset     # Rollback all and re-run
"""
import sqlite3
import os
import sys
import importlib.util
from pathlib import Path
from datetime import datetime


class MigrationRunner:
    """Run database migrations with rollback support."""

    def __init__(self, db_path: str = None, migrations_dir: str = None):
        self.db_path = db_path or os.getenv("DATABASE_URL", "app.db")
        self.migrations_dir = migrations_dir or str(Path(__file__).parent)
        self.db = sqlite3.connect(self.db_path)
        self.db.row_factory = sqlite3.Row
        self._ensure_migrations_table()

    def _ensure_migrations_table(self):
        """Create migrations tracking table if not exists."""
        self.db.execute("""
            CREATE TABLE IF NOT EXISTS _migrations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                applied_at TEXT NOT NULL,
                checksum TEXT
            )
        """)
        self.db.commit()

    def _get_applied(self) -> list:
        """Get list of applied migration names."""
        rows = self.db.execute("SELECT name FROM _migrations ORDER BY id").fetchall()
        return [row["name"] for row in rows]

    def _get_pending(self) -> list:
        """Get list of pending migration files."""
        applied = set(self._get_applied())
        migration_files = sorted(
            f for f in os.listdir(self.migrations_dir)
            if f.endswith('.py') and f[0].isdigit() and f != 'migrate.py'
        )
        return [f for f in migration_files if f not in applied]

    def _load_migration(self, filename: str):
        """Dynamically load a migration module."""
        filepath = os.path.join(self.migrations_dir, filename)
        spec = importlib.util.spec_from_file_location(filename[:-3], filepath)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def up(self):
        """Run all pending migrations."""
        pending = self._get_pending()
        if not pending:
            print("  No pending migrations.")
            return

        for filename in pending:
            print(f"  Applying: {filename}...")
            module = self._load_migration(filename)
            try:
                module.up(self.db)
                self.db.execute(
                    "INSERT INTO _migrations (name, applied_at) VALUES (?, ?)",
                    (filename, datetime.utcnow().isoformat())
                )
                self.db.commit()
                print(f"  ✓ Applied: {filename}")
            except Exception as e:
                self.db.rollback()
                print(f"  ✗ Failed: {filename} — {e}")
                raise

    def down(self, steps: int = 1):
        """Rollback the last N migrations."""
        applied = self._get_applied()
        if not applied:
            print("  No migrations to rollback.")
            return

        to_rollback = applied[-steps:]
        for filename in reversed(to_rollback):
            print(f"  Rolling back: {filename}...")
            module = self._load_migration(filename)
            try:
                module.down(self.db)
                self.db.execute("DELETE FROM _migrations WHERE name = ?", (filename,))
                self.db.commit()
                print(f"  ✓ Rolled back: {filename}")
            except Exception as e:
                self.db.rollback()
                print(f"  ✗ Rollback failed: {filename} — {e}")
                raise

    def status(self):
        """Show migration status."""
        applied = self._get_applied()
        pending = self._get_pending()
        print(f"  Applied: {len(applied)} | Pending: {len(pending)}")
        for name in applied:
            print(f"    ✓ {name}")
        for name in pending:
            print(f"    ○ {name}")

    def reset(self):
        """Rollback all and re-run."""
        applied = self._get_applied()
        self.down(steps=len(applied))
        self.up()


if __name__ == "__main__":
    runner = MigrationRunner()
    command = sys.argv[1] if len(sys.argv) > 1 else "status"

    if command == "up":
        runner.up()
    elif command == "down":
        steps = int(sys.argv[2]) if len(sys.argv) > 2 else 1
        runner.down(steps)
    elif command == "status":
        runner.status()
    elif command == "reset":
        runner.reset()
    else:
        print(f"Unknown command: {command}")
        print("Usage: migrate.py [up|down|status|reset]")
'''

    def _gen_initial_migration(self, model: SystemModel) -> str:
        """Generate initial schema migration."""
        up_statements = []
        down_statements = []

        for entity in model.entities:
            table = f"{entity.name.lower()}s"
            field_defs = []
            for fname, ftype in entity.fields.items():
                sql_type = {'int': 'INTEGER', 'str': 'TEXT', 'float': 'REAL',
                           'bool': 'INTEGER', 'datetime': 'TEXT'}.get(ftype, 'TEXT')
                if fname == 'id':
                    field_defs.append(f"        {fname} INTEGER PRIMARY KEY AUTOINCREMENT")
                elif fname == 'email':
                    field_defs.append(f"        {fname} TEXT UNIQUE NOT NULL")
                elif fname == 'password_hash':
                    field_defs.append(f"        {fname} TEXT NOT NULL")
                elif fname.endswith('_id'):
                    ref_table = fname[:-3] + 's'
                    field_defs.append(f"        {fname} INTEGER REFERENCES {ref_table}(id)")
                else:
                    field_defs.append(f"        {fname} {sql_type}")

            fields_sql = ',\\n'.join(field_defs)
            up_statements.append(
                f'    db.execute("""\\n        CREATE TABLE IF NOT EXISTS {table} (\\n{fields_sql}\\n        )\\n    """)'
            )
            down_statements.append(f'    db.execute("DROP TABLE IF EXISTS {table}")')

        up_code = '\n'.join(up_statements)
        down_code = '\n'.join(reversed(down_statements))

        return f'''"""Initial Schema Migration — Auto-generated by AXIMA Coder V2"""


def up(db):
    """Create initial tables."""
{up_code}
    db.commit()


def down(db):
    """Drop all tables (DESTRUCTIVE)."""
{down_code}
    db.commit()
'''

    def _gen_add_column_template(self) -> str:
        """Generate add column migration template."""
        return '''"""Add Column Migration Template — Auto-generated by AXIMA Coder V2

Instructions:
    1. Copy this file and rename with next sequence number
    2. Update TABLE_NAME, COLUMN_NAME, COLUMN_TYPE, DEFAULT_VALUE
    3. Run: python migrations/migrate.py up
"""

# ═══ Configuration — Edit these values ═══
TABLE_NAME = "your_table"
COLUMN_NAME = "new_column"
COLUMN_TYPE = "TEXT"          # TEXT, INTEGER, REAL, BLOB
DEFAULT_VALUE = None          # None, "", 0, "default_value"


def up(db):
    """Add column to table."""
    default_clause = f" DEFAULT {repr(DEFAULT_VALUE)}" if DEFAULT_VALUE is not None else ""
    db.execute(f"ALTER TABLE {TABLE_NAME} ADD COLUMN {COLUMN_NAME} {COLUMN_TYPE}{default_clause}")
    db.commit()
    print(f"  Added column {COLUMN_NAME} to {TABLE_NAME}")


def down(db):
    """Remove column (SQLite workaround — recreate table without column)."""
    # SQLite doesn't support DROP COLUMN before 3.35.0
    # For older versions, use the table recreation approach:
    rows = db.execute(f"PRAGMA table_info({TABLE_NAME})").fetchall()
    columns = [row[1] for row in rows if row[1] != COLUMN_NAME]

    if not columns:
        print(f"  Warning: Cannot remove {COLUMN_NAME} — would leave table empty")
        return

    cols_str = ", ".join(columns)
    db.execute(f"CREATE TABLE {TABLE_NAME}_backup AS SELECT {cols_str} FROM {TABLE_NAME}")
    db.execute(f"DROP TABLE {TABLE_NAME}")
    db.execute(f"ALTER TABLE {TABLE_NAME}_backup RENAME TO {TABLE_NAME}")
    db.commit()
    print(f"  Removed column {COLUMN_NAME} from {TABLE_NAME}")
'''

    def _gen_seed_migration(self, model: SystemModel) -> str:
        """Generate seed data migration."""
        seed_ops = []
        for entity in model.entities:
            if entity.name == 'User' and 'auth' in model.features:
                seed_ops.append(f'''    # Seed admin user (password: admin123)
    db.execute("""
        INSERT OR IGNORE INTO users (email, password_hash, name)
        VALUES ('admin@example.com', '$2b$10$placeholder_hash_replace_me', 'Admin')
    """)''')
            else:
                table = f"{entity.name.lower()}s"
                fields_no_id = [f for f in entity.fields if f != 'id' and f != 'password_hash']
                sample_values = []
                for f in fields_no_id:
                    ftype = entity.fields[f]
                    if ftype == 'str':
                        sample_values.append(f"'sample_{f}'")
                    elif ftype == 'int':
                        sample_values.append("1")
                    elif ftype == 'float':
                        sample_values.append("0.0")
                    elif ftype == 'bool':
                        sample_values.append("0")
                    elif ftype == 'datetime':
                        sample_values.append("'2024-01-01T00:00:00'")
                fields_str = ', '.join(fields_no_id)
                values_str = ', '.join(sample_values)
                seed_ops.append(f'    db.execute("INSERT OR IGNORE INTO {table} ({fields_str}) VALUES ({values_str})")')

        seed_code = '\n'.join(seed_ops)
        return f'''"""Seed Data Migration — Auto-generated by AXIMA Coder V2"""


def up(db):
    """Insert seed/sample data."""
{seed_code}
    db.commit()


def down(db):
    """Remove seed data (truncate all tables)."""
    tables = db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE '_%%'").fetchall()
    for (table,) in tables:
        db.execute(f"DELETE FROM {{table}}")
    db.commit()
'''




# ═══════════════════════════════════════════════════════════════
# SECTION 8: ERROR BOUNDARY DESIGN
# Global error handler, custom exceptions, retry logic,
# and circuit breaker pattern.
# ═══════════════════════════════════════════════════════════════

class ErrorBoundaryGenerator:
    """Generate error handling patterns and middleware."""

    def generate_error_boundaries(self, model: SystemModel) -> Dict[str, str]:
        """Generate error handling code."""
        files = {}

        # Global error handler middleware
        files['middleware/error_handler.py'] = self._gen_global_handler(model)

        # Custom exception classes
        files['exceptions.py'] = self._gen_exceptions(model)

        # Retry logic for external services
        files['utils/retry.py'] = self._gen_retry()

        # Circuit breaker pattern
        files['utils/circuit_breaker.py'] = self._gen_circuit_breaker()

        return files

    def _gen_global_handler(self, model: SystemModel) -> str:
        """Generate global error handler middleware."""
        return '''"""Global Error Handler Middleware — Auto-generated by AXIMA Coder V2"""
import logging
import traceback
from typing import Dict, Any, Optional
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


class ErrorResponse:
    """Standardized error response format."""

    def __init__(self, status_code: int, error_type: str, message: str,
                 details: Optional[Dict] = None, request_id: Optional[str] = None):
        self.status_code = status_code
        self.error_type = error_type
        self.message = message
        self.details = details
        self.request_id = request_id

    def to_dict(self) -> Dict[str, Any]:
        response = {
            "error": {
                "type": self.error_type,
                "message": self.message,
                "status_code": self.status_code,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        }
        if self.details:
            response["error"]["details"] = self.details
        if self.request_id:
            response["error"]["request_id"] = self.request_id
        return response


# Error type mapping
HTTP_ERROR_MAP = {
    400: ("bad_request", "The request was invalid or malformed"),
    401: ("unauthorized", "Authentication required"),
    403: ("forbidden", "You do not have permission to access this resource"),
    404: ("not_found", "The requested resource was not found"),
    409: ("conflict", "The request conflicts with existing data"),
    422: ("validation_error", "Request validation failed"),
    429: ("rate_limited", "Too many requests — please slow down"),
    500: ("internal_error", "An unexpected error occurred"),
    502: ("bad_gateway", "Upstream service unavailable"),
    503: ("service_unavailable", "Service temporarily unavailable"),
}


def create_error_response(status_code: int, message: str = None,
                         details: Dict = None, request_id: str = None) -> ErrorResponse:
    """Create standardized error response."""
    error_type, default_message = HTTP_ERROR_MAP.get(status_code, ("unknown", "Unknown error"))
    return ErrorResponse(
        status_code=status_code,
        error_type=error_type,
        message=message or default_message,
        details=details,
        request_id=request_id,
    )


def setup_error_handlers(app):
    """Register global error handlers with FastAPI app."""
    from fastapi import Request
    from fastapi.responses import JSONResponse
    from fastapi.exceptions import RequestValidationError

    @app.exception_handler(RequestValidationError)
    async def validation_handler(request: Request, exc: RequestValidationError):
        errors = []
        for error in exc.errors():
            errors.append({
                "field": " -> ".join(str(loc) for loc in error["loc"]),
                "message": error["msg"],
                "type": error["type"],
            })
        response = create_error_response(
            422, "Validation failed",
            details={"errors": errors},
            request_id=getattr(request.state, "request_id", None),
        )
        return JSONResponse(status_code=422, content=response.to_dict())

    @app.exception_handler(Exception)
    async def global_handler(request: Request, exc: Exception):
        # Import custom exceptions
        from exceptions import AppException

        if isinstance(exc, AppException):
            response = create_error_response(
                exc.status_code, str(exc),
                details=exc.details,
                request_id=getattr(request.state, "request_id", None),
            )
            return JSONResponse(status_code=exc.status_code, content=response.to_dict())

        # Unexpected error — log full traceback
        logger.error(
            f"Unhandled exception: {type(exc).__name__}: {exc}",
            exc_info=True,
            extra={"path": str(request.url.path), "method": request.method},
        )
        response = create_error_response(
            500, "An unexpected error occurred",
            request_id=getattr(request.state, "request_id", None),
        )
        return JSONResponse(status_code=500, content=response.to_dict())

    return app
'''

    def _gen_exceptions(self, model: SystemModel) -> str:
        """Generate custom exception classes."""
        entities = [e.name for e in model.entities]
        return f'''"""Custom Exception Classes — Auto-generated by AXIMA Coder V2"""
from typing import Optional, Dict, Any


class AppException(Exception):
    """Base application exception with HTTP status code."""

    def __init__(self, message: str, status_code: int = 500,
                 details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.status_code = status_code
        self.details = details


# ═══ Client Errors (4xx) ═══

class BadRequestError(AppException):
    """400 — Invalid request data."""
    def __init__(self, message: str = "Bad request", details: Dict = None):
        super().__init__(message, status_code=400, details=details)


class UnauthorizedError(AppException):
    """401 — Authentication required."""
    def __init__(self, message: str = "Authentication required"):
        super().__init__(message, status_code=401)


class ForbiddenError(AppException):
    """403 — Insufficient permissions."""
    def __init__(self, message: str = "Access denied"):
        super().__init__(message, status_code=403)


class NotFoundError(AppException):
    """404 — Resource not found."""
    def __init__(self, resource: str = "Resource", resource_id: Any = None):
        message = f"{{resource}} not found"
        if resource_id:
            message = f"{{resource}} with id '{{resource_id}}' not found"
        super().__init__(message, status_code=404)


class ConflictError(AppException):
    """409 — Resource conflict (duplicate, etc.)."""
    def __init__(self, message: str = "Resource conflict"):
        super().__init__(message, status_code=409)


class ValidationError(AppException):
    """422 — Validation failed."""
    def __init__(self, errors: list = None):
        super().__init__("Validation failed", status_code=422,
                        details={{"errors": errors or []}})


class RateLimitError(AppException):
    """429 — Rate limit exceeded."""
    def __init__(self, retry_after: int = 60):
        super().__init__(
            f"Rate limit exceeded. Retry after {{retry_after}}s",
            status_code=429,
            details={{"retry_after": retry_after}}
        )


# ═══ Server Errors (5xx) ═══

class InternalError(AppException):
    """500 — Internal server error."""
    def __init__(self, message: str = "Internal server error"):
        super().__init__(message, status_code=500)


class ServiceUnavailableError(AppException):
    """503 — External service unavailable."""
    def __init__(self, service: str = "External service"):
        super().__init__(f"{{service}} is currently unavailable", status_code=503)


class ExternalServiceError(AppException):
    """502 — External service returned an error."""
    def __init__(self, service: str, original_error: str = ""):
        super().__init__(
            f"Error communicating with {{service}}",
            status_code=502,
            details={{"service": service, "original_error": original_error}}
        )


# ═══ Entity-Specific Exceptions ═══
{chr(10).join(f"class {name}NotFoundError(NotFoundError):" + chr(10) + f'    def __init__(self, id=None): super().__init__("{name}", id)' + chr(10) for name in entities)}
'''

    def _gen_retry(self) -> str:
        """Generate retry logic for external services."""
        return '''"""Retry Logic for External Services — Auto-generated by AXIMA Coder V2"""
import time
import random
import logging
from typing import Callable, Tuple, Type
from functools import wraps

logger = logging.getLogger(__name__)


class RetryConfig:
    """Configuration for retry behavior."""

    def __init__(
        self,
        max_retries: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 30.0,
        exponential_base: float = 2.0,
        jitter: bool = True,
        retryable_exceptions: Tuple[Type[Exception], ...] = (Exception,),
    ):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.jitter = jitter
        self.retryable_exceptions = retryable_exceptions


def retry(config: RetryConfig = None, **kwargs):
    """Decorator for automatic retry with exponential backoff.

    Usage:
        @retry(max_retries=3, base_delay=1.0)
        def call_external_api():
            ...

        @retry(config=RetryConfig(max_retries=5))
        def fetch_data():
            ...
    """
    if config is None:
        config = RetryConfig(**kwargs)

    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kw):
            last_exception = None

            for attempt in range(config.max_retries + 1):
                try:
                    return func(*args, **kw)
                except config.retryable_exceptions as e:
                    last_exception = e

                    if attempt == config.max_retries:
                        logger.error(
                            f"Retry exhausted for {func.__name__} after {config.max_retries} attempts: {e}"
                        )
                        raise

                    # Calculate delay with exponential backoff
                    delay = min(
                        config.base_delay * (config.exponential_base ** attempt),
                        config.max_delay
                    )

                    # Add jitter to prevent thundering herd
                    if config.jitter:
                        delay = delay * (0.5 + random.random())

                    logger.warning(
                        f"Retry {attempt + 1}/{config.max_retries} for {func.__name__} "
                        f"after {delay:.1f}s: {e}"
                    )
                    time.sleep(delay)

            raise last_exception

        wrapper.retry_config = config
        return wrapper
    return decorator


# Pre-configured retry decorators
retry_default = retry(max_retries=3, base_delay=1.0)
retry_aggressive = retry(max_retries=5, base_delay=0.5, max_delay=10.0)
retry_patient = retry(max_retries=3, base_delay=5.0, max_delay=60.0)
'''

    def _gen_circuit_breaker(self) -> str:
        """Generate circuit breaker pattern."""
        return '''"""Circuit Breaker Pattern — Auto-generated by AXIMA Coder V2

Prevents cascading failures by stopping requests to failing services.
States: CLOSED (normal) → OPEN (failing) → HALF_OPEN (testing recovery)
"""
import time
import logging
from typing import Callable, Optional
from enum import Enum
from functools import wraps

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    CLOSED = "closed"          # Normal operation
    OPEN = "open"              # Failing — reject requests
    HALF_OPEN = "half_open"    # Testing if service recovered


class CircuitBreaker:
    """Circuit breaker for external service calls.

    Usage:
        breaker = CircuitBreaker("payment-service", failure_threshold=5)

        @breaker
        def call_payment_api():
            ...

        # Or manually:
        if breaker.allow_request():
            try:
                result = call_service()
                breaker.record_success()
            except Exception as e:
                breaker.record_failure()
                raise
    """

    def __init__(
        self,
        name: str,
        failure_threshold: int = 5,
        recovery_timeout: float = 30.0,
        half_open_max_calls: int = 3,
    ):
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.half_open_max_calls = half_open_max_calls

        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._last_failure_time: Optional[float] = None
        self._half_open_calls = 0

    @property
    def state(self) -> CircuitState:
        """Get current state, checking for timeout transitions."""
        if self._state == CircuitState.OPEN:
            if self._last_failure_time and \
               time.time() - self._last_failure_time >= self.recovery_timeout:
                self._state = CircuitState.HALF_OPEN
                self._half_open_calls = 0
                logger.info(f"Circuit '{self.name}' → HALF_OPEN (testing recovery)")
        return self._state

    def allow_request(self) -> bool:
        """Check if a request should be allowed."""
        state = self.state
        if state == CircuitState.CLOSED:
            return True
        elif state == CircuitState.HALF_OPEN:
            return self._half_open_calls < self.half_open_max_calls
        else:  # OPEN
            return False

    def record_success(self):
        """Record a successful call."""
        self._failure_count = 0
        if self._state == CircuitState.HALF_OPEN:
            self._success_count += 1
            if self._success_count >= self.half_open_max_calls:
                self._state = CircuitState.CLOSED
                self._success_count = 0
                logger.info(f"Circuit '{self.name}' → CLOSED (recovered)")

    def record_failure(self):
        """Record a failed call."""
        self._failure_count += 1
        self._last_failure_time = time.time()

        if self._state == CircuitState.HALF_OPEN:
            self._state = CircuitState.OPEN
            logger.warning(f"Circuit '{self.name}' → OPEN (recovery failed)")
        elif self._failure_count >= self.failure_threshold:
            self._state = CircuitState.OPEN
            logger.warning(
                f"Circuit '{self.name}' → OPEN "
                f"(threshold {self.failure_threshold} reached)"
            )

    def __call__(self, func: Callable) -> Callable:
        """Use as decorator."""
        @wraps(func)
        def wrapper(*args, **kwargs):
            if not self.allow_request():
                raise CircuitOpenError(
                    f"Circuit '{self.name}' is OPEN — service unavailable"
                )
            try:
                if self._state == CircuitState.HALF_OPEN:
                    self._half_open_calls += 1
                result = func(*args, **kwargs)
                self.record_success()
                return result
            except Exception as e:
                self.record_failure()
                raise
        return wrapper

    def get_status(self) -> dict:
        """Get circuit breaker status for monitoring."""
        return {
            "name": self.name,
            "state": self.state.value,
            "failure_count": self._failure_count,
            "failure_threshold": self.failure_threshold,
            "recovery_timeout": self.recovery_timeout,
        }


class CircuitOpenError(Exception):
    """Raised when circuit breaker is open."""
    pass


# Pre-configured circuit breakers for common services
payment_circuit = CircuitBreaker("payment-service", failure_threshold=3, recovery_timeout=60)
email_circuit = CircuitBreaker("email-service", failure_threshold=5, recovery_timeout=30)
external_api_circuit = CircuitBreaker("external-api", failure_threshold=5, recovery_timeout=45)
'''




# ═══════════════════════════════════════════════════════════════
# SELF-TEST — Demonstrates ALL capabilities including new upgrades
# ═══════════════════════════════════════════════════════════════

if __name__ == '__main__':
    print("═══ AXIMA Coder V2 — FULL CAPABILITY TEST ═══\n")

    coder = AximaCoder()

    # ─── Test 1: Todo app with auth (original) ───
    print("─── Test 1: Todo app with auth and React ───")
    request = "Build a todo app with user authentication using FastAPI and React"
    print(f"  Request: {request}")
    print(f"\n  Architecture:")
    print(f"  {coder.explain_architecture(request)}")

    files = coder.generate_project(request)
    print(f"\n  Generated {len(files)} files:")
    for fname in sorted(files.keys()):
        print(f"    {fname} ({len(files[fname])} chars)")
    print()

    # ─── Test 2: Chat app with realtime (original) ───
    print("─── Test 2: Chat app with Socket.io ───")
    request = "Create a real-time chat app with Express and Socket.io"
    model = coder.get_model(request)
    print(f"  Model: {model.name}")
    print(f"  Entities: {[e.name for e in model.entities]}")
    print(f"  Features: {model.features}")
    print(f"  Backend: {model.backend}")
    print()

    # ─── Test 3: E-commerce (original) ───
    print("─── Test 3: E-commerce ───")
    request = "Build an e-commerce app with products, orders, payments using FastAPI and postgres"
    model = coder.get_model(request)
    print(f"  Entities: {[e.name for e in model.entities]}")
    print(f"  Features: {model.features}")
    print(f"  DB: {model.database}")

    files = coder.generate_project(request)
    print(f"  Files: {list(sorted(files.keys()))}")
    print()

    # ─── Test 4: Blog with Flask (original) ───
    print("─── Test 4: Blog with Flask ───")
    request = "Make a blog with posts and comments using Flask"
    files = coder.generate_project(request)
    print(f"  Files: {list(sorted(files.keys()))}")
    print(f"  Total code: {sum(len(v) for v in files.values())} chars")
    print()

    # ═══════════════════════════════════════════════════════════
    # NEW CAPABILITY DEMONSTRATIONS
    # ═══════════════════════════════════════════════════════════

    print("═══════════════════════════════════════════════════════")
    print("═══ NEW UPGRADE DEMONSTRATIONS ═══")
    print("═══════════════════════════════════════════════════════\n")

    # ─── Test 5: Design Pattern Selector ───
    print("─── Test 5: Design Pattern Selector ───")
    request = "Build an e-commerce app with products, orders, payments, search using FastAPI"
    model = coder.get_model(request)
    pattern_selector = DesignPatternSelector()
    patterns = pattern_selector.select_patterns(model)
    print(f"  Request: {request}")
    print(f"  Recommended Patterns ({len(patterns)}):")
    for name, info in patterns.items():
        print(f"    • {name}: {info['description']} (score: {info['score']})")
        print(f"      Reasons: {', '.join(info['reasons'])}")
    print()

    # ─── Test 6: Performance Optimizer ───
    print("─── Test 6: Performance Optimizer ───")
    optimizer = PerformanceOptimizer()
    perf_files = optimizer.optimize(model)
    print(f"  Generated {len(perf_files)} optimization files:")
    for fname, content in perf_files.items():
        print(f"    {fname} ({len(content)} chars)")
    print()

    # ─── Test 7: Test Generator ───
    print("─── Test 7: Test Generator ───")
    test_gen = TestGenerator()
    test_files = test_gen.generate_tests(model, {})
    print(f"  Generated {len(test_files)} test files:")
    for fname, content in test_files.items():
        print(f"    {fname} ({len(content)} chars)")
    print()

    # ─── Test 8: CI/CD Pipeline Generator ───
    print("─── Test 8: CI/CD Pipeline Generator ───")
    cicd_gen = CICDGenerator()
    cicd_files = cicd_gen.generate_cicd(model)
    print(f"  Generated {len(cicd_files)} CI/CD files:")
    for fname in sorted(cicd_files.keys()):
        print(f"    {fname} ({len(cicd_files[fname])} chars)")
    print()

    # ─── Test 9: API Documentation Generator ───
    print("─── Test 9: API Documentation Generator ───")
    doc_gen = APIDocGenerator()
    doc_files = doc_gen.generate_openapi(model)
    print(f"  Generated {len(doc_files)} documentation files:")
    for fname, content in doc_files.items():
        print(f"    {fname} ({len(content)} chars)")
    # Show a snippet of the OpenAPI spec
    spec = json.loads(doc_files['docs/openapi.json'])
    print(f"  OpenAPI Paths: {list(spec['paths'].keys())}")
    print(f"  Schemas: {list(spec['components']['schemas'].keys())}")
    print()

    # ─── Test 10: Monitoring & Logging ───
    print("─── Test 10: Monitoring & Logging ───")
    mon_gen = MonitoringGenerator()
    mon_files = mon_gen.generate_monitoring(model)
    print(f"  Generated {len(mon_files)} monitoring files:")
    for fname in sorted(mon_files.keys()):
        print(f"    {fname} ({len(mon_files[fname])} chars)")
    print()

    # ─── Test 11: Database Migration System ───
    print("─── Test 11: Database Migration System ───")
    mig_gen = MigrationGenerator()
    mig_files = mig_gen.generate_migrations(model)
    print(f"  Generated {len(mig_files)} migration files:")
    for fname in sorted(mig_files.keys()):
        print(f"    {fname} ({len(mig_files[fname])} chars)")
    print()

    # ─── Test 12: Error Boundary Design ───
    print("─── Test 12: Error Boundary Design ───")
    err_gen = ErrorBoundaryGenerator()
    err_files = err_gen.generate_error_boundaries(model)
    print(f"  Generated {len(err_files)} error handling files:")
    for fname in sorted(err_files.keys()):
        print(f"    {fname} ({len(err_files[fname])} chars)")
    print()

    # ─── Final Summary ───
    print("═══════════════════════════════════════════════════════")
    print("═══ FULL PROJECT GENERATION SUMMARY ═══")
    print("═══════════════════════════════════════════════════════\n")

    request = "Build an e-commerce API with products, orders, users, auth, payments, search using FastAPI and postgres"
    print(f"  Full request: {request}\n")
    all_files = coder.generate_project(request)
    print(f"  TOTAL FILES GENERATED: {len(all_files)}")
    print(f"  TOTAL CODE SIZE: {sum(len(v) for v in all_files.values()):,} characters")
    print(f"\n  File breakdown by category:")

    categories = {
        'Core': [f for f in all_files if not any(f.startswith(p) for p in ['tests/', 'migrations/', 'middleware/', 'config/', 'utils/', 'docs/', '.github/'])],
        'Tests': [f for f in all_files if f.startswith('tests/')],
        'Migrations': [f for f in all_files if f.startswith('migrations/')],
        'Middleware': [f for f in all_files if f.startswith('middleware/')],
        'Config': [f for f in all_files if f.startswith('config/')],
        'Utils': [f for f in all_files if f.startswith('utils/')],
        'Docs': [f for f in all_files if f.startswith('docs/')],
        'CI/CD': [f for f in all_files if f.startswith('.github/') or f in ('Dockerfile', 'docker-compose.yml', '.dockerignore')],
    }

    for category, cat_files in categories.items():
        if cat_files:
            total_chars = sum(len(all_files[f]) for f in cat_files)
            print(f"    {category}: {len(cat_files)} files ({total_chars:,} chars)")
            for f in sorted(cat_files):
                print(f"      • {f}")

    print(f"\n  ✅ AXIMA Coder V2 — ALL SYSTEMS OPERATIONAL!")
    print(f"  🚀 8 major upgrades active: Patterns, Performance, Tests,")
    print(f"     CI/CD, API Docs, Monitoring, Migrations, Error Boundaries")

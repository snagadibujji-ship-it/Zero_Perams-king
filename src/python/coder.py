"""
AXIMA CODER — Unified Code Generation Interface
Routes requests to the right engine:
  - Algorithm/snippet → codegen_engine (100+ algorithms, 15 languages)
  - Full project/app → axima_coder (36+ files with CI/CD, tests, monitoring)
  - Explain code → codegen_engine.explain_code
  - Debug error → codegen_engine.debug_error

One call: ax.code("build a todo app with React")
         ax.code("binary search in python")
         ax.code("explain this: def fib(n)...")
         ax.code("fix this error: TypeError...")
"""

import re
from typing import Dict, Optional, Tuple, Union
from dataclasses import dataclass, field


@dataclass
class CodeResult:
    """Result from any code generation."""
    kind: str           # "algorithm" | "project" | "explanation" | "debug"
    code: str           # The generated code (or main file content)
    language: str       # Programming language detected/used
    files: Dict[str, str] = field(default_factory=dict)  # For projects: filename→content
    explanation: str = ""  # For explain/debug: the explanation
    metadata: Dict = field(default_factory=dict)  # Extra info


class AximaCoderUnified:
    """
    Unified entry point for all code generation.
    
    Usage:
        coder = AximaCoderUnified()
        result = coder.code("binary search in python")
        result = coder.code("build a todo app with React")
        result = coder.code("explain: def fib(n)...")
        result = coder.code("fix: TypeError: 'NoneType'...")
    """

    def __init__(self):
        self._codegen = None
        self._axima_coder = None

    def _get_codegen(self):
        if self._codegen is None:
            import codegen_engine
            self._codegen = codegen_engine
        return self._codegen

    def _get_project_coder(self):
        if self._axima_coder is None:
            from axima_coder import AximaCoder
            self._axima_coder = AximaCoder()
        return self._axima_coder

    def code(self, request: str) -> CodeResult:
        """
        Main entry point. Routes to the right engine automatically.
        
        Examples:
            code("binary search in python")      → algorithm
            code("build a todo app with React")  → full project
            code("explain: def fib(n)...")        → explanation
            code("fix: TypeError...")             → debug
            code("build a landing page for a coffee shop") → HTML page
        """
        kind, lang = self._classify(request)

        if kind == "explain":
            return self._explain(request)
        elif kind == "debug":
            return self._debug(request)
        elif kind == "webpage":
            return self._webpage(request)
        elif kind == "project":
            return self._project(request)
        else:
            return self._algorithm(request, lang)

    def _classify(self, request: str) -> Tuple[str, str]:
        """Classify what kind of code request this is."""
        req = request.lower().strip()

        # EXPLAIN: starts with "explain" or contains code to explain
        if req.startswith(('explain', 'what does', 'how does')):
            return "explain", ""
        if 'explain' in req and ('def ' in request or 'function' in request or 'class ' in request):
            return "explain", ""

        # DEBUG: error messages, fix requests
        if req.startswith(('fix', 'debug', 'error')):
            return "debug", ""
        if any(err in req for err in ['error:', 'traceback', 'exception', 'typeerror', 'syntaxerror']):
            return "debug", ""

        # PROJECT: full app/website/API requests
        project_signals = [
            r'\b(build|create|make|scaffold|generate)\b.*\b(app|application|website|site|api|project|server|bot|game)\b',
            r'\b(todo|chat|blog|ecommerce|portfolio|dashboard|landing)\b.*\b(app|page|site)\b',
            r'\b(full.?stack|frontend|backend|microservice)\b',
            r'\b(react|vue|svelte|next|nuxt|flask|django|express|fastapi|nest)\b.*\b(app|project|api)\b',
            r'\b(build|create)\b.*\b(with|using)\b.*\b(react|vue|flask|django|express|firebase)\b',
        ]

        # WEBPAGE: single HTML page (landing page, website for X)
        webpage_signals = [
            r'\b(landing\s*page|web\s*page|webpage|html\s*page)\b',
            r'\b(build|create|make|generate)\b.*\b(page|website|site)\b.*\b(for|of)\b.*\b(a|an|my)\b',
            r'\b(website|site|page)\b.*\b(for|of)\b.*\b(coffee|restaurant|gym|salon|shop|agency|startup|portfolio|clinic)\b',
        ]
        for pattern in webpage_signals:
            if re.search(pattern, req):
                return "webpage", "html"

        for pattern in project_signals:
            if re.search(pattern, req):
                return "project", ""

        # ALGORITHM: everything else (sort, search, data structure, snippet)
        lang = self._detect_lang(req)
        return "algorithm", lang

    def _detect_lang(self, req: str) -> str:
        """Detect programming language from request."""
        langs = {
            'python': ['python', 'py'], 'javascript': ['javascript', 'js', 'node'],
            'typescript': ['typescript', 'ts'], 'java': ['java'],
            'cpp': ['c++', 'cpp'], 'c': [' c '], 'rust': ['rust'],
            'go': ['golang', ' go '], 'ruby': ['ruby'],
            'swift': ['swift'], 'kotlin': ['kotlin'],
            'csharp': ['c#', 'csharp'], 'php': ['php'],
            'r': [' r '], 'sql': ['sql'],
        }
        for lang, keywords in langs.items():
            for kw in keywords:
                if kw in req.lower():
                    return lang
        return "python"  # default

    def _algorithm(self, request: str, lang: str) -> CodeResult:
        """Generate algorithm/snippet."""
        cg = self._get_codegen()
        result = cg.generate_code(request)

        if isinstance(result, tuple):
            code, detected_lang, info = result[0], result[1], result[2] if len(result) > 2 else ""
        else:
            code, detected_lang, info = str(result), lang, ""

        return CodeResult(
            kind="algorithm",
            code=code,
            language=detected_lang or lang,
            explanation=info if isinstance(info, str) else "",
            metadata={"source": "codegen_engine"}
        )

    def _project(self, request: str) -> CodeResult:
        """Generate full project."""
        pc = self._get_project_coder()
        files = pc.generate_project(request)

        # Find the main file
        main_candidates = ['main.py', 'app.py', 'index.js', 'App.jsx', 'server.js']
        main_content = ""
        for candidate in main_candidates:
            if candidate in files:
                main_content = files[candidate]
                break
        if not main_content and files:
            main_content = list(files.values())[0]

        return CodeResult(
            kind="project",
            code=main_content,
            language="python",  # primary
            files=files,
            explanation=f"Generated {len(files)} files. Run with appropriate tooling.",
            metadata={"file_count": len(files), "source": "axima_coder"}
        )

    def _explain(self, request: str) -> CodeResult:
        """Explain code."""
        cg = self._get_codegen()
        # Extract the code from the request
        code = request
        for prefix in ['explain:', 'explain this:', 'what does this do:', 'how does this work:']:
            if request.lower().startswith(prefix):
                code = request[len(prefix):].strip()
                break

        explanation = cg.explain_code(code)
        return CodeResult(
            kind="explanation",
            code=code,
            language=self._detect_lang(code),
            explanation=explanation if isinstance(explanation, str) else str(explanation),
            metadata={"source": "codegen_engine"}
        )

    def _debug(self, request: str) -> CodeResult:
        """Debug an error."""
        cg = self._get_codegen()
        result = cg.debug_error(request)

        if isinstance(result, tuple):
            fix, explanation = result[0], result[1] if len(result) > 1 else ""
        else:
            fix, explanation = str(result), ""

        return CodeResult(
            kind="debug",
            code=fix if isinstance(fix, str) else str(fix),
            language="python",
            explanation=explanation if isinstance(explanation, str) else str(explanation),
            metadata={"source": "codegen_engine"}
        )

    def _webpage(self, request: str) -> CodeResult:
        """Generate a single-file HTML website."""
        from web_generator import get_web_generator
        wb = get_web_generator()
        project = wb.generate(request)
        html = project.get_full_html()
        return CodeResult(
            kind="webpage",
            code=html,
            language="html",
            files={"index.html": html},
            explanation=f"Complete {project.framework} page ({len(html)} chars). Open index.html in browser.",
            metadata={"source": "web_generator", "framework": project.framework, "project": project}
        )


def get_coder():
    """Get the unified coder instance."""
    return AximaCoderUnified()

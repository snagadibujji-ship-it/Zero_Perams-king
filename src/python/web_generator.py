"""
AXIMA Web Builder v2 — Like Replit/Lovable/Bolt/v0
Built by: Ghias + Kiro | 2026

CAPABILITIES:
  1. Generate ANY type of web project (React, Three.js, vanilla, Tailwind)
  2. EDIT existing output (change colors, add sections, modify content)
  3. Modern components (parallax, 3D, glassmorphism, animations)
  4. Iterative — user keeps modifying until happy

Usage:
  wb = WebBuilder()
  result = wb.generate("build a 3D portfolio with Three.js")
  result = wb.edit(result, "change background to dark purple")
  result = wb.edit(result, "add a contact form section")
"""

import re
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field


# ═══════════════════════════════════════════════════════════════
# DATA MODELS
# ═══════════════════════════════════════════════════════════════

@dataclass
class WebProject:
    """Complete web project state — can be edited iteratively."""
    html: str = ""
    css: str = ""
    js: str = ""
    framework: str = "vanilla"  # vanilla/react/threejs/vue/svelte
    spec: Dict = field(default_factory=dict)
    history: List[str] = field(default_factory=list)  # edit history

    def get_full_html(self) -> str:
        """Get deployable single-file HTML."""
        if self.framework == "react":
            return self._react_html()
        elif self.framework == "threejs":
            return self._threejs_html()
        else:
            return self._vanilla_html()

    def _vanilla_html(self) -> str:
        return f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{self.spec.get('name', 'My Site')}</title>
<style>
{self.css}
</style>
</head>
<body>
{self.html}
<script>
{self.js}
</script>
</body>
</html>'''

    def _react_html(self) -> str:
        return f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{self.spec.get('name', 'My App')}</title>
<script src="https://unpkg.com/react@18/umd/react.production.min.js"></script>
<script src="https://unpkg.com/react-dom@18/umd/react-dom.production.min.js"></script>
<script src="https://unpkg.com/@babel/standalone/babel.min.js"></script>
<style>
{self.css}
</style>
</head>
<body>
<div id="root"></div>
<script type="text/babel">
{self.js}
</script>
</body>
</html>'''

    def _threejs_html(self) -> str:
        return f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{self.spec.get('name', '3D Scene')}</title>
<style>
{self.css}
</style>
</head>
<body>
{self.html}
<script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/controls/OrbitControls.js"></script>
<script>
{self.js}
</script>
</body>
</html>'''


# ═══════════════════════════════════════════════════════════════
# FRAMEWORK DETECTOR
# ═══════════════════════════════════════════════════════════════

class FrameworkDetector:
    """Detect which framework/approach to use."""

    def detect(self, request: str) -> str:
        req = request.lower()
        if any(w in req for w in ['three.js', 'threejs', '3d', '3js', 'webgl', 'orbit']):
            return "threejs"
        if any(w in req for w in ['react', 'jsx', 'component', 'useState', 'hooks']):
            return "react"
        if any(w in req for w in ['vue', 'vuejs']):
            return "vue"
        if any(w in req for w in ['svelte']):
            return "svelte"
        return "vanilla"


# ═══════════════════════════════════════════════════════════════
# COLOR ENGINE
# ═══════════════════════════════════════════════════════════════

class ColorEngine:
    """Modern color palettes + custom color support."""

    PALETTES = {
        "warm": {"primary": "#c8553d", "secondary": "#f28f3b", "bg": "#fefae0", "text": "#2b2d42", "accent": "#588b8b", "surface": "#ffffff"},
        "cool": {"primary": "#2563eb", "secondary": "#7c3aed", "bg": "#f8fafc", "text": "#1e293b", "accent": "#06b6d4", "surface": "#ffffff"},
        "dark": {"primary": "#8b5cf6", "secondary": "#ec4899", "bg": "#0f172a", "text": "#f1f5f9", "accent": "#22d3ee", "surface": "#1e293b"},
        "nature": {"primary": "#16a34a", "secondary": "#65a30d", "bg": "#f0fdf4", "text": "#1a2e05", "accent": "#84cc16", "surface": "#ffffff"},
        "vibrant": {"primary": "#dc2626", "secondary": "#f97316", "bg": "#fffbeb", "text": "#1c1917", "accent": "#eab308", "surface": "#ffffff"},
        "ocean": {"primary": "#0891b2", "secondary": "#06b6d4", "bg": "#ecfeff", "text": "#164e63", "accent": "#67e8f9", "surface": "#ffffff"},
        "sunset": {"primary": "#e11d48", "secondary": "#f97316", "bg": "#fff1f2", "text": "#1c1917", "accent": "#fb923c", "surface": "#ffffff"},
        "midnight": {"primary": "#6366f1", "secondary": "#a855f7", "bg": "#020617", "text": "#e2e8f0", "accent": "#818cf8", "surface": "#1e1b4b"},
        "forest": {"primary": "#15803d", "secondary": "#4d7c0f", "bg": "#052e16", "text": "#dcfce7", "accent": "#86efac", "surface": "#14532d"},
        "neon": {"primary": "#00ff88", "secondary": "#00ccff", "bg": "#0a0a0a", "text": "#ffffff", "accent": "#ff00ff", "surface": "#1a1a2e"},
    }

    # Named colors for user requests like "change to blue"
    COLOR_MAP = {
        "red": "#dc2626", "blue": "#2563eb", "green": "#16a34a", "purple": "#7c3aed",
        "pink": "#ec4899", "orange": "#f97316", "yellow": "#eab308", "cyan": "#06b6d4",
        "teal": "#0d9488", "indigo": "#4f46e5", "rose": "#e11d48", "emerald": "#10b981",
        "violet": "#8b5cf6", "amber": "#d97706", "lime": "#65a30d", "sky": "#0284c7",
        "black": "#0a0a0a", "white": "#ffffff", "gray": "#6b7280", "slate": "#475569",
    }

    def get_palette(self, request: str) -> Dict[str, str]:
        req = request.lower()
        for name, palette in self.PALETTES.items():
            if name in req:
                return palette
        # Check for specific color mentions
        if any(w in req for w in ['dark', 'black', 'night']): return self.PALETTES["dark"]
        if any(w in req for w in ['neon', 'cyberpunk', 'glow']): return self.PALETTES["neon"]
        if any(w in req for w in ['ocean', 'sea', 'water']): return self.PALETTES["ocean"]
        if any(w in req for w in ['sunset', 'warm', 'fire']): return self.PALETTES["sunset"]
        return self.PALETTES["cool"]

    def change_color(self, css: str, what: str, to_color: str) -> str:
        """Change a specific color in existing CSS."""
        # Resolve color name to hex
        color_hex = self.COLOR_MAP.get(to_color, to_color)
        if not color_hex.startswith('#'):
            color_hex = self.COLOR_MAP.get(color_hex, '#2563eb')

        if what in ('primary', 'main', 'brand'):
            css = re.sub(r'--primary:\s*[^;]+;', f'--primary: {color_hex};', css)
        elif what in ('secondary', 'accent'):
            css = re.sub(r'--secondary:\s*[^;]+;', f'--secondary: {color_hex};', css)
        elif what in ('background', 'bg'):
            css = re.sub(r'--bg:\s*[^;]+;', f'--bg: {color_hex};', css)
        elif what in ('text', 'font'):
            css = re.sub(r'--text:\s*[^;]+;', f'--text: {color_hex};', css)
        else:
            # Change primary by default
            css = re.sub(r'--primary:\s*[^;]+;', f'--primary: {color_hex};', css)
        return css


# ═══════════════════════════════════════════════════════════════
# COMPONENT LIBRARY
# ═══════════════════════════════════════════════════════════════

class ComponentLibrary:
    """Modern web components — all the pieces to build any site."""

    def nav(self, name: str, links: List[str], style: str = "glass") -> str:
        link_html = ''.join(f'<a href="#{l.lower()}">{l}</a>' for l in links)
        return f'''<nav class="navbar {'glass' if style == 'glass' else ''}">
    <div class="nav-brand">{name}</div>
    <div class="nav-links">{link_html}</div>
    <button class="nav-toggle" onclick="document.querySelector('.nav-links').classList.toggle('active')">&#9776;</button>
</nav>'''

    def hero_gradient(self, title: str, subtitle: str, cta: str = "Get Started") -> str:
        return f'''<section class="hero hero-gradient">
    <div class="hero-content">
        <h1 class="hero-title animate-in">{title}</h1>
        <p class="hero-subtitle animate-in">{subtitle}</p>
        <button class="btn btn-primary animate-in">{cta}</button>
    </div>
    <div class="hero-shapes">
        <div class="shape shape-1"></div>
        <div class="shape shape-2"></div>
        <div class="shape shape-3"></div>
    </div>
</section>'''

    def hero_video(self, title: str, subtitle: str) -> str:
        return f'''<section class="hero hero-video">
    <div class="hero-overlay"></div>
    <div class="hero-content">
        <h1 class="hero-title">{title}</h1>
        <p class="hero-subtitle">{subtitle}</p>
    </div>
</section>'''

    def hero_3d(self, title: str) -> str:
        return f'''<section class="hero hero-3d">
    <canvas id="hero-canvas"></canvas>
    <div class="hero-content">
        <h1 class="hero-title">{title}</h1>
    </div>
</section>'''

    def features_grid(self, features: List[Tuple[str, str, str]]) -> str:
        """features = [(icon_emoji, title, desc), ...]"""
        cards = ''.join(f'''<div class="feature-card">
        <div class="feature-icon">{icon}</div>
        <h3>{title}</h3>
        <p>{desc}</p>
    </div>''' for icon, title, desc in features)
        return f'''<section class="features" id="features">
    <h2 class="section-title">Features</h2>
    <div class="features-grid">{cards}</div>
</section>'''

    def pricing_cards(self, plans: List[Tuple[str, str, List[str]]]) -> str:
        """plans = [(name, price, [features]), ...]"""
        cards = ''
        for i, (name, price, feats) in enumerate(plans):
            popular = ' popular' if i == 1 else ''
            feat_html = ''.join(f'<li>{f}</li>' for f in feats)
            cards += f'''<div class="pricing-card{popular}">
        {'<span class="badge">Most Popular</span>' if i == 1 else ''}
        <h3>{name}</h3>
        <div class="price">{price}</div>
        <ul>{feat_html}</ul>
        <button class="btn btn-{'primary' if i == 1 else 'outline'}">Choose Plan</button>
    </div>'''
        return f'''<section class="pricing" id="pricing">
    <h2 class="section-title">Pricing</h2>
    <div class="pricing-grid">{cards}</div>
</section>'''

    def testimonials(self, items: List[Tuple[str, str, str]]) -> str:
        """items = [(quote, name, role), ...]"""
        cards = ''.join(f'''<div class="testimonial-card">
        <p class="quote">"{quote}"</p>
        <div class="author"><strong>{name}</strong><span>{role}</span></div>
    </div>''' for quote, name, role in items)
        return f'''<section class="testimonials" id="testimonials">
    <h2 class="section-title">What People Say</h2>
    <div class="testimonials-grid">{cards}</div>
</section>'''

    def contact_form(self) -> str:
        return '''<section class="contact" id="contact">
    <h2 class="section-title">Get In Touch</h2>
    <form class="form" onsubmit="handleSubmit(event)">
        <div class="form-row">
            <input type="text" placeholder="Name" required>
            <input type="email" placeholder="Email" required>
        </div>
        <textarea placeholder="Message" rows="5" required></textarea>
        <button type="submit" class="btn btn-primary">Send Message</button>
    </form>
</section>'''

    def gallery(self, count: int = 6) -> str:
        items = ''.join(f'<div class="gallery-item"><div class="gallery-placeholder">Image {i+1}</div></div>' for i in range(count))
        return f'''<section class="gallery" id="gallery">
    <h2 class="section-title">Gallery</h2>
    <div class="gallery-grid">{items}</div>
</section>'''

    def footer(self, name: str) -> str:
        return f'''<footer class="footer">
    <div class="footer-content">
        <div class="footer-brand">{name}</div>
        <div class="footer-links">
            <a href="#">Privacy</a>
            <a href="#">Terms</a>
            <a href="#">Contact</a>
        </div>
    </div>
    <p class="footer-copy">&copy; 2026 {name}. All rights reserved.</p>
</footer>'''

    def parallax_section(self, title: str, text: str) -> str:
        return f'''<section class="parallax-section">
    <div class="parallax-bg"></div>
    <div class="parallax-content">
        <h2>{title}</h2>
        <p>{text}</p>
    </div>
</section>'''

    def stats(self, items: List[Tuple[str, str]]) -> str:
        """items = [(number, label), ...]"""
        cards = ''.join(f'<div class="stat"><div class="stat-number">{num}</div><div class="stat-label">{label}</div></div>' for num, label in items)
        return f'''<section class="stats">{cards}</section>'''


# ═══════════════════════════════════════════════════════════════
# CSS GENERATOR
# ═══════════════════════════════════════════════════════════════

class CSSGenerator:
    """Generate full CSS from palette + framework."""

    def generate(self, palette: Dict[str, str], framework: str) -> str:
        base = self._base_css(palette)
        components = self._component_css(palette)
        animations = self._animation_css()
        return base + components + animations

    def _base_css(self, p: Dict) -> str:
        return f'''* {{ margin: 0; padding: 0; box-sizing: border-box; }}
:root {{
    --primary: {p['primary']}; --secondary: {p['secondary']};
    --bg: {p['bg']}; --text: {p['text']};
    --accent: {p['accent']}; --surface: {p['surface']};
    --radius: 12px; --shadow: 0 4px 30px rgba(0,0,0,0.1);
}}
html {{ scroll-behavior: smooth; }}
body {{ font-family: 'Inter', system-ui, sans-serif; background: var(--bg); color: var(--text); line-height: 1.6; overflow-x: hidden; }}
h1,h2,h3 {{ line-height: 1.2; }}
a {{ color: var(--primary); text-decoration: none; }}
.btn {{ display: inline-flex; align-items: center; gap: 0.5rem; padding: 0.875rem 2rem; border-radius: var(--radius); font-weight: 600; font-size: 1rem; cursor: pointer; transition: all 0.3s ease; border: none; }}
.btn-primary {{ background: var(--primary); color: white; }}
.btn-primary:hover {{ transform: translateY(-2px); box-shadow: 0 10px 40px {p['primary']}40; }}
.btn-outline {{ background: transparent; border: 2px solid var(--primary); color: var(--primary); }}
.btn-outline:hover {{ background: var(--primary); color: white; }}
.section-title {{ font-size: clamp(2rem, 4vw, 3rem); text-align: center; margin-bottom: 3rem; }}
'''

    def _component_css(self, p: Dict) -> str:
        is_dark = p['bg'].startswith('#0') or p['bg'].startswith('#1') or p['bg'] == '#020617'
        glass_bg = 'rgba(255,255,255,0.05)' if is_dark else 'rgba(255,255,255,0.8)'
        glass_border = 'rgba(255,255,255,0.1)' if is_dark else 'rgba(0,0,0,0.05)'

        return f'''
/* Navbar */
.navbar {{ position: fixed; top: 0; width: 100%; padding: 1rem 2rem; display: flex; justify-content: space-between; align-items: center; z-index: 1000; background: {glass_bg}; backdrop-filter: blur(20px); border-bottom: 1px solid {glass_border}; }}
.navbar.glass {{ background: {glass_bg}; }}
.nav-brand {{ font-size: 1.5rem; font-weight: 800; background: linear-gradient(135deg, var(--primary), var(--secondary)); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }}
.nav-links {{ display: flex; gap: 2rem; }}
.nav-links a {{ color: var(--text); font-weight: 500; transition: color 0.3s; }}
.nav-links a:hover {{ color: var(--primary); }}
.nav-toggle {{ display: none; background: none; border: none; font-size: 1.5rem; color: var(--text); cursor: pointer; }}

/* Hero */
.hero {{ min-height: 100vh; display: flex; align-items: center; justify-content: center; text-align: center; position: relative; padding: 6rem 2rem; overflow: hidden; }}
.hero-gradient {{ background: linear-gradient(135deg, var(--bg) 0%, var(--surface) 100%); }}
.hero-content {{ position: relative; z-index: 2; max-width: 800px; }}
.hero-title {{ font-size: clamp(3rem, 8vw, 6rem); font-weight: 900; margin-bottom: 1.5rem; background: linear-gradient(135deg, var(--primary), var(--secondary)); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }}
.hero-subtitle {{ font-size: 1.25rem; opacity: 0.7; margin-bottom: 2.5rem; max-width: 600px; margin-left: auto; margin-right: auto; }}
.hero-shapes {{ position: absolute; inset: 0; overflow: hidden; }}
.shape {{ position: absolute; border-radius: 50%; opacity: 0.1; }}
.shape-1 {{ width: 600px; height: 600px; background: var(--primary); top: -200px; right: -200px; animation: float 8s ease-in-out infinite; }}
.shape-2 {{ width: 400px; height: 400px; background: var(--secondary); bottom: -100px; left: -100px; animation: float 6s ease-in-out infinite reverse; }}
.shape-3 {{ width: 300px; height: 300px; background: var(--accent); top: 50%; left: 50%; animation: float 10s ease-in-out infinite; }}

/* Hero 3D */
.hero-3d {{ position: relative; }}
.hero-3d canvas {{ position: absolute; inset: 0; width: 100%; height: 100%; }}

/* Features */
.features {{ padding: 6rem 2rem; }}
.features-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 2rem; max-width: 1200px; margin: 0 auto; }}
.feature-card {{ background: var(--surface); padding: 2.5rem; border-radius: var(--radius); box-shadow: var(--shadow); transition: transform 0.3s, box-shadow 0.3s; border: 1px solid {glass_border}; }}
.feature-card:hover {{ transform: translateY(-8px); box-shadow: 0 20px 60px rgba(0,0,0,0.15); }}
.feature-icon {{ font-size: 2.5rem; margin-bottom: 1rem; }}
.feature-card h3 {{ margin-bottom: 0.5rem; font-size: 1.25rem; }}
.feature-card p {{ opacity: 0.7; }}

/* Pricing */
.pricing {{ padding: 6rem 2rem; }}
.pricing-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 2rem; max-width: 1000px; margin: 0 auto; align-items: start; }}
.pricing-card {{ background: var(--surface); padding: 2.5rem; border-radius: var(--radius); box-shadow: var(--shadow); text-align: center; border: 1px solid {glass_border}; transition: transform 0.3s; }}
.pricing-card.popular {{ border: 2px solid var(--primary); transform: scale(1.05); }}
.pricing-card .badge {{ background: var(--primary); color: white; padding: 0.25rem 1rem; border-radius: 99px; font-size: 0.75rem; font-weight: 600; display: inline-block; margin-bottom: 1rem; }}
.pricing-card .price {{ font-size: 3rem; font-weight: 900; color: var(--primary); margin: 1rem 0; }}
.pricing-card ul {{ list-style: none; margin: 1.5rem 0; text-align: left; }}
.pricing-card ul li {{ padding: 0.5rem 0; border-bottom: 1px solid {glass_border}; }}
.pricing-card ul li::before {{ content: "✓ "; color: var(--primary); font-weight: 700; }}

/* Testimonials */
.testimonials {{ padding: 6rem 2rem; }}
.testimonials-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 2rem; max-width: 1200px; margin: 0 auto; }}
.testimonial-card {{ background: var(--surface); padding: 2rem; border-radius: var(--radius); box-shadow: var(--shadow); border: 1px solid {glass_border}; }}
.testimonial-card .quote {{ font-style: italic; margin-bottom: 1.5rem; font-size: 1.05rem; opacity: 0.8; }}
.testimonial-card .author strong {{ display: block; }}
.testimonial-card .author span {{ opacity: 0.6; font-size: 0.875rem; }}

/* Contact */
.contact {{ padding: 6rem 2rem; }}
.form {{ max-width: 600px; margin: 0 auto; display: flex; flex-direction: column; gap: 1rem; }}
.form-row {{ display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; }}
.form input, .form textarea {{ padding: 1rem; border: 2px solid {glass_border}; border-radius: var(--radius); font-size: 1rem; background: var(--surface); color: var(--text); transition: border-color 0.3s; }}
.form input:focus, .form textarea:focus {{ outline: none; border-color: var(--primary); }}

/* Gallery */
.gallery {{ padding: 6rem 2rem; }}
.gallery-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 1rem; max-width: 1200px; margin: 0 auto; }}
.gallery-item {{ aspect-ratio: 4/3; border-radius: var(--radius); overflow: hidden; background: var(--surface); display: flex; align-items: center; justify-content: center; border: 1px solid {glass_border}; }}
.gallery-placeholder {{ opacity: 0.4; font-weight: 600; }}

/* Stats */
.stats {{ display: flex; justify-content: center; gap: 4rem; padding: 4rem 2rem; flex-wrap: wrap; }}
.stat {{ text-align: center; }}
.stat-number {{ font-size: 3rem; font-weight: 900; color: var(--primary); }}
.stat-label {{ opacity: 0.6; margin-top: 0.25rem; }}

/* Parallax */
.parallax-section {{ position: relative; padding: 8rem 2rem; text-align: center; overflow: hidden; }}
.parallax-bg {{ position: absolute; inset: 0; background: linear-gradient(135deg, var(--primary), var(--secondary)); opacity: 0.9; }}
.parallax-content {{ position: relative; z-index: 2; color: white; }}
.parallax-content h2 {{ font-size: 2.5rem; margin-bottom: 1rem; }}

/* Footer */
.footer {{ padding: 3rem 2rem; border-top: 1px solid {glass_border}; }}
.footer-content {{ display: flex; justify-content: space-between; align-items: center; max-width: 1200px; margin: 0 auto; }}
.footer-brand {{ font-size: 1.25rem; font-weight: 700; }}
.footer-links {{ display: flex; gap: 2rem; }}
.footer-links a {{ opacity: 0.6; transition: opacity 0.3s; }}
.footer-links a:hover {{ opacity: 1; }}
.footer-copy {{ text-align: center; opacity: 0.4; margin-top: 2rem; font-size: 0.875rem; }}

/* Responsive */
@media (max-width: 768px) {{
    .nav-links {{ display: none; position: absolute; top: 100%; left: 0; right: 0; background: var(--surface); flex-direction: column; padding: 2rem; gap: 1rem; box-shadow: var(--shadow); }}
    .nav-links.active {{ display: flex; }}
    .nav-toggle {{ display: block; }}
    .hero-title {{ font-size: 2.5rem; }}
    .form-row {{ grid-template-columns: 1fr; }}
    .stats {{ gap: 2rem; }}
    .footer-content {{ flex-direction: column; gap: 1rem; text-align: center; }}
    .pricing-card.popular {{ transform: scale(1); }}
}}
'''

    def _animation_css(self) -> str:
        return '''
/* Animations */
@keyframes float { 0%,100% { transform: translateY(0) rotate(0deg); } 50% { transform: translateY(-20px) rotate(5deg); } }
@keyframes fadeInUp { from { opacity: 0; transform: translateY(30px); } to { opacity: 1; transform: translateY(0); } }
.animate-in { animation: fadeInUp 0.8s ease forwards; }
.animate-in:nth-child(2) { animation-delay: 0.2s; }
.animate-in:nth-child(3) { animation-delay: 0.4s; }
.fade-in { opacity: 0; transform: translateY(20px); transition: all 0.6s ease; }
.fade-in.visible { opacity: 1; transform: translateY(0); }
'''


# ═══════════════════════════════════════════════════════════════
# THREE.JS SCENE GENERATOR
# ═══════════════════════════════════════════════════════════════

class ThreeJSGenerator:
    """Generate Three.js 3D scenes."""

    def generate(self, request: str) -> str:
        req = request.lower()
        if any(w in req for w in ['planet', 'earth', 'sphere', 'globe']):
            return self._planet_scene()
        elif any(w in req for w in ['cube', 'box', 'geometric']):
            return self._geometric_scene()
        elif any(w in req for w in ['particles', 'stars', 'space']):
            return self._particle_scene()
        else:
            return self._portfolio_scene()

    def _portfolio_scene(self) -> str:
        return '''const scene = new THREE.Scene();
const camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);
const renderer = new THREE.WebGLRenderer({ canvas: document.getElementById('hero-canvas'), alpha: true, antialias: true });
renderer.setSize(window.innerWidth, window.innerHeight);
renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));

// Floating geometric shapes
const shapes = [];
const geometries = [new THREE.IcosahedronGeometry(1), new THREE.OctahedronGeometry(1), new THREE.TorusGeometry(0.7, 0.3, 16, 32)];
const material = new THREE.MeshStandardMaterial({ color: 0x6366f1, metalness: 0.7, roughness: 0.2, wireframe: true });

for (let i = 0; i < 15; i++) {
    const geo = geometries[i % geometries.length];
    const mesh = new THREE.Mesh(geo, material.clone());
    mesh.position.set((Math.random()-0.5)*20, (Math.random()-0.5)*10, (Math.random()-0.5)*10 - 5);
    mesh.rotation.set(Math.random()*Math.PI, Math.random()*Math.PI, 0);
    mesh.scale.setScalar(0.3 + Math.random()*0.7);
    mesh.material.color.setHSL(0.6 + Math.random()*0.2, 0.8, 0.5);
    shapes.push(mesh);
    scene.add(mesh);
}

// Lighting
const ambient = new THREE.AmbientLight(0xffffff, 0.5);
scene.add(ambient);
const point = new THREE.PointLight(0x6366f1, 2, 50);
point.position.set(5, 5, 5);
scene.add(point);

camera.position.z = 8;

// Mouse interaction
let mouseX = 0, mouseY = 0;
document.addEventListener('mousemove', (e) => {
    mouseX = (e.clientX / window.innerWidth - 0.5) * 2;
    mouseY = (e.clientY / window.innerHeight - 0.5) * 2;
});

function animate() {
    requestAnimationFrame(animate);
    shapes.forEach((s, i) => {
        s.rotation.x += 0.005 + i*0.001;
        s.rotation.y += 0.003 + i*0.001;
        s.position.y += Math.sin(Date.now()*0.001 + i) * 0.002;
    });
    camera.position.x += (mouseX * 2 - camera.position.x) * 0.02;
    camera.position.y += (-mouseY * 2 - camera.position.y) * 0.02;
    camera.lookAt(scene.position);
    renderer.render(scene, camera);
}
animate();

window.addEventListener('resize', () => {
    camera.aspect = window.innerWidth / window.innerHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(window.innerWidth, window.innerHeight);
});'''

    def _particle_scene(self) -> str:
        return '''const scene = new THREE.Scene();
const camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);
const renderer = new THREE.WebGLRenderer({ canvas: document.getElementById('hero-canvas'), alpha: true });
renderer.setSize(window.innerWidth, window.innerHeight);

// Particle system
const count = 5000;
const positions = new Float32Array(count * 3);
const colors = new Float32Array(count * 3);
for (let i = 0; i < count * 3; i += 3) {
    positions[i] = (Math.random() - 0.5) * 50;
    positions[i+1] = (Math.random() - 0.5) * 50;
    positions[i+2] = (Math.random() - 0.5) * 50;
    colors[i] = 0.4 + Math.random() * 0.6;
    colors[i+1] = 0.2 + Math.random() * 0.3;
    colors[i+2] = 0.8 + Math.random() * 0.2;
}
const geometry = new THREE.BufferGeometry();
geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
geometry.setAttribute('color', new THREE.BufferAttribute(colors, 3));
const material = new THREE.PointsMaterial({ size: 0.05, vertexColors: true, transparent: true, opacity: 0.8 });
const particles = new THREE.Points(geometry, material);
scene.add(particles);

camera.position.z = 15;

function animate() {
    requestAnimationFrame(animate);
    particles.rotation.y += 0.001;
    particles.rotation.x += 0.0005;
    renderer.render(scene, camera);
}
animate();

window.addEventListener('resize', () => {
    camera.aspect = window.innerWidth / window.innerHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(window.innerWidth, window.innerHeight);
});'''

    def _planet_scene(self) -> str:
        return '''const scene = new THREE.Scene();
const camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);
const renderer = new THREE.WebGLRenderer({ canvas: document.getElementById('hero-canvas'), alpha: true, antialias: true });
renderer.setSize(window.innerWidth, window.innerHeight);

const sphere = new THREE.Mesh(
    new THREE.SphereGeometry(3, 64, 64),
    new THREE.MeshStandardMaterial({ color: 0x2563eb, metalness: 0.3, roughness: 0.7, wireframe: false })
);
scene.add(sphere);

// Atmosphere glow
const atmo = new THREE.Mesh(
    new THREE.SphereGeometry(3.2, 64, 64),
    new THREE.MeshBasicMaterial({ color: 0x06b6d4, transparent: true, opacity: 0.1, side: THREE.BackSide })
);
scene.add(atmo);

const light = new THREE.DirectionalLight(0xffffff, 1);
light.position.set(5, 3, 5);
scene.add(light);
scene.add(new THREE.AmbientLight(0xffffff, 0.3));

camera.position.z = 8;

function animate() {
    requestAnimationFrame(animate);
    sphere.rotation.y += 0.003;
    atmo.rotation.y -= 0.001;
    renderer.render(scene, camera);
}
animate();

window.addEventListener('resize', () => {
    camera.aspect = window.innerWidth / window.innerHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(window.innerWidth, window.innerHeight);
});'''

    def _geometric_scene(self) -> str:
        return self._portfolio_scene()


# ═══════════════════════════════════════════════════════════════
# REACT GENERATOR
# ═══════════════════════════════════════════════════════════════

class ReactGenerator:
    """Generate React component code."""

    def generate(self, spec: Dict) -> str:
        name = spec.get('name', 'MyApp')
        sections = spec.get('sections', ['hero', 'features', 'contact'])
        components = [self._component(s, spec) for s in sections]
        
        return f'''const {{ useState, useEffect }} = React;

{chr(10).join(components)}

function App() {{
    useEffect(() => {{
        // Scroll animation observer
        const observer = new IntersectionObserver((entries) => {{
            entries.forEach(e => {{ if(e.isIntersecting) e.target.classList.add('visible'); }});
        }}, {{ threshold: 0.1 }});
        document.querySelectorAll('.fade-in').forEach(el => observer.observe(el));
    }}, []);

    return (
        <div className="app">
            {''.join(f'<{s.capitalize()} />' for s in sections)}
            <Footer />
        </div>
    );
}}

function Footer() {{
    return <footer className="footer"><p>&copy; 2026 {name}</p></footer>;
}}

ReactDOM.render(<App />, document.getElementById('root'));'''

    def _component(self, section: str, spec: Dict) -> str:
        name = spec.get('name', 'App')
        if section == 'hero':
            return f'''function Hero() {{
    return (
        <section className="hero hero-gradient">
            <div className="hero-content">
                <h1 className="hero-title animate-in">{name}</h1>
                <p className="hero-subtitle animate-in">Build something amazing</p>
                <button className="btn btn-primary animate-in">Get Started</button>
            </div>
        </section>
    );
}}'''
        elif section == 'features':
            return '''function Features() {
    const features = [
        { icon: "⚡", title: "Lightning Fast", desc: "Optimized for speed" },
        { icon: "🔒", title: "Secure", desc: "Enterprise-grade security" },
        { icon: "🚀", title: "Scalable", desc: "Grows with you" },
    ];
    return (
        <section className="features fade-in" id="features">
            <h2 className="section-title">Features</h2>
            <div className="features-grid">
                {features.map((f,i) => (
                    <div key={i} className="feature-card">
                        <div className="feature-icon">{f.icon}</div>
                        <h3>{f.title}</h3>
                        <p>{f.desc}</p>
                    </div>
                ))}
            </div>
        </section>
    );
}'''
        elif section == 'contact':
            return '''function Contact() {
    const [sent, setSent] = useState(false);
    const handleSubmit = (e) => { e.preventDefault(); setSent(true); setTimeout(() => setSent(false), 2000); };
    return (
        <section className="contact fade-in" id="contact">
            <h2 className="section-title">Contact</h2>
            <form className="form" onSubmit={handleSubmit}>
                <div className="form-row"><input placeholder="Name" required /><input type="email" placeholder="Email" required /></div>
                <textarea placeholder="Message" rows="5" required></textarea>
                <button className="btn btn-primary" type="submit">{sent ? "Sent! ✓" : "Send"}</button>
            </form>
        </section>
    );
}'''
        else:
            return f'''function {section.capitalize()}() {{
    return <section className="fade-in" id="{section}"><h2 className="section-title">{section.capitalize()}</h2></section>;
}}'''


# ═══════════════════════════════════════════════════════════════
# EDIT ENGINE — Modify existing projects
# ═══════════════════════════════════════════════════════════════

class EditEngine:
    """Edit existing WebProject based on user commands."""

    def __init__(self):
        self.color_engine = ColorEngine()
        self.components = ComponentLibrary()

    def edit(self, project: WebProject, command: str) -> WebProject:
        """Apply an edit command to existing project."""
        cmd = command.lower()
        project.history.append(command)

        # COLOR CHANGES
        color_match = re.search(r'change\s+(?:the\s+)?(?:color|colour)\s+(?:to\s+)?(\w+)', cmd)
        if color_match:
            color = color_match.group(1)
            project.css = self.color_engine.change_color(project.css, 'primary', color)
            return project

        bg_match = re.search(r'(?:change|make)\s+(?:the\s+)?(?:background|bg)\s+(?:to\s+)?(\w+)', cmd)
        if bg_match:
            color = bg_match.group(1)
            project.css = self.color_engine.change_color(project.css, 'background', color)
            return project

        # THEME CHANGES
        if any(w in cmd for w in ['dark mode', 'dark theme', 'make it dark']):
            palette = self.color_engine.PALETTES['dark']
            project.css = re.sub(r'--primary:\s*[^;]+;', f'--primary: {palette["primary"]};', project.css)
            project.css = re.sub(r'--bg:\s*[^;]+;', f'--bg: {palette["bg"]};', project.css)
            project.css = re.sub(r'--text:\s*[^;]+;', f'--text: {palette["text"]};', project.css)
            project.css = re.sub(r'--surface:\s*[^;]+;', f'--surface: {palette["surface"]};', project.css)
            return project

        if any(w in cmd for w in ['light mode', 'light theme', 'make it light']):
            palette = self.color_engine.PALETTES['cool']
            project.css = re.sub(r'--primary:\s*[^;]+;', f'--primary: {palette["primary"]};', project.css)
            project.css = re.sub(r'--bg:\s*[^;]+;', f'--bg: {palette["bg"]};', project.css)
            project.css = re.sub(r'--text:\s*[^;]+;', f'--text: {palette["text"]};', project.css)
            project.css = re.sub(r'--surface:\s*[^;]+;', f'--surface: {palette["surface"]};', project.css)
            return project

        # ADD SECTIONS
        if 'add' in cmd:
            if 'pricing' in cmd:
                plans = [("Starter", "$29/mo", ["5 projects", "Basic analytics"]),
                         ("Pro", "$79/mo", ["Unlimited", "Priority support", "API access"]),
                         ("Enterprise", "Custom", ["Dedicated manager", "SLA", "Custom dev"])]
                new_section = self.components.pricing_cards(plans)
                project.html = self._insert_before_footer(project.html, new_section)
            elif 'testimonial' in cmd:
                items = [("Amazing product!", "Sarah", "CEO"), ("Changed everything", "James", "Developer")]
                new_section = self.components.testimonials(items)
                project.html = self._insert_before_footer(project.html, new_section)
            elif 'contact' in cmd or 'form' in cmd:
                new_section = self.components.contact_form()
                project.html = self._insert_before_footer(project.html, new_section)
            elif 'gallery' in cmd:
                new_section = self.components.gallery()
                project.html = self._insert_before_footer(project.html, new_section)
            elif 'stats' in cmd:
                items = [("10K+", "Users"), ("99.9%", "Uptime"), ("50+", "Countries")]
                new_section = self.components.stats(items)
                project.html = self._insert_before_footer(project.html, new_section)
            return project

        # REMOVE SECTIONS
        if 'remove' in cmd or 'delete' in cmd:
            for section in ['pricing', 'testimonials', 'contact', 'gallery', 'features', 'stats']:
                if section in cmd:
                    project.html = re.sub(f'<section[^>]*id="{section}"[^>]*>.*?</section>', '', project.html, flags=re.DOTALL)
                    break
            return project

        # STYLE CHANGES
        if 'rounded' in cmd or 'round' in cmd:
            project.css = re.sub(r'--radius:\s*[^;]+;', '--radius: 24px;', project.css)
        elif 'sharp' in cmd or 'square' in cmd:
            project.css = re.sub(r'--radius:\s*[^;]+;', '--radius: 0px;', project.css)
        elif 'sticky' in cmd and ('header' in cmd or 'nav' in cmd):
            project.css += '\n.navbar { position: sticky !important; top: 0; }'

        # FONT CHANGES
        if 'font' in cmd:
            if 'mono' in cmd: project.css = re.sub(r"font-family:[^;]+;", "font-family: 'JetBrains Mono', monospace;", project.css, count=1)
            elif 'serif' in cmd: project.css = re.sub(r"font-family:[^;]+;", "font-family: 'Playfair Display', serif;", project.css, count=1)

        return project

    def _insert_before_footer(self, html: str, new_section: str) -> str:
        if '<footer' in html:
            return html.replace('<footer', f'{new_section}\n<footer', 1)
        return html + '\n' + new_section


# ═══════════════════════════════════════════════════════════════
# MAIN WEB BUILDER
# ═══════════════════════════════════════════════════════════════

class WebBuilder:
    """Main entry point — generate and edit web projects."""

    def __init__(self):
        self.detector = FrameworkDetector()
        self.colors = ColorEngine()
        self.css_gen = CSSGenerator()
        self.components = ComponentLibrary()
        self.threejs = ThreeJSGenerator()
        self.react_gen = ReactGenerator()
        self.editor = EditEngine()
        self._current_project: Optional[WebProject] = None

    def generate(self, request: str) -> WebProject:
        """Generate a new web project from natural language."""
        framework = self.detector.detect(request)
        palette = self.colors.get_palette(request)
        spec = self._parse_spec(request)
        spec['framework'] = framework

        project = WebProject(framework=framework, spec=spec)
        project.css = self.css_gen.generate(palette, framework)

        if framework == "threejs":
            project.html = self._build_threejs_html(spec)
            project.js = self.threejs.generate(request)
        elif framework == "react":
            project.html = '<div id="root"></div>'
            project.js = self.react_gen.generate(spec)
        else:
            project.html = self._build_vanilla_html(spec)
            project.js = self._build_js(spec)

        self._current_project = project
        project.history.append(f"Generated: {request}")
        return project

    def edit(self, project: WebProject, command: str) -> WebProject:
        """Edit existing project with natural language command."""
        project = self.editor.edit(project, command)
        self._current_project = project
        return project

    def _parse_spec(self, request: str) -> Dict:
        """Parse request into spec dict."""
        req = request.lower()
        spec = {'name': 'My Site', 'sections': ['hero', 'features', 'contact'], 'type': 'landing'}

        # Extract name
        called = re.search(r'called\s+([A-Z][A-Za-z\s&]+)', request)
        if called: spec['name'] = called.group(1).strip()
        quoted = re.search(r'["\']([^"\']+)["\']', request)
        if quoted: spec['name'] = quoted.group(1)
        named = re.search(r'named\s+([A-Z][A-Za-z\s&]+)', request)
        if named: spec['name'] = named.group(1).strip()

        # Business type detection for auto-naming
        biz_names = {'coffee': 'Brew & Co', 'gym': 'Iron Core', 'saas': 'FlowStack',
                    'restaurant': 'Saveur', 'agency': 'Pixel & Code', 'portfolio': 'Alex Chen',
                    'startup': 'LaunchPad', 'salon': 'Luxe Studio'}
        if spec['name'] == 'My Site':
            for key, name in biz_names.items():
                if key in req:
                    spec['name'] = name
                    break

        # Sections based on context
        if any(w in req for w in ['portfolio', 'personal']):
            spec['sections'] = ['hero', 'work', 'skills', 'contact']
        elif any(w in req for w in ['saas', 'startup', 'product', 'app']):
            spec['sections'] = ['hero', 'features', 'pricing', 'testimonials', 'contact']
        elif any(w in req for w in ['restaurant', 'coffee', 'cafe', 'food']):
            spec['sections'] = ['hero', 'menu', 'gallery', 'contact']
        elif any(w in req for w in ['agency', 'studio', 'company']):
            spec['sections'] = ['hero', 'services', 'work', 'testimonials', 'contact']

        return spec

    def _build_vanilla_html(self, spec: Dict) -> str:
        """Build HTML for vanilla sites."""
        name = spec.get('name', 'My Site')
        sections = spec.get('sections', ['hero', 'features', 'contact'])

        parts = [self.components.nav(name, [s.capitalize() for s in sections[1:]])]

        for section in sections:
            if section == 'hero':
                parts.append(self.components.hero_gradient(name, "Build something extraordinary"))
            elif section == 'features':
                parts.append(self.components.features_grid([
                    ("⚡", "Lightning Fast", "Optimized performance at every level"),
                    ("🔒", "Secure by Default", "Enterprise-grade security built in"),
                    ("🚀", "Scales Infinitely", "From prototype to production seamlessly"),
                    ("🎨", "Beautiful Design", "Pixel-perfect interfaces that delight"),
                    ("📱", "Mobile First", "Responsive across every device"),
                    ("🔄", "Always Updated", "Continuous improvements and features"),
                ]))
            elif section == 'pricing':
                parts.append(self.components.pricing_cards([
                    ("Starter", "$29/mo", ["5 projects", "Basic analytics", "Email support"]),
                    ("Pro", "$79/mo", ["Unlimited projects", "Advanced analytics", "Priority support", "API access"]),
                    ("Enterprise", "Custom", ["Dedicated manager", "SLA guarantee", "Custom development"]),
                ]))
            elif section == 'testimonials':
                parts.append(self.components.testimonials([
                    ("Completely transformed how we work. Can't imagine going back.", "Sarah Chen", "CEO at TechFlow"),
                    ("The best investment we made this year. ROI was immediate.", "James Rodriguez", "VP Engineering"),
                    ("Simple, powerful, and the support is incredible.", "Priya Sharma", "Product Lead"),
                ]))
            elif section == 'contact':
                parts.append(self.components.contact_form())
            elif section == 'gallery':
                parts.append(self.components.gallery())
            elif section == 'menu':
                parts.append(self.components.features_grid([
                    ("☕", "Espresso", "Rich and bold — $4"),
                    ("🥛", "Latte", "Silky smooth — $5.50"),
                    ("🍵", "Matcha", "Ceremonial grade — $6"),
                    ("🧊", "Cold Brew", "18-hour steep — $5"),
                    ("🥐", "Pastries", "Fresh daily — $4"),
                    ("🍰", "Desserts", "House specials — $7"),
                ]))
            elif section == 'services':
                parts.append(self.components.features_grid([
                    ("💻", "Web Development", "Custom solutions built for scale"),
                    ("📱", "Mobile Apps", "Native and cross-platform"),
                    ("🎨", "UI/UX Design", "Human-centered design that converts"),
                ]))
            elif section in ('work', 'skills'):
                parts.append(self.components.gallery(6))

        parts.append(self.components.footer(name))
        return '\n\n'.join(parts)

    def _build_threejs_html(self, spec: Dict) -> str:
        """Build HTML for Three.js sites."""
        name = spec.get('name', '3D Scene')
        nav = self.components.nav(name, ["About", "Work", "Contact"])
        hero = self.components.hero_3d(name)
        content = self.components.features_grid([
            ("🌐", "3D Experiences", "Immersive web-based 3D"),
            ("⚡", "Real-time", "60fps smooth rendering"),
            ("🎮", "Interactive", "Full mouse/touch control"),
        ])
        footer = self.components.footer(name)
        return f'{nav}\n\n{hero}\n\n{content}\n\n{footer}'

    def _build_js(self, spec: Dict) -> str:
        """Build JS for vanilla sites."""
        return '''// Scroll animations
const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) entry.target.classList.add('visible');
    });
}, { threshold: 0.1 });
document.querySelectorAll('.fade-in').forEach(el => observer.observe(el));

// Smooth scroll
document.querySelectorAll('a[href^="#"]').forEach(a => {
    a.addEventListener('click', (e) => {
        e.preventDefault();
        const target = document.querySelector(a.getAttribute('href'));
        if (target) target.scrollIntoView({ behavior: 'smooth' });
    });
});

// Form handler
function handleSubmit(e) {
    e.preventDefault();
    const btn = e.target.querySelector('button');
    btn.textContent = 'Sent! ✓';
    btn.style.background = 'var(--accent)';
    setTimeout(() => { btn.textContent = 'Send Message'; btn.style.background = ''; e.target.reset(); }, 2000);
}

// Nav scroll effect
window.addEventListener('scroll', () => {
    const nav = document.querySelector('.navbar');
    nav.style.boxShadow = window.scrollY > 50 ? 'var(--shadow)' : 'none';
});'''


def get_web_generator():
    """Backward compatible — returns WebBuilder."""
    return WebBuilder()

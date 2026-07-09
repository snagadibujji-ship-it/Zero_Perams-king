#!/usr/bin/env python3
"""Downloads Wikipedia summaries and auto-builds knowledge base."""
import os, time, urllib.request, json, subprocess, sys

TOPICS = [
    # Countries (50)
    "United States","China","India","Brazil","Germany","France","Japan","Russia","United Kingdom",
    "Canada","Australia","Mexico","Italy","Spain","South Korea","Indonesia","Turkey","Saudi Arabia",
    "Argentina","Nigeria","Egypt","South Africa","Thailand","Vietnam","Pakistan","Iran","Poland",
    "Netherlands","Sweden","Norway","Denmark","Finland","Switzerland","Belgium","Austria","Ireland",
    "Portugal","Greece","Czech Republic","Israel","Colombia","Chile","Peru","Philippines","Malaysia",
    "New Zealand","Singapore","Ukraine","Romania","Kenya",
    # Animals (50)
    "Dog","Cat","Lion","Eagle","Shark","Whale","Elephant","Tiger","Bear","Wolf","Horse","Dolphin",
    "Penguin","Octopus","Butterfly","Snake","Crocodile","Gorilla","Cheetah","Kangaroo","Owl","Bee",
    "Ant","Spider","Frog","Turtle","Parrot","Salmon","Jellyfish","Bat","Deer","Fox","Rabbit","Rat",
    "Crow","Camel","Giraffe","Hippopotamus","Rhinoceros","Zebra","Panda","Koala","Leopard","Hawk",
    "Mosquito","Scorpion","Lobster","Starfish","Chameleon","Peacock",
    # Science (50)
    "Gravity","Photosynthesis","DNA","Evolution","Atom","Quantum mechanics","Relativity",
    "Electromagnetism","Thermodynamics","Cell biology","Genetics","Chemistry","Physics","Biology",
    "Astronomy","Geology","Ecology","Neuroscience","Particle physics","Dark matter","Black hole",
    "Big Bang","Nuclear fusion","Entropy","Wave","Light","Sound","Magnetism","Radioactivity",
    "Periodic table","Chemical bond","Protein","Enzyme","Mitosis","Natural selection","Fossil",
    "Plate tectonics","Climate change","Ozone layer","Carbon cycle","Photon","Electron","Proton",
    "Neutron","Molecule","Acid","Base (chemistry)","Oxidation","Catalyst","Semiconductor",
    # People (50)
    "Albert Einstein","Isaac Newton","William Shakespeare","Cleopatra","Mahatma Gandhi",
    "Nikola Tesla","Leonardo da Vinci","Marie Curie","Charles Darwin","Aristotle","Plato",
    "Alexander the Great","Napoleon","Abraham Lincoln","Martin Luther King Jr.","Nelson Mandela",
    "Queen Victoria","Julius Caesar","Galileo Galilei","Confucius","Buddha","Muhammad","Jesus",
    "Mozart","Beethoven","Michelangelo","Socrates","Karl Marx","Sigmund Freud","Thomas Edison",
    "Wright brothers","Alan Turing","Ada Lovelace","Pythagoras","Archimedes","Genghis Khan",
    "Marco Polo","Christopher Columbus","Copernicus","Kepler","Mendeleev","Hawking","Curie",
    "Rosalind Franklin","James Watt","Gutenberg","Florence Nightingale","Hippocrates",
    "Ramanujan","Euler",
    # Tech (50)
    "Computer","Internet","Artificial intelligence","Blockchain","Robot","Smartphone","Software",
    "Algorithm","Database","Cloud computing","Machine learning","Programming language","Linux",
    "World Wide Web","Email","Encryption","Virtual reality","3D printing","Nanotechnology",
    "Semiconductor device","Transistor","Microprocessor","Operating system","Python (programming language)",
    "JavaScript","Java (programming language)","C (programming language)","HTML","HTTP","TCP/IP",
    "Wi-Fi","Bluetooth","GPS","Satellite","Laser","Fiber optics","Quantum computing","Bitcoin",
    "Cryptocurrency","Neural network","Deep learning","Natural language processing","Computer vision",
    "Cybersecurity","Open source","Git","Docker (software)","Kubernetes","API","Silicon Valley",
    # Geography (50)
    "Pacific Ocean","Atlantic Ocean","Indian Ocean","Mount Everest","Amazon River","Nile",
    "Sahara","Antarctica","Arctic","Mediterranean Sea","Himalayas","Alps","Andes","Rocky Mountains",
    "Great Barrier Reef","Amazon rainforest","Ganges","Mississippi River","Lake Baikal",
    "Dead Sea","Mariana Trench","Grand Canyon","Niagara Falls","Victoria Falls","Yellowstone",
    "Galápagos Islands","Madagascar","Iceland","Greenland","Borneo","Sumatra","Java","Caspian Sea",
    "Black Sea","Red Sea","Persian Gulf","Suez Canal","Panama Canal","Strait of Gibraltar",
    "Cape of Good Hope","Kilimanjaro","Mount Fuji","Vesuvius","Great Wall of China",
    "Taj Mahal","Machu Picchu","Stonehenge","Colosseum","Parthenon","Angkor Wat",
    # History (50)
    "World War II","World War I","French Revolution","Industrial Revolution","Renaissance",
    "Ancient Rome","Ancient Greece","Ancient Egypt","Cold War","American Revolution",
    "Russian Revolution","Roman Empire","Ottoman Empire","British Empire","Mongol Empire",
    "Silk Road","Crusades","Black Death","Slavery","Colonialism","Imperialism",
    "Declaration of Independence","Constitution","Magna Carta","Feudalism","Middle Ages",
    "Bronze Age","Iron Age","Stone Age","Agricultural revolution","Scientific Revolution",
    "Enlightenment","Protestant Reformation","Spanish Inquisition","Fall of Constantinople",
    "Viking Age","Samurai","Ancient China","Mesopotamia","Indus Valley Civilisation",
    "Maya civilization","Aztec","Inca Empire","Apartheid","Berlin Wall","Moon landing",
    "Hiroshima","Holocaust","D-Day","Treaty of Versailles",
    # Food (50)
    "Rice","Bread","Chocolate","Coffee","Tea","Pizza","Pasta","Sushi","Cheese","Wine","Beer",
    "Sugar","Salt","Olive oil","Butter","Milk","Egg","Wheat","Corn","Potato","Tomato","Banana",
    "Apple","Orange (fruit)","Strawberry","Grape","Mango","Coconut","Avocado","Garlic","Onion",
    "Pepper","Cinnamon","Vanilla","Honey","Yogurt","Tofu","Curry","Hamburger","Hot dog",
    "Ice cream","Cake","Soup","Salad","Barbecue","Kimchi","Hummus","Taco","Croissant","Dumpling",
    # Sports (30)
    "Football","Cricket","Tennis","Swimming","Basketball","Baseball","Golf","Rugby","Boxing",
    "Athletics","Volleyball","Table tennis","Badminton","Cycling","Gymnastics","Wrestling",
    "Martial arts","Surfing","Skiing","Ice hockey","Formula One","Chess","Olympic Games",
    "FIFA World Cup","Marathon","Archery","Fencing","Rowing","Weightlifting","Skateboarding",
    # Music (30)
    "Piano","Guitar","Violin","Drums","Flute","Trumpet","Saxophone","Cello","Harp","Organ",
    "Jazz","Rock music","Classical music","Hip hop music","Blues","Opera","Symphony","Orchestra",
    "Choir","Reggae","Electronic music","Country music","Folk music","Soul music","Punk rock",
    "Heavy metal music","Pop music","Rap","Disco","Techno",
    # Medicine (40)
    "Cancer","Diabetes","Vaccine","Surgery","Antibiotic","Virus","Bacteria","Malaria","HIV/AIDS",
    "Tuberculosis","Heart disease","Stroke","Alzheimer's disease","Parkinson's disease","Asthma",
    "Allergy","Depression (mood)","Anxiety disorder","Schizophrenia","Autism","Obesity","Anesthesia",
    "Blood transfusion","Organ transplant","X-ray","MRI","Ultrasound","Pharmacology","Immunology",
    "Epidemiology","Public health","Mental health","Nutrition","Sleep","Exercise","DNA sequencing",
    "CRISPR","Stem cell","Pandemic","Influenza",
    # Misc (50)
    "Democracy","Money","Time","Love","Language","Mathematics","Philosophy","Religion","Art",
    "Literature","Film","Photography","Architecture","Education","University","Library","Museum",
    "Law","Human rights","United Nations","Economics","Capitalism","Socialism","Globalization",
    "Population","Urbanization","Pollution","Renewable energy","Solar energy","Nuclear energy",
    "Electricity","Water","Fire","Earth","Sun","Moon","Mars","Jupiter","Saturn","Venus","Mercury",
    "Milky Way","Galaxy","Universe","Supernova","Asteroid","Comet","Telescope","Space exploration",
    "International Space Station",
]

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
WIKI_FILE = os.path.join(DATA_DIR, "wiki_knowledge.txt")
API = "https://en.wikipedia.org/api/rest_v1/page/summary/"

def download_top_articles(count=1000):
    """Download Wikipedia summaries for hardcoded topics."""
    os.makedirs(DATA_DIR, exist_ok=True)
    if os.path.exists(WIKI_FILE):
        with open(WIKI_FILE) as f:
            if sum(1 for _ in f) > 5000:
                print("wiki_knowledge.txt already has >5000 lines, skipping download.")
                return
    topics = TOPICS[:count]
    lines = []
    for i, topic in enumerate(topics):
        try:
            url = API + urllib.parse.quote(topic.replace(" ", "_"))
            req = urllib.request.Request(url, headers={"User-Agent": "KnowledgeLoader/1.0"})
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode())
            extract = data.get("extract", "")
            sentences = [s.strip() for s in extract.split(". ")[:3] if s.strip()]
            for s in sentences:
                lines.append(s if s.endswith(".") else s + ".")
            print(f"\r[{i+1}/{len(topics)}] Downloaded: {topic}", end="", flush=True)
        except Exception:
            pass
        time.sleep(0.1)
    print(f"\nSaving {len(lines)} lines to {WIKI_FILE}")
    with open(WIKI_FILE, "w") as f:
        f.write("\n".join(lines) + "\n")

def build_knowledge():
    """Run concept_build to rebuild knowledge.dat from data files."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    concept_build = os.path.join(script_dir, "concept_build.py")
    if os.path.exists(concept_build):
        print("Building knowledge.dat...")
        subprocess.run([sys.executable, concept_build], cwd=script_dir)
    else:
        print(f"concept_build.py not found at {concept_build}, skipping build step.")

if __name__ == "__main__":
    import urllib.parse
    download_top_articles()
    build_knowledge()
    print("Done.")

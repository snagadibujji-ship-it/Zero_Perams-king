"""
REALISM ENGINE — Wave 1
========================
Makes generated data indistinguishable from real industrial communication.

Components:
1. TimeOfDayEngine — realistic hourly peaks
2. MessageRealism — typos, abbreviations, emojis, varied length
3. PersonContinuity — same person for multiple events
4. JokeEngine — workplace humor (makes it feel HUMAN)
5. SeriousSituations — tense moments that feel real
"""
import random
from datetime import datetime



# ═══════════════════════════════════════════════════════
# 1. TIME OF DAY ENGINE
# ═══════════════════════════════════════════════════════

# Activity weight per hour (higher = more events at this hour)
# Modeled on real 24/7 factory with 3 shifts
HOURLY_WEIGHT_24x7 = {
    0: 2, 1: 1, 2: 1, 3: 1, 4: 2, 5: 4,
    6: 15, 7: 12, 8: 10, 9: 9, 10: 11,  # Tea break peak at 10
    11: 8, 12: 13, 13: 7, 14: 12,  # Lunch peak 12, shift change 14
    15: 9, 16: 8, 17: 10, 18: 6, 19: 5,
    20: 4, 21: 3, 22: 8, 23: 3,  # Night shift change at 22
}

HOURLY_WEIGHT_DAY_ONLY = {
    0: 0, 1: 0, 2: 0, 3: 0, 4: 0, 5: 1,
    6: 3, 7: 5, 8: 12, 9: 15, 10: 14,
    11: 12, 12: 8, 13: 10, 14: 12, 15: 11,
    16: 10, 17: 8, 18: 3, 19: 1, 20: 0,
    21: 0, 22: 0, 23: 0,
}

def get_time_weight(hour: int, shift_pattern: str = "24x7") -> float:
    """Get activity weight for a given hour."""
    if shift_pattern == "day_only":
        return HOURLY_WEIGHT_DAY_ONLY.get(hour, 1)
    return HOURLY_WEIGHT_24x7.get(hour, 1)


def get_time_interval(hour: int, rng, mood_state: str = "routine") -> float:
    """Get realistic time interval (minutes) based on hour and mood."""
    weight = HOURLY_WEIGHT_24x7.get(hour, 1)
    
    # Base interval inversely proportional to activity
    if mood_state == "crisis":
        base = rng.uniform(0.5, 2)
    elif mood_state == "urgent":
        base = rng.uniform(1, 5)
    elif weight >= 12:  # Peak hours
        base = rng.uniform(2, 8)
    elif weight >= 8:  # Active hours
        base = rng.uniform(5, 15)
    elif weight >= 4:  # Moderate
        base = rng.uniform(10, 30)
    elif weight >= 2:  # Quiet
        base = rng.uniform(20, 60)
    else:  # Deep night
        base = rng.uniform(30, 120)
    
    return base



# ═══════════════════════════════════════════════════════
# 2. MESSAGE REALISM — Typos, abbreviations, emojis
# ═══════════════════════════════════════════════════════

COMMON_TYPOS = {
    # Original common words
    "the": ["teh", "hte", "th"],
    "and": ["adn", "nad", "an"],
    "just": ["jsut", "jst", "jus"],
    "that": ["taht", "tht", "tha"],
    "have": ["hve", "ahve", "hav"],
    "this": ["tihs", "ths", "tis"],
    "with": ["wiht", "wth", "wit"],
    "from": ["form", "frm", "fron"],
    "what": ["waht", "wht", "wat"],
    "when": ["wehn", "whn", "wen"],
    "where": ["wehre", "wher", "whre"],
    "there": ["thre", "ther", "tehre"],
    "their": ["thier", "theri", "ther"],
    "which": ["whihc", "wich", "whch"],
    "should": ["shoudl", "shuld", "shoud"],
    "would": ["woudl", "wuld", "woud"],
    "could": ["coudl", "culd", "coud"],
    "about": ["abuot", "abut", "aboit"],
    "after": ["aftre", "aftr", "atfer"],
    "before": ["befoer", "befre", "bfore"],
    "because": ["becuase", "becuz", "bcause"],
    "between": ["betwen", "betwene", "btwn"],
    "through": ["trhough", "throgh", "thru"],
    "already": ["alredy", "alreday", "alrady"],
    "another": ["anohter", "anothr", "anthor"],
    "people": ["poeple", "peple", "peopl"],
    "started": ["strted", "startd", "staretd"],
    "working": ["workign", "wrking", "workin"],
    "running": ["runnign", "runnin", "runing"],
    "waiting": ["waitign", "waitin", "wating"],
    "getting": ["gettign", "gettin", "gtting"],
    "coming": ["comign", "comin", "comng"],
    "going": ["goign", "goin", "giong"],
    "during": ["durign", "durin", "durng"],
    "everything": ["evrything", "everthing", "evrthing"],
    "something": ["somethign", "somethin", "somthing"],
    "nothing": ["nothign", "nothin", "nohting"],
    "someone": ["soemone", "somone", "someoen"],
    "everyone": ["evryone", "evreyone", "evrone"],
    
    # Industrial equipment
    "check": ["chekc", "chk", "chck"],
    "pressure": ["pressue", "presure", "preesure", "pressur"],
    "temperature": ["temprature", "temperture", "tempreture", "temperatur"],
    "maintenance": ["maintainance", "maintenace", "maintanance", "maintnance"],
    "machine": ["machien", "machin", "machne", "mashine"],
    "equipment": ["equipmnet", "equpiment", "equipmet", "equiptment"],
    "compressor": ["compresser", "compresor", "comprssor", "compresssr"],
    "generator": ["generater", "genertor", "genrator", "generatr"],
    "conveyor": ["conveyer", "convyor", "convayer", "conveeyor"],
    "transformer": ["transfermer", "tranformer", "transformr", "transfrmer"],
    "hydraulic": ["hydrualic", "hydralic", "hydraulc", "hydrulic"],
    "pneumatic": ["pnuematic", "pneumatc", "pnematic", "pneumtic"],
    "bearing": ["bearign", "bering", "bearin", "bearng"],
    "gasket": ["gakset", "gaskt", "gascket", "gaskte"],
    "valve": ["vlave", "valv", "valave", "valev"],
    "pump": ["pupm", "pmup", "pmp", "pujp"],
    "motor": ["moter", "motro", "motr", "motir"],
    "turbine": ["turbien", "turbin", "turbne", "turbnine"],
    "boiler": ["boilder", "bolier", "boilr", "boielr"],
    "furnace": ["furnase", "furnce", "furance", "furnnace"],
    "reactor": ["reacter", "reactr", "reactro", "ractor"],
    "condenser": ["condensor", "condensr", "condneser", "condensser"],
    "cylinder": ["cylindr", "cylnder", "cylindre", "cyliner"],
    "piston": ["pisten", "pistn", "pison", "pistion"],
    "crankshaft": ["crankshaf", "crankshft", "cranksahft", "crankshaft"],
    "gearbox": ["gearbok", "gerbox", "gearbx", "gearobx"],
    "cooling": ["coolign", "coolin", "coolng", "coolig"],
    "heating": ["heatign", "heatin", "heatng", "heting"],
    "welding": ["weldign", "weldin", "weldng", "wleding"],
    "grinding": ["grindign", "grindin", "grindng", "grining"],
    "drilling": ["drillign", "drillin", "drillng", "drlling"],
    "milling": ["millign", "millin", "millng", "mlling"],
    "casting": ["castign", "castin", "castng", "csting"],
    "forging": ["forgign", "forgin", "forgng", "froging"],
    "stamping": ["stampign", "stampin", "stampng", "stamipng"],
    "assembly": ["asembly", "assmbly", "assemby", "assemlby"],
    "inspection": ["inspectionn", "inspecton", "inpection", "insepction"],
    "calibration": ["calibraton", "calibraion", "calbraton", "calibrtion"],
    "lubrication": ["lubricaton", "lubricaion", "lubrcation", "lubrcaton"],
    "vibration": ["vibraton", "vibraion", "vibrtion", "vibation"],
    "alignment": ["alignmnet", "aligment", "allignment", "alignmet"],
    "insulation": ["insulaton", "insulaion", "insultion", "insualtion"],
    "ventilation": ["ventilaton", "ventiltion", "ventialtion", "ventlation"],
    "filtration": ["filtraton", "filtraion", "filtrtion", "filtation"],
    "corrosion": ["corrision", "corosion", "corroson", "corrsoion"],
    "erosion": ["errosion", "erosin", "eroison", "erosoin"],
    "leakage": ["leakge", "leakag", "lekage", "leakeage"],
    "blockage": ["blockge", "blocakge", "blokage", "blocage"],
    "shortage": ["shortge", "shortag", "shrotage", "shortaeg"],
    "voltage": ["voltge", "voltag", "vltage", "volatge"],
    "amperage": ["amperge", "amprage", "amperag", "ampereage"],
    "frequency": ["frequncy", "frequeny", "freqency", "frequnecy"],
    "capacity": ["capcity", "capacty", "capcaity", "capaciy"],
    "efficiency": ["efficency", "efficieny", "eficiency", "efficeincy"],
    "reliability": ["reliabilty", "reliablity", "reliabiliy", "relability"],
    "availability": ["availabilty", "availablity", "avialability", "availbility"],
    
    # Measurement/readings
    "reading": ["readign", "readin", "readng", "rading"],
    "measurement": ["measurment", "measuremnt", "measurment", "mesurement"],
    "tolerance": ["tolerence", "tolernce", "toleranc", "tolerace"],
    "threshold": ["threshhold", "thresold", "treshold", "threshod"],
    "parameter": ["paramter", "paraemter", "paramater", "parameer"],
    "specification": ["specificaton", "specifiction", "specificaion", "specfication"],
    "deviation": ["deviaton", "devation", "devaition", "deviaiton"],
    "fluctuation": ["fluctuaton", "fluctution", "flucutation", "fluctation"],
    
    # Process terms
    "shutdown": ["shutdwon", "shutdwn", "shtdown", "shutdonw"],
    "startup": ["startpu", "strtup", "start up", "statrup"],
    "changeover": ["chanegover", "changover", "changeovr", "chnageover"],
    "breakdown": ["braekdown", "breakdwon", "brekdown", "breakdow"],
    "overhaul": ["overhaule", "overhaul", "overhual", "ovrhaul"],
    "shutdown": ["shutdwon", "shtdown", "shutdow", "shutdonw"],
    "operation": ["operaton", "opertion", "opertaion", "operaion"],
    "production": ["producton", "prodution", "productin", "prodcution"],
    "processing": ["processign", "processin", "procesing", "proccessing"],
    "manufacturing": ["manufactruing", "manufcturing", "manufacturng", "manufaturing"],
    "installation": ["installaton", "instalation", "installtion", "insatllation"],
    "commissioning": ["commisionning", "comissioning", "commisionig", "commissining"],
    "decommissioning": ["decomissioning", "decommisioning", "decommissionig"],
    "troubleshooting": ["troubleshootign", "troubleshoting", "troublshooting"],
    "monitoring": ["monitorign", "monitring", "monitorin", "monitoing"],
    "scheduling": ["schedulign", "schedulin", "scheduing", "sheduling"],
    "dispatching": ["dispatchign", "dipatching", "dispathing", "dispathcing"],
    "warehousing": ["warehouisng", "warehousign", "warehouing", "warehousin"],
    
    # Materials
    "material": ["materal", "materail", "materil", "matrial"],
    "chemical": ["chemcial", "chemcal", "chemiacl", "chemica"],
    "lubricant": ["lubricent", "lubricnat", "lubricatn", "lubrcant"],
    "solvent": ["solvnet", "solvant", "slovent", "solvnt"],
    "adhesive": ["adhesve", "adhsive", "adheisve", "adhesiv"],
    "abrasive": ["abrasve", "abrsive", "abraisve", "abrasiv"],
    "coolant": ["coolent", "colant", "cooolant", "coolnat"],
    "refrigerant": ["refrigerent", "refrigrant", "refrigerant", "refridgerant"],
    "insulation": ["insulaton", "insualtion", "insulation", "insulaiton"],
    "concrete": ["concret", "concrte", "concreate", "conrete"],
    "aluminum": ["aluminium", "aluminm", "alumnum", "alumnium"],
    "stainless": ["stainles", "stanless", "stainlss", "stianless"],
    "galvanized": ["galvanised", "galvanizd", "galvnized", "galvanzied"],
    
    # Safety terms
    "safety": ["saftey", "safty", "safetey", "sefety"],
    "hazard": ["hazzard", "hazrd", "hzard", "hazaard"],
    "accident": ["accidnet", "acident", "accidnt", "acccident"],
    "incident": ["incidnet", "inident", "incidnt", "inicdent"],
    "emergency": ["emergancy", "emrgency", "emergncy", "emergecny"],
    "evacuation": ["evacuaton", "evacution", "evacuaion", "evacuaiton"],
    "protection": ["protecton", "protecion", "protction", "protectin"],
    "violation": ["violaton", "violtion", "violaion", "viloation"],
    "compliance": ["complience", "complance", "compilance", "complianc"],
    "procedure": ["proceedure", "procedur", "procedue", "procedrue"],
    "protocol": ["protocal", "protcol", "protocl", "protoocol"],
    "regulation": ["regulaton", "regultion", "regulaion", "reguatlion"],
    "certificate": ["certifcate", "certificte", "certifiate", "certficate"],
    "permission": ["permision", "permssion", "permision", "permisison"],
    
    # Workplace terms
    "supervisor": ["superviser", "suprevisor", "supervisr", "superviosr"],
    "manager": ["manger", "managr", "mnager", "managre"],
    "engineer": ["enginere", "enginer", "engneer", "engineeer"],
    "technician": ["technican", "techncian", "technician", "technicain"],
    "operator": ["operater", "opertor", "opertaor", "operatr"],
    "inspector": ["inspecter", "insepctor", "inpsector", "inspctor"],
    "contractor": ["contracter", "contracor", "contractr", "contrcator"],
    "department": ["departmnet", "dpartment", "departmet", "deparment"],
    "schedule": ["schdule", "scheule", "scheduel", "scedule"],
    "delivery": ["delivry", "dlivery", "delivrey", "delvery"],
    "inventory": ["inventroy", "invntory", "inventoy", "invetory"],
    "warehouse": ["warehosue", "warehoue", "warhouse", "warehous"],
    "document": ["documnet", "docuemnt", "documnt", "doument"],
    "approval": ["approvel", "appoval", "approvl", "aproval"],
    "requisition": ["requisiton", "requistion", "requisiion", "requsition"],
    "procurement": ["procurment", "procuremnt", "procuremnent", "procuremnet"],
    
    # Quality terms
    "quality": ["quailty", "qualiy", "qality", "qualty"],
    "defect": ["defct", "defcet", "dfect", "deffect"],
    "reject": ["rejcet", "rejct", "reejct", "rejet"],
    "rework": ["rewrok", "rewok", "rwork", "rewrk"],
    "scrap": ["scarp", "scap", "scrp", "scraap"],
    "sample": ["sampl", "smple", "sampel", "smaple"],
    "testing": ["testign", "testin", "testng", "tsting"],
    "analysis": ["anaylsis", "analyis", "analsis", "anlaysis"],
    "report": ["reprot", "reort", "reprt", "reoprt"],
    "standard": ["standrd", "standad", "standrad", "stanard"],
    "tolerance": ["tolerence", "tolrance", "toleranc", "tolerace"],
    
    # Time/shift terms
    "shift": ["shfit", "shif", "shiift", "shft"],
    "overtime": ["overtme", "ovrtime", "overitme", "overtim"],
    "morning": ["mornign", "mornin", "mornng", "mornnig"],
    "afternoon": ["afteroon", "afternon", "aftroon", "afternoo"],
    "evening": ["evenign", "evenin", "evning", "eveing"],
    "yesterday": ["yestrday", "yesterdy", "yeterday", "yestarday"],
    "tomorrow": ["tomorow", "tomorrw", "tmorrow", "tomoroow"],
    "weekend": ["weeknd", "weekned", "wekend", "weekennd"],
    "holiday": ["holday", "holidya", "hoilday", "holdiay"],
    
    # Action verbs (industrial)
    "replace": ["relace", "replce", "relpace", "repalce"],
    "install": ["instal", "instll", "intall", "insatll"],
    "remove": ["remov", "reomve", "rmove", "removee"],
    "repair": ["repiar", "repai", "rpair", "reapir"],
    "adjust": ["adjsut", "adjut", "adjst", "adujst"],
    "tighten": ["tightn", "tighen", "tihgten", "tighte"],
    "loosen": ["loosn", "losen", "loosen", "looesn"],
    "connect": ["conect", "conncet", "connct", "connetc"],
    "disconnect": ["disconect", "disconnct", "disconnet", "disonnect"],
    "isolate": ["isolte", "isloate", "isolat", "islolate"],
    "activate": ["activte", "actvate", "activat", "actiavte"],
    "deactivate": ["deactivte", "deactvate", "deactivat", "deactiavte"],
    "operate": ["operat", "oeprate", "operaet", "oprate"],
    "transfer": ["tranfer", "transfe", "trnasfer", "trasfer"],
    "deliver": ["delivr", "deilver", "delivre", "delievr"],
    "receive": ["recieve", "recive", "receiv", "recevie"],
    "dispatch": ["dispath", "dispach", "disaptch", "dispatc"],
    "complete": ["complet", "comlete", "complte", "compleet"],
    "approve": ["appove", "aprove", "approv", "approvee"],
    "confirm": ["confrim", "confrm", "confim", "cofnirm"],
    "verify": ["verfiy", "verfy", "vreify", "veirfy"],
    "inspect": ["insepct", "inpsect", "inspcet", "inpsct"],
    "measure": ["measrue", "measur", "mesure", "measrure"],
    "calibrate": ["calibarte", "calibrat", "calbirate", "calibrte"],
    "lubricate": ["lubricte", "lubriacte", "lubrciate", "lubircate"],
    "diagnose": ["diagnos", "diagnsoe", "diagnoes", "diagose"],
    "troubleshoot": ["troubleshoo", "troubleshot", "troubeshoot", "troublshoot"],
    
    # Common misspellings specific to keyboard/mobile
    "available": ["avaliable", "availble", "avalable", "avialable"],
    "necessary": ["neccessary", "necesary", "neccesary", "necessray"],
    "immediately": ["immediatly", "immeditaly", "immedately", "immediatley"],
    "unfortunately": ["unfortunatly", "unfortunatley", "unfortunetly"],
    "responsible": ["responsble", "responisble", "responsibel", "reponsible"],
    "professional": ["proffessional", "profesional", "proffesional"],
    "environment": ["enviroment", "environmnet", "environmet", "enviromnent"],
    "management": ["managment", "managemnt", "managemet", "managmenet"],
    "performance": ["performnce", "performace", "perfomance", "performnace"],
    "information": ["informaton", "informtion", "informatoin", "infomation"],
    "requirement": ["requirment", "requiremnt", "requirment", "requiremet"],
    "experience": ["experiance", "expereince", "experienc", "exprience"],
    "communication": ["communicaton", "communiction", "communicatin", "communcation"],
    "distribution": ["distribtuon", "distributon", "distrubtion", "distribtion"],
    "investigation": ["investigaton", "investigtion", "investigaiton", "investiation"],
    "recommendation": ["reccommendation", "recomendation", "recommendaton"],
    "configuration": ["configuraton", "configration", "configurtion", "configuartion"],
    "documentation": ["documentaton", "documenttion", "documention", "documentaiton"],
    "authorization": ["authorizaton", "authrization", "authoriztion", "authoriation"],
}

ABBREVIATIONS = {
    "please": "pls",
    "tomorrow": "tmrw",
    "today": "2day",
    "thanks": "thx",
    "brother": "bro",
    "sister": "sis",
    "okay": "ok",
    "because": "coz",
    "before": "b4",
    "about": "abt",
    "between": "btwn",
    "something": "smthng",
    "nothing": "nthng",
    "coming": "cmng",
    "going": "gng",
    "morning": "mrng",
    "evening": "evng",
    "meeting": "mtg",
    "minute": "min",
    "second": "sec",
    "problem": "prblm",
    "supervisor": "supvr",
    "manager": "mgr",
    "engineer": "engr",
    "department": "dept",
    "maintenance": "maint",
    "production": "prodn",
    "quality": "qty",
    "inspection": "inspn",
    "immediately": "immdtly",
    "information": "info",
    "regarding": "re",
    "available": "avail",
    "electricity": "elect",
    "temperature": "temp",
    "approximately": "approx",
}

EMOJIS_WORK = ["👍", "✅", "❌", "⚠️", "🔥", "💪", "🙏", "😤", "😂", "🤦",
               "👀", "📸", "🔧", "⏰", "☕", "🍕", "🎂", "🏠", "🚗", "📞"]

RESPONSE_MESSAGES = [
    "ok", "ok 👍", "done", "noted", "will do", "on it", "copy",
    "roger that", "understood", "coming", "5 min", "after lunch",
    "sure", "no problem", "got it", "checking", "wait",
    "one sec", "hold on", "yes sir", "ok boss", "right away",
    "already done", "in progress", "almost done", "just finished",
    "sent", "updated", "confirmed", "approved", "rejected",
    "not now", "busy", "later", "tmrw", "next week",
    "who?", "where?", "when?", "how much?", "which one?",
    "really?", "again??", "seriously?", "why???", "since when?",
    "haha", "lol", "nice", "wow", "damn", "oops",
    "👍👍", "🙏", "✅ done", "❌ no", "⚠️ careful",
]


def add_typos(message: str, rng, probability: float = 0.05) -> str:
    """Add realistic typos to a message."""
    if rng.random() > probability:
        return message
    words = message.split()
    if not words:
        return message
    # Pick a random word to typo
    idx = rng.randint(0, len(words) - 1)
    word_lower = words[idx].lower()
    if word_lower in COMMON_TYPOS:
        words[idx] = rng.choice(COMMON_TYPOS[word_lower])
    return " ".join(words)


def add_abbreviations(message: str, rng, probability: float = 0.15) -> str:
    """Replace words with common abbreviations."""
    if rng.random() > probability:
        return message
    words = message.split()
    for i, word in enumerate(words):
        word_lower = word.lower().rstrip(".,!?")
        if word_lower in ABBREVIATIONS and rng.random() < 0.4:
            words[i] = ABBREVIATIONS[word_lower]
    return " ".join(words)


def add_emoji(message: str, rng, probability: float = 0.08) -> str:
    """Add emoji to message (simulating WhatsApp/Teams)."""
    if rng.random() > probability:
        return message
    emoji = rng.choice(EMOJIS_WORK)
    if rng.random() < 0.7:
        return message + " " + emoji
    return emoji + " " + message


def remove_punctuation(message: str, rng, probability: float = 0.4) -> str:
    """Remove punctuation (most casual messages don't have any)."""
    if rng.random() > probability:
        return message
    return message.rstrip(".,!?;:")


def add_caps_urgency(message: str, rng, probability: float = 0.02) -> str:
    """Make message ALL CAPS for urgency."""
    if rng.random() > probability:
        return message
    return message.upper() + "!!!"


def make_message_realistic(message: str, rng, platform: str = "whatsapp",
                           industry_id: str = None, subsector: str = None) -> str:
    """Apply all realism transforms to a message."""
    # 20% chance it's just a response message (ultra short)
    if rng.random() < 0.20:
        # Use industry-specific responses if available
        if industry_id:
            try:
                from world_engine.industry_jargon import get_industry_response
                resp = get_industry_response(industry_id, subsector or "", rng)
                if resp:
                    # Deduplication: add slight variation to avoid exact repeats
                    if rng.random() < 0.15:
                        resp = resp + " " + rng.choice(["👍", "✅", "", "", ""])
                    return resp.strip()
            except ImportError:
                pass
        return rng.choice(RESPONSE_MESSAGES)
    
    # Apply transforms in order
    message = add_typos(message, rng, 0.05)
    message = add_abbreviations(message, rng, 0.12)
    message = remove_punctuation(message, rng, 0.4)
    
    if platform == "whatsapp":
        message = add_emoji(message, rng, 0.10)
    
    message = add_caps_urgency(message, rng, 0.015)
    
    # Sometimes make it a question
    if rng.random() < 0.08:
        message = message + "?"
    
    # Sometimes add trailing dots (thinking/trailing off)
    if rng.random() < 0.05:
        message = message + "..."
    
    # Sometimes cut off (interrupted)
    if rng.random() < 0.03:
        words = message.split()
        cut = rng.randint(max(1, len(words)//3), max(2, len(words)-1))
        message = " ".join(words[:cut]) + "—"
    
    return message



# ═══════════════════════════════════════════════════════
# 3. WORKPLACE JOKES & HUMOR
# ═══════════════════════════════════════════════════════

WORKPLACE_JOKES = [
    # Universal factory jokes
    "somebody tell the machine it's not Monday anymore, it's still acting up 😂",
    "if this valve gets stuck one more time I'm naming it after my ex",
    "maintenance said 15 minutes... that was 2 hours ago 🤦",
    "canteen biryani today = half the plant in the toilet after lunch",
    "new safety rule: don't die. that's it. that's the rule",
    "this machine and my relationship have something in common — both need maintenance I can't afford",
    "boss said work smarter not harder... still waiting for the smart part",
    "whoever set the AC to 16 degrees wants us to work in Antarctica",
    "Friday feeling but it's only Wednesday 😤",
    "night shift motto: we're not sleeping, we're just resting our eyes",
    "overtime = over time I should have been home",
    "my tools: missing. my lunch: stolen. my patience: gone",
    "legends say the previous shift actually completed all their tasks... just legends though",
    "they should rename the toolbox talk to 'things we already know but pretend to hear for the first time'",
    "me explaining to my wife why I smell like oil: it's not what you think 😂",
    "safety officer saw me and I panicked even though I wasn't doing anything wrong",
    "the WiFi in the break room is the real reason people take long breaks",
    "asked for a raise, got extra responsibility instead 🙃",
    "that moment when the shift is almost over and alarm goes off 💀",
    "weekend plans: sleep. backup plan: more sleep",
    # Language-specific humor
    "anna idi fix ayyi 3 months ayindi... confidence ichchi fix ayyindi antunnaaru 😂",
    "chai break extend chesukunna ani supervisor ki report chesaru 🤦 snitch alert",
    "bhai sahab machine ne aaj mood dikhaya... start nahi ho rahi",
    "oru vela machine human feelings irundha, ithu definitely Monday blues thaan",
    "maintenance bhai ko bulao, machine ne phirse tantrums shuru kiye",
    "ek kaam bolo toh 10 meetings hoti hai, 10 kaam bolo toh 0 meetings",
]

WORKPLACE_HUMOR_RESPONSES = [
    "hahaha 😂", "bro 💀💀", "dead 😂😂😂", "lmaooo", "stopppp 🤣",
    "so true bro", "nailed it 😂", "why is this so accurate",
    "I felt that 😤", "bro same", "real talk though 😂",
    "forwarding this to the group 😂", "screenshot taken 📸",
    "don't let supervisor see this 🤫", "haha but seriously though",
]


# ═══════════════════════════════════════════════════════
# 4. SERIOUS SITUATIONS (Tension, Conflict, Real Drama)
# ═══════════════════════════════════════════════════════

SERIOUS_SITUATIONS = {
    "near_miss_tension": [
        "guys STOP everything. Ravi almost got his hand caught in the conveyor. Everyone take 5 minutes NOW.",
        "I'm shaking... the load almost fell on Suresh. 2 inches. 2 fucking inches from his head.",
        "ok nobody is hurt but this is NOT ok. who removed the guard plate? I want names.",
        "ambulance is here but he's conscious, thank god. just burns on the arm. could have been worse.",
        "this is exactly what I warned about last month. EXACTLY. nobody listened.",
    ],
    "argument_conflict": [
        "I don't care what the previous shift said, this IS my responsibility and they left it like this",
        "with all due respect sir, we've been asking for this part for 3 weeks. production can't wait forever",
        "bro I'm not covering your shift again. last time you said same thing and didn't return the favor",
        "why am I getting blamed? I followed the exact procedure written in the SOP. check the camera.",
        "you call this maintenance? this is the third time in one month. either fix it properly or don't touch it",
        "I'm going to HR about this. I've tolerated enough. this is not about work anymore.",
        "fine. do it your way. but when it fails don't come to me. I'm documenting this.",
    ],
    "emotional_moment": [
        "guys I need to leave early today... my father was admitted to hospital this morning",
        "just got a call. I'm a father now 🙏 baby girl, mother and baby both healthy. sorry for being distracted today",
        "today is Ramu's last day after 28 years. whatever he needs today, we make it happen. no questions.",
        "I know we're all stressed about the layoff rumors. let's just focus on work. whatever happens, happens.",
        "Venkat's accident last week really affected everyone. counselor is available in conference room till 5pm.",
        "they approved my transfer... mixed feelings honestly. going to miss this team. been here 7 years.",
    ],
    "management_pressure": [
        "corporate wants 20% more output with same people. I told them it's not possible. they said make it happen.",
        "quarterly review tomorrow. numbers are 12% below target. everyone needs to push today and tomorrow.",
        "client visiting day after tomorrow. I need this place spotless. every single machine cleaned and painted.",
        "budget cut by 30%. we're losing 2 positions. I'm sorry. I fought for it but headquarters decided.",
        "new KPIs start Monday. attendance, output per hour, quality rate, and zero incidents. yes all of them.",
    ],
    "safety_crisis": [
        "🚨 EMERGENCY — gas leak detected in Zone C. Evacuate NOW. Assembly point B. Head count in 5 minutes.",
        "FIRE ALARM ACTIVATED — this is NOT a drill. everyone out through nearest exit. DO NOT use elevator.",
        "ALL STOP. Power isolation confirmed. Nobody enters the panel room until I give clearance personally.",
        "man down in confined space. rescue team deployed. ambulance called. everyone else stay CLEAR.",
        "chemical spill in lab section. corridor blocked. use alternate route via canteen side. decontamination team en route.",
    ],
    "financial_worry": [
        "salary still not credited... it's the 7th already. anyone else facing this?",
        "heard from accounts that bonus is not happening this year. after all the overtime we put in 😤",
        "PF withdrawal rejected AGAIN. third time. these government websites I swear...",
        "inflation killing us bro. same salary for 3 years but petrol, rice, rent everything doubled",
        "they're outsourcing our department... the contractor guys will do same work for half our salary",
    ],
    "resignation_shock": [
        "whaaaaat Kumar resigned???? he was here for 12 years. who's going to handle boiler section now?",
        "3 people resigned this month alone. management still thinks there's no problem 🙄",
        "I handed in my resignation today. got a better offer. serving notice period from Monday.",
        "team meeting at 3pm. apparently Sharma sir is retiring next month. this is unexpected.",
    ],
}


def generate_joke(rng) -> str:
    """Generate a workplace joke/humor message."""
    return rng.choice(WORKPLACE_JOKES)


def generate_joke_response(rng) -> str:
    """Generate a response to a joke."""
    return rng.choice(WORKPLACE_HUMOR_RESPONSES)


def generate_serious_situation(rng, situation_type: str = None) -> str:
    """Generate a serious workplace situation message."""
    if situation_type is None:
        situation_type = rng.choice(list(SERIOUS_SITUATIONS.keys()))
    return rng.choice(SERIOUS_SITUATIONS[situation_type])



# ═══════════════════════════════════════════════════════
# 5. PERSON CONTINUITY ENGINE
# ═══════════════════════════════════════════════════════

class PersonContinuityEngine:
    """Keeps the same person active for 3-10 events before switching."""
    
    def __init__(self, workers: list, rng):
        self.workers = workers
        self.rng = rng
        self.current_person = rng.choice(workers) if workers else None
        self.events_remaining = rng.randint(3, 10)
        self.conversation_partner = None
    
    def get_active_person(self) -> dict:
        """Get the currently active person (same for multiple events)."""
        if self.events_remaining <= 0:
            # Switch to new person
            self.current_person = self.rng.choice(self.workers)
            self.events_remaining = self.rng.randint(3, 10)
            self.conversation_partner = None
        
        self.events_remaining -= 1
        return self.current_person
    
    def get_conversation_partner(self) -> dict:
        """Get someone for the active person to talk to."""
        if self.conversation_partner is None:
            possible = [w for w in self.workers if w != self.current_person]
            if possible:
                self.conversation_partner = self.rng.choice(possible)
        return self.conversation_partner
    
    def should_generate_response(self) -> bool:
        """30% chance the next event is a response to the previous."""
        return self.rng.random() < 0.30


# ═══════════════════════════════════════════════════════
# 6. MOOD PERSISTENCE ENGINE
# ═══════════════════════════════════════════════════════

class MoodEngine:
    """Mood persists for hours, only changes on triggers."""
    
    MOODS = ["routine", "focused", "tired", "cheerful", "stressed", 
             "bored", "anxious", "irritated", "excited", "calm"]
    
    def __init__(self, rng):
        self.rng = rng
        self.current_mood = "routine"
        self.mood_duration = rng.randint(20, 80)  # Events until mood might change
        self.events_in_mood = 0
    
    def get_mood(self) -> str:
        """Get current mood (persists across many events)."""
        self.events_in_mood += 1
        
        # Small chance of natural mood drift
        if self.events_in_mood > self.mood_duration:
            if self.rng.random() < 0.3:  # 30% chance to change after duration
                self.current_mood = self.rng.choice(self.MOODS)
                self.mood_duration = self.rng.randint(20, 80)
                self.events_in_mood = 0
        
        return self.current_mood
    
    def trigger_mood_change(self, trigger: str):
        """Force mood change based on event trigger."""
        triggers = {
            "accident": "anxious",
            "joke": "cheerful",
            "argument": "irritated",
            "praise": "excited",
            "bad_news": "stressed",
            "end_of_shift": "tired",
            "pay_day": "cheerful",
            "overtime_announced": "irritated",
            "problem_solved": "calm",
            "deadline": "stressed",
        }
        if trigger in triggers:
            self.current_mood = triggers[trigger]
            self.mood_duration = self.rng.randint(15, 50)
            self.events_in_mood = 0


# ═══════════════════════════════════════════════════════
# 7. INTEGRATION — Apply all realism to a message
# ═══════════════════════════════════════════════════════

def apply_full_realism(message: str, rng, category: str, hour: int,
                       mood: str, platform: str = "whatsapp",
                       industry_id: str = None, subsector: str = None) -> str:
    """Apply all realism layers to a message.
    
    This is the master function that makes output undetectable.
    """
    # 5% chance: replace with a joke (humans joke at work!)
    if rng.random() < 0.04 and category in ("human_relations", "canteen_food", 
                                             "gossip_rumors", "personal_life"):
        return generate_joke(rng)
    
    # 3% chance: replace with joke response
    if rng.random() < 0.03 and category == "human_relations":
        return generate_joke_response(rng)
    
    # 2% chance: serious situation
    if rng.random() < 0.02 and category in ("safety_accidents", "workforce", 
                                             "business", "leadership"):
        return generate_serious_situation(rng)
    
    # 1% chance: emotional moment
    if rng.random() < 0.01:
        return generate_serious_situation(rng, "emotional_moment")
    
    # Night shift: sometimes add tired/lonely messages
    if hour >= 23 or hour <= 4:
        if rng.random() < 0.1:
            night_msgs = [
                "still 4 more hours to go 😴", "so quiet tonight its creepy",
                "anyone else awake?", "coffee #4 ☕", "counting hours...",
                "heard something in zone B... probably just the wind",
                "my eyes are closing... need to walk around",
                "dawn coming soon, almost there", "last round then chai break",
            ]
            return rng.choice(night_msgs)
    
    # Lunch time: food messages
    if 12 <= hour <= 13:
        if rng.random() < 0.08:
            food_msgs = [
                "what's in canteen today?", "brought lunch from home 🍱",
                "biryani!!! finally 🔥", "same dal chawal again 😤",
                "anyone ordering from outside?", "too spicy today bro",
                "saving seat for you", "hurry up line is getting long",
            ]
            return rng.choice(food_msgs)
    
    # Apply message realism (typos, abbreviations, emoji, etc.)
    message = make_message_realistic(message, rng, platform,
                                     industry_id=industry_id, subsector=subsector)
    
    return message

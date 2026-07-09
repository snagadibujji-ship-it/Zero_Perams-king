"""
Industry-Specific Message Templates
=====================================
Real messages that sound like they come from THAT specific industry.
Based on research into actual operations, jargon, and daily routines.

Each industry gets templates for:
- daily_ops: Normal day-to-day work
- maintenance: Equipment issues and fixes
- safety_accidents: Safety events specific to that industry
- crisis: Industry-specific emergencies
- night: What happens at night in this industry
- quality: Quality-specific issues
- human_relations: How workers in this industry socialize

Usage:
    from world_engine.industry_messages import get_industry_message
    msg = get_industry_message(industry_id, category, rng)
"""
import random
from typing import Optional, Dict, List


# ═══════════════════════════════════════════════════════════════════
# TOP 20 INDUSTRIES — Fully researched, real-world accurate
# ═══════════════════════════════════════════════════════════════════

INDUSTRY_MESSAGES: Dict[str, Dict[str, List[str]]] = {}


# ─── AI RESEARCH LAB ────────────────────────────────────────────
INDUSTRY_MESSAGES["ai_research_lab"] = {
    "daily_ops": [
        "training run epoch {n}/100, loss dropped to 0.{x} — looking good",
        "GPU cluster utilization at {n}%, 3 A100s idle — anyone need compute?",
        "model checkpoint saved at step {n}k. running eval on val set now",
        "pip install hanging on the shared node again. who's hogging /tmp?",
        "jupyter kernel died mid-experiment. lost my notebook state 😤",
        "wandb dashboard shows training diverged after lr warmup. rolling back to last checkpoint",
        "new dataset uploaded to s3. 2.3M samples after dedup, needs quality check",
        "code review for the attention patch has 47 comments already 🙄",
        "hyperparameter sweep done. best config: lr=3e-4, batch=512, warmup=2k steps",
        "tokenizer vocab size debate again... 32k vs 64k. running ablation",
        "downloading pretrained weights from HF hub. 14GB, slow connection",
        "distributed training on 8 nodes started. watching for stragglers",
        "eval metrics: perplexity 4.2, BLEU 38.7, ROUGE-L 0.41. not bad",
        "slurm job queued for 3 hours. cluster is packed this week",
        "mixed precision training enabled. memory usage dropped 40%",
        "data pipeline bottleneck — GPU util only 60% because data loading is slow",
        "paper deadline in 4 days. results section still needs 2 more experiments",
        "ablation study running: with vs without rotary embeddings",
        "model inference latency: 45ms/token on A100. need to get under 30ms",
        "pushed training script to main branch. CI tests passing",
    ],
    "maintenance": [
        "GPU 7 in node-03 showing ECC memory errors. pulling from pool",
        "CUDA out of memory on A100 — someone is leaking tensors. checking processes",
        "NVLink bandwidth degraded between GPU 4-5. hardware team reseating tomorrow",
        "cooling loop pressure drop in server room B. HVAC team notified, temps rising",
        "NFS mount hung on /data partition. all training jobs stalled across cluster",
        "VRAM ghost — 8GB allocated but no process claiming it. need to reboot node",
        "InfiniBand switch showing packet drops. network team investigating",
        "SSD in storage node almost full. archiving old checkpoints to cold storage",
        "power supply unit failed in rack 7. redundant PSU holding but need replacement",
        "fan failure alert on GPU node-12. ambient temp climbing to 35°C",
        "firmware update needed on all H100s. scheduling maintenance window for Sunday",
        "memory bank error on node-05 DIMM slot 3. running memtest overnight",
    ],
    "safety_accidents": [
        "server room fire suppression system test tomorrow 2pm. everyone out by 1:45",
        "someone tripped over network cables in the GPU room. cable management needed",
        "burned hand on hot GPU heatsink during maintenance. first aid applied",
        "UPS battery leaked acid. hazmat protocol for server room C",
        "ergonomic assessment — 3 people reporting wrist pain from keyboard use",
    ],
    "crisis": [
        "🔥 FIRE ALARM server room B — sprinklers activated. ALL GPUs OFFLINE",
        "complete power outage to GPU cluster. 3 days of training GONE. no recent checkpoint",
        "data breach — credentials found in public GitHub repo. rotating all keys NOW",
        "cooling system failure — GPUs throttling hard, cluster shutting down automatically",
        "ransomware detected on storage server. isolating network segment immediately",
    ],
    "night": [
        "overnight training run going smooth. loss: 0.23 → 0.19 past 4 hours",
        "3am GPU temp check: all cards under 78°C. cluster humming along",
        "model finished training at 4:17am. eval looks promising. will review in morning",
        "silent night in the lab. just the hum of 128 GPUs and the AC",
        "automated sweep found a better hyperparameter config at 2am. nice",
        "night build broke. CI failure on the preprocessing pipeline. leaving note for morning team",
        "only me and the GPUs awake. monitoring long training run",
        "checkpoint auto-saved at 1am. if anything crashes overnight we're safe",
    ],
    "quality": [
        "model output showing repetition artifacts. investigating tokenizer issue",
        "benchmark scores dropped 2 points after yesterday's code change. reverting",
        "data contamination found — test set samples leaked into training data",
        "hallucination rate increased to 12% on factual QA. need better RLHF",
        "evaluation reproducibility issue — different seeds giving 5% variance",
    ],
    "human_relations": [
        "paper got accepted at NeurIPS! team celebration tonight 🎉",
        "who wants coffee? making a run to the machine",
        "new intern starting Monday. someone show them the cluster docs",
        "research meeting in 10 min. bring your results or bring your excuses",
        "friday demo day — who's presenting this week?",
        "arxiv paper drop today — our competitor beat us to the same idea 😤",
    ],
}


# ─── OIL REFINERY ───────────────────────────────────────────────
INDUSTRY_MESSAGES["oil_refining"] = {
    "daily_ops": [
        "board operator log: CDU running at {n}% capacity. overhead temp stable at 127°C",
        "field rounds complete. checked cat cracker, hydrogen plant, all normal",
        "crude throughput today: {n},000 barrels. target met",
        "shift handover: turnaround prep starts next week. punchlist has 47 items",
        "flare header pressure steady at 0.3 barg. no flaring events this shift",
        "tank farm levels: T-101 at 72%, T-103 at 45%, T-107 at 88% — dispatch needed",
        "process permit issued for hot work on exchanger E-201",
        "furnace F-301 firing rate adjusted. tube skin temps within spec",
        "lab results back: pour point OK, sulfur content 0.8% — within grade spec",
        "panel readings all green. DCS showing no active alarms",
        "crude unit desalter performing well. BS&W at 0.3%",
        "control valve CV-105 hunting. tuning needed but stable for now",
        "night shift handover: main issues are cooling tower fan 3 vibration and steam trap leak on unit 5",
        "pump P-201A swap done. B pump now primary, A on standby",
        "permit to work #4567 closed out. confined space entry complete, gas free confirmed",
    ],
    "maintenance": [
        "pump P-401 seal leak getting worse. planned replacement next turnaround but monitoring daily",
        "heat exchanger E-105 fouling — approach temp up 8°C from design. scheduling cleaning",
        "control valve positioner failed on FV-301. manual operation until spare arrives",
        "cooling tower fan #3 vibration at 8mm/s. bearing replacement scheduled",
        "steam trap survey: 12 out of 180 found failed open. wasting {n} tons/hr of steam",
        "instrument air dryer showing high dew point. switching to backup while we service",
        "fin fan air cooler tube bundle leak confirmed with helium test. isolating for repair",
        "safety relief valve SRV-201 due for bench test. ops preparing isolation plan",
        "compressor K-101 lube oil analysis: iron particles elevated. increasing monitoring frequency",
        "DCS controller card showing intermittent faults. spare card on order, ETA 3 days",
    ],
    "safety_accidents": [
        "H2S alarm at unit 5 boundary fence. wind direction check — all clear, dissipated",
        "near miss: dropped wrench from platform level 3. barricade area below immediately",
        "small hydrocarbon leak on flange joint. isolated, depressured, bolting being retorqued",
        "LEL detector reading 15% at ground level near sump. gas testing in progress",
        "permit violation: contractor found without gas monitor in hazardous zone",
        "safety stand-down called after near miss. toolbox talk in control room at 0800",
    ],
    "crisis": [
        "🚨 EMERGENCY SHUTDOWN initiated — high level in knockout drum V-301",
        "unit trip — loss of instrument air. all control valves failed to safe position",
        "FIRE at pump P-501. fire monitors activated. emergency response team deployed",
        "H2S release detected. wind sock shows toward parking lot. MUSTER POINT B",
        "cat cracker reactor temp excursion — 30°C above normal. emergency quench activated",
        "power failure to MCC-7. crude unit lighting and some instruments lost",
    ],
    "night": [
        "2am field round: all pump seals dry, no leaks detected this round",
        "night shift quiet. only alarm is level transmitter on T-104 — known drift issue",
        "panel watch: CDU stable. waiting for lab results on diesel cloud point",
        "3am boiler blowdown completed as per schedule. logs updated",
        "flare tip glowing slightly — normal for this throughput. no flaring events",
        "night handover note: watch P-301 discharge pressure. been trending up slowly",
    ],
    "quality": [
        "product off-spec: diesel sulfur at 12ppm vs 10ppm limit. re-routing to slop tank",
        "lab flash point test failed on kerosene. holding in tank pending reprocessing",
        "crude assay results received. new cargo higher in naphthenic acids than expected",
        "blending error: wrong tank selected for gasoline component. investigating",
    ],
    "human_relations": [
        "chai break at control room. panel operator watching for the team",
        "turnaround bonus confirmed for all who worked the shutdown. finally",
        "retirement function for Rajan sir next Friday. 32 years at this refinery",
        "who's swapping shifts for Diwali week? check the roster board",
    ],
}


# ─── RICE FARMING (Indian context) ──────────────────────────────
INDUSTRY_MESSAGES["rice_farming"] = {
    "daily_ops": [
        "transplanting started in field 3. 8 laborers working since 6am",
        "bore well water level at {n} feet. running pump for 4 hours today",
        "DAP fertilizer application done in eastern plot. 2 bags per acre",
        "checked paddy growth — tillers coming nicely. about 45 days old now",
        "tractor sent for land leveling in the new plot. should finish by evening",
        "spraying pesticide today — wearing mask and gloves as advised",
        "canal water release scheduled tomorrow. opening our channel gate at 5am",
        "harvester booked for next week. crop looks ready in 10-12 days",
        "mandi rate today: paddy at ₹{n}/quintal. should we sell or hold?",
        "loaded 40 bags onto truck for mandi. driver says he'll be back by evening",
        "bund repair done on western side. last monsoon washed it partially",
        "nursery bed prepared for next season. seedlings should be ready in 25 days",
        "drip irrigation pipe clogged again in section 2. cleaning with acid treatment",
        "soil testing report came: nitrogen low, need more urea this time",
        "labor contractor says workers available only after 9am tomorrow. festival today",
    ],
    "maintenance": [
        "pump motor winding burnt. electrician coming from town. ₹2500 for repair",
        "tractor hydraulic leak from the PTO shaft area. mechanic checking tomorrow",
        "sprinkler nozzles clogged with calcium deposits. soaking in vinegar",
        "motor starter capacitor blown. bought new one from hardware shop",
        "bore well pipe rusted at 50 feet. pulling out for replacement next week",
        "thresher belt worn thin. ordered new one. using neighbor's machine till then",
    ],
    "safety_accidents": [
        "snake seen near pump house. everyone be careful walking in tall grass",
        "labor got stung by wasp nest while cutting bunds. gave antihistamine",
        "tractor tyre punctured on field road. nobody hurt but delayed work 2 hours",
        "pesticide drift to neighbor's organic field. he's upset. need to be more careful with wind direction",
        "scorpion found in storage shed this morning. cleared area with torch",
    ],
    "crisis": [
        "heavy rain forecast next 3 days — paddy is almost ready. need emergency harvest NOW",
        "canal breach near village. fields getting flooded. all hands to strengthen bund",
        "bore well collapsed. total loss. need ₹80,000 for new boring. devastated",
        "locust swarm sighted 20km away. preparing nets and smokers",
        "crop insurance claim rejected AGAIN. writing to collector's office",
    ],
    "night": [
        "sleeping at field tonight. nilgai tracks seen near boundary yesterday",
        "torch patrol done at 11pm. no animals near the standing crop. back to cot",
        "wild boar dug up 3 rows of planted area on north side. heartbreaking",
        "set up firecrackers on trip wire near field entry. should scare animals",
        "can't sleep. mosquitoes terrible tonight. burning neem leaves near cot",
        "neighbor's dog barking continuously. might be jackal nearby. going to check",
        "2am — heard movement in paddy. shone torch. just a hare. false alarm",
        "cold tonight at the field. wrapped in blanket on charpai. pump humming in background",
        "full moon night. can see the entire field clearly. all good so far",
        "woke up to sound of munching. nilgai already in field. chased with torch and shouting",
        "set up solar light near crop boundary. animals avoid lighted areas usually",
        "WhatsApp group says wild boar attacked Ramappa's sugarcane field last night. staying alert",
    ],
    "quality": [
        "some yellowing in paddy leaves. might be nitrogen deficiency or blast disease",
        "grain filling stage — checking for discoloration. looks healthy",
        "moisture content of harvested paddy: 14%. good for storage",
        "some weevil damage in stored bags. fumigation needed before selling",
    ],
    "human_relations": [
        "tea and biscuit break under the neem tree. good morning everyone",
        "labor payment day. ₹400/day per person. 8 workers × 6 days",
        "neighbor's son got government job. whole village celebrating",
        "village meeting tonight about canal water sharing dispute",
        "harvest festival next week. planning pooja at field before cutting starts",
    ],
}

# Also apply to wheat and sugarcane with slight variations
INDUSTRY_MESSAGES["wheat_farming"] = INDUSTRY_MESSAGES["rice_farming"].copy()
INDUSTRY_MESSAGES["sugarcane_farming"] = INDUSTRY_MESSAGES["rice_farming"].copy()


# ─── HOSPITAL ───────────────────────────────────────────────────
INDUSTRY_MESSAGES["hospital"] = {
    "daily_ops": [
        "morning rounds complete. 34 patients on floor, 3 critical in ICU",
        "bed occupancy at {n}%. only 4 beds available in general ward",
        "OT schedule: 6 surgeries today. first one started at 8am — knee replacement",
        "pharmacy stock check: insulin running low. raised indent for 200 vials",
        "patient discharge summary pending for bed 12, 14, 22. doctors please update",
        "lab results uploaded for all morning samples. 3 flagged — critical values called in",
        "emergency dept wait time currently 45 minutes. 12 patients in queue",
        "visiting hours 4-6pm. security to enforce no more than 2 visitors per patient",
        "blood bank stock: O+ low (4 units), AB- critical (1 unit). calling donors",
        "new admission from ER — chest pain, male, 52 years. ECG done, troponin sent",
        "dietitian rounds complete. 8 diabetic patients counseled on meal plan",
        "consultant on call today: Dr. Sharma (Medicine), Dr. Rao (Surgery)",
        "MRI machine booked solid till 6pm. urgent scan needs approval from HOD",
        "infection control audit this week. hand hygiene compliance last month: 78%",
        "NABH documentation review for accreditation. files needed from all departments",
    ],
    "maintenance": [
        "ventilator #3 in ICU showing error code E-07. biomedical engineer called",
        "elevator stuck between 2nd and 3rd floor. no patients inside. technician on way",
        "AC in operation theatre not cooling properly. temp at 24°C instead of 20°C",
        "suction machine not building adequate vacuum. checking for leaks in tubing",
        "nurse call bell system down in ward B. electrician working on it",
        "autoclave failed validation run. sterilization delayed. using sterile supplies from CSSD backup",
        "oxygen pipeline pressure drop in ICU wing. manifold room checking cylinder changeover",
        "UPS battery backup: only 20 minutes remaining if power fails. generator test scheduled",
    ],
    "safety_accidents": [
        "needle stick injury reported by staff nurse Priya. PEP protocol initiated",
        "patient fall from bed — elderly lady, ward 3. no fracture on X-ray, observation",
        "blood spill in corridor near lab. housekeeping doing spill protocol cleanup",
        "fire drill scheduled for Thursday 2pm. all departments to participate",
        "COVID-suspected patient in ER. isolation protocol activated. PPE donned",
    ],
    "crisis": [
        "🚨 CODE BLUE — cardiac arrest bed 18 ICU. crash cart to bedside. team assembling",
        "mass casualty alert: bus accident on highway. 15+ injured incoming. activate disaster plan",
        "oxygen supply critically low. tanker delayed by 4 hours. rationing O2 flow rates",
        "blood bank contamination suspected. quarantining batch #4521. crossmatch all pending units",
        "power failure — generator kicked in but OT lights flickered. surgery was in progress",
    ],
    "night": [
        "night round 11pm: all ICU patients stable. ventilator settings unchanged",
        "emergency admission at 2am — road accident, multiple fractures. OT being prepared",
        "ward quiet. only call from bed 7 — patient needs pain medication. given injection",
        "3am vital signs: patient in bed 4 BP dropping. calling resident doctor",
        "night sister report: 2 new admissions, 1 discharge, no code events so far",
        "crash cart check done at midnight. defibrillator charged, drugs not expired",
        "security called — relative trying to enter ICU after hours. counseled and sent back",
        "labor room update: delivery expected around 4am. midwife monitoring",
        "ventilator alarm in ICU — circuit disconnected. reconnected immediately. patient fine",
    ],
    "quality": [
        "medication error caught by pharmacist — wrong dose prescribed. corrected before administration",
        "surgical site infection rate this month: 2.1%. target is <2%. root cause analysis needed",
        "patient satisfaction survey: 4.2/5 this quarter. complaint about food quality",
        "hand hygiene audit: OT compliance 95%, ward B only 68%. remedial training scheduled",
    ],
    "human_relations": [
        "happy birthday Dr. Kumar! cake in the duty room at lunch break",
        "night duty is killing me. 4th consecutive night. need rest badly",
        "new batch of nursing students starting posting today. please be patient with them",
        "hospital day celebration next week. cultural program rehearsals in auditorium",
        "canteen food complaint again. same dal-rice every day 😤",
    ],
}


# ─── COAL MINING ────────────────────────────────────────────────
INDUSTRY_MESSAGES["coal_mining"] = {
    "daily_ops": [
        "pre-shift gas examination complete. CH4 at 0.3%, within safe limits. cleared to enter",
        "cage winding done. first batch of 20 miners descended to Level {n}",
        "continuous miner advancing face at 3.2m per cut. roof bolting following behind",
        "coal production this shift: {n} tonnes. conveyor running at full speed",
        "ventilation check: airflow at face 1.8 m³/s. adequate for this section",
        "shot firing scheduled for 2pm. all personnel to withdraw beyond 200m mark",
        "belt conveyor #3 running. coal transfer from section B to surface bunker",
        "deputy's inspection complete. no unsafe conditions reported in districts 4 and 5",
        "pumping station running. water level in sump at 1.2m — normal",
        "stone dusting completed in return airway as per schedule",
        "coal handling plant processing at {n} tonnes/hour. washery operating normally",
        "pit head bath operational. shift change at 2pm, all men accounted for",
        "manriding system checked. all signals working on cage indicators",
        "roof condition in panel 7: some convergence noticed. installing extra props",
        "blasting report: 45 holes drilled, 38 charged. firing at end of shift",
    ],
    "maintenance": [
        "continuous miner cutter head worn. changing picks during maintenance shift",
        "conveyor belt splice failed at junction 4. repair team dispatched. 2 hour delay",
        "shuttle car hydraulic hose burst. oil spill contained. replacement in progress",
        "roof bolter drill bit stuck in sandstone layer. extracting carefully",
        "ventilation fan bearing temperature high. reducing speed and monitoring",
        "pump #2 impeller worn. flow rate dropped. switching to standby pump",
        "electrical cable damage in section 6. power isolated for repair",
        "methane drainage borehole clogged. re-drilling from surface planned",
    ],
    "safety_accidents": [
        "methane spike at face: 1.8% CH4. operations stopped. ventilation being checked",
        "minor roof fall in old workings. no one in area. cordoned off",
        "miner's lamp damaged by falling rock. replacement issued. no injury",
        "gas monitoring alarm activated in return airway. evacuation initiated as precaution",
        "first aid: miner's hand caught in conveyor nip point. superficial laceration. wearing gloves",
        "safety inspection by DGMS tomorrow. all deputies check their districts tonight",
    ],
    "crisis": [
        "🚨 METHANE LEVEL 2.5% — ALL PERSONNEL EVACUATE IMMEDIATELY. power tripped automatically",
        "ROOF COLLAPSE in panel 9. all men accounted for. no one in affected zone. rescue team standby",
        "underground fire detected by CO sensors. sealing protocol initiated. everyone to surface NOW",
        "cage stuck between levels. 8 miners inside. manual winding being attempted. calm voices on intercom",
        "water inrush from old abandoned workings. pumps at maximum capacity. water level rising",
    ],
    "night": [
        "night shift underground. face advancing slowly. roof conditions tricky in this section",
        "surface operations quiet. coal stockpile being loaded onto rakes for dispatch",
        "3am gas check: all readings normal. CH4 0.2%, CO nil, O2 20.8%",
        "continuous miner operating on night shift. {n} tonnes cut so far",
        "winding engine room night watch: all clear. cage movements logged",
        "ventilation system running. monitoring temperatures in deep sections",
    ],
    "quality": [
        "coal sample analysis: ash content 34%, within Grade D specification",
        "oversized coal blocking crusher inlet. breaking manually before feeding",
        "washery recovery rate at 62% today. middlings going to reject dump",
        "customer complaint about high moisture in last rake. sampling more carefully now",
    ],
    "human_relations": [
        "tea at pit head canteen. everyone gathering before going underground",
        "bonus announcement for Diwali. miners celebrating",
        "new batch of mining trainees joining next month. safety training first week",
        "retirement of Overman Shankar ji after 30 years underground. respect 🙏",
        "union meeting about overtime rates and mechanization concerns",
    ],
}
INDUSTRY_MESSAGES["iron_ore_mining"] = INDUSTRY_MESSAGES["coal_mining"].copy()


# ─── SEMICONDUCTOR FAB ──────────────────────────────────────────
INDUSTRY_MESSAGES["semiconductor_fab"] = {
    "daily_ops": [
        "particle count check: Bay 4 reading 3 particles/m³ at 0.1μm. ISO Class 1 compliant",
        "lot WF-{n}47 entered photolithography. 300mm wafers, 7nm node",
        "etch tool chamber A qualified after PM. running 5 monitor wafers first",
        "CMP process running on lot 23. slurry flow rate stable at 200ml/min",
        "wafer inspection: 2 defects found on wafer #12. SEM review scheduled",
        "ion implant dose verification passed. uniformity within 0.5%",
        "FOUP transfer from stocker to litho track complete. 25 wafers in lot",
        "fab yield this week: 93.2%. target 95%. investigating defect source",
        "reticle inspection clean. no haze detected. cleared for production",
        "CVD film thickness: 52.3nm ± 0.4nm. within spec. proceeding to next step",
        "AMC monitor alarm in Bay 7 — checking molecular contamination levels",
        "metrology data uploaded. CD measurements within 1nm tolerance",
        "recipe change request approved for poly etch. implementing on tool 3B",
        "WIP count: 847 lots in fab. cycle time trending 2 days above target",
        "gowning room audit: all personnel compliant. no exposed skin, no cosmetics",
    ],
    "maintenance": [
        "etch chamber seasoning after wet clean. running 25 conditioning wafers",
        "turbo pump on CVD tool showing elevated vibration. PM scheduled for tonight",
        "chemical delivery system: TEOS bottle almost empty. bottle change at 6pm",
        "chiller on litho tool #2 not holding temperature. fluctuating ±0.5°C",
        "robot arm on track tool misaligned by 0.2mm. recalibrating",
        "gas cabinet leak check failed on SiH4 line. isolating until fixed",
        "particle excursion after PM on sputter tool. running extra qualification wafers",
    ],
    "safety_accidents": [
        "chemical spill in wet bench area — HF containment protocol activated",
        "toxic gas monitor alarmed in gas yard. SiH4 level at 3ppm. evacuating area",
        "cleanroom gown tear detected during entry. technician re-gowned before entering",
        "compressed gas cylinder restraint found loose in gas cabinet. secured immediately",
    ],
    "crisis": [
        "FAB SHUTDOWN — particle event detected. all tools stopped for investigation",
        "chemical supply interrupted. 5 wet bench tools down. production halted",
        "power flicker caused 12 tools to fault. requalification needed. 2-day yield impact",
        "contamination found on reticle. potentially affected 200+ wafers. quarantining lots",
    ],
    "night": [
        "night shift: fab running automated. monitoring tools from control room",
        "3am — particle counter excursion in Bay 2. investigating source. might be filter",
        "overnight lot processing smooth. 15 lots completed through etch",
        "maintenance window 2-4am on litho tool 5. PM and qualification running",
    ],
    "quality": [
        "wafer defect map shows clustering in center. possible chuck contamination",
        "electrical test yield: lot 45 at 88%. lower than normal. parametric check needed",
        "SPC chart showing drift on film thickness. adjusting deposition time",
        "customer audit next week. preparing documentation for ISO 9001 and IATF 16949",
    ],
    "human_relations": [
        "shift handover meeting in cleanroom conference room. 10 min",
        "new engineer doing bunny suit training today. showing them gowning procedure",
        "team dinner to celebrate 95% yield milestone last month 🎉",
        "anyone want to swap Saturday night shift? I have a family event",
    ],
}
INDUSTRY_MESSAGES["electronics_pcb"] = INDUSTRY_MESSAGES["semiconductor_fab"].copy()


# ─── SOFTWARE COMPANY ───────────────────────────────────────────
INDUSTRY_MESSAGES["software_company"] = {
    "daily_ops": [
        "standup: working on the auth service refactor. should have PR up by EOD",
        "deployed v2.4.1 to staging. running regression tests now",
        "JIRA board: 8 tickets in progress, 3 in review, 12 in backlog",
        "sprint planning at 11am. bring your estimates. no sandbagging please 😂",
        "merged the API pagination fix. CI/CD pipeline building... fingers crossed",
        "production metrics: 99.7% uptime this month. one blip on Tuesday",
        "code review done for Arun's PR. 4 comments, mostly style fixes",
        "database migration script tested on staging. ready for production Friday night",
        "customer reported bug: timeout on search when results > 1000. investigating",
        "load test results: API handles 5k req/s before degrading. need optimization",
        "new feature flag added for dark mode. rolling out to 10% of users first",
        "AWS bill this month: ${n}k. that unused RDS instance is still running",
        "documentation updated for the new webhook API. swagger spec published",
        "intern's first PR merged! clean code. good variable names. impressed",
        "tech debt sprint next week. finally tackling that auth module everyone hates",
    ],
    "maintenance": [
        "production alert: disk space at 92% on primary DB server. expanding volume",
        "SSL certificate expiring in 7 days. renewing through ACM",
        "Redis cache hit rate dropped to 60%. investigating key eviction pattern",
        "Kubernetes pod OOMKilled. increasing memory limit from 512MB to 1GB",
        "log aggregation pipeline lagging 30 minutes. Elasticsearch cluster overloaded",
        "CDN cache invalidation not propagating. users seeing stale content",
        "dependency vulnerability alert: critical CVE in logging library. patching today",
    ],
    "safety_accidents": [
        "phishing email targeting engineering team detected. don't click links from 'IT Admin'",
        "someone accidentally pushed to main without PR review. reverting",
        "production credentials were briefly visible in Slack. rotated immediately",
    ],
    "crisis": [
        "🚨 PRODUCTION DOWN — database connection pool exhausted. all APIs returning 503",
        "data corruption detected in user profiles table. rolling back to last backup",
        "DDoS attack ongoing. WAF rules updated but traffic still spiking at 50x normal",
        "deployment broke checkout flow. $$$$ revenue impact. ROLLING BACK NOW",
        "AWS us-east-1 regional outage affecting all services. failover to us-west-2 initiated",
    ],
    "night": [
        "2am deployment window. migration running. estimated 45 min downtime",
        "on-call alert: 5xx error rate spiked to 2%. checking logs",
        "overnight batch job completed. 2.3M records processed successfully",
        "got paged at 3am for a false alarm. monitoring threshold too sensitive",
        "production stable through the night. no incidents. going back to sleep",
    ],
    "quality": [
        "code coverage dropped to 72%. we agreed on 80% minimum. adding tests",
        "performance regression: page load time increased from 1.2s to 2.8s. profiling",
        "accessibility audit: 14 violations found. mostly missing alt text and contrast issues",
        "unit tests flaky — 3 tests fail randomly on CI. timing-dependent. fixing",
    ],
    "human_relations": [
        "who broke the build? 🔥 check your commits people",
        "team lunch at 1pm. ordering from the new Thai place",
        "WFH tomorrow — plumber coming. will be on Slack though",
        "annual hackathon next month. forming teams. who's in?",
        "farewell for Sneha on Friday. 3 years here. cake in meeting room at 4pm",
    ],
}


# ─── AUTOMOBILE ASSEMBLY ────────────────────────────────────────
INDUSTRY_MESSAGES["automobile_assembly"] = {
    "daily_ops": [
        "line speed at {n} units/hour. target 58 JPH. running smooth",
        "body shop: 234 bodies welded this shift. 2 rework for weld spatter",
        "paint booth humidity at 62%. within spec for metallic clear coat",
        "trim line: door panel fit issue on unit #4{n}7. adjusted jig alignment",
        "engine marriage station running. torque values all within spec",
        "JIT delivery arrived from vendor — seats for today's 2nd shift production",
        "quality gate check: 3 vehicles held for inspection. paint defect, gap issue, missing clip",
        "shift production: 467 units. target was 480. 13 short due to line stop at 10:30",
        "andon pull at station 23 — worker needed help with windshield alignment",
        "chassis line takt time: 62 seconds. team leader monitoring bottleneck at station 18",
        "new model changeover prep: fixtures arriving next week for MY2025 variant",
        "material kitting area restocked. next 4 hours of parts ready on lineside",
        "robot program updated for new weld pattern on rear subframe",
        "vehicle #12{n}8 completed final inspection. rolling off line to yard",
        "kanban cards triggered for 200 bumper fascias. supplier delivering by 3pm",
    ],
    "maintenance": [
        "robot R-07 in body shop showing servo error. maintenance resetting",
        "paint booth filter differential pressure high. changing filters tonight",
        "conveyor chain stretch detected at station 14. tension adjustment needed",
        "spot weld gun tip worn on robot 12. tip dress cycle overdue. replacing",
        "air supply pressure drop on pneumatic tools. compressor #2 tripped offline",
        "AGV battery low on carrier #8. routing to charging station",
    ],
    "safety_accidents": [
        "pinch point injury: operator's finger caught in clamp fixture. first aid given. no fracture",
        "ergonomic concern: overhead operation at station 22 causing shoulder strain. rotation needed",
        "near miss: AGV stopped 30cm from pedestrian. sensor worked correctly",
        "chemical splash from sealer gun. operator wearing face shield — no injury",
        "daily safety topic: proper lifting technique when handling heavy parts",
    ],
    "crisis": [
        "LINE DOWN — supplier failed to deliver door hinges. zero stock. production stopped",
        "paint booth fire suppression activated. evacuation of paint shop. no one inside",
        "robot collision in body shop. 2 robots damaged. structural check required. line stopped 4+ hours",
        "quality hold: 89 vehicles suspected of wrong torque on suspension bolt. recall risk assessment",
    ],
    "night": [
        "night maintenance window: all robots getting PM. production stopped 10pm-6am",
        "night shift trim line running at reduced speed. 35 JPH for complex variants",
        "quality audit team checking today's production overnight. sampling 20 vehicles",
        "tooling changeover happening tonight for Monday's new color introduction",
    ],
    "quality": [
        "customer complaint: wind noise from driver door seal on VIN ending {n}47. investigating",
        "paint orange peel measurement: 8.2 on Wavescan. target is <8.0. adjusting gun settings",
        "dimensional check on body side panel: 0.3mm out at B-pillar. within tolerance but monitoring",
        "water leak test: 2 vehicles failed. sunroof drain tube kinked during assembly",
    ],
    "human_relations": [
        "line stop for 5 min — birthday celebration for team leader Ravi 🎂",
        "production bonus this month: ₹3,500 per person if we hit 98% FTT",
        "new team members from ITI joining assembly line tomorrow. assign mentors",
        "union rep visiting floor at 2pm for monthly safety walk",
    ],
}


# ─── THERMAL POWER PLANT ───────────────────────────────────────
INDUSTRY_MESSAGES["thermal_power_plant"] = {
    "daily_ops": [
        "unit {n} generating at 490MW. coal stock: 12 days. ash level normal",
        "boiler drum level steady at +50mm. feed water flow 620 TPH",
        "turbine bearing temp: #1=72°C, #2=68°C, #3=71°C. all within limits",
        "coal mill C pulverizing at 55 TPH. classifier adjusted for fineness",
        "condenser vacuum at 680mmHg. cooling tower performance satisfactory",
        "ESP collection efficiency at 99.2%. stack emissions within CPCB norms",
        "load dispatch center asked us to ramp up by 50MW. adjusting firing rate",
        "ash disposal: slurry pipeline running. ash pond level at 65%",
        "DM water plant producing 120 m³/hr. enough for today's demand",
        "hydrogen cooling system: purity at 98.4%, pressure 3.5 kg/cm²",
    ],
    "maintenance": [
        "boiler tube leak detected in economizer section. unit derated to 350MW",
        "turbine LP stage blade inspection due next overhaul. vibration trending up slightly",
        "coal crusher hammer replaced. was causing oversized coal and mill rejections",
        "air preheater basket clogging. soot blowing frequency increased",
        "transformer tap changer mechanism stiff. servicing during next outage",
        "cooling tower fills in cell 3 deteriorated. replacement material ordered",
    ],
    "crisis": [
        "UNIT TRIP — boiler tube failure. steam leak detected. emergency cooldown initiated",
        "coal supply disrupted — railway rake cancelled. stock at 3 days only. CRITICAL",
        "generator rotor earth fault alarm. tripping unit. investigation needed",
        "ash pipeline burst near colony area. slurry flowing on road. emergency repair team",
    ],
    "night": [
        "night shift: both units running stable. load at 480MW and 495MW",
        "coal unloading from rake continuing overnight. 58 wagons, tippler running",
        "3am patrol: turbine hall walkdown. all bearings normal temp. oil levels OK",
        "night load reduction from dispatch center. backing down to 400MW",
    ],
}
INDUSTRY_MESSAGES["solar_farm"] = {
    "daily_ops": [
        "generation today: {n} MWh so far. irradiance at 850 W/m². good sun day",
        "inverter 7 showing slightly lower efficiency. 96.2% vs expected 97.5%",
        "panel cleaning crew working on Block C. soiling loss was at 4%",
        "tracker motors on row 12-15 adjusted. following sun angle correctly",
        "grid export meter reading: cumulative 4.{n} GWh this month",
        "monitoring portal shows string 23 underperforming. possible hot spot on panel",
        "vegetation management: grass cutting around panels done in section A",
        "weather forecast: cloudy tomorrow. expected generation drop 30%",
    ],
    "maintenance": [
        "inverter 3 faulted — IGBT overtemp. waiting for ambient to cool before restart",
        "cable termination failure on DC combiner box. electrician replacing connector",
        "tracker stuck at 35° angle. motor gearbox seized. manual override applied",
        "bird dropping accumulation on panels in row 8. scheduling cleaning",
    ],
    "night": [
        "generation zero. nighttime. checking inverter standby status remotely",
        "security patrol around perimeter. fence intact. no theft attempts",
        "overnight firmware update pushed to all inverters. will verify in morning",
    ],
}


# ─── PHARMACEUTICAL ─────────────────────────────────────────────
INDUSTRY_MESSAGES["pharmaceutical_tablet"] = {
    "daily_ops": [
        "batch #{n}47 granulation started. binder addition at 2.5 kg/min",
        "compression running on Fette 3090. tablet weight: 450mg ± 3mg. hardness 8 kP",
        "coating pan loaded. 200kg core tablets. spraying polymer coat at 12 g/min",
        "room 204 environmental monitoring: temp 22°C, RH 45%. within spec",
        "in-process check: dissolution test on batch 56 — 85% at 30 min. passes",
        "raw material received: 500kg of API. QC sampling done. under quarantine pending analysis",
        "batch record review: 3 deviations noted — all minor (timing, manual correction entries)",
        "cleaning validation on blender BL-03 complete. swab results pending from QC lab",
        "changeover from Product A to Product B. 4-hour cleaning protocol in progress",
        "packaging line running. 60 blisters/min. printing check every 30 min",
        "water system TOC at 320 ppb. USP limit is 500 ppb. within spec",
        "HVAC system maintaining pressure differential: corridor +15Pa vs production -5Pa",
    ],
    "maintenance": [
        "tablet press lower punch broke during compression. die replaced. production paused 45 min",
        "granulator spray nozzle clogged. disassembled and ultrasonically cleaned",
        "HVAC filter replacement in classified area. environmental recovery time 20 min",
        "metal detector on packaging line giving false rejects. sensitivity recalibrated",
    ],
    "safety_accidents": [
        "operator exposed to powder during charging. wearing RPE but shower taken as precaution",
        "solvent spill in granulation area — 2L IPA. absorbed with spill kit. area ventilated",
        "gowning failure found during area monitoring. particle count elevated. investigating",
    ],
    "crisis": [
        "PRODUCT RECALL: dissolution failure on stability sample. batch 34-42 under investigation",
        "FDA 483 observation: data integrity concern in QC lab. management response in 15 days",
        "cross-contamination detected: Product A residue found in Product B batch. entire lot rejected",
        "clean room classification failed: particle count exceeded Class 100,000 limit. production halted",
    ],
    "night": [
        "night shift: coating still running on batch 56. expected completion 4am",
        "stability chamber check: all 40°C/75% RH and 25°C/60% RH chambers running",
        "WFI system sanitization running overnight as per SOP",
        "compression completed at 2am. yield: 98.3%. tablets transferred to coating",
    ],
    "quality": [
        "dissolution failure on 1 of 6 tablets in stage 1 testing. proceeding to S2 with 12 tablets",
        "content uniformity RSD at 2.8%. acceptance criteria is <6%. passes",
        "impurity peak detected at RRT 0.87. below 0.10% reporting threshold",
        "annual product review identifies 3 OOS results in 12 months. trending investigation required",
    ],
}
INDUSTRY_MESSAGES["vaccine_manufacturing"] = INDUSTRY_MESSAGES["pharmaceutical_tablet"].copy()


# ─── RESTAURANT KITCHEN ─────────────────────────────────────────
INDUSTRY_MESSAGES["restaurant_kitchen"] = {
    "daily_ops": [
        "lunch prep started. chopping station 1 and 2 working on mise en place",
        "today's special: butter chicken and dal makhani. prep for 80 portions",
        "delivery from vendor — 20kg chicken, 10kg paneer, vegetables. checking quality",
        "lunch rush started. 15 orders in queue already. everyone on stations!",
        "tandoor lit at 11am. needs 45 min to reach temperature for naan",
        "table 7 wants no onion no garlic. marking ticket clearly. ALLERGY",
        "biryani almost done for evening service. dum on low flame for 20 more minutes",
        "cold storage check: fridge 1 at 4°C, fridge 2 at 3°C, freezer at -18°C",
        "evening prep: marination started for tomorrow's kebab orders",
        "closing time. last order in kitchen. fire off desserts for table 12",
    ],
    "maintenance": [
        "gas burner on station 3 not igniting properly. cleaning pilot tube",
        "walk-in fridge compressor making loud noise. calling refrigeration mechanic",
        "exhaust hood filter needs deep cleaning. grease buildup heavy after weekend rush",
        "dishwasher not draining. drain clogged with food waste. clearing manually",
    ],
    "safety_accidents": [
        "burn injury — cook splashed hot oil while frying. cold water applied. minor burn",
        "knife cut on prep station. finger bandaged. using cut-proof glove now",
        "floor slippery near dishwash area. mopped and put wet floor sign",
        "gas smell near cylinder storage. turned off valve. calling gas company",
    ],
    "crisis": [
        "KITCHEN FIRE — oil caught fire in deep fryer. fire blanket used. under control",
        "food safety inspector arrived unannounced. checking hygiene, FSSAI license, pest control records",
        "customer severe allergic reaction. ambulance called. checking what was served",
        "entire evening booking cancelled — 50 people. food already prepped. major loss",
    ],
    "night": [
        "closing kitchen. deep clean starting. degreasing all surfaces",
        "prep for tomorrow morning: cutting vegetables, making dough for rotis",
        "freezer stock count for tomorrow's ordering. running low on fish",
        "night security checking gas cylinder valves and back door locks",
    ],
    "quality": [
        "customer complaint: biryani rice overcooked today. adjusting water ratio",
        "food photography session for new menu items. plating practice",
        "Swiggy rating dropped to 4.1 from 4.3. checking recent negative reviews",
        "taste check before service: gravy needs more salt. adjusted",
    ],
}


# ─── CALL CENTER / BPO ──────────────────────────────────────────
INDUSTRY_MESSAGES["call_center"] = {
    "daily_ops": [
        "queue depth at {n} calls. average wait time 3 min 20 sec. within SLA",
        "handled 47 calls this shift so far. average handle time 4 min 12 sec",
        "quality score this week: 88%. need 90% to hit bonus. focusing on call opening",
        "supervisor listening in on calls for the new batch. coaching session at break",
        "system slow today — CRM taking 8 seconds to load customer profile. IT notified",
        "escalation call transferred to team lead. customer very upset about billing",
        "first call resolution rate today: 72%. target 78%. too many transfers happening",
        "break schedule: Team A at 2pm, Team B at 2:30pm, Team C at 3pm",
        "floor manager walk: check posture, headset position, water bottle at desk",
        "new product training module assigned. complete by Friday or lose shift preference",
        "dialer predictive mode engaged. abandon rate at 3.8% — below 5% threshold",
    ],
    "maintenance": [
        "headset mic not working on station 14. swapping with spare from storage",
        "softphone application crashed. restarting. lost 2 calls in queue",
        "UPS beeping on floor 3. battery replacement needed. facilities informed",
        "AC vent directly above station 8 causing cold draft. requested redirect",
    ],
    "safety_accidents": [
        "agent fainted at desk — BP issue. first aid given. sent home in cab",
        "power strip overloaded — small spark at station block D. unplugged immediately",
        "fire drill completed. evacuation time: 4 min 30 sec. target was 3 min",
    ],
    "crisis": [
        "SYSTEM DOWN — telephony platform crashed. zero calls connecting. all agents idle. client SLA breach",
        "mass outage at client side — call volume 5x normal. all hands on deck. overtime approved",
        "data breach suspected — customer records accessed from unauthorized terminal. IT security investigating",
        "client contract termination notice received. 200 seats affected. town hall at 4pm",
    ],
    "night": [
        "night shift — handling US timezone calls. volume lighter after midnight EST",
        "only 12 agents on floor tonight. queue manageable. ~2 min wait times",
        "3am slump — energy levels low. ordering coffee for the floor",
        "graveyard shift quiet. mostly account balance inquiries at this hour",
        "night batch processing support calls — standing by for escalations",
    ],
    "quality": [
        "call audit: agent didn't verify customer identity before making changes. coaching needed",
        "customer satisfaction survey: 3.8/5 for yesterday. below target 4.2. team meeting scheduled",
        "script compliance at 85%. agents skipping the disclosure statement. reminder sent",
        "recording quality issue — background noise from adjacent stations bleeding into calls",
    ],
    "human_relations": [
        "attrition report: 3 resignations this week. exit interview cites 'no growth'",
        "team building activity Saturday. attendance is 'voluntary' (but noted 👀)",
        "new hire batch of 15 starting OJT Monday. floor mentors assigned",
        "birthday celebration at desk — small cake. no singing. this is a call floor 😂",
        "who's swapping Saturday night for Sunday morning shift? DM me",
    ],
}


# ─── LOGISTICS WAREHOUSE ───────────────────────────────────────
INDUSTRY_MESSAGES["logistics_warehouse"] = {
    "daily_ops": [
        "inbound: 3 trucks arrived. unloading dock 2 and 4. manifest check in progress",
        "pick list generated for {n} orders. wave picking started in Zone A",
        "outbound dispatch: 45 shipments ready. last pickup at 6pm today",
        "cycle count in aisle 7: 2 SKUs showing variance. investigating",
        "forklift operators assigned: 4 on receiving, 2 on shipping, 1 on replenishment",
        "conveyor sort system running. diverter issue on lane 3 fixed earlier",
        "receiving inspection: 5 damaged cartons in today's shipment. vendor claim filed",
        "putaway complete for morning receipts. 340 locations updated in WMS",
        "packing station throughput: 120 parcels/hour. target 150. short staffed today",
        "returns processing: 67 items to inspect, sort, and restock or dispose",
    ],
    "maintenance": [
        "forklift #7 battery not holding charge. replacing with spare from charging bay",
        "conveyor belt jammed at merge point. clearing obstruction — oversized package",
        "rack beam damaged by forklift impact. section cordoned off. structural check ordered",
        "handheld scanner firmware update pushed. some units rebooting. 5 min disruption",
        "dock leveler hydraulics leaking. dock 3 out of service until repaired",
    ],
    "safety_accidents": [
        "near miss: forklift reversed without checking mirror. pedestrian had to jump aside",
        "box fell from height in bulk storage area. area was clear. re-stacking properly",
        "worker strained back lifting 25kg box without using proper technique. sent to clinic",
        "racking inspection: 2 uprights with dents exceeding allowable limits. flagged for repair",
    ],
    "crisis": [
        "FIRE ALARM — smoke detected in charging bay. all forklifts powered off. evacuating",
        "WMS system crash — no pick/put operations possible. IT working on restore. manual tracking",
        "major client order shipped to wrong destination. recall in progress. courier intercepted",
        "flood water entering from loading dock during heavy rain. sandbagging and moving ground stock",
    ],
    "night": [
        "night shift: e-commerce orders picking for next-day delivery. target 2000 parcels",
        "overnight inventory count ongoing. Zone C and D scheduled tonight",
        "truck arrival at 2am for cold chain goods. receiving team on standby",
        "night security patrol: all doors secure, CCTV functional, no unauthorized access",
    ],
    "quality": [
        "mispick rate this week: 0.3%. target 0.2%. additional barcode verification added",
        "customer complaint: wrong item shipped. investigating pick location and scan logs",
        "damaged goods report: 12 items damaged during transit this month. packaging review needed",
    ],
}


# ═══════════════════════════════════════════════════════════════════
# FAMILY-BASED TEMPLATES — Cover remaining 480+ industries
# Each family provides templates for industries in that category
# ═══════════════════════════════════════════════════════════════════

# ─── HEAVY INDUSTRY FAMILY (steel, cement, aluminum, etc.) ──────
_HEAVY_INDUSTRY = {
    "daily_ops": [
        "furnace temperature at {n}°C. within operating range. tapping scheduled in 2 hours",
        "production today: {n} tonnes. shift target on track",
        "raw material feed rate steady. hopper level at 60%",
        "shift handover briefing: no major issues from outgoing crew",
        "crane operator moving ladle to casting position. floor clear",
        "cooling water flow rate normal. heat exchangers performing well",
        "dispatch: 3 trucks loaded and left. 2 more waiting at weighbridge",
        "dust suppression system running. emissions within permit limits",
    ],
    "maintenance": [
        "refractory lining showing wear at hot zone. next reline due in {n} days",
        "hydraulic system pressure drop. checking for leaks on main cylinder",
        "crane hook NDT inspection completed. certified for continued use",
        "conveyor belt splice showing signs of separation. monitoring closely",
        "cooling tower pump cavitating. checking NPSH and strainer",
    ],
    "night": [
        "continuous operations overnight. all critical parameters stable",
        "night round: checked all rotating equipment. temperatures and vibrations normal",
        "furnace running steady. night shift maintaining feed rate",
        "emergency lighting tested. backup generator on standby",
    ],
    "crisis": [
        "EMERGENCY STOP — molten metal spill detected. area evacuation in progress",
        "power failure to main drive. production halted. UPS supporting controls only",
        "gas leak alarm on {n}th floor. evacuation initiated. checking source",
    ],
}

# ─── FOOD PROCESSING FAMILY ─────────────────────────────────────
_FOOD_PROCESSING = {
    "daily_ops": [
        "production line started after CIP cleaning. sanitization records signed off",
        "batch mixing: following recipe card #{n}. ingredients weighed and verified",
        "packaging line running at {n} units/min. date coding verified",
        "cold chain monitoring: all cold rooms between 2-4°C. within limits",
        "FSSAI documentation check — all records up to date for this month",
        "incoming raw material: visual inspection done. no foreign matter. accepting",
        "metal detector test with test piece passed. running production",
        "shift hygiene check: all workers wearing hairnets, gloves, no jewelry",
    ],
    "maintenance": [
        "filling machine nozzle clogged. dismantling for cleaning",
        "conveyor belt showing wear near drive roller. ordering replacement",
        "chiller compressor running hot. checking refrigerant levels",
        "sealing machine temperature fluctuating. thermostat may need replacement",
    ],
    "night": [
        "CIP cleaning running overnight on production Line 2. takes 4 hours",
        "frozen storage check at midnight: -20°C maintained. door seals intact",
        "pest control activity overnight while production stopped. fumigation in storage area",
    ],
    "crisis": [
        "PRODUCT RECALL: foreign object found in customer complaint. tracing batch",
        "cold chain break — refrigeration failed for 3 hours. assessing product safety",
        "contamination suspected: microbiological test positive. halting line for investigation",
    ],
    "quality": [
        "microbiological test results: TPC within limits. coliforms negative. batch cleared",
        "taste panel: new recipe variant scored 7.2/10. needs improvement on sweetness",
        "label check: allergen declaration verified against recipe. correct",
    ],
}

# ─── CONSTRUCTION FAMILY ────────────────────────────────────────
_CONSTRUCTION = {
    "daily_ops": [
        "toolbox talk completed. today's topic: working at heights. all {n} workers signed",
        "concrete pour scheduled for 2pm. ready mix plant confirmed 40 m³",
        "rebar tying in progress on 3rd floor slab. structural engineer to inspect before pour",
        "crane lift planned for steel beam. radius check done. ground conditions verified",
        "daily site inspection: housekeeping good, scaffolding tags current, no unsafe acts observed",
        "material delivery: 200 bags cement, 10 tonnes sand arrived. stacking at designated area",
        "survey team checking levels for next floor. benchmark confirmed",
        "shuttering work in progress. carpenter team on formwork for column C3-C7",
    ],
    "maintenance": [
        "tower crane: daily checks done. wire rope condition OK. slew ring greased",
        "batching plant: mixer drum liner worn. scheduling replacement for weekend",
        "generator fuel topped up. running time today estimated 6 hours",
        "pump for dewatering running continuously. pit water level controlled",
    ],
    "night": [
        "NO WORK AT NIGHT. site secured. watchman on duty",
        "night concrete curing: water spraying on yesterday's pour as per schedule",
        "security patrol: all materials accounted for. gate locked. CCTV recording",
    ],
    "crisis": [
        "SCAFFOLDING COLLAPSE on east face. all workers evacuated. headcount confirmed. no injuries",
        "heavy rain — excavation walls showing movement. stop all work near trench immediately",
        "crane load swung into building facade. structural damage. crane operations suspended",
        "worker fell from height — safety harness caught him. shaken but unhurt. safety stand-down",
    ],
    "safety_accidents": [
        "daily toolbox talk: proper use of fall arrest systems. everyone sign the register",
        "near miss: material fell from 2nd floor during hoisting. barricade was in place fortunately",
        "safety officer found 3 workers without hard hats. warning issued. zero tolerance reminder",
        "hot work permit required for welding on 4th floor. fire watch assigned",
    ],
}

# ─── RETAIL / SERVICE FAMILY ────────────────────────────────────
_RETAIL = {
    "daily_ops": [
        "store opened at 9am. {n} customers already in first hour",
        "shelf restocking in progress. aisle 3 and 7 done. fresh produce next",
        "POS system all terminals working. checked cash in all 8 registers",
        "flash sale starting at 2pm. signage team putting up banners now",
        "inventory count: discrepancy in electronics section. {n} items variance",
        "customer service desk: 4 returns processed, 2 exchanges, 1 complaint",
        "security team reported suspicious activity near cosmetics aisle. monitoring CCTV",
        "delivery received: 340 SKUs. sorting and putting away in back storage",
    ],
    "maintenance": [
        "AC unit on 2nd floor not cooling properly. facility team checking",
        "escalator stopped near food court entrance. technician called. using stairs",
        "refrigerator in dairy section showing 6°C. should be 4°C. adjusting",
        "shopping cart wheels stuck on 4 carts. removing from floor",
    ],
    "night": [
        "store closed at 10pm. closing cash reconciliation in progress",
        "overnight shelf restocking by night crew. heavy load — new promotional stock",
        "deep cleaning team in from 11pm. floor scrubbing and sanitization",
        "security night patrol: hourly rounds. all entry points checked",
    ],
    "crisis": [
        "SHOPLIFTER caught with ₹15,000 worth of electronics. police called. CCTV evidence saved",
        "power outage: backup generator running cold chain. checkout down. cash only at 2 registers",
        "customer medical emergency — collapsed in aisle 5. first aid given. ambulance called",
    ],
}

# ─── AGRICULTURE (NON-RICE) FAMILY ──────────────────────────────
_AGRICULTURE = {
    "daily_ops": [
        "field work started at 6am. {n} workers on weeding and hoeing duty",
        "irrigation running since 5am. bore well pump operating normally",
        "pesticide spraying completed in plot 2. using safety equipment as advised",
        "tractor plowing the fallow section. diesel topped up for today's work",
        "checked crop growth. healthy. no signs of pest or disease infestation",
        "loaded {n} bags of produce onto truck for market",
        "fertilizer application done — following soil test recommendations",
        "labor payment day. settled accounts with all workers",
    ],
    "maintenance": [
        "pump motor overheating. letting it cool down. will check winding insulation",
        "drip pipe blocked at 3 points. cleaning with acid flush",
        "tractor battery dead. jumpstarted from neighbor's vehicle",
        "sprayer nozzle leaking. replaced rubber washer. working now",
    ],
    "night": [
        "sleeping at field tonight. crop is at vulnerable stage",
        "torch patrol done. no animal intrusion. going back to sleep",
        "wild animals active nearby. keeping fire burning at field boundary",
        "pump running overnight for irrigation. will switch off at 4am",
        "heard sounds near crop. checked — was a rabbit. set up additional deterrent",
    ],
    "crisis": [
        "hailstorm damaged standing crop. 40% loss estimated. heartbroken 😔",
        "pest attack spreading rapidly. emergency spraying needed today itself",
        "water source dried up unexpectedly. crop will suffer if no rain in 3 days",
        "fire in neighbor's field spreading towards ours. creating fire break urgently",
    ],
}

# ─── IT / KNOWLEDGE WORK FAMILY ─────────────────────────────────
_IT_KNOWLEDGE = {
    "daily_ops": [
        "standup meeting: discussed blockers, sprint progress at 65%",
        "working on feature ticket #{n}. estimated 2 more days to completion",
        "deployed latest build to staging environment. testing in progress",
        "client call at 3pm. preparing demo slides and test environment",
        "code committed and pushed. waiting for CI pipeline to pass",
        "documentation update for API v2.1 completed. sharing with team",
        "meeting notes shared from yesterday's architecture review",
        "work from home today. connected on Slack. deep focus on backend module",
    ],
    "maintenance": [
        "server disk space at 88%. cleaning old logs and temp files",
        "VPN connection dropping intermittently. IT team investigating",
        "email server maintenance tonight. expect 30 min downtime at 11pm",
        "laptop battery swelling. raised IT ticket for replacement",
    ],
    "night": [
        "working late to meet deadline. coffee number 4. almost done with the module",
        "on-call rotation: monitoring alerts dashboard. quiet so far tonight",
        "overnight deployment scheduled for 2am. will be awake for rollback if needed",
    ],
    "crisis": [
        "PRODUCTION INCIDENT — client-facing API returning errors. all hands investigating",
        "security breach detected. suspicious login from unknown location. forcing password reset",
        "critical bug found in billing module. overcharging customers. hotfix needed NOW",
    ],
}

# ─── HEALTHCARE / WELLNESS FAMILY ───────────────────────────────
_HEALTHCARE = {
    "daily_ops": [
        "morning rounds completed. all patients reviewed with attending doctor",
        "new admissions: {n} patients since last shift. beds available: 4",
        "medication round done. all patients received prescribed doses on time",
        "lab samples collected and sent. reports expected by 2pm",
        "discharge process for 5 patients. summary and medication explained",
        "ambulance on standby. one emergency call received, team dispatched",
        "housekeeping completed in all wards. fumigation in ICU as scheduled",
    ],
    "maintenance": [
        "oxygen concentrator showing error. switching to cylinder supply for now",
        "AC in ward 3 not working. patients complaining of heat. technician called",
        "patient monitor screen flickering in bed 7. replacing with spare unit",
    ],
    "night": [
        "night round: all patients sleeping. vitals stable. IV running as ordered",
        "emergency admission at 1am. attending doctor informed. stabilizing patient",
        "ICU ventilator alarm — tube kinked. repositioned. patient saturation recovered",
        "night shift handover notes prepared. 2 critical patients to watch closely",
    ],
    "crisis": [
        "CODE BLUE — cardiac arrest. crash cart brought. CPR in progress",
        "mass casualty: accident victims incoming. activating disaster protocol",
        "oxygen supply pressure dropping. checking main pipeline and backup cylinders",
    ],
}

# ─── LIVESTOCK / AQUACULTURE FAMILY ─────────────────────────────
_LIVESTOCK = {
    "daily_ops": [
        "morning feeding done. all {n} animals fed on schedule",
        "egg collection: {n} eggs today. slightly below average. checking feed quality",
        "water quality check: pH 7.2, ammonia 0.02 ppm. within safe range",
        "veterinarian visit scheduled for vaccination round this week",
        "shed cleaning completed. fresh bedding laid down",
        "temperature inside shed: 28°C. fans running to maintain ventilation",
        "feed stock check: 5 days of feed remaining. ordering next batch",
        "mortality report: 0 today. flock/herd health looking good",
    ],
    "maintenance": [
        "automatic feeder jammed. cleared blockage. running again",
        "water nipple leaking in section 3. replaced fitting",
        "exhaust fan motor bearing noise. lubricating before it fails",
        "generator tested — starts within 10 seconds. important for overnight ventilation",
    ],
    "night": [
        "night check: all animals calm. temperature holding at 26°C",
        "heard fox/mongoose activity outside. fence electrification confirmed working",
        "automatic lights dimmed as per schedule. birds settling down",
        "water pump running overnight. timer set to fill overhead tank by 5am",
        "predator alert — unusual barking from guard dogs. checking perimeter",
    ],
    "crisis": [
        "DISEASE OUTBREAK suspected — 8 birds showing respiratory symptoms. isolating immediately",
        "power failure — ventilation fans stopped. generator starting. critical for young stock",
        "flood water approaching farm. moving animals to higher ground urgently",
        "feed contamination suspected after sudden drop in production. quarantining current batch",
    ],
}
INDUSTRY_MESSAGES["poultry_farming"] = _LIVESTOCK.copy()
INDUSTRY_MESSAGES["dairy_farming"] = _LIVESTOCK.copy()
INDUSTRY_MESSAGES["shrimp_farming"] = _LIVESTOCK.copy()


# ═══════════════════════════════════════════════════════════════════
# FAMILY MAPPING — Maps subsectors to their family templates
# ═══════════════════════════════════════════════════════════════════

FAMILY_TEMPLATES = {
    "metallurgy": _HEAVY_INDUSTRY,
    "cement": _HEAVY_INDUSTRY,
    "chemical": _HEAVY_INDUSTRY,
    "petrochemical": _HEAVY_INDUSTRY,
    "energy": _HEAVY_INDUSTRY,
    "food_processing": _FOOD_PROCESSING,
    "food_beverage": _FOOD_PROCESSING,
    "civil": _CONSTRUCTION,
    "construction": _CONSTRUCTION,
    "retail": _RETAIL,
    "hospitality": _RETAIL,
    "agriculture": _AGRICULTURE,
    "horticulture": _AGRICULTURE,
    "fisheries": _AGRICULTURE,
    "livestock": _LIVESTOCK,
    "software": _IT_KNOWLEDGE,
    "it_services": _IT_KNOWLEDGE,
    "ai_data": _IT_KNOWLEDGE,
    "services": _IT_KNOWLEDGE,
    "education": _IT_KNOWLEDGE,
    "healthcare": _HEALTHCARE,
    "wellness": _HEALTHCARE,
    "mining": INDUSTRY_MESSAGES["coal_mining"],
    "oil_gas": INDUSTRY_MESSAGES["oil_refining"],
    "renewable": INDUSTRY_MESSAGES.get("solar_farm", {}),
    "power_generation": INDUSTRY_MESSAGES.get("thermal_power_plant", {}),
    "textile": _HEAVY_INDUSTRY,
    "electrical": _HEAVY_INDUSTRY,
    "precision": _HEAVY_INDUSTRY,
    "advanced_materials": _HEAVY_INDUSTRY,
    "biotech": _HEALTHCARE,
    "logistics": INDUSTRY_MESSAGES.get("logistics_warehouse", {}),
    "entertainment": _RETAIL,
    "facility_management": _RETAIL,
    "space": _IT_KNOWLEDGE,
    # Additional subsectors to reach ~95% coverage
    "misc": _RETAIL,
    "utility": _HEAVY_INDUSTRY,
    "machinery": _HEAVY_INDUSTRY,
    "personal_care": _FOOD_PROCESSING,
    "paper_pulp": _HEAVY_INDUSTRY,
    "medical": _HEALTHCARE,
    "media": _IT_KNOWLEDGE,
    "rubber": _HEAVY_INDUSTRY,
    "furniture": _HEAVY_INDUSTRY,
    "plastic": _HEAVY_INDUSTRY,
    "building_material": _CONSTRUCTION,
    "telecom": _IT_KNOWLEDGE,
    "printing": _HEAVY_INDUSTRY,
    "appliance": _HEAVY_INDUSTRY,
    "footwear": _FOOD_PROCESSING,
    "electronics": _HEAVY_INDUSTRY,
    "medical_tech": _HEALTHCARE,
    "forestry": _AGRICULTURE,
    "aerospace": _IT_KNOWLEDGE,
    "quarrying": _HEAVY_INDUSTRY,
    "heavy_engineering": _HEAVY_INDUSTRY,
    "automobile": _HEAVY_INDUSTRY,
    "robotics": _IT_KNOWLEDGE,
    "banking": _IT_KNOWLEDGE,
    "consulting": _IT_KNOWLEDGE,
    "wood": _HEAVY_INDUSTRY,
    "gas": _HEAVY_INDUSTRY,
    "storage": _RETAIL,
    "oil": _HEAVY_INDUSTRY,
    "safety": _IT_KNOWLEDGE,
    "mechanical": _HEAVY_INDUSTRY,
    "environmental": _AGRICULTURE,
    "leather": _HEAVY_INDUSTRY,
    "textile_garment": _HEAVY_INDUSTRY,
    "fmcg": _FOOD_PROCESSING,
    "insurance": _IT_KNOWLEDGE,
    "security": _RETAIL,
    "shipping": _RETAIL,
    "defense": _HEAVY_INDUSTRY,
    "tourism": _RETAIL,
    "waste": _HEAVY_INDUSTRY,
    "stone": _HEAVY_INDUSTRY,
    "tobacco": _FOOD_PROCESSING,
    "pharmaceutical": _HEALTHCARE,
    "manufacturing": _HEAVY_INDUSTRY,
    "coal": _HEAVY_INDUSTRY,
    "maintenance": _HEAVY_INDUSTRY,
    "recycling": _HEAVY_INDUSTRY,
    "finance": _IT_KNOWLEDGE,
    "water": _HEAVY_INDUSTRY,
}


# ═══════════════════════════════════════════════════════════════════
# LOOKUP FUNCTION
# ═══════════════════════════════════════════════════════════════════

def get_industry_message(industry_id: str, subsector: str, category: str,
                         rng: random.Random) -> Optional[str]:
    """Get an industry-specific message template.
    
    Lookup priority:
    1. Direct industry match (e.g., 'ai_research_lab')
    2. Subsector family match (e.g., 'software' family)
    3. Return None (caller falls back to generic)
    
    Args:
        industry_id: The specific industry ID
        subsector: The industry's subsector
        category: Event category (daily_ops, maintenance, etc.)
        rng: Random number generator
    
    Returns:
        A message string with {n} and {x} placeholders, or None
    """
    # 1. Direct industry match
    if industry_id in INDUSTRY_MESSAGES:
        templates = INDUSTRY_MESSAGES[industry_id].get(category)
        if templates:
            msg = rng.choice(templates)
            # Replace placeholders
            msg = msg.replace("{n}", str(rng.randint(50, 999)))
            msg = msg.replace("{x}", str(rng.randint(10, 99)))
            return msg
    
    # 2. Subsector family match
    if subsector in FAMILY_TEMPLATES:
        family = FAMILY_TEMPLATES[subsector]
        templates = family.get(category) if isinstance(family, dict) else None
        if templates:
            msg = rng.choice(templates)
            msg = msg.replace("{n}", str(rng.randint(50, 999)))
            msg = msg.replace("{x}", str(rng.randint(10, 99)))
            return msg
    
    # 3. No match — caller should use generic templates
    return None

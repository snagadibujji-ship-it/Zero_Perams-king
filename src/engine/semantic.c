#include "semantic.h"
#include <string.h>
#include <stdlib.h>
#include <stdio.h>
#include <ctype.h>

/* Static synonym groups - each row is a group of synonyms */
static const char* SYNONYM_GROUPS[][MAX_SYNONYMS_PER_WORD] = {
    {"big","large","huge","enormous","gigantic","vast","massive","immense"},
    {"small","tiny","little","miniature","minute","petite","compact",NULL},
    {"fast","quick","rapid","swift","speedy","hasty","brisk",NULL},
    {"slow","sluggish","unhurried","leisurely","gradual","lazy",NULL,NULL},
    {"good","great","excellent","wonderful","superb","fantastic","fine",NULL},
    {"bad","terrible","awful","horrible","dreadful","poor","lousy",NULL},
    {"beautiful","pretty","gorgeous","stunning","lovely","attractive",NULL,NULL},
    {"ugly","hideous","unsightly","grotesque","repulsive",NULL,NULL,NULL},
    {"smart","intelligent","clever","brilliant","wise","bright","sharp",NULL},
    {"stupid","dumb","foolish","ignorant","dense","dim",NULL,NULL},
    {"happy","joyful","glad","cheerful","delighted","pleased","content",NULL},
    {"sad","unhappy","sorrowful","depressed","miserable","gloomy","glum",NULL},
    {"angry","mad","furious","enraged","irritated","livid","irate",NULL},
    {"afraid","scared","frightened","terrified","anxious","fearful",NULL,NULL},
    {"start","begin","commence","initiate","launch","activate",NULL,NULL},
    {"end","finish","complete","conclude","terminate","cease","stop",NULL},
    {"make","create","build","construct","produce","generate","craft",NULL},
    {"break","destroy","damage","shatter","wreck","ruin","smash",NULL},
    {"move","go","travel","walk","proceed","advance","journey",NULL},
    {"say","tell","speak","state","declare","announce","utter",NULL},
    {"think","believe","consider","suppose","reckon","ponder","reflect",NULL},
    {"want","desire","wish","crave","need","yearn","long",NULL},
    {"give","provide","offer","supply","deliver","grant","bestow",NULL},
    {"take","grab","seize","acquire","obtain","snatch","collect",NULL},
    {"help","assist","aid","support","serve","facilitate",NULL,NULL},
    {"important","significant","crucial","vital","essential","key","critical",NULL},
    {"easy","simple","straightforward","effortless","trivial","basic",NULL,NULL},
    {"hard","difficult","challenging","tough","complex","arduous",NULL,NULL},
    {"old","ancient","elderly","aged","vintage","antique","mature",NULL},
    {"new","fresh","recent","modern","novel","current","latest",NULL},
    {"true","correct","right","accurate","valid","genuine","authentic",NULL},
    {"false","wrong","incorrect","inaccurate","invalid","fake","bogus",NULL},
    {"hot","warm","burning","boiling","heated","scorching","fiery",NULL},
    {"cold","cool","freezing","chilly","icy","frigid","frosty",NULL},
    {"rich","wealthy","affluent","prosperous","opulent",NULL,NULL,NULL},
    {"poor","impoverished","destitute","needy","broke",NULL,NULL,NULL},
    {"strong","powerful","mighty","robust","sturdy","tough",NULL,NULL},
    {"weak","feeble","frail","fragile","delicate","flimsy",NULL,NULL},
    {"clean","pure","spotless","pristine","immaculate",NULL,NULL,NULL},
    {"dirty","filthy","grimy","soiled","unclean","messy",NULL,NULL},
    {"loud","noisy","deafening","thunderous","blaring",NULL,NULL,NULL},
    {"quiet","silent","hushed","muted","still","peaceful",NULL,NULL},
    {"bright","luminous","radiant","brilliant","vivid","glowing",NULL,NULL},
    {"dark","dim","gloomy","murky","shadowy","black",NULL,NULL},
    {"wet","moist","damp","soaked","drenched","soggy",NULL,NULL},
    {"dry","arid","parched","dehydrated","barren",NULL,NULL,NULL},
    {"tall","high","towering","lofty","elevated",NULL,NULL,NULL},
    {"short","low","brief","compact","squat",NULL,NULL,NULL},
    {"wide","broad","expansive","extensive","vast",NULL,NULL,NULL},
    {"narrow","thin","slim","slender","tight",NULL,NULL,NULL},
};
static const char* SYNONYM_GROUPS2[][MAX_SYNONYMS_PER_WORD] = {
    {"brave","courageous","fearless","bold","valiant","heroic",NULL,NULL},
    {"kind","gentle","generous","compassionate","benevolent","caring",NULL,NULL},
    {"cruel","harsh","brutal","ruthless","merciless","savage",NULL,NULL},
    {"polite","courteous","civil","respectful","mannerly",NULL,NULL,NULL},
    {"rude","impolite","discourteous","insolent","disrespectful",NULL,NULL,NULL},
    {"calm","peaceful","serene","tranquil","composed","relaxed",NULL,NULL},
    {"nervous","anxious","tense","worried","uneasy","jittery",NULL,NULL},
    {"tired","exhausted","fatigued","weary","drained","sleepy",NULL,NULL},
    {"energetic","lively","active","vigorous","dynamic","spirited",NULL,NULL},
    {"hungry","starving","famished","ravenous",NULL,NULL,NULL,NULL},
    {"sick","ill","unwell","ailing","diseased",NULL,NULL,NULL},
    {"funny","humorous","amusing","comical","hilarious","witty",NULL,NULL},
    {"serious","grave","solemn","earnest","somber","stern",NULL,NULL},
    {"strange","weird","odd","peculiar","bizarre","unusual","curious",NULL},
    {"normal","ordinary","usual","typical","regular","standard","common",NULL},
    {"empty","vacant","void","hollow","bare","blank",NULL,NULL},
    {"safe","secure","protected","sheltered","guarded",NULL,NULL,NULL},
    {"dangerous","hazardous","risky","perilous","unsafe","threatening",NULL,NULL},
    {"cheap","inexpensive","affordable","economical","budget",NULL,NULL,NULL},
    {"expensive","costly","pricey","overpriced","premium",NULL,NULL,NULL},
    {"soft","gentle","tender","smooth","delicate","supple",NULL,NULL},
    {"smooth","even","sleek","polished","glossy",NULL,NULL,NULL},
    {"deep","profound","bottomless","intense",NULL,NULL,NULL,NULL},
    {"heavy","weighty","hefty","massive","ponderous",NULL,NULL,NULL},
    {"light","lightweight","feathery","airy","weightless",NULL,NULL,NULL},
    {"busy","occupied","engaged","active","hectic",NULL,NULL,NULL},
    {"free","available","unoccupied","idle","spare",NULL,NULL,NULL},
};
static const char* SYNONYM_GROUPS3[][MAX_SYNONYMS_PER_WORD] = {
    {"look","see","watch","observe","view","gaze","glance","peer"},
    {"eat","consume","devour","dine","feast","munch",NULL,NULL},
    {"drink","sip","gulp","swallow","guzzle",NULL,NULL,NULL},
    {"sleep","rest","nap","doze","slumber","snooze",NULL,NULL},
    {"laugh","giggle","chuckle","snicker","cackle",NULL,NULL,NULL},
    {"cry","weep","sob","wail","whimper","bawl",NULL,NULL},
    {"fight","battle","combat","struggle","clash","brawl",NULL,NULL},
    {"win","triumph","prevail","succeed","conquer","overcome",NULL,NULL},
    {"lose","fail","forfeit","surrender","yield",NULL,NULL,NULL},
    {"buy","purchase","acquire","procure","obtain",NULL,NULL,NULL},
    {"sell","trade","vend","market","peddle",NULL,NULL,NULL},
    {"teach","instruct","educate","train","tutor","coach",NULL,NULL},
    {"learn","study","absorb","grasp","master","understand",NULL,NULL},
    {"work","labor","toil","operate","function","perform",NULL,NULL},
    {"write","compose","author","pen","draft","inscribe",NULL,NULL},
    {"read","peruse","scan","browse","study","examine",NULL,NULL},
    {"show","display","exhibit","demonstrate","reveal","present",NULL,NULL},
    {"hide","conceal","cover","mask","obscure","camouflage",NULL,NULL},
    {"open","unlock","uncover","expose","reveal",NULL,NULL,NULL},
    {"close","shut","seal","lock","fasten",NULL,NULL,NULL},
    {"push","shove","press","thrust","force",NULL,NULL,NULL},
    {"pull","drag","tug","haul","draw","yank",NULL,NULL},
    {"cut","slice","chop","sever","trim","carve",NULL,NULL},
    {"join","connect","link","unite","merge","combine","attach",NULL},
    {"separate","divide","split","part","detach","disconnect",NULL,NULL},
    {"grow","expand","develop","increase","enlarge","flourish",NULL,NULL},
    {"shrink","reduce","diminish","decrease","contract","dwindle",NULL,NULL},
    {"rise","ascend","climb","soar","mount","elevate",NULL,NULL},
    {"fall","drop","descend","plunge","tumble","collapse",NULL,NULL},
    {"send","transmit","dispatch","deliver","forward","ship",NULL,NULL},
    {"receive","get","accept","obtain","collect","gather",NULL,NULL},
    {"hurry","rush","hasten","race","dash","sprint",NULL,NULL},
    /* Computing synonyms */
    {"code","program","script","software","source",NULL,NULL,NULL},
    {"bug","error","defect","issue","problem","fault","glitch",NULL},
    {"fix","repair","resolve","patch","debug","mend","correct",NULL},
    {"run","execute","launch","invoke","trigger",NULL,NULL,NULL},
    {"computer","machine","system","device","PC","server",NULL,NULL},
    {"file","document","record","asset","resource",NULL,NULL,NULL},
    {"performant","efficient","optimized","speedy","responsive",NULL,NULL,NULL},
    {"data","information","content","payload","input",NULL,NULL,NULL},
    {"function","method","procedure","routine","subroutine",NULL,NULL,NULL},
    {"variable","parameter","argument","value","field",NULL,NULL,NULL},
    {"array","list","collection","sequence","vector",NULL,NULL,NULL},
    {"string","text","characters","literal",NULL,NULL,NULL,NULL},
    {"test","verify","validate","check","assert","confirm",NULL,NULL},
    {"deploy","release","publish","ship","distribute",NULL,NULL,NULL},
    {"database","store","repository","warehouse","storage",NULL,NULL,NULL},
    {"network","internet","web","connection","link",NULL,NULL,NULL},
    {"secure","protected","encrypted","safe","guarded",NULL,NULL,NULL},
    {"delete","remove","erase","purge","discard","drop",NULL,NULL},
    {"copy","duplicate","clone","replicate","mirror",NULL,NULL,NULL},
    {"search","find","query","lookup","seek","locate",NULL,NULL},
    {"save","persist","preserve","archive","cache",NULL,NULL,NULL},
    {"load","fetch","retrieve","import","download",NULL,NULL,NULL},
    {"update","modify","change","alter","edit","revise",NULL,NULL},
    {"install","setup","configure","provision",NULL,NULL,NULL,NULL},
    {"compile","build","assemble","translate",NULL,NULL,NULL,NULL},
    {"crash","freeze","hang","abort","die",NULL,NULL,NULL},
    /* More general */
    {"answer","reply","respond","retort",NULL,NULL,NULL,NULL},
    {"ask","question","inquire","query","request",NULL,NULL,NULL},
    {"allow","permit","let","authorize","enable","grant",NULL,NULL},
    {"forbid","prohibit","ban","block","prevent","deny",NULL,NULL},
    {"like","enjoy","love","appreciate","adore","fancy",NULL,NULL},
    {"hate","despise","loathe","detest","abhor",NULL,NULL,NULL},
    {"agree","concur","accept","approve","consent",NULL,NULL,NULL},
    {"disagree","reject","oppose","deny","refuse","decline",NULL,NULL},
    {"change","alter","modify","transform","adjust","adapt",NULL,NULL},
    {"keep","retain","maintain","preserve","hold",NULL,NULL,NULL},
    {"throw","toss","hurl","fling","pitch","cast",NULL,NULL},
    {"catch","grab","snag","capture","trap","seize",NULL,NULL},
    {"choose","select","pick","elect","opt","decide",NULL,NULL},
    {"add","append","attach","include","insert","supplement",NULL,NULL},
    {"remove","eliminate","subtract","extract","withdraw",NULL,NULL,NULL},
    {"improve","enhance","upgrade","refine","boost","optimize",NULL,NULL},
    {"protect","defend","guard","shield","safeguard","shelter",NULL,NULL},
    {"attack","assault","strike","invade","raid","charge",NULL,NULL},
};

#define GROUP_COUNT1 (sizeof(SYNONYM_GROUPS)/sizeof(SYNONYM_GROUPS[0]))
#define GROUP_COUNT2 (sizeof(SYNONYM_GROUPS2)/sizeof(SYNONYM_GROUPS2[0]))
#define GROUP_COUNT3 (sizeof(SYNONYM_GROUPS3)/sizeof(SYNONYM_GROUPS3[0]))
#define TOTAL_GROUPS (GROUP_COUNT1 + GROUP_COUNT2 + GROUP_COUNT3)

/* Helper: add one synonym group to the DB */
static void add_group(SynonymDB* db, const char* group[], int max_words) {
    int wcount = 0;
    for (int i = 0; i < max_words && group[i] != NULL; i++) wcount++;
    for (int i = 0; i < wcount; i++) {
        if (db->count >= db->capacity) return;
        SynonymEntry* e = &db->entries[db->count];
        strncpy(e->word, group[i], MAX_WORD_LEN - 1);
        e->word[MAX_WORD_LEN - 1] = '\0';
        e->synonym_count = 0;
        for (int j = 0; j < wcount && e->synonym_count < MAX_SYNONYMS_PER_WORD; j++) {
            if (j == i) continue;
            strncpy(e->synonyms[e->synonym_count], group[j], MAX_WORD_LEN - 1);
            e->synonyms[e->synonym_count][MAX_WORD_LEN - 1] = '\0';
            e->synonym_count++;
        }
        db->count++;
    }
}

int synonym_init(SynonymDB* db) {
    db->capacity = (int)(TOTAL_GROUPS * MAX_SYNONYMS_PER_WORD);
    db->entries = (SynonymEntry*)calloc(db->capacity, sizeof(SynonymEntry));
    if (!db->entries) return -1;
    db->count = 0;
    for (int i = 0; i < (int)GROUP_COUNT1; i++)
        add_group(db, SYNONYM_GROUPS[i], MAX_SYNONYMS_PER_WORD);
    for (int i = 0; i < (int)GROUP_COUNT2; i++)
        add_group(db, SYNONYM_GROUPS2[i], MAX_SYNONYMS_PER_WORD);
    for (int i = 0; i < (int)GROUP_COUNT3; i++)
        add_group(db, SYNONYM_GROUPS3[i], MAX_SYNONYMS_PER_WORD);
    return 0;
}

void synonym_destroy(SynonymDB* db) {
    if (db->entries) { free(db->entries); db->entries = NULL; }
    db->count = 0;
    db->capacity = 0;
}

void word_normalize(const char* input, char* output, int max_len) {
    int len = (int)strlen(input);
    if (len < 4 || max_len < 2) { strncpy(output, input, max_len-1); output[max_len-1]='\0'; return; }
    char buf[MAX_WORD_LEN];
    for (int i = 0; i < len && i < MAX_WORD_LEN-1; i++) buf[i] = tolower((unsigned char)input[i]);
    buf[len < MAX_WORD_LEN ? len : MAX_WORD_LEN-1] = '\0';
    len = (int)strlen(buf);
    /* -tion → te */
    if (len > 5 && strcmp(buf+len-4, "tion") == 0) { buf[len-4]='\0'; strcat(buf,"te"); goto done; }
    /* -sion → de */
    if (len > 5 && strcmp(buf+len-4, "sion") == 0) { buf[len-4]='\0'; strcat(buf,"de"); goto done; }
    /* -ing → base */
    if (len > 4 && strcmp(buf+len-3, "ing") == 0) {
        buf[len-3] = '\0'; int blen = (int)strlen(buf);
        if (blen >= 3 && buf[blen-1] == buf[blen-2]) buf[blen-1] = '\0';
        else if (blen >= 3 && buf[blen-1]!='a' && buf[blen-1]!='e' && buf[blen-1]!='i' && buf[blen-1]!='o' && buf[blen-1]!='u')
            { if (blen >= 3) strcat(buf, "e"); }
        goto done;
    }
    /* -ed → base */
    if (len > 3 && strcmp(buf+len-2, "ed") == 0) {
        buf[len-2] = '\0'; int blen = (int)strlen(buf);
        if (blen >= 3 && buf[blen-1] == buf[blen-2]) buf[blen-1] = '\0';
        else if (blen >= 2 && buf[blen-1]!='a' && buf[blen-1]!='e' && buf[blen-1]!='i' && buf[blen-1]!='o' && buf[blen-1]!='u')
            { if (buf[blen-1]=='t'||buf[blen-1]=='k'||buf[blen-1]=='v') strcat(buf,"e"); }
        goto done;
    }
    /* -est → base */
    if (len > 4 && strcmp(buf+len-3, "est") == 0) {
        buf[len-3]='\0'; int blen=(int)strlen(buf);
        if (blen>=3 && buf[blen-1]==buf[blen-2]) { buf[blen-1]='\0'; } goto done;
    }
    /* -er → base */
    if (len > 3 && strcmp(buf+len-2, "er") == 0) {
        buf[len-2]='\0'; int blen=(int)strlen(buf);
        if (blen>=3 && buf[blen-1]==buf[blen-2]) { buf[blen-1]='\0'; } goto done;
    }
    /* -ly → adjective */
    if (len > 3 && strcmp(buf+len-2, "ly") == 0) {
        buf[len-2]='\0'; int blen=(int)strlen(buf);
        if (blen>0 && buf[blen-1]=='i') { buf[blen-1]='y'; } goto done;
    }
    /* -es → singular */
    if (len > 3 && strcmp(buf+len-2, "es") == 0) {
        if (len>4 && (buf[len-3]=='s'||buf[len-3]=='h'||buf[len-3]=='x'||buf[len-3]=='z')) buf[len-2]='\0';
        else buf[len-1]='\0';
        goto done;
    }
    /* -s → singular */
    if (len > 3 && buf[len-1]=='s' && buf[len-2]!='s') { buf[len-1]='\0'; goto done; }
done:
    strncpy(output, buf, max_len-1); output[max_len-1]='\0';
}
static SynonymEntry* find_entry(SynonymDB* db, const char* word) {
    for (int i = 0; i < db->count; i++) {
        if (strcmp(db->entries[i].word, word) == 0) return &db->entries[i];
    }
    return NULL;
}

int synonym_lookup(SynonymDB* db, const char* word, char results[][MAX_WORD_LEN], int max_results) {
    char norm[MAX_WORD_LEN];
    /* Try direct lookup */
    SynonymEntry* e = find_entry(db, word);
    if (!e) {
        word_normalize(word, norm, MAX_WORD_LEN);
        e = find_entry(db, norm);
    }
    if (!e) return 0;
    int n = e->synonym_count < max_results ? e->synonym_count : max_results;
    for (int i = 0; i < n; i++) strncpy(results[i], e->synonyms[i], MAX_WORD_LEN);
    return n;
}

int synonym_are_synonyms(SynonymDB* db, const char* a, const char* b) {
    char na[MAX_WORD_LEN], nb[MAX_WORD_LEN];
    word_normalize(a, na, MAX_WORD_LEN);
    word_normalize(b, nb, MAX_WORD_LEN);
    /* Check a's synonyms for b */
    const char* checks_a[] = {a, na};
    const char* checks_b[] = {b, nb};
    for (int ai = 0; ai < 2; ai++) {
        SynonymEntry* e = find_entry(db, checks_a[ai]);
        if (!e) continue;
        for (int i = 0; i < e->synonym_count; i++) {
            for (int bi = 0; bi < 2; bi++) {
                if (strcmp(e->synonyms[i], checks_b[bi]) == 0) return 1;
            }
        }
    }
    /* Check b's synonyms for a */
    for (int bi = 0; bi < 2; bi++) {
        SynonymEntry* e = find_entry(db, checks_b[bi]);
        if (!e) continue;
        for (int i = 0; i < e->synonym_count; i++) {
            for (int ai = 0; ai < 2; ai++) {
                if (strcmp(e->synonyms[i], checks_a[ai]) == 0) return 1;
            }
        }
    }
    return 0;
}

float word_distance(SynonymDB* db, const char* a, const char* b) {
    if (strcmp(a, b) == 0) return 0.0f;
    /* Normalized forms match */
    char na[MAX_WORD_LEN], nb[MAX_WORD_LEN];
    word_normalize(a, na, MAX_WORD_LEN);
    word_normalize(b, nb, MAX_WORD_LEN);
    if (strcmp(na, nb) == 0) return 0.05f;
    /* Direct synonyms */
    if (synonym_are_synonyms(db, a, b)) return 0.1f;
    /* Share a synonym (transitive check) */
    SynonymEntry* ea = find_entry(db, a);
    if (!ea) ea = find_entry(db, na);
    SynonymEntry* eb = find_entry(db, b);
    if (!eb) eb = find_entry(db, nb);
    if (ea && eb) {
        for (int i = 0; i < ea->synonym_count; i++) {
            for (int j = 0; j < eb->synonym_count; j++) {
                if (strcmp(ea->synonyms[i], eb->synonyms[j]) == 0) return 0.3f;
            }
        }
    }
    return 1.0f;
}

#ifdef TEST_MODE
int main(void) {
    SynonymDB db;
    int pass = 0, fail = 0;
    printf("=== Semantic Engine Tests ===\n");
    if (synonym_init(&db) != 0) { printf("FAIL: init\n"); return 1; }
    printf("Loaded %d synonym entries from %d groups\n", db.count, (int)TOTAL_GROUPS);

    /* Test: big and large are synonyms */
    if (synonym_are_synonyms(&db, "big", "large")) { printf("PASS: big/large synonyms\n"); pass++; }
    else { printf("FAIL: big/large synonyms\n"); fail++; }

    /* Test: running normalizes to run */
    char norm[MAX_WORD_LEN];
    word_normalize("running", norm, MAX_WORD_LEN);
    if (strcmp(norm, "run") == 0) { printf("PASS: running→run\n"); pass++; }
    else { printf("FAIL: running→%s (expected run)\n", norm); fail++; }

    /* Test: dogs normalizes to dog */
    word_normalize("dogs", norm, MAX_WORD_LEN);
    if (strcmp(norm, "dog") == 0) { printf("PASS: dogs→dog\n"); pass++; }
    else { printf("FAIL: dogs→%s (expected dog)\n", norm); fail++; }

    /* Test: bigger normalizes to big */
    word_normalize("bigger", norm, MAX_WORD_LEN);
    if (strcmp(norm, "big") == 0) { printf("PASS: bigger→big\n"); pass++; }
    else { printf("FAIL: bigger→%s (expected big)\n", norm); fail++; }

    /* Test: word_distance big/large < 0.2 */
    float d = word_distance(&db, "big", "large");
    if (d < 0.2f) { printf("PASS: distance(big,large)=%.2f\n", d); pass++; }
    else { printf("FAIL: distance(big,large)=%.2f\n", d); fail++; }

    /* Test: word_distance big/fish == 1.0 */
    d = word_distance(&db, "big", "fish");
    if (d == 1.0f) { printf("PASS: distance(big,fish)=%.2f\n", d); pass++; }
    else { printf("FAIL: distance(big,fish)=%.2f\n", d); fail++; }

    /* Test: synonym_lookup happy */
    char results[MAX_SYNONYMS_PER_WORD][MAX_WORD_LEN];
    int n = synonym_lookup(&db, "happy", results, MAX_SYNONYMS_PER_WORD);
    if (n > 0) { printf("PASS: lookup(happy) returned %d synonyms:", n); for(int i=0;i<n;i++) printf(" %s",results[i]); printf("\n"); pass++; }
    else { printf("FAIL: lookup(happy) returned 0\n"); fail++; }

    /* Test: quickly normalizes to quick */
    word_normalize("quickly", norm, MAX_WORD_LEN);
    if (strcmp(norm, "quick") == 0) { printf("PASS: quickly→quick\n"); pass++; }
    else { printf("FAIL: quickly→%s (expected quick)\n", norm); fail++; }

    /* Test: created normalizes to create */
    word_normalize("created", norm, MAX_WORD_LEN);
    if (strcmp(norm, "create") == 0) { printf("PASS: created→create\n"); pass++; }
    else { printf("FAIL: created→%s (expected create)\n", norm); fail++; }

    printf("\n=== Results: %d passed, %d failed ===\n", pass, fail);
    synonym_destroy(&db);
    return fail > 0 ? 1 : 0;
}
#endif

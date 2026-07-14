#!/usr/bin/env python3
"""
MEGA Knowledge Expansion — Target: 1M+ unique subjects, max facts.
Domains: Health, Crypto, Trading, Finance, + all DBpedia maxed out.
"""
import urllib.request, urllib.parse, json, time, os, sys, gzip, csv

SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
RAW_DIR = os.path.join(SCRIPTS_DIR, '..', 'data', 'raw')
OUTPUT = os.path.join(RAW_DIR, 'batch_mega_expansion.txt')
os.makedirs(RAW_DIR, exist_ok=True)

DBPEDIA_URL = "https://dbpedia.org/sparql"
facts_added = 0
queries_done = 0


def dbpedia_query(query, retries=3):
    global queries_done
    for attempt in range(retries):
        try:
            params = urllib.parse.urlencode({
                'default-graph-uri': 'http://dbpedia.org',
                'query': query, 'format': 'application/json'
            })
            url = f"{DBPEDIA_URL}?{params}"
            req = urllib.request.Request(url, headers={'User-Agent': 'Axima/3.0'})
            resp = urllib.request.urlopen(req, timeout=120)
            data = json.loads(resp.read().decode())
            queries_done += 1
            time.sleep(1.5)
            return data
        except Exception as e:
            print(f"    [Q{queries_done+1}] attempt {attempt+1} fail: {e}", flush=True)
            time.sleep(8 * (attempt + 1))
    return None

def n(uri):
    """Extract name from URI."""
    if not uri: return None
    nm = uri.split('/')[-1].replace('_', ' ')
    if '(' in nm: nm = nm.split('(')[0].strip()
    return nm if len(nm) > 1 and len(nm) < 128 else None

def w(f, subj, rel, obj, conf=90):
    """Write triple."""
    global facts_added
    if subj and obj and len(subj) > 1 and len(obj) > 0:
        s = subj.lower().strip()[:127]
        o = obj.lower().strip()[:127]
        if s and o and len(s) > 1:
            f.write(f"{s}|{rel}|{o}|{conf}\n")
            facts_added += 1


# ═══════════════════════════════════════════════════════════
# HEALTH & MEDICAL (massive)
# ═══════════════════════════════════════════════════════════
def health_medical(f):
    print("\n[HEALTH] Diseases, symptoms, treatments, anatomy, drugs...", flush=True)

    # Diseases with symptoms
    print("  Diseases...", flush=True)
    for offset in range(0, 50000, 10000):
        q = f"""SELECT ?disease ?symptom ?cause WHERE {{
          ?disease a dbo:Disease .
          OPTIONAL {{ ?disease dbo:symptom ?symptom }}
          OPTIONAL {{ ?disease dbo:cause ?cause }}
        }} LIMIT 10000 OFFSET {offset}"""
        data = dbpedia_query(q)
        if not data or not data['results']['bindings']: break
        for row in data['results']['bindings']:
            d = n(row.get('disease',{}).get('value',''))
            if not d: continue
            w(f, d, 'is_a', 'disease', 90)
            s = n(row.get('symptom',{}).get('value',''))
            if s: w(f, d, 'has_symptom', s, 85)
            c = n(row.get('cause',{}).get('value',''))
            if c: w(f, d, 'caused_by', c, 85)

    # Drugs / medications
    print("  Drugs & medications...", flush=True)
    for offset in range(0, 50000, 10000):
        q = f"""SELECT ?drug ?use ?tradeName WHERE {{
          ?drug a dbo:Drug .
          OPTIONAL {{ ?drug dbo:drugName ?tradeName }}
          OPTIONAL {{ ?drug dbp:type ?use }}
        }} LIMIT 10000 OFFSET {offset}"""
        data = dbpedia_query(q)
        if not data or not data['results']['bindings']: break
        for row in data['results']['bindings']:
            d = n(row.get('drug',{}).get('value',''))
            if not d: continue
            w(f, d, 'is_a', 'drug', 90)
            u = row.get('use',{}).get('value','')
            if u and not u.startswith('http'): w(f, d, 'drug_type', u.lower()[:127], 80)
            tn = row.get('tradeName',{}).get('value','')
            if tn and not tn.startswith('http'): w(f, d, 'trade_name', tn.lower()[:127], 80)

    # Anatomy - bones, muscles, organs
    print("  Anatomy...", flush=True)
    q = """SELECT ?bone ?part WHERE {
      ?bone a dbo:Bone .
      OPTIONAL { ?bone dbo:nervousSystem ?part }
    } LIMIT 10000"""
    data = dbpedia_query(q)
    if data:
        for row in data['results']['bindings']:
            b = n(row.get('bone',{}).get('value',''))
            if b: w(f, b, 'is_a', 'bone', 90)

    q2 = """SELECT ?muscle ?origin ?insertion WHERE {
      ?muscle a dbo:Muscle .
      OPTIONAL { ?muscle dbo:origin ?origin }
      OPTIONAL { ?muscle dbo:insertion ?insertion }
    } LIMIT 10000"""
    data = dbpedia_query(q2)
    if data:
        for row in data['results']['bindings']:
            m = n(row.get('muscle',{}).get('value',''))
            if not m: continue
            w(f, m, 'is_a', 'muscle', 90)
            o = n(row.get('origin',{}).get('value',''))
            if o: w(f, m, 'origin', o, 80)

    # Arteries & Veins
    print("  Blood vessels...", flush=True)
    q3 = """SELECT ?vessel ?supplies WHERE {
      ?vessel a dbo:Artery .
      OPTIONAL { ?vessel dbo:supplyTo ?supplies }
    } LIMIT 5000"""
    data = dbpedia_query(q3)
    if data:
        for row in data['results']['bindings']:
            v = n(row.get('vessel',{}).get('value',''))
            if not v: continue
            w(f, v, 'is_a', 'artery', 90)
            s = n(row.get('supplies',{}).get('value',''))
            if s: w(f, v, 'supplies', s, 85)

    q4 = """SELECT ?vein ?drains WHERE {
      ?vein a dbo:Vein .
      OPTIONAL { ?vein dbo:drainsTo ?drains }
    } LIMIT 5000"""
    data = dbpedia_query(q4)
    if data:
        for row in data['results']['bindings']:
            v = n(row.get('vein',{}).get('value',''))
            if not v: continue
            w(f, v, 'is_a', 'vein', 90)

    # Nerves
    q5 = """SELECT ?nerve WHERE {
      ?nerve a dbo:Nerve .
    } LIMIT 5000"""
    data = dbpedia_query(q5)
    if data:
        for row in data['results']['bindings']:
            nv = n(row.get('nerve',{}).get('value',''))
            if nv: w(f, nv, 'is_a', 'nerve', 90)

    # Medical procedures/treatments
    print("  Medical specialties...", flush=True)
    q6 = """SELECT ?spec WHERE {
      ?spec a dbo:MedicalSpecialty .
    } LIMIT 1000"""
    data = dbpedia_query(q6)
    if data:
        for row in data['results']['bindings']:
            s = n(row.get('spec',{}).get('value',''))
            if s: w(f, s, 'is_a', 'medical specialty', 90)


# ═══════════════════════════════════════════════════════════
# CRYPTO & BLOCKCHAIN
# ═══════════════════════════════════════════════════════════
def crypto_blockchain(f):
    print("\n[CRYPTO] Cryptocurrencies, exchanges, DeFi, blockchain...", flush=True)

    # Programmatic: top cryptocurrencies with full details
    cryptos = [
        ("bitcoin", "btc", "satoshi nakamoto", "2009", "21000000", "proof of work"),
        ("ethereum", "eth", "vitalik buterin", "2015", "unlimited", "proof of stake"),
        ("binance coin", "bnb", "changpeng zhao", "2017", "200000000", "proof of stake authority"),
        ("solana", "sol", "anatoly yakovenko", "2020", "unlimited", "proof of history"),
        ("cardano", "ada", "charles hoskinson", "2017", "45000000000", "proof of stake"),
        ("ripple", "xrp", "chris larsen", "2012", "100000000000", "consensus protocol"),
        ("polkadot", "dot", "gavin wood", "2020", "unlimited", "nominated proof of stake"),
        ("dogecoin", "doge", "billy markus", "2013", "unlimited", "proof of work"),
        ("avalanche", "avax", "emin gun sirer", "2020", "720000000", "proof of stake"),
        ("chainlink", "link", "sergey nazarov", "2017", "1000000000", "oracle network"),
        ("polygon", "matic", "sandeep nailwal", "2017", "10000000000", "proof of stake"),
        ("uniswap", "uni", "hayden adams", "2018", "1000000000", "automated market maker"),
        ("litecoin", "ltc", "charlie lee", "2011", "84000000", "proof of work"),
        ("cosmos", "atom", "jae kwon", "2019", "unlimited", "tendermint consensus"),
        ("monero", "xmr", "riccardo spagni", "2014", "unlimited", "proof of work"),
        ("stellar", "xlm", "jed mccaleb", "2014", "50000000000", "stellar consensus"),
        ("tezos", "xtz", "arthur breitman", "2018", "unlimited", "liquid proof of stake"),
        ("algorand", "algo", "silvio micali", "2019", "10000000000", "pure proof of stake"),
        ("near protocol", "near", "illia polosukhin", "2020", "1000000000", "nightshade sharding"),
        ("filecoin", "fil", "juan benet", "2020", "2000000000", "proof of replication"),
        ("aave", "aave", "stani kulechov", "2020", "16000000", "defi lending"),
        ("maker", "mkr", "rune christensen", "2017", "1000000", "defi governance"),
        ("compound", "comp", "robert leshner", "2018", "10000000", "defi lending"),
        ("sushi", "sushi", "chef nomi", "2020", "250000000", "decentralized exchange"),
        ("curve", "crv", "michael egorov", "2020", "3000000000", "stablecoin dex"),
        ("fantom", "ftm", "andre cronje", "2018", "3175000000", "dag consensus"),
        ("hedera", "hbar", "leemon baird", "2019", "50000000000", "hashgraph"),
        ("aptos", "apt", "mo shaikh", "2022", "unlimited", "proof of stake"),
        ("sui", "sui", "evan cheng", "2023", "10000000000", "delegated proof of stake"),
        ("arbitrum", "arb", "ed felten", "2021", "10000000000", "optimistic rollup"),
        ("optimism", "op", "jinglan wang", "2021", "4294967296", "optimistic rollup"),
        ("tron", "trx", "justin sun", "2017", "unlimited", "delegated proof of stake"),
        ("vechain", "vet", "sunny lu", "2015", "86712634466", "proof of authority"),
        ("theta", "theta", "mitch liu", "2018", "1000000000", "multi-bft consensus"),
        ("eos", "eos", "dan larimer", "2018", "unlimited", "delegated proof of stake"),
        ("iota", "miota", "david sonstebo", "2016", "2779530283", "directed acyclic graph"),
        ("zilliqa", "zil", "xinshu dong", "2017", "21000000000", "practical byzantine fault tolerance"),
        ("decentraland", "mana", "ari meilich", "2017", "2194000000", "metaverse"),
        ("the sandbox", "sand", "arthur madrid", "2012", "3000000000", "metaverse gaming"),
        ("axie infinity", "axs", "trung nguyen", "2018", "270000000", "play to earn"),
    ]
    for name_val, symbol, creator, year, supply, consensus in cryptos:
        w(f, name_val, 'is_a', 'cryptocurrency', 99)
        w(f, name_val, 'symbol', symbol, 99)
        w(f, name_val, 'created_by', creator, 95)
        w(f, name_val, 'launch_year', year, 95)
        w(f, name_val, 'max_supply', supply, 90)
        w(f, name_val, 'consensus_mechanism', consensus, 90)

    # Exchanges
    exchanges = [
        ("binance", "changpeng zhao", "2017", "cayman islands"),
        ("coinbase", "brian armstrong", "2012", "united states"),
        ("kraken", "jesse powell", "2011", "united states"),
        ("ftx", "sam bankman-fried", "2019", "bahamas"),
        ("kucoin", "johnny lyu", "2017", "seychelles"),
        ("bybit", "ben zhou", "2018", "dubai"),
        ("okx", "star xu", "2017", "seychelles"),
        ("gate.io", "lin han", "2013", "cayman islands"),
        ("huobi", "leon li", "2013", "seychelles"),
        ("bitfinex", "giancarlo devasini", "2012", "hong kong"),
        ("gemini", "cameron winklevoss", "2014", "united states"),
        ("bitstamp", "nejc kodric", "2011", "luxembourg"),
        ("crypto.com", "kris marszalek", "2016", "singapore"),
        ("deribit", "john jansen", "2016", "panama"),
        ("bitget", "sandra lou", "2018", "singapore"),
    ]
    for ex, founder, year, location in exchanges:
        w(f, ex, 'is_a', 'cryptocurrency exchange', 95)
        w(f, ex, 'founded_by', founder, 90)
        w(f, ex, 'founded_year', year, 90)
        w(f, ex, 'headquartered_in', location, 85)

    # DeFi concepts
    defi_concepts = [
        ("defi", "stands_for", "decentralized finance"),
        ("liquidity pool", "is_a", "defi mechanism"),
        ("liquidity pool", "purpose", "provide liquidity for token swaps"),
        ("yield farming", "is_a", "defi strategy"),
        ("yield farming", "purpose", "earn rewards by providing liquidity"),
        ("impermanent loss", "is_a", "defi risk"),
        ("impermanent loss", "occurs_when", "token prices diverge from deposit ratio"),
        ("flash loan", "is_a", "defi mechanism"),
        ("flash loan", "property", "borrow and repay in single transaction"),
        ("staking", "is_a", "crypto earning method"),
        ("staking", "purpose", "validate transactions and earn rewards"),
        ("smart contract", "is_a", "self-executing code on blockchain"),
        ("smart contract", "invented_by", "nick szabo"),
        ("gas fee", "is_a", "transaction cost on blockchain"),
        ("nft", "stands_for", "non-fungible token"),
        ("nft", "is_a", "unique digital asset on blockchain"),
        ("dao", "stands_for", "decentralized autonomous organization"),
        ("dex", "stands_for", "decentralized exchange"),
        ("cex", "stands_for", "centralized exchange"),
        ("amm", "stands_for", "automated market maker"),
        ("tvl", "stands_for", "total value locked"),
        ("apy", "stands_for", "annual percentage yield"),
        ("apr", "stands_for", "annual percentage rate"),
        ("hodl", "means", "hold on for dear life"),
        ("whale", "means", "large cryptocurrency holder"),
        ("rug pull", "is_a", "crypto scam where developers abandon project"),
        ("pump and dump", "is_a", "market manipulation scheme"),
        ("layer 1", "is_a", "base blockchain network"),
        ("layer 2", "is_a", "scaling solution built on top of layer 1"),
        ("rollup", "is_a", "layer 2 scaling technology"),
        ("sidechain", "is_a", "separate blockchain connected to main chain"),
        ("bridge", "is_a", "protocol connecting different blockchains"),
        ("oracle", "is_a", "service providing external data to blockchain"),
        ("tokenomics", "is_a", "economic model of a cryptocurrency"),
        ("whitepaper", "is_a", "technical document describing crypto project"),
        ("cold wallet", "is_a", "offline cryptocurrency storage"),
        ("hot wallet", "is_a", "online cryptocurrency storage"),
        ("seed phrase", "is_a", "recovery words for crypto wallet"),
        ("private key", "is_a", "secret cryptographic key for wallet access"),
        ("public key", "is_a", "shareable address for receiving crypto"),
        ("mining", "is_a", "process of validating blockchain transactions"),
        ("halving", "is_a", "event reducing bitcoin mining rewards by 50%"),
        ("bitcoin halving", "occurs_every", "210000 blocks approximately 4 years"),
        ("merkle tree", "is_a", "data structure used in blockchain verification"),
        ("hash function", "is_a", "one-way cryptographic function"),
        ("sha-256", "used_by", "bitcoin"),
        ("keccak-256", "used_by", "ethereum"),
    ]
    for s, r, o in defi_concepts:
        w(f, s, r, o, 95)

    # Blockchain types & concepts
    blockchain_facts = [
        ("blockchain", "is_a", "distributed ledger technology"),
        ("blockchain", "invented_by", "satoshi nakamoto"),
        ("blockchain", "first_implementation", "bitcoin 2009"),
        ("proof of work", "is_a", "consensus mechanism"),
        ("proof of work", "requires", "computational power"),
        ("proof of stake", "is_a", "consensus mechanism"),
        ("proof of stake", "requires", "token staking"),
        ("delegated proof of stake", "is_a", "consensus mechanism"),
        ("proof of history", "is_a", "consensus mechanism"),
        ("proof of history", "used_by", "solana"),
        ("byzantine fault tolerance", "is_a", "consensus property"),
        ("51% attack", "is_a", "blockchain vulnerability"),
        ("double spending", "is_a", "blockchain problem solved by consensus"),
        ("immutability", "is_a", "blockchain property"),
        ("decentralization", "is_a", "blockchain principle"),
        ("web3", "is_a", "decentralized internet concept"),
        ("metaverse", "is_a", "virtual world powered by blockchain"),
        ("gamefi", "is_a", "gaming combined with defi"),
        ("socialfi", "is_a", "social media combined with defi"),
    ]
    for s, r, o in blockchain_facts:
        w(f, s, r, o, 95)


# ═══════════════════════════════════════════════════════════
# TRADING & FINANCE
# ═══════════════════════════════════════════════════════════
def trading_finance(f):
    print("\n[TRADING] Stocks, markets, indicators, strategies...", flush=True)

    # Stock exchanges
    stock_exchanges = [
        ("new york stock exchange", "nyse", "united states", "1792"),
        ("nasdaq", "nasdaq", "united states", "1971"),
        ("london stock exchange", "lse", "united kingdom", "1801"),
        ("tokyo stock exchange", "tse", "japan", "1878"),
        ("shanghai stock exchange", "sse", "china", "1990"),
        ("hong kong stock exchange", "hkex", "hong kong", "1891"),
        ("euronext", "enx", "europe", "2000"),
        ("toronto stock exchange", "tsx", "canada", "1852"),
        ("deutsche borse", "db", "germany", "1992"),
        ("bombay stock exchange", "bse", "india", "1875"),
        ("national stock exchange of india", "nse", "india", "1992"),
        ("australian securities exchange", "asx", "australia", "1987"),
        ("korea exchange", "krx", "south korea", "2005"),
        ("taiwan stock exchange", "twse", "taiwan", "1961"),
        ("singapore exchange", "sgx", "singapore", "1999"),
        ("swiss exchange", "six", "switzerland", "1850"),
        ("johannesburg stock exchange", "jse", "south africa", "1887"),
        ("moscow exchange", "moex", "russia", "2011"),
        ("b3", "b3", "brazil", "2017"),
        ("bolsa mexicana de valores", "bmv", "mexico", "1894"),
    ]
    for name_val, symbol, country, year in stock_exchanges:
        w(f, name_val, 'is_a', 'stock exchange', 99)
        w(f, name_val, 'symbol', symbol, 95)
        w(f, name_val, 'located_in', country, 95)
        w(f, name_val, 'founded_year', year, 90)

    # Major stock indices
    indices = [
        ("s&p 500", "tracks", "500 largest us companies"),
        ("dow jones industrial average", "tracks", "30 major us companies"),
        ("nasdaq composite", "tracks", "all nasdaq listed stocks"),
        ("ftse 100", "tracks", "100 largest uk companies"),
        ("dax", "tracks", "40 largest german companies"),
        ("nikkei 225", "tracks", "225 japanese companies"),
        ("hang seng", "tracks", "hong kong companies"),
        ("shanghai composite", "tracks", "all shanghai exchange stocks"),
        ("sensex", "tracks", "30 largest indian companies"),
        ("nifty 50", "tracks", "50 largest indian companies"),
        ("cac 40", "tracks", "40 largest french companies"),
        ("asx 200", "tracks", "200 largest australian companies"),
        ("russell 2000", "tracks", "2000 small cap us companies"),
        ("vix", "measures", "market volatility expectations"),
    ]
    for idx, rel, desc in indices:
        w(f, idx, 'is_a', 'stock index', 99)
        w(f, idx, rel, desc, 95)

    # Trading indicators & concepts
    trading_concepts = [
        ("moving average", "is_a", "technical indicator"),
        ("moving average", "purpose", "smooth price data over time period"),
        ("exponential moving average", "is_a", "technical indicator"),
        ("exponential moving average", "abbreviation", "ema"),
        ("simple moving average", "is_a", "technical indicator"),
        ("simple moving average", "abbreviation", "sma"),
        ("relative strength index", "is_a", "momentum indicator"),
        ("relative strength index", "abbreviation", "rsi"),
        ("relative strength index", "range", "0 to 100"),
        ("rsi above 70", "indicates", "overbought condition"),
        ("rsi below 30", "indicates", "oversold condition"),
        ("macd", "stands_for", "moving average convergence divergence"),
        ("macd", "is_a", "trend-following momentum indicator"),
        ("bollinger bands", "is_a", "volatility indicator"),
        ("bollinger bands", "created_by", "john bollinger"),
        ("bollinger bands", "components", "middle band sma upper band lower band"),
        ("fibonacci retracement", "is_a", "technical analysis tool"),
        ("fibonacci retracement", "key_levels", "23.6% 38.2% 50% 61.8% 78.6%"),
        ("support level", "is_a", "price level where buying pressure exceeds selling"),
        ("resistance level", "is_a", "price level where selling pressure exceeds buying"),
        ("candlestick chart", "is_a", "price chart type"),
        ("candlestick chart", "shows", "open high low close prices"),
        ("doji", "is_a", "candlestick pattern indicating indecision"),
        ("hammer", "is_a", "bullish reversal candlestick pattern"),
        ("shooting star", "is_a", "bearish reversal candlestick pattern"),
        ("engulfing pattern", "is_a", "reversal candlestick pattern"),
        ("head and shoulders", "is_a", "reversal chart pattern"),
        ("double top", "is_a", "bearish reversal pattern"),
        ("double bottom", "is_a", "bullish reversal pattern"),
        ("cup and handle", "is_a", "bullish continuation pattern"),
        ("ascending triangle", "is_a", "bullish chart pattern"),
        ("descending triangle", "is_a", "bearish chart pattern"),
        ("volume", "is_a", "number of shares traded"),
        ("market capitalization", "is_a", "total value of all shares outstanding"),
        ("price to earnings ratio", "abbreviation", "p/e ratio"),
        ("price to earnings ratio", "measures", "stock price relative to earnings"),
        ("earnings per share", "abbreviation", "eps"),
        ("dividend yield", "measures", "annual dividend as percentage of stock price"),
        ("beta", "measures", "stock volatility relative to market"),
        ("alpha", "measures", "excess return above benchmark"),
        ("sharpe ratio", "measures", "risk-adjusted return"),
        ("drawdown", "is_a", "peak to trough decline in portfolio value"),
        ("stop loss", "is_a", "order to sell at predetermined loss level"),
        ("take profit", "is_a", "order to sell at predetermined profit level"),
        ("trailing stop", "is_a", "stop loss that moves with price"),
        ("limit order", "is_a", "order to buy or sell at specific price"),
        ("market order", "is_a", "order to buy or sell at current market price"),
        ("bid ask spread", "is_a", "difference between buy and sell prices"),
        ("liquidity", "is_a", "ease of buying or selling without price impact"),
        ("slippage", "is_a", "difference between expected and execution price"),
        ("leverage", "is_a", "using borrowed money to increase position size"),
        ("margin call", "occurs_when", "account equity falls below maintenance margin"),
        ("short selling", "is_a", "selling borrowed shares expecting price decline"),
        ("long position", "is_a", "buying asset expecting price increase"),
        ("short position", "is_a", "selling asset expecting price decrease"),
        ("bull market", "is_a", "sustained period of rising prices"),
        ("bear market", "is_a", "sustained period of falling prices"),
        ("correction", "is_a", "10-20% decline from recent high"),
        ("crash", "is_a", "sudden severe decline in market prices"),
        ("rally", "is_a", "sustained increase in market prices"),
        ("consolidation", "is_a", "period of sideways price movement"),
        ("breakout", "is_a", "price moving above resistance level"),
        ("breakdown", "is_a", "price moving below support level"),
        ("trend", "is_a", "general direction of price movement"),
        ("uptrend", "defined_as", "series of higher highs and higher lows"),
        ("downtrend", "defined_as", "series of lower highs and lower lows"),
        ("ichimoku cloud", "is_a", "comprehensive technical indicator"),
        ("stochastic oscillator", "is_a", "momentum indicator"),
        ("average true range", "is_a", "volatility indicator"),
        ("average true range", "abbreviation", "atr"),
        ("on balance volume", "is_a", "volume-based indicator"),
        ("on balance volume", "abbreviation", "obv"),
        ("williams %r", "is_a", "momentum indicator"),
        ("pivot point", "is_a", "support resistance calculation"),
        ("vwap", "stands_for", "volume weighted average price"),
        ("vwap", "is_a", "intraday benchmark"),
    ]
    for s, r, o in trading_concepts:
        w(f, s, r, o, 95)

    # Trading strategies
    strategies = [
        ("scalping", "is_a", "trading strategy"),
        ("scalping", "timeframe", "seconds to minutes"),
        ("scalping", "goal", "small profits from many trades"),
        ("day trading", "is_a", "trading strategy"),
        ("day trading", "timeframe", "single trading day"),
        ("swing trading", "is_a", "trading strategy"),
        ("swing trading", "timeframe", "days to weeks"),
        ("position trading", "is_a", "trading strategy"),
        ("position trading", "timeframe", "weeks to months"),
        ("momentum trading", "is_a", "strategy following strong price trends"),
        ("mean reversion", "is_a", "strategy betting prices return to average"),
        ("pairs trading", "is_a", "strategy trading correlated assets"),
        ("arbitrage", "is_a", "exploiting price differences across markets"),
        ("dollar cost averaging", "is_a", "investing fixed amount at regular intervals"),
        ("value investing", "is_a", "buying undervalued assets"),
        ("value investing", "pioneer", "benjamin graham"),
        ("growth investing", "is_a", "buying high growth potential companies"),
        ("index investing", "is_a", "passive strategy matching market index"),
        ("contrarian investing", "is_a", "going against market consensus"),
        ("technical analysis", "is_a", "using charts and indicators for decisions"),
        ("fundamental analysis", "is_a", "analyzing financial statements and economics"),
        ("quantitative trading", "is_a", "algorithmic strategy using mathematical models"),
        ("high frequency trading", "is_a", "algorithmic trading at microsecond speeds"),
        ("options trading", "is_a", "trading derivative contracts"),
        ("call option", "gives_right_to", "buy asset at strike price"),
        ("put option", "gives_right_to", "sell asset at strike price"),
        ("futures contract", "is_a", "agreement to buy/sell at future date"),
        ("forex trading", "is_a", "trading currency pairs"),
        ("commodity trading", "is_a", "trading raw materials"),
        ("etf", "stands_for", "exchange traded fund"),
        ("mutual fund", "is_a", "pooled investment vehicle"),
        ("hedge fund", "is_a", "alternative investment fund for accredited investors"),
        ("portfolio diversification", "purpose", "reduce risk by spreading investments"),
        ("risk management", "is_a", "process of identifying and managing trading risks"),
        ("position sizing", "is_a", "determining how much capital to risk per trade"),
        ("kelly criterion", "is_a", "formula for optimal position sizing"),
        ("monte carlo simulation", "is_a", "risk modeling technique"),
        ("backtest", "is_a", "testing strategy on historical data"),
        ("paper trading", "is_a", "simulated trading without real money"),
    ]
    for s, r, o in strategies:
        w(f, s, r, o, 95)

    # Major companies (stocks)
    major_companies = [
        ("apple", "aapl", "technology", "1976", "united states"),
        ("microsoft", "msft", "technology", "1975", "united states"),
        ("amazon", "amzn", "e-commerce", "1994", "united states"),
        ("alphabet", "googl", "technology", "1998", "united states"),
        ("meta platforms", "meta", "social media", "2004", "united states"),
        ("nvidia", "nvda", "semiconductors", "1993", "united states"),
        ("tesla", "tsla", "electric vehicles", "2003", "united states"),
        ("berkshire hathaway", "brk", "conglomerate", "1839", "united states"),
        ("johnson & johnson", "jnj", "healthcare", "1886", "united states"),
        ("jpmorgan chase", "jpm", "banking", "1799", "united states"),
        ("visa", "v", "financial services", "1958", "united states"),
        ("walmart", "wmt", "retail", "1962", "united states"),
        ("procter & gamble", "pg", "consumer goods", "1837", "united states"),
        ("unitedhealth", "unh", "healthcare", "1977", "united states"),
        ("mastercard", "ma", "financial services", "1966", "united states"),
        ("samsung", "005930", "technology", "1938", "south korea"),
        ("toyota", "tm", "automotive", "1937", "japan"),
        ("tencent", "0700", "technology", "1998", "china"),
        ("alibaba", "baba", "e-commerce", "1999", "china"),
        ("tsmc", "tsm", "semiconductors", "1987", "taiwan"),
        ("nestle", "nesn", "food", "1866", "switzerland"),
        ("roche", "rog", "pharmaceuticals", "1896", "switzerland"),
        ("lvmh", "mc", "luxury goods", "1987", "france"),
        ("novo nordisk", "nvo", "pharmaceuticals", "1923", "denmark"),
        ("asml", "asml", "semiconductors", "1984", "netherlands"),
    ]
    for company, ticker, sector, year, country in major_companies:
        w(f, company, 'is_a', 'publicly traded company', 95)
        w(f, company, 'ticker_symbol', ticker, 95)
        w(f, company, 'sector', sector, 90)
        w(f, company, 'founded_year', year, 90)
        w(f, company, 'country', country, 90)

    # Financial concepts
    finance_concepts = [
        ("inflation", "is_a", "general increase in price levels"),
        ("deflation", "is_a", "general decrease in price levels"),
        ("interest rate", "is_a", "cost of borrowing money"),
        ("federal reserve", "is_a", "central bank of united states"),
        ("european central bank", "is_a", "central bank of eurozone"),
        ("bank of japan", "is_a", "central bank of japan"),
        ("bank of england", "is_a", "central bank of united kingdom"),
        ("gdp", "stands_for", "gross domestic product"),
        ("gdp", "measures", "total economic output of a country"),
        ("recession", "defined_as", "two consecutive quarters of negative gdp growth"),
        ("depression", "is_a", "severe prolonged economic downturn"),
        ("quantitative easing", "is_a", "central bank buying assets to increase money supply"),
        ("bond", "is_a", "fixed income debt instrument"),
        ("yield curve", "is_a", "graph of bond yields across maturities"),
        ("inverted yield curve", "indicates", "potential recession"),
        ("treasury bond", "is_a", "us government debt instrument"),
        ("corporate bond", "is_a", "debt issued by corporations"),
        ("credit rating", "measures", "borrower creditworthiness"),
        ("ipo", "stands_for", "initial public offering"),
        ("spac", "stands_for", "special purpose acquisition company"),
        ("market maker", "is_a", "entity providing liquidity by quoting buy and sell prices"),
        ("dark pool", "is_a", "private exchange for trading securities"),
        ("circuit breaker", "is_a", "mechanism halting trading during extreme moves"),
        ("black swan", "is_a", "rare unpredictable event with severe consequences"),
        ("black swan", "coined_by", "nassim nicholas taleb"),
    ]
    for s, r, o in finance_concepts:
        w(f, s, r, o, 95)


# ═══════════════════════════════════════════════════════════
# MAX OUT DBPEDIA — ALL CATEGORIES AT HUGE LIMITS
# ═══════════════════════════════════════════════════════════
def max_dbpedia(f):
    print("\n[DBPEDIA MAX] Pulling maximum data from all categories...", flush=True)

    categories = [
        ("dbo:Person", "person", 50000),
        ("dbo:Place", "place", 50000),
        ("dbo:Organisation", "organization", 50000),
        ("dbo:Work", "creative work", 50000),
        ("dbo:Species", "species", 50000),
        ("dbo:Event", "event", 30000),
        ("dbo:MeanOfTransportation", "vehicle", 30000),
        ("dbo:ArchitecturalStructure", "architectural structure", 30000),
        ("dbo:CelestialBody", "celestial body", 10000),
        ("dbo:Food", "food", 10000),
        ("dbo:Device", "device", 10000),
        ("dbo:SportsSeason", "sports season", 20000),
        ("dbo:MilitaryUnit", "military unit", 10000),
        ("dbo:Weapon", "weapon", 5000),
        ("dbo:EthnicGroup", "ethnic group", 5000),
        ("dbo:Convention", "convention", 5000),
        ("dbo:EducationalInstitution", "educational institution", 30000),
        ("dbo:GovernmentAgency", "government agency", 10000),
        ("dbo:Hospital", "hospital", 10000),
        ("dbo:Legislation", "legislation", 10000),
        ("dbo:NaturalPlace", "natural place", 20000),
        ("dbo:Settlement", "settlement", 50000),
        ("dbo:SportsEvent", "sports event", 20000),
        ("dbo:TelevisionEpisode", "tv episode", 30000),
        ("dbo:Song", "song", 30000),
        ("dbo:Single", "music single", 20000),
        ("dbo:ComicsCharacter", "comics character", 10000),
        ("dbo:FictionalCharacter", "fictional character", 20000),
        ("dbo:Protein", "protein", 10000),
        ("dbo:Gene", "gene", 10000),
        ("dbo:AnatomicalStructure", "anatomical structure", 10000),
    ]

    for cls, label, limit in categories:
        print(f"    {label} (limit {limit})...", flush=True)
        for offset in range(0, limit, 10000):
            q = f"""SELECT ?item WHERE {{
              ?item a {cls} .
            }} LIMIT 10000 OFFSET {offset}"""
            data = dbpedia_query(q)
            if not data or not data['results']['bindings']:
                break
            for row in data['results']['bindings']:
                item = n(row.get('item',{}).get('value',''))
                if item:
                    w(f, item, 'is_a', label, 85)


# ═══════════════════════════════════════════════════════════
# RE-PARSE CONCEPTNET WITH LOWER THRESHOLD (get MORE facts)
# ═══════════════════════════════════════════════════════════
def conceptnet_aggressive(f):
    print("\n[CONCEPTNET] Re-parsing with weight > 0.5 (more facts)...", flush=True)
    DL_FILE = os.path.join(RAW_DIR, 'conceptnet.csv.gz')

    if not os.path.isfile(DL_FILE):
        print("    ConceptNet file not found, downloading...", flush=True)
        DL_URL = "https://s3.amazonaws.com/conceptnet/downloads/2019/edges/conceptnet-assertions-5.7.0.csv.gz"
        urllib.request.urlretrieve(DL_URL, DL_FILE)

    RELATION_MAP = {
        '/r/IsA': 'is_a', '/r/HasA': 'has_part', '/r/PartOf': 'part_of',
        '/r/UsedFor': 'used_for', '/r/CapableOf': 'capable_of',
        '/r/Causes': 'causes', '/r/HasProperty': 'has_property',
        '/r/MadeOf': 'made_of', '/r/AtLocation': 'found_at',
        '/r/HasPrerequisite': 'requires', '/r/MotivatedByGoal': 'purpose',
        '/r/CreatedBy': 'created_by', '/r/DefinedAs': 'defined_as',
        '/r/SymbolOf': 'symbolizes', '/r/RelatedTo': 'related_to',
        '/r/Desires': 'desires', '/r/HasFirstSubevent': 'first_step',
        '/r/HasLastSubevent': 'last_step', '/r/HasSubevent': 'involves',
        '/r/ReceivesAction': 'receives_action', '/r/Antonym': 'opposite_of',
        '/r/Synonym': 'synonym_of', '/r/SimilarTo': 'similar_to',
        '/r/DerivedFrom': 'derived_from', '/r/FormOf': 'form_of',
        '/r/InstanceOf': 'instance_of', '/r/DistinctFrom': 'different_from',
        '/r/MannerOf': 'manner_of', '/r/LocatedNear': 'near',
        '/r/HasContext': 'context', '/r/EtymologicallyRelatedTo': 'etymologically_related',
    }

    count = 0
    with gzip.open(DL_FILE, 'rt', encoding='utf-8', errors='ignore') as gz:
        reader = csv.reader(gz, delimiter='\t')
        for row in reader:
            if len(row) < 5: continue
            relation, source, target, info = row[1], row[2], row[3], row[4]
            if not source.startswith('/c/en/') or not target.startswith('/c/en/'):
                continue
            if relation not in RELATION_MAP:
                continue
            try:
                meta = json.loads(info)
                weight = meta.get('weight', 0)
                if weight < 0.5: continue  # Lower threshold than before
            except: continue

            subj = source[6:].split('/')[0].replace('_', ' ')
            obj = target[6:].split('/')[0].replace('_', ' ')
            rel = RELATION_MAP[relation]
            if subj and obj and len(subj) > 1 and len(obj) > 1:
                conf = min(95, int(40 + weight * 10))
                w(f, subj, rel, obj, conf)
                count += 1
                if count % 500000 == 0:
                    print(f"      {count:,} facts...", flush=True)
    print(f"    ConceptNet total: {count:,} facts", flush=True)


# ═══════════════════════════════════════════════════════════
# MASSIVE PROGRAMMATIC GENERATION
# ═══════════════════════════════════════════════════════════
def massive_programmatic(f):
    print("\n[PROGRAMMATIC] Generating structured facts...", flush=True)

    # Health conditions & symptoms (comprehensive)
    print("  Health conditions...", flush=True)
    conditions = {
        "diabetes": ["increased thirst", "frequent urination", "fatigue", "blurred vision", "slow healing"],
        "hypertension": ["headache", "shortness of breath", "nosebleeds", "dizziness", "chest pain"],
        "asthma": ["wheezing", "shortness of breath", "chest tightness", "coughing", "difficulty breathing"],
        "depression": ["persistent sadness", "loss of interest", "fatigue", "sleep changes", "concentration difficulty"],
        "anxiety": ["excessive worry", "restlessness", "rapid heartbeat", "sweating", "difficulty concentrating"],
        "heart disease": ["chest pain", "shortness of breath", "fatigue", "irregular heartbeat", "swelling"],
        "stroke": ["sudden numbness", "confusion", "trouble speaking", "vision problems", "severe headache"],
        "cancer": ["unexplained weight loss", "fatigue", "pain", "skin changes", "unusual bleeding"],
        "arthritis": ["joint pain", "stiffness", "swelling", "reduced range of motion", "redness"],
        "alzheimer": ["memory loss", "confusion", "difficulty planning", "personality changes", "disorientation"],
        "parkinson": ["tremor", "slow movement", "rigid muscles", "impaired balance", "speech changes"],
        "epilepsy": ["seizures", "temporary confusion", "staring spells", "uncontrollable jerking", "loss of consciousness"],
        "migraine": ["severe headache", "nausea", "sensitivity to light", "sensitivity to sound", "visual disturbances"],
        "pneumonia": ["cough", "fever", "chills", "shortness of breath", "chest pain"],
        "tuberculosis": ["persistent cough", "coughing blood", "weight loss", "night sweats", "fever"],
        "malaria": ["fever", "chills", "headache", "nausea", "muscle pain"],
        "hiv": ["fever", "fatigue", "swollen lymph nodes", "weight loss", "night sweats"],
        "hepatitis": ["fatigue", "nausea", "abdominal pain", "jaundice", "dark urine"],
        "influenza": ["fever", "cough", "body aches", "fatigue", "sore throat"],
        "covid-19": ["fever", "cough", "loss of taste", "loss of smell", "fatigue"],
        "anemia": ["fatigue", "pale skin", "shortness of breath", "dizziness", "cold hands"],
        "osteoporosis": ["bone fractures", "back pain", "loss of height", "stooped posture", "bone weakness"],
        "kidney disease": ["nausea", "fatigue", "decreased urine", "swelling", "shortness of breath"],
        "liver disease": ["jaundice", "abdominal pain", "swelling", "fatigue", "nausea"],
        "thyroid disorder": ["weight changes", "fatigue", "sensitivity to temperature", "hair loss", "mood changes"],
        "celiac disease": ["diarrhea", "bloating", "weight loss", "fatigue", "anemia"],
        "crohn disease": ["diarrhea", "abdominal pain", "fatigue", "weight loss", "blood in stool"],
        "multiple sclerosis": ["numbness", "vision problems", "tingling", "muscle weakness", "fatigue"],
        "lupus": ["joint pain", "fatigue", "skin rash", "fever", "hair loss"],
        "psoriasis": ["red patches", "dry skin", "itching", "burning", "thick nails"],
        "eczema": ["itching", "dry skin", "red patches", "swelling", "cracked skin"],
        "gout": ["sudden joint pain", "swelling", "redness", "tenderness", "limited movement"],
        "fibromyalgia": ["widespread pain", "fatigue", "cognitive difficulty", "sleep problems", "headaches"],
        "insomnia": ["difficulty falling asleep", "waking during night", "daytime fatigue", "irritability", "poor concentration"],
        "sleep apnea": ["loud snoring", "stopped breathing during sleep", "morning headache", "insomnia", "excessive daytime sleepiness"],
        "adhd": ["inattention", "hyperactivity", "impulsivity", "difficulty organizing", "forgetfulness"],
        "autism": ["social difficulty", "repetitive behaviors", "communication challenges", "sensory sensitivity", "routine preference"],
        "ptsd": ["flashbacks", "nightmares", "severe anxiety", "uncontrollable thoughts", "emotional numbness"],
        "bipolar disorder": ["mood swings", "manic episodes", "depressive episodes", "energy changes", "sleep disruption"],
        "schizophrenia": ["hallucinations", "delusions", "disorganized thinking", "social withdrawal", "reduced motivation"],
    }
    for condition, symptoms in conditions.items():
        w(f, condition, 'is_a', 'medical condition', 95)
        for symptom in symptoms:
            w(f, condition, 'has_symptom', symptom, 90)
            w(f, symptom, 'symptom_of', condition, 85)

    # Vitamins & nutrients
    print("  Vitamins & nutrients...", flush=True)
    vitamins = [
        ("vitamin a", "supports", "vision and immune system", "carrots spinach sweet potato"),
        ("vitamin b1", "supports", "energy metabolism", "whole grains pork beans"),
        ("vitamin b2", "supports", "energy production", "eggs dairy leafy greens"),
        ("vitamin b3", "supports", "digestive and nervous system", "meat fish whole grains"),
        ("vitamin b5", "supports", "hormone and cholesterol production", "avocado eggs mushrooms"),
        ("vitamin b6", "supports", "brain development and immune function", "chickpeas fish potatoes"),
        ("vitamin b7", "supports", "hair skin and nail health", "eggs nuts seeds"),
        ("vitamin b9", "supports", "cell division and dna synthesis", "leafy greens legumes citrus"),
        ("vitamin b12", "supports", "nerve function and blood cells", "meat fish dairy eggs"),
        ("vitamin c", "supports", "immune system and collagen", "citrus fruits peppers strawberries"),
        ("vitamin d", "supports", "bone health and calcium absorption", "sunlight fish eggs"),
        ("vitamin e", "supports", "antioxidant protection", "nuts seeds vegetable oils"),
        ("vitamin k", "supports", "blood clotting and bone health", "leafy greens broccoli"),
        ("iron", "supports", "oxygen transport in blood", "red meat spinach lentils"),
        ("calcium", "supports", "bone and teeth health", "dairy leafy greens tofu"),
        ("magnesium", "supports", "muscle and nerve function", "nuts seeds whole grains"),
        ("zinc", "supports", "immune function and wound healing", "meat shellfish legumes"),
        ("potassium", "supports", "heart and muscle function", "bananas potatoes spinach"),
        ("omega-3", "supports", "brain and heart health", "fatty fish walnuts flaxseed"),
        ("fiber", "supports", "digestive health", "whole grains fruits vegetables legumes"),
        ("protein", "supports", "muscle growth and repair", "meat fish eggs legumes"),
    ]
    for vitamin, rel, function, sources in vitamins:
        w(f, vitamin, 'is_a', 'nutrient', 95)
        w(f, vitamin, rel, function, 95)
        for source in sources.split():
            w(f, vitamin, 'found_in', source, 85)

    # Body systems
    print("  Body systems...", flush=True)
    body_systems = {
        "circulatory system": ["heart", "blood vessels", "blood", "arteries", "veins", "capillaries"],
        "respiratory system": ["lungs", "trachea", "bronchi", "diaphragm", "alveoli"],
        "digestive system": ["stomach", "intestines", "liver", "pancreas", "esophagus", "gallbladder"],
        "nervous system": ["brain", "spinal cord", "nerves", "neurons", "synapses"],
        "skeletal system": ["bones", "joints", "cartilage", "ligaments", "tendons"],
        "muscular system": ["skeletal muscles", "smooth muscles", "cardiac muscle", "tendons"],
        "endocrine system": ["pituitary gland", "thyroid", "adrenal glands", "pancreas", "hypothalamus"],
        "immune system": ["white blood cells", "lymph nodes", "spleen", "thymus", "bone marrow"],
        "urinary system": ["kidneys", "bladder", "ureters", "urethra"],
        "reproductive system": ["ovaries", "testes", "uterus", "fallopian tubes"],
        "integumentary system": ["skin", "hair", "nails", "sweat glands"],
        "lymphatic system": ["lymph nodes", "lymph vessels", "tonsils", "spleen", "thymus"],
    }
    for system, organs in body_systems.items():
        w(f, system, 'is_a', 'body system', 95)
        for organ in organs:
            w(f, organ, 'part_of', system, 90)
            w(f, system, 'contains', organ, 90)

    # Medical specialties & what they treat
    print("  Medical specialties...", flush=True)
    specialties = {
        "cardiology": "heart diseases",
        "neurology": "nervous system disorders",
        "oncology": "cancer",
        "dermatology": "skin conditions",
        "ophthalmology": "eye diseases",
        "orthopedics": "bone and joint problems",
        "pediatrics": "children diseases",
        "psychiatry": "mental health disorders",
        "gastroenterology": "digestive system disorders",
        "endocrinology": "hormone disorders",
        "pulmonology": "lung diseases",
        "nephrology": "kidney diseases",
        "rheumatology": "autoimmune and joint diseases",
        "hematology": "blood disorders",
        "urology": "urinary system disorders",
        "otolaryngology": "ear nose and throat conditions",
        "immunology": "immune system disorders",
        "radiology": "medical imaging diagnosis",
        "anesthesiology": "pain management and anesthesia",
        "pathology": "disease diagnosis from tissue samples",
        "geriatrics": "elderly health",
        "obstetrics": "pregnancy and childbirth",
        "gynecology": "female reproductive health",
    }
    for spec, treats in specialties.items():
        w(f, spec, 'is_a', 'medical specialty', 95)
        w(f, spec, 'treats', treats, 90)


    # More crypto - DeFi protocols with details
    print("  DeFi protocols...", flush=True)
    defi_protocols = [
        ("uniswap", "decentralized exchange", "ethereum", "2018"),
        ("aave", "lending protocol", "ethereum", "2020"),
        ("compound", "lending protocol", "ethereum", "2018"),
        ("makerdao", "stablecoin protocol", "ethereum", "2017"),
        ("curve finance", "stablecoin dex", "ethereum", "2020"),
        ("pancakeswap", "decentralized exchange", "binance smart chain", "2020"),
        ("sushiswap", "decentralized exchange", "ethereum", "2020"),
        ("yearn finance", "yield aggregator", "ethereum", "2020"),
        ("synthetix", "synthetic assets", "ethereum", "2018"),
        ("balancer", "liquidity protocol", "ethereum", "2020"),
        ("1inch", "dex aggregator", "ethereum", "2020"),
        ("dydx", "derivatives exchange", "ethereum", "2017"),
        ("lido", "liquid staking", "ethereum", "2020"),
        ("rocket pool", "liquid staking", "ethereum", "2021"),
        ("convex finance", "yield optimizer", "ethereum", "2021"),
        ("frax", "algorithmic stablecoin", "ethereum", "2020"),
        ("gmx", "perpetual exchange", "arbitrum", "2021"),
        ("raydium", "amm and dex", "solana", "2021"),
        ("jupiter", "dex aggregator", "solana", "2021"),
        ("orca", "decentralized exchange", "solana", "2021"),
        ("trader joe", "decentralized exchange", "avalanche", "2021"),
        ("benqi", "lending protocol", "avalanche", "2021"),
        ("spookyswap", "decentralized exchange", "fantom", "2021"),
        ("velodrome", "decentralized exchange", "optimism", "2022"),
        ("camelot", "decentralized exchange", "arbitrum", "2022"),
    ]
    for protocol, ptype, chain, year in defi_protocols:
        w(f, protocol, 'is_a', 'defi protocol', 95)
        w(f, protocol, 'protocol_type', ptype, 90)
        w(f, protocol, 'blockchain', chain, 90)
        w(f, protocol, 'launch_year', year, 85)

    # Stablecoins
    stablecoins = [
        ("usdt", "tether", "us dollar", "2014"),
        ("usdc", "circle", "us dollar", "2018"),
        ("dai", "makerdao", "us dollar", "2017"),
        ("busd", "binance", "us dollar", "2019"),
        ("frax", "frax finance", "us dollar", "2020"),
        ("tusd", "trust token", "us dollar", "2018"),
        ("ust", "terra", "us dollar", "2020"),
    ]
    for symbol, issuer, pegged_to, year in stablecoins:
        w(f, symbol, 'is_a', 'stablecoin', 95)
        w(f, symbol, 'issued_by', issuer, 90)
        w(f, symbol, 'pegged_to', pegged_to, 95)
        w(f, symbol, 'launch_year', year, 85)

    # NFT marketplaces & collections
    nft_facts = [
        ("opensea", "is_a", "nft marketplace"),
        ("blur", "is_a", "nft marketplace"),
        ("rarible", "is_a", "nft marketplace"),
        ("foundation", "is_a", "nft marketplace"),
        ("magic eden", "is_a", "nft marketplace"),
        ("bored ape yacht club", "is_a", "nft collection"),
        ("cryptopunks", "is_a", "nft collection"),
        ("azuki", "is_a", "nft collection"),
        ("doodles", "is_a", "nft collection"),
        ("erc-721", "is_a", "nft token standard"),
        ("erc-1155", "is_a", "multi-token standard"),
        ("erc-20", "is_a", "fungible token standard"),
    ]
    for s, r, o in nft_facts:
        w(f, s, r, o, 90)

    # More trading - commodities
    print("  Commodities...", flush=True)
    commodities = [
        ("gold", "commodity", "precious metal", "xau"),
        ("silver", "commodity", "precious metal", "xag"),
        ("platinum", "commodity", "precious metal", "xpt"),
        ("palladium", "commodity", "precious metal", "xpd"),
        ("crude oil wti", "commodity", "energy", "cl"),
        ("brent crude", "commodity", "energy", "bz"),
        ("natural gas", "commodity", "energy", "ng"),
        ("copper", "commodity", "industrial metal", "hg"),
        ("aluminum", "commodity", "industrial metal", "al"),
        ("wheat", "commodity", "agricultural", "zw"),
        ("corn", "commodity", "agricultural", "zc"),
        ("soybeans", "commodity", "agricultural", "zs"),
        ("cotton", "commodity", "agricultural", "ct"),
        ("sugar", "commodity", "agricultural", "sb"),
        ("coffee", "commodity", "agricultural", "kc"),
        ("cocoa", "commodity", "agricultural", "cc"),
        ("lumber", "commodity", "agricultural", "ls"),
        ("iron ore", "commodity", "industrial metal", "io"),
        ("lithium", "commodity", "industrial metal", "li"),
        ("uranium", "commodity", "energy", "ux"),
    ]
    for name_val, category, subtype, symbol in commodities:
        w(f, name_val, 'is_a', category, 95)
        w(f, name_val, 'commodity_type', subtype, 90)
        w(f, name_val, 'trading_symbol', symbol, 85)

    # Forex pairs
    print("  Forex...", flush=True)
    forex_pairs = [
        ("eur/usd", "euro vs us dollar", "most traded"),
        ("gbp/usd", "british pound vs us dollar", "cable"),
        ("usd/jpy", "us dollar vs japanese yen", "gopher"),
        ("usd/chf", "us dollar vs swiss franc", "swissie"),
        ("aud/usd", "australian dollar vs us dollar", "aussie"),
        ("usd/cad", "us dollar vs canadian dollar", "loonie"),
        ("nzd/usd", "new zealand dollar vs us dollar", "kiwi"),
        ("eur/gbp", "euro vs british pound", "chunnel"),
        ("eur/jpy", "euro vs japanese yen", "yuppy"),
    ]
    for pair, description, nickname in forex_pairs:
        w(f, pair, 'is_a', 'forex pair', 95)
        w(f, pair, 'represents', description, 90)
        w(f, pair, 'nickname', nickname, 80)


# ═══════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════
if __name__ == '__main__':
    start = time.time()
    print("=" * 60)
    print("  MEGA KNOWLEDGE EXPANSION")
    print("  Target: 1M+ unique subjects, maximize facts")
    print("=" * 60, flush=True)

    with open(OUTPUT, 'w') as f:
        # Priority domains
        health_medical(f)
        crypto_blockchain(f)
        trading_finance(f)

        # Massive programmatic
        massive_programmatic(f)

        # Max out DBpedia
        max_dbpedia(f)

        # Re-parse ConceptNet aggressively
        conceptnet_aggressive(f)

    elapsed = time.time() - start
    print(f"\n{'=' * 60}")
    print(f"  MEGA EXPANSION COMPLETE!")
    print(f"  Facts added: {facts_added:,}")
    print(f"  DBpedia queries: {queries_done}")
    print(f"  Time: {elapsed/60:.1f} min")
    print(f"  File: {OUTPUT}")
    print(f"  Size: {os.path.getsize(OUTPUT)/1e6:.1f} MB")
    print(f"{'=' * 60}", flush=True)

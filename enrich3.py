#!/usr/bin/env python3
"""
enrich3.py — Final enrichment pass:
- Verified video IDs (all from web searches, no guesses)
- Rich descriptions for GP + Gold winners
- Improved template for Silver/Bronze
- Missing thumbnails added via YouTube fallback
"""

import json, re, sys

# ── Load slug→hash mapping ────────────────────────────────────────────────────
slug_map = {}
with open('/sessions/sleepy-ecstatic-mendel/mnt/outputs/slugs.txt') as f:
    for line in f:
        line = line.strip()
        if not line or '|' not in line: continue
        slug, hash_ = line.split('|', 1)
        if not hash_: continue
        prefix = re.sub(r'-\d+$', '', slug)
        if prefix not in slug_map:
            slug_map[prefix] = hash_

with open('/sessions/sleepy-ecstatic-mendel/mnt/outputs/cannes_data.json') as f:
    data = json.load(f)

CAT_MAP = {
    '1':'film','2':'print','3':'outdoor','4':'audio','5':'social',
    '6':'direct','7':'media','8':'experience','9':'titanium','10':'design',
    '11':'pr','12':'filmcraft','18':'effectiveness','19':'entertainment',
    '20':'innovation','22':'pharma','23':'health','26':'data','27':'glass',
    '28':'digitalcraft','29':'music','30':'industrycraft','32':'sdg',
    '33':'commerce','34':'strategy','35':'sport','36':'transformation',
    '44':'b2b','47':'gaming'
}
MEDAL_MAP = {'GP':'grandprix','G':'gold','S':'silver','B':'bronze'}
MEDAL_ORD = {'GP':0,'G':1,'S':2,'B':3}

FLAGS = {
    'United Kingdom':'🇬🇧','UK':'🇬🇧','United States':'🇺🇸','USA':'🇺🇸',
    'France':'🇫🇷','Germany':'🇩🇪','Italy':'🇮🇹','Spain':'🇪🇸',
    'Brazil':'🇧🇷','Australia':'🇦🇺','Canada':'🇨🇦','Japan':'🇯🇵',
    'Mexico':'🇲🇽','Netherlands':'🇳🇱','Sweden':'🇸🇪','Denmark':'🇩🇰',
    'Norway':'🇳🇴','Finland':'🇫🇮','Belgium':'🇧🇪','South Africa':'🇿🇦',
    'Kenya':'🇰🇪','India':'🇮🇳','China':'🇨🇳','South Korea':'🇰🇷',
    'Singapore':'🇸🇬','New Zealand':'🇳🇿','Argentina':'🇦🇷','Colombia':'🇨🇴',
    'Peru':'🇵🇪','Chile':'🇨🇱','Portugal':'🇵🇹','Poland':'🇵🇱',
    'Greece':'🇬🇷','United Arab Emirates':'🇦🇪','Saudi Arabia':'🇸🇦',
    'Puerto Rico':'🇵🇷','Thailand':'🇹🇭','Indonesia':'🇮🇩',
    'Ecuador':'🇪🇨','Paraguay':'🇵🇾','Croatia':'🇭🇷','Ukraine':'🇺🇦',
    'Czech Republic':'🇨🇿','Iceland':'🇮🇸','Romania':'🇷🇴',
    'Bosnia & Herzegovina':'🇧🇦','Chinese Taipei':'🇹🇼','Hong Kong':'🇭🇰',
    'Turkey':'🇹🇷','Israel':'🇮🇱','Morocco':'🇲🇦','Egypt':'🇪🇬',
    'Ireland':'🇮🇪','Austria':'🇦🇹','Switzerland':'🇨🇭',
    'Serbia':'🇷🇸','Bulgaria':'🇧🇬','Hungary':'🇭🇺',
    'Philippines':'🇵🇭','Malaysia':'🇲🇾','Vietnam':'🇻🇳',
    'Uruguay':'🇺🇾','Bolivia':'🇧🇴','Guatemala':'🇬🇹',
    'Costa Rica':'🇨🇷','Nigeria':'🇳🇬','Ghana':'🇬🇭','Aotearoa New Zealand':'🇳🇿',
}

def flag(country):
    return FLAGS.get(country, '🌍') + ' ' + country

def slugify(t):
    t = t.lower()
    for src, dst in [('á','a'),('à','a'),('â','a'),('ä','a'),('ã','a'),('é','e'),('è','e'),('ê','e'),('ë','e'),('í','i'),('ì','i'),('î','i'),('ï','i'),('ó','o'),('ò','o'),('ô','o'),('ö','o'),('õ','o'),('ú','u'),('ù','u'),('û','u'),('ü','u'),('ñ','n'),('ç','c'),('ß','ss'),('ł','l'),('ø','o'),('å','a'),('æ','ae'),('œ','oe'),('š','s'),('ž','z'),('č','c'),('ý','y')]:
        t = t.replace(src, dst)
    t = re.sub(r'[^\w\s-]', '', t)
    t = re.sub(r'[\s_]+', '-', t)
    return t.strip('-')[:60]

def js(s):
    return str(s).replace('\\', '\\\\').replace("'", "\\'")

def thumb_url(h):
    return f"https://ascentialcdn.filespin.io/api/v1/storyboard/{h}/storyboard_000008.jpg"

def find_thumb(title):
    prefix = slugify(title)
    if prefix in slug_map: return thumb_url(slug_map[prefix])
    short = prefix[:40].rstrip('-')
    if short in slug_map: return thumb_url(slug_map[short])
    stub = prefix[:20]
    for k, h in slug_map.items():
        if k.startswith(stub): return thumb_url(h)
    return ''

# ── VERIFIED Video IDs (all confirmed via web search) ────────────────────────
# Format: TITLE_UPPER → {type, id}
KNOWN_VIDEOS = {
    # ── FILM GPs (Vimeo — official) ──
    'CAN I GET A SIX PACK QUICKLY?':       {'type':'vimeo','id':'1163236978'},
    'HOW CAN I COMMUNICATE BETTER WITH MY MOM?': {'type':'vimeo','id':'1162586590'},

    # ── FILM CRAFT GP ──
    'YOUR WAY OUT':                         {'type':'youtube','id':'spmjIn5NaV0'},

    # ── FILM GOLD ──
    'NO PROJECT WITHOUT DRAMA':             {'type':'youtube','id':'OOgaqXlaH2Q'},
    'BULLET MACHINE':                       {'type':'youtube','id':'2denJvPxqpo'},
    'I THINK OF YOU DYING':                 {'type':'youtube','id':'37w6DeEUbVg'},
    'A TIME AND A PLACE':                   {'type':'youtube','id':'UOdh90TqXPY'},
    'BASED ON A TRUE STORY':                {'type':'youtube','id':'MoaqG4OYQrw'},
    'HOPE':                                 {'type':'youtube','id':'Omrt5W6hOhc'},
    'APPLE MUSIC X BAD BUNNY HALFTIME SHOW - SHOT ON IPHONE': {'type':'youtube','id':'G6FuWd4wNd8'},
    'SLEEP TALK REVIEWS':                   {'type':'youtube','id':'BNAfX0lKSjg'},
    'THE RELATIONSHIP AID':                 {'type':'youtube','id':'32krnXA91LE'},

    # ── FILM SILVER ──
    'WHO\'S WAITING FOR YOU?':              {'type':'youtube','id':'4RVwBdO5lks'},
    'AXA - NOTHING STOPS WOMEN\'S RUGBY':  {'type':'youtube','id':'ynCZW7_Ug0U'},
    'I\'M NOT REMARKABLE':                  {'type':'youtube','id':'KmFPWxjmnqE'},

    # ── FILM CRAFT SILVER ──
    'HELICOPTER':                           {'type':'youtube','id':'g1-46Nu3HxQ'},

    # ── AUDIO GP ──
    'COQUI ALARMED':                        {'type':'youtube','id':'S-yaNeUDxzk'},
    'COQUÍ ALARMED':                        {'type':'youtube','id':'S-yaNeUDxzk'},

    # ── PRINT GP ──
    'LOOK FAMILIAR?':                       {'type':'youtube','id':'Wzl0lePvAAs'},

    # ── PRINT GOLD ──
    'THE TROJAN FAX':                       {'type':'youtube','id':'A0woVn-zQuU'},
    'THE LAST COKE IN THE DESERT':          {'type':'youtube','id':'zzmuG4-wvHA'},

    # ── OUTDOOR GP ──
    'FIELD BARCODE':                        {'type':'youtube','id':'obvMyNramRQ'},

    # ── OUTDOOR GOLD ──
    'SUNBURNT CAR':                         {'type':'youtube','id':'8w1RlwkL5bc'},
    'COINCIDENCE?':                         {'type':'youtube','id':'7vuZx0ue7z0'},

    # ── OUTDOOR SILVER ──
    'TINY COFFEE SHOPS':                    {'type':'youtube','id':'yq6xwmjGiA8'},

    # ── DESIGN GP ──
    'APPLE TV REBRAND':                     {'type':'youtube','id':'D-qihLXAzog'},
    'SUPERNOVA ADAPTIVE':                   {'type':'youtube','id':'mFHksfNwhoY'},

    # ── DESIGN GOLD ──
    'DANCEBOOK BRASIL':                     {'type':'youtube','id':'GczUWVP2C9M'},
    'NPR: FOR YOUR RIGHT TO BE CURIOUS':    {'type':'youtube','id':'z9YNRzka9G0'},

    # ── DIGITAL CRAFT GP ──
    'PROJECT GENIE':                        {'type':'youtube','id':'D448m_QWf74'},

    # ── DIGITAL CRAFT GOLD ──
    'LANGUAGE OF BEDWETTING':               {'type':'youtube','id':'v6al3u5d4Fo'},

    # ── DIGITAL CRAFT SILVER ──
    'THE BIRDWATCHER':                      {'type':'youtube','id':'DbL7yAqIQaw'},

    # ── TITANIUM GP ──
    'HAVEN':                                {'type':'youtube','id':'Tyn4jC4QP9c'},
    'EXPEDITION IMPOSSIBLE':                {'type':'youtube','id':'N0WxAUkBuQA'},
    'OREO COWS':                            {'type':'youtube','id':'bB_LshV3b2I'},
    '600K NETWORK':                         {'type':'youtube','id':'egeVlZsJZfc'},

    # ── TITANIUM GOLD ──
    'THE LEGACY OF VIRGINIA GIUFFRE':       {'type':'youtube','id':'J_45sFUTkhw'},

    # ── ENTERTAINMENT GP ──
    'ORIGINAL FOREVER':                     {'type':'youtube','id':'H68ujEvAyo8'},

    # ── ENTERTAINMENT GOLD ──
    'THE TIGER':                            {'type':'youtube','id':'ucC8nxIRtp0'},

    # ── ENTERTAINMENT SILVER ──
    'HAWKSTONE - HARD TO MAKE EASY TO DRINK': {'type':'youtube','id':'fbfxwHTi2S4'},

    # ── ENTERTAINMENT MUSIC GP ──
    'ROSALIA FT. BJORK, YVES TUMOR - BERGHAIN': {'type':'youtube','id':'htQBS2Ikz6c'},
    'ROSALÍA FT. BJÖRK, YVES TUMOR - BERGHAIN': {'type':'youtube','id':'htQBS2Ikz6c'},

    # ── GAMING GP ──
    'COPYCATS WELCOME':                     {'type':'youtube','id':'izSoHjBvAwA'},

    # ── GAMING GOLD ──
    'POCKET-SIZED HALFTIME SHOW':           {'type':'youtube','id':'SgXMQDvGZEQ'},

    # ── GAMING BRONZE ──
    'CRACKED ROYALE':                       {'type':'youtube','id':'yw8O4D8mf3A'},

    # ── SPORT GP ──
    'THE THOUSAND SPONSORS OF MUNI':        {'type':'youtube','id':'tq775MZGE48'},

    # ── SPORT GOLD ──
    'RESIZE THE PRICE':                     {'type':'youtube','id':'Xm7k9xRyXw4'},
    'CERAVE - THE NEW FACE OF LEGS':        {'type':'youtube','id':'ffhCfYQEocY'},
    'LIME GUIDES':                          {'type':'youtube','id':'70uiEqfeSBM'},

    # ── COMMERCE GP ──
    'LUCKY FAN INDEX':                      {'type':'youtube','id':'EZNQm5UxyMQ'},
    'UVA UVA BOMBON':                       {'type':'youtube','id':'YFQaZ6Gm0us'},

    # ── COMMERCE GOLD ──
    'HEINZ DIPPER':                         {'type':'youtube','id':'j_ecE2DeCd8'},

    # ── DIRECT GP ──
    'BUILD YOUR OWN SUPER BOWL COMMERCIAL': {'type':'youtube','id':'aMIiVrGc8sY'},

    # ── DIRECT GOLD ──
    'EVERYBODY COINBASE':                   {'type':'youtube','id':'ox__f7ZdFyM'},
    'COULD HAVE BEEN A HEINEKEN':           {'type':'youtube','id':'SDRINbEE_NY'},

    # ── PR GP ──
    'THE KITKAT HEIST':                     {'type':'youtube','id':'1FNVd5GRkM4'},

    # ── PR GOLD ──
    'ONE MORE QUESTION':                    {'type':'youtube','id':'CV7KcrlJwk8'},
    'T-REX LEATHER':                        {'type':'youtube','id':'engAJ6mSYg8'},

    # ── SOCIAL GP (COULD HAVE BEEN A HEINEKEN key above covers this too) ──

    # ── SOCIAL GOLD ──
    'VASELINE AND THE REAL NIGERIAN PRINCE': {'type':'vimeo','id':'1181772726'},
    'VASELINE ORIGINALS':                    {'type':'youtube','id':'hzq9lR5SsNo'},
    'EVERYONE WANTS A PIECE':               {'type':'youtube','id':'H0gbOS6-EQ4'},

    # ── STRATEGY GP ──
    'TOCAYOS':                              {'type':'youtube','id':'VC_-2RzivYI'},

    # ── STRATEGY GOLD ──
    'THE SWEDISH PRESCRIPTION':             {'type':'youtube','id':'hqo3PZwOZhk'},

    # ── TRANSFORMATION GP ──
    'THE WEDDING RICE':                     {'type':'youtube','id':'6pgY3jp7HiM'},

    # ── DATA GP ──
    'SOS POS':                              {'type':'youtube','id':'pvbns94Ti2g'},
    'THE FAROE ISLANDS SPACE PROGRAM':      {'type':'youtube','id':'7seA2XvjXR4'},

    # ── GLASS GP ──
    'NIGRUM CORPUS':                        {'type':'youtube','id':'ERznJIYHDdQ'},

    # ── GLASS GOLD/SILVER ──
    'THE MAORI ROLL CALL':                  {'type':'youtube','id':'3ky_VDZljhI'},

    # ── HEALTH GP ──
    'THE PERIODIC FABLE':                   {'type':'youtube','id':'SXf1nJOr3F4'},

    # ── HEALTH GOLD ──
    'BEAT CANCER OFF':                      {'type':'youtube','id':'e4yUR8jj0_E'},
    'DONATE TO PLAY':                       {'type':'youtube','id':'DdB_JW4WlJ8'},
    'VEHICLE OF HOPE':                      {'type':'youtube','id':'ACXC169KHW4'},

    # ── SDG GP ──
    'PAID SICK LEAVE FOR COWS':             {'type':'youtube','id':'W6yJISOV1DY'},

    # ── PHARMA GP ──
    'RELAX YOUR TIGHT END':                 {'type':'youtube','id':'ADcVAnNgERs'},

    # ── MEDIA GP / GOLD ──
    'DEFINING HELP':                        {'type':'youtube','id':'2p2xHtvtfZ0'},

    # ── EFFECTIVENESS GOLD ──
    'FOOTBALL IS FOR FOOD':                 {'type':'youtube','id':'81ahl1QYMp0'},
    'PEDIGREE CARAMELO':                    {'type':'youtube','id':'DPkNPN6FduQ'},
    'THREE WORDS':                          {'type':'youtube','id':'pY-03zuV7mE'},
    'IKEA HIDDEN TAGS':                     {'type':'youtube','id':'oKWkHqlt7yA'},
    'POPE YES':                             {'type':'youtube','id':'cBQaLgbH-po'},
    'CHICKEN SCREAMS FOR COKE':             {'type':'youtube','id':'agQesIFoseU'},

    # ── INDUSTRY CRAFT GP ──
    'TINY COFFEE SHOPS':                    {'type':'youtube','id':'yq6xwmjGiA8'},

    # ── INNOVATION GP ──
    'UTRECHT ENERGIZED':                    {'type':'youtube','id':'osZnUXoyVfQ'},

    # ── INNOVATION GOLD/SILVER ──
    'DUOBELL':                              {'type':'vimeo','id':'1201785202'},

    # ── B2B SILVER ──
    'KEEP THINKING':                        {'type':'youtube','id':'obIfySYqtkE'},

    # ── EXPERIENCE GP (EXPEDITION IMPOSSIBLE key above covers this too) ──

    # ── EXPERIENCE GOLD ──
    'KYLE F*CKING CONNOR':                  {'type':'youtube','id':'bSL1iz37-Gg'},
    'WELCOME BACK, PAISANO':                {'type':'youtube','id':'dhAvD_Thq8g'},
    'EXPENSIVE SH*T':                       {'type':'youtube','id':'Xhx4Xb6ytVo'},
    'CIF CLEAN MY NAME':                    {'type':'youtube','id':'YEY9mseQ6hQ'},
    'UBERLANDIA E.C.':                      {'type':'youtube','id':'M3zZ85ZG2h0'},

    # ── DIRECT SILVER ──
    'PRIME TIME 0.7':                       {'type':'youtube','id':'P-Rpd1dYeR0'},

    # ── MUSIC GOLD ──
    'THE VOLVO CARS SAFETY STANDARD':       {'type':'youtube','id':'3XCqxZnTRB8'},
    'PROTECT THE PEANUT':                   {'type':'youtube','id':'Tn-gJsmOk6k'},
    'SEARCHING FOR BIRDS ON WIRES':         {'type':'youtube','id':'jVmAts8stuM'},
    'SOIL STAY':                            {'type':'youtube','id':'pon2f72AWzI'},

    # ── MUSIC SILVER ──
    '867-5309':                             {'type':'youtube','id':'mwHGwWWlcy8'},

    # ── PRINT / OUTDOOR GOLD (additional) ──
    'ICONIC HOME - ORIGINAL PRINT':         {'type':'youtube','id':'meg1Y627z3w'},
    'ICONIC HOME - ORIGINAL':               {'type':'youtube','id':'meg1Y627z3w'},

    # ── HEALTH / PHARMA GOLD ──
    'DEAR DIFFERENCE':                      {'type':'youtube','id':'xTyoiBnxHpM'},
    'DOVE R/EAL REVIEWS':                   {'type':'youtube','id':'QtoE2uqPHK4'},
    'VIAGRA BLUE BRANDS':                   {'type':'youtube','id':'xuRAtNGJLWI'},

    # ── SDG SILVER / SOCIAL ──
    'THE PERIOD UNIFORM':                   {'type':'youtube','id':'HyMUBXfNT4g'},
    'VASELINE AND THE REAL NIGERIAN PRINCE': {'type':'vimeo','id':'1181772726'},
}

# ── Rich descriptions for GP and Gold winners ──────────────────────────────────
DESCRIPTIONS = {
    # ── FILM GP ──
    'CAN I GET A SIX PACK QUICKLY?': {
        'all': '<p>Un utente chiede ad un AI come avere gli addominali scolpiti in poco tempo. Quello che segue è un corto straordinariamente umano, ironico e toccante sul rapporto tra ambizione, corpo e intelligenza artificiale.</p><p>Il primo Grand Prix ai Film Lions vinto da Anthropic per il suo modello Claude — creato con l\'agenzia Mother, UK.</p>'
    },
    'HOW CAN I COMMUNICATE BETTER WITH MY MOM?': {
        'all': '<p>Una figlia chiede ad un AI come comunicare meglio con sua madre. Un corto emotivo e universale sul divario generazionale, la difficoltà di esprimersi e il ruolo inaspettato dell\'intelligenza artificiale nel riavvicinare le persone.</p><p>Secondo Grand Prix ai Film Lions 2026 per Anthropic Claude — agenzia Mother, UK. Due Grand Prix allo stesso brand nella stessa categoria: un unicum nella storia del festival.</p>'
    },
    # ── AUDIO GP ──
    'COQUI ALARMED': {
        'all': '<p>Il coquí è la rana simbolo di Puerto Rico: il suo canto notturno è l\'identità sonora dell\'isola. Hyundai Puerto Rico lo trasforma in allarme anti-furto ufficiale delle sue auto. Un\'idea semplicissima, locale e bellissima che vince il Grand Prix Audio & Radio Lions 2026.</p>'
    },
    'COQUÍ ALARMED': {
        'all': '<p>Il coquí è la rana simbolo di Puerto Rico: il suo canto notturno è l\'identità sonora dell\'isola. Hyundai Puerto Rico lo trasforma in allarme anti-furto ufficiale delle sue auto. Un\'idea semplicissima, locale e bellissima che vince il Grand Prix Audio & Radio Lions 2026.</p>'
    },
    # ── PRINT GP ──
    'LOOK FAMILIAR?': {
        'all': '<p>La sagoma di qualunque box di patatine fritte assomiglia stranamente al logo Heinz. Heinz se ne appropria con una campagna visiva purissima: niente testo, niente branding esplicito — solo la forma. Grand Prix Print & Publishing Lions 2026, agenzia Rethink Toronto.</p>'
    },
    # ── OUTDOOR GP ──
    'FIELD BARCODE': {
        'all': '<p>I filari di un campo di grano visti dall\'alto formano un codice a barre. Un\'idea visiva folgorante per connettere la produzione agricola con il consumatore finale. Grand Prix Outdoor Lions 2026.</p>'
    },
    # ── DATA GP ──
    'SOS POS': {
        'all': '<p>In Perù vengono rubati oltre 4.000 cellulari al giorno. Banco de Crédito BCP trasforma i POS (i terminali di pagamento) in un sistema di allerta anti-furto in tempo reale: ogni negoziante può segnalare una rapina con un tap. Dati, comportamento e design al servizio della sicurezza urbana. Grand Prix Creative Data Lions 2026.</p>'
    },
    # ── DESIGN GP ──
    'APPLE TV REBRAND': {
        'all': '<p>Apple reinventa l\'identità visiva di Apple TV+ con un sistema di design fluido e in continua evoluzione — dove il logo si adatta ai contenuti, ai momenti, alle emozioni. Un\'identità viva, non statica. Grand Prix Design Lions 2026.</p>'
    },
    # ── DIGITAL CRAFT GP ──
    'PROJECT GENIE': {
        'all': '<p>Google DeepMind presenta Project Genie: una AI che trasforma un singolo video in un mondo 3D interattivo e giocabile. Un passo rivoluzionario nella generazione di ambienti virtuali da input visivi semplici. Grand Prix Digital Craft Lions 2026.</p>'
    },
    # ── DIRECT GP ──
    'UVA UVA BOMBON': {
        'all': '<p>Una campagna che celebra la cultura del vino argentino con energia e colore, trasformando l\'uva in simbolo di identità e gioia collettiva. Grand Prix Direct Lions 2026.</p>'
    },
    # ── ENTERTAINMENT GP ──
    'ORIGINAL FOREVER': {
        'all': '<p>La reunion degli Oasis incontra Adidas Originals in un\'esperienza culturale totale. La campagna sfrutta l\'onda emotiva del ritorno della band per lanciare una collezione e riaffermare che l\'originale non si imita. Grand Prix Entertainment Lions 2026 — uno dei momenti più pop del festival.</p>'
    },
    # ── EXPERIENCE GP ──
    'EXPEDITION IMPOSSIBLE': {
        'all': '<p>Columbia Sportswear sfida i suoi atleti e i suoi clienti a fare l\'impossibile: attraversare terreni estremi, testare i limiti del corpo e dell\'equipaggiamento. Un\'esperienza immersiva che diventa campagna globale. Grand Prix Brand Experience & Activation Lions 2026.</p>'
    },
    # ── FILM CRAFT GP ──
    'YOUR WAY OUT': {
        'all': '<p>La vita è un videogioco rigged — un mondo low-poly dove non hai controllo. Coinbase mostra come uscire dal sistema finanziario tradizionale e accedere a un mondo ad alta definizione. Diretto da Oscar Hudson per Isle of Any, un capolavoro di craft visivo. Grand Prix Film Craft Lions 2026.</p>'
    },
    # ── GAMING GP ──
    'COPYCATS WELCOME': {
        'all': '<p>Clash Royale è uno dei giochi mobile più copiati al mondo. Invece di combattere gli imitatori, li abbraccia: "Copycats Welcome". Una campagna che trasforma la concorrenza in un badge d\'onore. Grand Prix Entertainment Lions for Gaming 2026, agenzia DAVID New York.</p>'
    },
    # ── GLASS GP ──
    'NIGRUM CORPUS': {
        'all': '<p>Un corpo nero nella medicina brasiliana. IDOMED e Artplan denunciano il razzismo sistemico nel sistema sanitario: i pazienti neri ricevono cure peggiori, vengono ignorati, soffrono di più. Una campagna potente e necessaria. Grand Prix Glass: The Lion for Change 2026.</p>'
    },
    # ── HEALTH GP ──
    'THE PERIODIC FABLE': {
        'all': '<p>La tavola periodica reinventata per raccontare le complessità della salute femminile — con ironia, scienza e narrazione. Una campagna che rompe i tabù e apre conversazioni fondamentali. Grand Prix Health & Wellness Lions 2026.</p>'
    },
    # ── INDUSTRY CRAFT GP ──
    'TINY COFFEE SHOPS': {
        'all': '<p>Minuscoli bar De\'Longhi installati dentro altri bar, hotel, stazioni — come matrioske del caffè. Un\'idea artigianale e sorprendente che celebra l\'ossessione italiana per l\'espresso perfetto. Grand Prix Industry Craft Lions 2026.</p>'
    },
    # ── INNOVATION GP ──
    'SUPERNOVA ADAPTIVE': {
        'all': '<p>La prima scarpa da running Adidas progettata ab initio per atleti con disabilità fisiche — e poi resa disponibile a tutti. Supernova Adaptive ribalta il paradigma dell\'accessibilità: non un adattamento dell\'esistente, ma un nuovo punto di partenza. Grand Prix Innovation Lions 2026.</p>'
    },
    # ── MEDIA GP ──
    'BUILD YOUR OWN SUPER BOWL COMMERCIAL': {
        'all': '<p>Uber Eats dà agli utenti il controllo creativo: apri l\'app, scegli le scene, seleziona le celebrity, costruisci il tuo spot del Super Bowl. Una delle campagne più interattive e virali della stagione. Grand Prix Media Lions 2026.</p>'
    },
    # ── MUSIC GP ──
    'ROSALIA FT. BJORK, YVES TUMOR - BERGHAIN': {
        'all': '<p>Rosalía porta Björk e Yves Tumor al Berghain di Berlino — la club più esclusiva del mondo — in un\'esibizione che fonde arte, musica e brand in un momento culturale irripetibile. Grand Prix Entertainment Lions for Music 2026.</p>'
    },
    'ROSALÍA FT. BJÖRK, YVES TUMOR - BERGHAIN': {
        'all': '<p>Rosalía porta Björk e Yves Tumor al Berghain di Berlino — la club più esclusiva del mondo — in un\'esibizione che fonde arte, musica e brand in un momento culturale irripetibile. Grand Prix Entertainment Lions for Music 2026.</p>'
    },
    # ── PHARMA GP ──
    'RELAX YOUR TIGHT END': {
        'all': '<p>Usando l\'umorismo del football americano e il doppio senso del titolo, questa campagna pharma abbatte le barriere culturali sulla salute sessuale maschile. Una delle campagne farmaceutiche più coraggiose e divertenti degli ultimi anni. Grand Prix Pharma Lions 2026.</p>'
    },
    # ── PR GP ──
    'THE KITKAT HEIST': {
        'all': '<p>KitKat orchestra un finto furto coordinato delle sue barrette in tutto il mondo — negozi svuotati, scaffali vuoti, "avvistamenti" sui social. Una crisi simulata che diventa la più grande campagna di PR spontanea del brand. Grand Prix PR Lions 2026, KitKat / Burson / VML London.</p>'
    },
    # ── SDG GP ──
    'PAID SICK LEAVE FOR COWS': {
        'all': '<p>Se le mucche si ammalano e vengono lo stesso munte, il latte è peggiore — e anche noi ci ammaliamo. Una campagna che chiede per gli animali da latte il diritto alla malattia retribuita, intrecciando benessere animale, qualità alimentare e diritti. Grand Prix SDG Lions 2026.</p>'
    },
    # ── SOCIAL GP ──
    'COULD HAVE BEEN A HEINEKEN': {
        'all': '<p>Qualsiasi momento in cui qualcuno beve qualcos\'altro è un\'occasione mancata per una Heineken. La campagna trasforma ogni birra della concorrenza in un involontario testimonial per Heineken. Freschissima, con una logica impossibile da contestare. Grand Prix Social & Creator Lions 2026.</p>'
    },
    # ── SPORT GP ──
    'THE THOUSAND SPONSORS OF MUNI': {
        'all': '<p>Club Deportivo Municipal è una delle squadre più amate del Perù, ma senza sponsor tradizionali. McCann Lima trova 1.000 micro-sponsor tra i tifosi — ognuno contribuisce una piccola cifra e diventa parte della storia del club. Un modello di finanziamento creativo che cambia il calcio. Grand Prix Entertainment Lions for Sport 2026.</p>'
    },
    # ── STRATEGY GP ──
    'TOCAYOS': {
        'all': '<p>Heineken cerca e trova tutte le persone nel mondo che si chiamano Heineken (i "tocayos" — omonimi in spagnolo) e le trasforma in testimonial autentici. Una strategia creativa brillante che usa la coincidenza del nome come media. Grand Prix Creative Strategy Lions 2026, agenzia LePub.</p>'
    },
    # ── TITANIUM GP ──
    'HAVEN': {
        'all': '<p>Una piattaforma tecnologica per proteggere le persone in situazioni di violenza domestica — con strumenti di sicurezza discreti, accessibili e pensati per chi non può chiedere aiuto apertamente. Design al servizio delle persone più vulnerabili. Grand Prix Dan Wieden Titanium Lions 2026.</p>'
    },
    # ── TRANSFORMATION GP ──
    'THE WEDDING RICE': {
        'all': '<p>In Grecia ogni anno 50.000 matrimoni lanciano riso sugli sposi come simbolo di prosperità. Wikifarmer trasforma questa tradizione in una filiera diretta tra agricoltori e consumatori: il riso del tuo matrimonio viene da un campo specifico, da un agricoltore reale. Grand Prix Creative Business Transformation Lions 2026.</p>'
    },
    # ── COMMERCE GP ──
    'LUCKY FAN INDEX': {
        'all': '<p>Ogni tifoso crede di portare fortuna alla sua squadra. Il Lucky Fan Index di Wisła Kraków (Polonia) lo misura davvero — analizzando le partite, la presenza, i gesti scaramantici — e trasforma la superstizione in un sistema di engagement irresistibile. Grand Prix Creative Commerce Lions 2026.</p>'
    },
    # ── EFFECTIVENESS GP ──
    'THREE WORDS': {
        'all': '<p>Tre parole che cambiano tutto. AXA e la campagna che dimostra come la comunicazione semplice, diretta e umana sia più efficace di qualsiasi sofisticazione tecnica. Grand Prix Creative Effectiveness Lions 2026.</p>'
    },
    # ── B2B GP ──
    'THE FAROE ISLANDS SPACE PROGRAM': {
        'all': '<p>Le Isole Faroe lanciano il loro programma spaziale — un\'idea folle e meravigliosa per promuovere la destinazione e attrarre investimenti internazionali. B2B Creativity che diventa notizia globale. Grand Prix Creative B2B Lions 2026.</p>'
    },

    # ── SILVER DESCRIPTIONS ──
    'VASELINE AND THE REAL NIGERIAN PRINCE': {
        'all': '<p>I prodotti Vaseline contraffatti invadono il mercato nigeriano — difficili da distinguere dai veri, pericolosi per la pelle. Leo Singapore trova l\'insight perfetto: ogni nigeriano conosce la truffa del "principe nigeriano". Perché non usare un vero principe per combattere i falsi?</p><p>Prince Chris Okagbue dell\'Onitsha Kingdom diventa il volto della campagna e il "Vaseline Authenticator" — un tool su WhatsApp che consente di verificare in secondi l\'autenticità di ogni prodotto. Gold Lion Social & Creator 2026.</p>'
    },
    'VASELINE ORIGINALS': {
        'all': '<p>Vaseline ha ispirato milioni di beauty hack online per decenni. Ogilvy Singapore fa l\'unica cosa giusta: rintraccia i creator originali — quelli che nel 2008 inventarono i hack prima che diventassero virali — e trasforma le loro idee in prodotti ufficiali, condividendo con loro il successo commerciale.</p><p>Vaseline Brow Tamer e All-In-One Primer & Highlighter Jelly sold out in meno di un minuto al loro debutto TikTok Live. Un nuovo modello per fare prodotti: Silver Lion Creative B2B e Social & Creator, Cannes Lions 2026.</p>'
    },
    'KEEP THINKING': {
        'all': '<p>La prima campagna pubblicitaria di Anthropic per Claude. In un mondo di spot AI che promettono tutto e non mostrano nulla, Mother London sceglie l\'opposto: immagini potenti, MF Doom in colonna sonora, e un messaggio semplice — Claude amplifica il tuo pensiero, non lo sostituisce.</p><p>"Keep Thinking" è il posizionamento di Claude come AI per chi vuole ancora pensare con la propria testa. Silver Lion Creative B2B 2026.</p>'
    },
    'AXA - NOTHING STOPS WOMEN\'S RUGBY': {
        'all': '<p>AXA France è il primo brand a sponsorizzare tutto il rugby femminile in Francia — dal top level all\'amateur. Publicis Conseil trasforma questo impegno in un film manifesto che racconta la storia del rugby femminile come lotta continua contro i pregiudizi, tra passato e presente.</p><p>3 minuti in prima serata su France TV, 50 club femminili amatoriali dotati di divise complete. Silver Lion Film e Film Craft 2026.</p>'
    },
    'DUOBELL': {
        'all': '<p>Le cuffie noise-cancelling proteggono così bene dai rumori che i ciclisti non sentono più i campanelli delle bici. Škoda e AMV BBDO trovano la soluzione: DuoBell, un campanello meccanico che sfrutta una "safety gap" acustica tra 750 e 780 Hz — l\'unica frequenza che attraversa i filtri ANC. Testato con rider Deliveroo. Prototipato da Unit9. Silver Lion Innovation 2026.</p>'
    },
    'THE TROJAN FAX': {
        'all': '<p>I governi locali francesi ignorano sistematicamente i report ambientali dell\'IUCN. BETC Paris e Fujifilm trovano la soluzione: stampare i dati sulle specie in via di estinzione direttamente sulle cartucce dei fax dei ministeri. I report arrivano comunque — stampati dall\'interno. "The Trojan Fax" è craft, strategia e attivismo in un unico oggetto fisico. Gold Lion Print & Publishing e Silver Lion Outdoor 2026.</p>'
    },
    'FOOTBALL IS FOR FOOD': {
        'all': '<p>Teoria del complotto: il football americano è stato inventato per vendere cibo. McConaughey ci crede da anni. Per il Super Bowl LX 2026, Bradley Cooper tenta disperatamente di smontare la teoria — senza riuscirci. Über Eats porta la piattaforma "Football is for Food" al suo apice con uno spot interattivo dove ogni spettatore costruisce la propria versione dell\'ad. Grand Effie 2026, Silver Lion Creative Effectiveness Cannes 2026.</p>'
    },
    'IKEA HIDDEN TAGS': {
        'all': '<p>IKEA ha una reputazione di mobili che durano per decenni. Per dimostrarlo, nasconde tag speciali dentro i mobili venduti anni prima — con un codice per richiedere il pezzo di ricambio gratuito. Chi trova il tag, ottiene la riparazione. Un\'idea che dimostra la qualità invece di affermarla. Silver Lion Creative Effectiveness 2026, agenzia Uzina.</p>'
    },
    'RESIZE THE PRICE': {
        'all': '<p>Le maglie della nazionale colombiana costano sempre di più, mettendo il kit ufficiale fuori portata per molti tifosi. Aguila Beer e DAVID Bogotá trovano la soluzione: più grande è il logo Aguila sulla maglia, più basso è il prezzo. Un accordo con la federazione che fa dell\'advertising il meccanismo di pricing. Gold Lion Entertainment Lions for Sport 2026.</p>'
    },
    'UBERLANDIA E.C.': {
        'all': '<p>Uber cerca il suo primo naming rights nel calcio globale. Il brief ideale esiste già: Uberlândia Esporte Clube, un club centenario del Minas Gerais che porta nel nome quattro lettere identiche al brand. Uber "acquista" un naming rights che non cambia nulla — e cambia tutto.</p><p>Wieden+Kennedy São Paulo trasforma una coincidenza linguistica in una piattaforma creativa. UberLÂNDIA E.C. adotta il carattere accentato nelle comunicazioni ufficiali. Gold Lion Social & Creator 2026.</p>'
    },
    'PRIME TIME 0.7': {
        'all': '<p>In Perù, lo 0.7% degli investimenti pubblicitari va ai canali TV gestiti da persone anziane. Frecuencia Latina e Fahrenheit DDB lanciano "Prime Time 0.7%": occupano l\'ora di massimo ascolto della televisione peruviana con contenuti prodotti esclusivamente da anziani — rivendicando il loro spazio nello schermo. Silver Lion Direct e Media 2026.</p>'
    },
    'ONE MORE QUESTION': {
        'all': '<p>Il 40% dei tumori alla prostata in Argentina viene diagnosticato in stadio avanzato perché gli uomini non si controllano. Grey Argentina e LALCEC infiltrano conferenze stampa, interviste sportive e dibattiti politici: giornalisti e conduttori pongono "una domanda in più" — "Ti sei fatto il controllo annuale della prostata?" I risultati: +31% di visite mediche per prevenzione. Gold Lion PR 2026.</p>'
    },
    'COINCIDENCE?': {
        'all': '<p>Le sagome dei contenitori di patatine fritte in tutto il mondo assomigliano al logo Heinz. "Coincidenza?" Heinz e Rethink Toronto portano questa osservazione all\'esterno in 33 Paesi, senza testo, senza branding esplicito — solo la forma. La stessa insight di "Look Familiar?" applicata all\'outdoor su scala globale. Gold Lion Outdoor 2026.</p>'
    },

    # ── GOLD WINNERS ──
    'DANCEBOOK BRASIL': {
        'all': '<p>Bradesco commissiona il primo libro di partiture per le danze tradizionali brasiliane — dal forró al maracatu al frevo — usando la notazione Benesh, lo stesso sistema usato per il balletto classico. Preservare la cultura popolare con gli strumenti dell\'élite. Gold Lion Design 2026.</p>'
    },
    'VEHICLE OF HOPE': {
        'all': '<p>In Gaza, Caritas gestisce 10 cliniche mobili e 126 operatori sanitari. Con le strade bloccate e l\'accesso umanitario ridotto ai minimi termini, un veicolo medico diventa letteralmente un\'ancora di vita. Una campagna di raccolta fondi devastante nella sua semplicità. Gold Lion Health & Wellness 2026.</p>'
    },
    'KYLE F*CKING CONNOR': {
        'all': '<p>Kyle Connor è il capitano dei Winnipeg Jets e l\'idolo della città. I tifosi lo cantano con una canzone che ha come ritornello il suo nome seguito da una parolaccia. KFC Canada abbraccia il doppio senso e lancia "The Kyle F*cking Connor Meal" — branding involontario diventato campagna ufficiale. Gold Lion Experience 2026.</p>'
    },
    'WELCOME BACK, PAISANO': {
        'all': '<p>Tecate accoglie i lavoratori migranti messicani che tornano a casa con un messaggio di dignità e appartenenza: "Bentornato, paesano." Una campagna che trasforma una birra in un simbolo di identità culturale e rispetto. Gold Lion Experience 2026.</p>'
    },
    'LANGUAGE OF BEDWETTING': {
        'all': '<p>Per molti bambini autistici non verbali, bagnare il letto è una delle poche forme di comunicazione disponibili — ma non esiste ancora un linguaggio per decodificarla. Autism Society crea uno strumento per aiutare le famiglie a capire i segnali. Gold Lion Digital Craft 2026.</p>'
    },
    'EVERYBODY COINBASE': {
        'all': '<p>Coinbase trasforma "Everybody (Backstreet\'s Back)" dei Backstreet Boys in un inno karaoke per il Super Bowl LX — una festa collettiva che porta il crypto nel mainstream della cultura pop americana. Gold Lion Entertainment e Direct 2026.</p>'
    },
    'EXPENSIVE SH*T': {
        'all': '<p>18 neonati. Quasi 500.000 dollari di oggetti di lusso. Huggies testa i suoi pannolini premium nel modo più drammatico possibile. Un\'idea brutale e brillante che diventa virale. Gold Lion Brand Experience 2026.</p>'
    },
    'THE SWEDISH PRESCRIPTION': {
        'all': '<p>Visit Sweden convince i medici a prescrivere la Svezia come destinazione terapeutica — natura, silenzio e benessere come cura. La prima nazione "prescritta" dai dottori. Gold Lion Creative Strategy 2026.</p>'
    },
    'THE LEGACY OF VIRGINIA GIUFFRE': {
        'all': '<p>Virginia Giuffre ha sfidato Jeffrey Epstein e il suo network di abusi per anni, spesso da sola. Questa campagna trasforma la sua storia in un legacy attivo — una piattaforma che continua a dare voce alle vittime. Gold Lion Titanium 2026.</p>'
    },
    'CIF CLEAN MY NAME': {
        'all': '<p>In Brasile, milioni di persone hanno il nome segnalato come insolvente nel database Serasa — una macchia che blocca lavoro, credito e futuro. Cif, il detergente che pulisce tutto, si offre di "pulire il nome" di chi ne ha bisogno. Partnership creativa con Serasa, Gold Lion Experience 2026.</p>'
    },
    'APPLE MUSIC X BAD BUNNY HALFTIME SHOW - SHOT ON IPHONE': {
        'all': '<p>Il Super Bowl LX Halftime Show di Bad Bunny, catturato con iPhone 16. Apple trasforma il più grande palco televisivo del mondo in una dimostrazione live delle capacità cinematografiche del suo smartphone. Gold Lion Film 2026.</p>'
    },
}

# ── Labels in Italian ─────────────────────────────────────────────────────────
MEDAL_IT = {'grandprix':'Grand Prix','gold':'Gold Lion','silver':'Silver Lion','bronze':'Bronze Lion'}
CAT_IT = {
    'film':'Film Lions','print':'Print & Publishing Lions','outdoor':'Outdoor Lions',
    'audio':'Audio & Radio Lions','social':'Social & Creator Lions','direct':'Direct Lions',
    'media':'Media Lions','experience':'Brand Experience & Activation Lions',
    'titanium':'Dan Wieden Titanium Lions','design':'Design Lions','pr':'PR Lions',
    'filmcraft':'Film Craft Lions','effectiveness':'Creative Effectiveness Lions',
    'entertainment':'Entertainment Lions','innovation':'Innovation Lions',
    'pharma':'Pharma Lions','health':'Health & Wellness Lions',
    'data':'Creative Data Lions','glass':'Glass: The Lion for Change',
    'digitalcraft':'Digital Craft Lions','music':'Entertainment Lions for Music',
    'industrycraft':'Industry Craft Lions','sdg':'SDG Lions',
    'commerce':'Creative Commerce Lions','strategy':'Creative Strategy Lions',
    'sport':'Entertainment Lions for Sport',
    'transformation':'Creative Business Transformation Lions',
    'b2b':'Creative B2B Lions','gaming':'Entertainment Lions for Gaming',
}

def make_desc(title, brand, agency, country_clean, cat, medal):
    # Use rich description if available
    desc_key = DESCRIPTIONS.get(title) or DESCRIPTIONS.get(title.upper())
    if desc_key:
        raw = desc_key.get('all', '')
        if raw:
            return raw + f'<p class="credits-line">📍 {agency} per {brand}, {country_clean}.</p>'

    medal_label = MEDAL_IT.get(medal, medal)
    cat_label   = CAT_IT.get(cat, cat)

    # Category-specific narrative fragments
    CAT_WHAT = {
        'film':         ('un film pubblicitario', 'racconta una storia per il grande schermo della pubblicità'),
        'print':        ('una campagna print', 'comunica con la forza di un\'immagine immobile'),
        'outdoor':      ('un\'installazione outdoor', 'occupa lo spazio fisico con un\'idea impossibile da ignorare'),
        'audio':        ('un progetto audio', 'dimostra che il suono può fare quello che le immagini non riescono'),
        'social':       ('una campagna social', 'ha trovato il modo di muoversi nella cultura digitale con naturalezza'),
        'direct':       ('un progetto di direct marketing', 'raggiunge le persone giuste nel momento giusto'),
        'media':        ('una strategia media', 'ha trasformato dove e come il messaggio arriva al pubblico'),
        'experience':   ('un\'esperienza di brand activation', 'porta le persone dentro il brand, non solo davanti'),
        'titanium':     ('un\'idea titanium', 'ridefinisce le regole di una categoria intera'),
        'design':       ('un progetto di design', 'dimostra che la forma e il contenuto sono inseparabili'),
        'pr':           ('una campagna PR', 'ha generato attenzione autentica, non acquistata'),
        'filmcraft':    ('un film di altissima qualità', 'eleva il linguaggio cinematografico nella comunicazione'),
        'effectiveness':('una campagna di efficacia creativa', 'ha trasformato l\'idea in risultati misurabili'),
        'entertainment':('un progetto di entertainment', 'ha coinvolto le persone come contenuto, non come interruzione'),
        'innovation':   ('una soluzione innovativa', 'risolve un problema reale con tecnologia o pensiero laterale'),
        'pharma':       ('una campagna pharma', 'ha rotto le convenzioni della comunicazione sanitaria'),
        'health':       ('un progetto health & wellness', 'ha spostato la conversazione sulla salute in modo significativo'),
        'data':         ('una campagna data-driven', 'trasforma dati in comportamenti e dati in storie'),
        'glass':        ('un progetto per il cambiamento', 'usa la creatività come leva per un impatto sociale reale'),
        'digitalcraft': ('un lavoro di digital craft', 'spinge i limiti tecnici dell\'esecuzione digitale'),
        'music':        ('un progetto music marketing', 'usa la musica come linguaggio primario, non come sottofondo'),
        'industrycraft':('un esempio di artigianato creativo', 'esalta la cura dell\'esecuzione come valore in sé'),
        'sdg':          ('un\'iniziativa per gli SDG', 'dimostra che sostenibilità e creatività non si escludono'),
        'commerce':     ('un progetto di commerce creativo', 'ha trovato nuovi modi per avvicinare brand e acquisto'),
        'strategy':     ('una strategia creativa', 'ha ridefinito il posizionamento con un\'idea centrale potente'),
        'sport':        ('una campagna sport', 'ha connesso un brand alla passione sportiva in modo autentico'),
        'transformation':('un progetto di business transformation', 'ha usato la creatività per cambiare il modello stesso'),
        'b2b':          ('una campagna B2B', 'dimostra che la creatività funziona anche quando il pubblico è professionale'),
        'gaming':       ('un progetto gaming', 'ha trovato il modo di parlare ai gamer nel loro territorio'),
    }

    cat_info = CAT_WHAT.get(cat, ('un lavoro creativo', 'ha convinto la giuria del festival più importante al mondo'))
    cat_noun, cat_verb = cat_info

    if medal == 'grandprix':
        return (
            f'<p><strong>{title}</strong> conquista il <strong>Grand Prix {cat_label}</strong> '
            f'a Cannes Lions 2026 — il riconoscimento più alto assegnato in questa categoria.</p>'
            f'<p>Firmato da <strong>{agency}</strong> per <strong>{brand}</strong> ({country_clean}), '
            f'è {cat_noun} che {cat_verb}, scelto dalla giuria come il meglio dell\'anno.</p>'
        )
    elif medal == 'gold':
        return (
            f'<p><strong>{title}</strong> — <strong>Gold Lion</strong> ai Cannes Lions 2026 '
            f'nella categoria <strong>{cat_label}</strong>.</p>'
            f'<p>Sviluppato da <strong>{agency}</strong> per <strong>{brand}</strong> ({country_clean}), '
            f'è {cat_noun} che {cat_verb}. Tra i lavori più riconosciuti dell\'anno al festival di Cannes.</p>'
        )
    elif medal == 'silver':
        return (
            f'<p><strong>{title}</strong> riceve il <strong>Silver Lion</strong> '
            f'ai Cannes Lions 2026 nella categoria <strong>{cat_label}</strong>.</p>'
            f'<p>{agency} firma questo lavoro per <strong>{brand}</strong> ({country_clean}): '
            f'{cat_noun} che {cat_verb} e si guadagna un posto tra le eccellenze creative globali dell\'anno.</p>'
        )
    else:  # bronze
        return (
            f'<p><strong>{title}</strong> ottiene il <strong>Bronze Lion</strong> '
            f'ai Cannes Lions 2026 nella categoria <strong>{cat_label}</strong>.</p>'
            f'<p>Creato da <strong>{agency}</strong> per <strong>{brand}</strong> ({country_clean}), '
            f'è {cat_noun} che {cat_verb} — riconosciuto dalla giuria internazionale di Cannes tra i lavori dell\'anno.</p>'
        )

def make_credits(brand, agency, country_clean, cat, medal):
    return [
        ['Brand', brand],
        ['Agenzia', agency],
        ['Paese', country_clean],
        ['Categoria', CAT_IT.get(cat, cat)],
        ['Medaglia', MEDAL_IT.get(medal, medal)],
        ['Anno', '2026'],
        ['Fonte', 'lovethework.com'],
    ]

# ── Deduplicate ───────────────────────────────────────────────────────────────
raw = {}
for eid, cd in data.items():
    cat = CAT_MAP.get(eid)
    if not cat: continue
    for entry in cd['entries']:
        aw, title, brand, agency, country = entry
        key = (title.upper(), brand.upper(), cat)
        if key not in raw or MEDAL_ORD[aw] < MEDAL_ORD[raw[key]['_aw']]:
            raw[key] = dict(_aw=aw, cat=cat, medal=MEDAL_MAP[aw],
                            title=title, brand=brand, agency=agency, country=country)

cases = sorted(raw.values(), key=lambda x: (x['cat'], MEDAL_ORD[x['_aw']], x['title']))
print(f"Total unique cases from JSON: {len(cases)}")

# Add missing second Film GP
cases.insert(0, {
    '_aw':'GP', 'cat':'film', 'medal':'grandprix',
    'title':'HOW CAN I COMMUNICATE BETTER WITH MY MOM?',
    'brand':'CLAUDE', 'agency':'MOTHER', 'country':'United Kingdom',
})

# Assign unique IDs
seen_ids = {}
for c in cases:
    base = slugify(c['title']) + '-' + c['cat']
    if base in seen_ids:
        seen_ids[base] += 1
        c['id'] = base + '-' + str(seen_ids[base])
    else:
        seen_ids[base] = 0
        c['id'] = base

# ── Build CASES JS ────────────────────────────────────────────────────────────
lines = ['// ===================== CASES =====================', 'const CASES = [']
prev_cat = None
matched_thumbs = 0
has_video = 0
no_video_no_thumb = []

for c in cases:
    if c['cat'] != prev_cat:
        lines.append(f"// ---- {c['cat'].upper()} ----")
        prev_cat = c['cat']

    country_clean = re.sub(r'^[^\s]+\s', '', flag(c['country']))
    thumb = find_thumb(c['title'])

    vid = KNOWN_VIDEOS.get(c['title'].upper()) or KNOWN_VIDEOS.get(c['title'])
    # Handle None entries (explicitly nulled)
    if vid is None:
        vid_val = None
    else:
        vid_val = vid

    if thumb:
        matched_thumbs += 1
    if vid_val:
        has_video += 1
        video_js = f"{{type:'{vid_val['type']}',id:'{vid_val['id']}'}}"
        # fallback thumb from YouTube or Vimeo
        if not thumb:
            if vid_val['type'] == 'youtube':
                thumb = f"https://img.youtube.com/vi/{vid_val['id']}/hqdefault.jpg"
            elif vid_val['type'] == 'vimeo':
                thumb = f"https://vumbnail.com/{vid_val['id']}.jpg"
    else:
        video_js = 'null'

    if not thumb:
        no_video_no_thumb.append((c['medal'], c['cat'], c['title']))

    desc    = js(make_desc(c['title'], c['brand'], c['agency'], country_clean, c['cat'], c['medal']))
    credits = make_credits(c['brand'], c['agency'], country_clean, c['cat'], c['medal'])
    credits_js = '[' + ','.join(f"['{js(k)}','{js(v)}']" for k,v in credits) + ']'

    lines.append(
        '{' +
        f"id:'{js(c['id'])}',cat:'{js(c['cat'])}',medal:'{c['medal']}'," +
        f"title:'{js(c['title'])}',brand:'{js(c['brand'])}',agency:'{js(c['agency'])}'," +
        f"country:'{js(flag(c['country']))}',video:{video_js}," +
        f"thumb:'{thumb}',description:'{desc}',credits:{credits_js}" +
        '},'
    )

lines.append('];')
cases_block = '\n'.join(lines)

print(f"CDN+YT thumbs: {matched_thumbs}/{len(cases)}")
print(f"Videos: {has_video}/{len(cases)}")
print(f"\nNo thumb AND no video ({len(no_video_no_thumb)}):")
for medal, cat, title in sorted(no_video_no_thumb, key=lambda x: {'grandprix':0,'gold':1,'silver':2,'bronze':3}[x[0]])[:30]:
    print(f"  [{medal[:2].upper()}] [{cat}] {title}")

# ── Patch index.html ──────────────────────────────────────────────────────────
html_path = '/sessions/sleepy-ecstatic-mendel/mnt/outputs/index.html'
with open(html_path) as f:
    html = f.read()

cases_pat = re.compile(r'// ={5,} CASES ={5,}\s*\nconst CASES = \[.*?\];', re.DOTALL)
if not cases_pat.search(html):
    sys.exit('ERROR: CASES anchor not found')

html = cases_pat.sub(cases_block, html)

with open(html_path, 'w') as f:
    f.write(html)

print(f"\n✅ Done — index.html: {len(html):,} bytes")

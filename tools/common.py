import csv,io,re,unicodedata
def norm(s):
    s=unicodedata.normalize('NFD',(s or '').lower());return re.sub(r'[^a-z]','',''.join(ch for ch in s if not unicodedata.combining(ch)))
ABBR=[(r'\bV\.?LE\b','VIALE'),(r'\bP\.?ZZA\b','PIAZZA'),(r'\bP\.?ZA\b','PIAZZA'),(r'\bP\.?LE\b','PIAZZALE'),(r'\bC\.?SO\b','CORSO'),(r'\bL\.?GO\b','LARGO'),(r'\bSTR\.?\b','STRADA'),(r'\bV\.\s*','VIA '),(r'\bS\.?S\.?\b','SS'),(r'\bSNC\b',''),(r'\bF\.?LLI\b','FRATELLI'),(r'\bG\.\s*','G '),(r'\bP\.\s*','P ')]
def akey(addr):
    s=unicodedata.normalize('NFD',(addr or '').upper());s=''.join(c for c in s if not unicodedata.combining(c))
    for a,b in ABBR:s=re.sub(a,b,s)
    s=re.sub(r'[^A-Z0-9 ]',' ',s);s=re.sub(r'\b(DI|DEL|DELLA|DELLE|DEI|DEGLI|DELL|D|AL|ALLA|LA|IL|LO|I|GLI|LE)\b',' ',s)
    return re.sub(r'\s+','',s)
def read_csv(path):
    raw=open(path,'rb').read()
    try:txt=raw.decode('utf-8-sig')
    except UnicodeDecodeError:txt=raw.decode('latin-1')
    return [r for r in csv.DictReader(io.StringIO(txt),delimiter=';') if r['STATO']=='ITALIA' and r['DATA CHIUSURA'].startswith('9999')]

# comuni nei CSV con il nome precedente a fusioni/rinominazioni -> nome nel dataset dei confini
ALIAS={'berra':'Riva del Po','carbonaradipo':'Borgocarbonara','coriglianocalabro':'Corigliano-Rossano','rossano':'Corigliano-Rossano','cutigliano':'Abetone Cutigliano','laterina':'Laterina Pergine Valdarno','pergine valdarno':'Laterina Pergine Valdarno','porrettaterme':'Alto Reno Terme','puosdalpago':'Alpago','revere':'Borgo Mantovano','riomarina':'Rio','sandorligodellavalle':'San Dorligo della Valle-Dolina','sangiovannidasso':'Montalcino','sangiovannidifassa':'San Giovanni di Fassa-Sèn Jan','sanmarcellopistoiese':'San Marcello Piteglio','santagostino':'Terre del Reno','sermide':'Sermide e Felonica','sorbolo':'Sorbolo Mezzani','tavarnellevaldipesa':'Barberino Tavarnelle','tresigallo':'Tresignana','vallecrosiaalmare':'Vallecrosia','vermezzo':'Vermezzo con Zelo','acquaricadelcapo':'Presicce-Acquarica','ortiseisanktulrichingroden':'Ortisei/St. Ulrich'}
ALIAS['perginevaldarno']=ALIAS['laterina']
ALIAS['gonnosfanadica']='Gonnosfanadiga'   # refuso nel CSV
def cname(city):
    k=norm(city);return norm(ALIAS[k]) if k in ALIAS else k

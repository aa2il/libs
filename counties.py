############################################################################################
#
# counties.py - Rev 1.0
# Copyright (C) 2024-5 by Joseph B. Attili, joe DOT aa2il AT gmail DOT com
#
# Lists counties for state QSO parties.
#
# Almost complete - there are a couple of entities I couldn't find county list for - try again later ...
#
############################################################################################
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
############################################################################################

COUNTIES={}

COUNTIES['AL']=['AUTA','BALD','BARB','BIBB','BLOU','BULL','BUTL','CHOU','CHMB','CKEE','CHIL','CHOC',
                'CLRK','CLAY','CLEB','COFF','COLB','CONE','COOS','COVI','CREN','CULM','DALE','DLLS',
                'DKLB','ELMO','ESCA','ETOW','FAYE','FRNK','GENE','GREE','HALE','HNRY','HOUS','JKSN',
                'JEFF','LAMA','LAUD','LAWR','LEE','LIME','LOWN','MACO','MDSN','MRGO','MARI','MRSH',
                'MOBI','MNRO','MGMY','MORG','PERR','PICK','PIKE','RAND','RSSL','SCLR','SHEL','SUMT',
                'TDEG','TPOO','TUSC','WLKR','WASH','WLCX','WINS']

COUNTIES['AB']=['BAR','BOW','BRC','CCE','CCF','CFL','CHE','CMD','CNH','CRR','CSD','CSH','CSK','EDC',
                'EDG','EDM','EDW','EMW','ERB','EST','EWE','FTH','FTM','GPM','LAK','LTH','MEDI','PRW',
                'RDL','RDM','SPK','STA','STR','YEL']

COUNTIES['AR']=['ASH','BAX','BEN','BOO','BRA','CAL','CAR','CHI','CLK','CLA','CLE','CLV','COL','CON',
                'CRG','CRA','CRI','CRO','DAL','DES','DRE','FAU','FRA','FUL','GAR','GNT','GRE','HEM',
                'HSP','HOW','IND','IZA','JAK','JEF','JON','LAF','LAW','LEE','LIN','LRV','LOG','LON',
                'MAD','MRN','MIL','MIS','MON','MGY','NEV','NEW','OUA','PER','PHI','PIK','POI','PLK',
                'POP','PRA','PUL','RAN','SFR','SAL','SCO','SCY','SEB','SVR','SHA','STO','UNI','VBN',
                'WAS','WHI','WOO','YEL']

COUNTIES['AZ']=['APH','CHS','CNO','GLA','GHM','GLE','LPZ','MCP','MHV','NVO','PMA','PNL','SCZ',
                'YVP','YMA']

# Cobbled together - RES may be another 
COUNTIES['BC']=['ABF','BNS','BUS','CHP','CLC','CML','COA','CPC','CPG','CSN','DEL','ESQ','FPK','KEL',
                'KOC','KTC','LAA','MMF','NAL','NOS','NPR','NVA','NWB','PMC','PMM','PPN','RIC','SBV',
                'SGI','STR','SUC','SUN','SWK','SWR','VAC','VAE','VAG','VAK','VAQ','VAS','VIC','WVS',
                'KSC','NVC','RCM','LTF','KTN','VLM']

COUNTIES['CA']=['ALAM', 'MARN', 'SMAT', 'ALPI', 'MARP', 'SBAR', 'AMAD', 'MEND', 'SCLA', 'BUTT', 'MERC', 'SCRU', \
                'CALA', 'MODO', 'SHAS', 'COLU', 'MONO', 'SIER', 'CCOS', 'MONT', 'SISK', 'DELN', 'NAPA', 'SOLA', \
                'ELDO', 'NEVA', 'SONO', 'FRES', 'ORAN', 'STAN', 'GLEN', 'PLAC', 'SUTT', 'HUMB', 'PLUM', 'TEHA', \
                'IMPE', 'RIVE', 'TRIN', 'INYO', 'SACR', 'TULA', 'KERN', 'SBEN', 'TUOL', 'KING', 'SBER', 'VENT', \
                'LAKE', 'SDIE', 'YOLO', 'LASS', 'SFRA', 'YUBA', 'LANG', 'SJOA', 'MADE', 'SLUI']

COUNTIES['CO']=['ADA','ARA','ARA','ARC','BAC','BEN','BOU','BRO','CHA','CHE','CLC','CON','COS','CRO',
                'CUS','DEL','DEN','DOL','DOU','EAG','ELP','ELB','FRE','GAR','GIL','GRA','GUN','HIN',
                'HUE','JAC','JEF','KIO','KIC','LAK','LAP','LAR','LAA','LIN','LOG','MES','MIN','MOF',
                'MON','MOT','MOR','OTE','OUR','PAR','PHI','PIT','PRO','PUE','RIB','RIG','ROU','SAG',
                'SAJ','SAM','SED','SUM','TEL','WAS','WEL','YUM']

# Changed in 2024?
#COUNTIES['CT']=['FAI','HAR','LIT','MID','NHV','NLN','TOL','WIN']
COUNTIES['CT']=['CAP','GBR','LCR','NAU','NOE','NOW','SOE','SOC','WES']

COUNTIES['DE']=['NDE','KDE','SDE']

COUNTIES['FL']=['ALC','BAK','BAY','BRA','BRE','BRO','CAH','CHA','CIT','CLA','CLM','CLR','DAD','DES',
                'DIX','DUV','ESC','FLG','FRA','GAD','GIL','GLA','GUL','HAM','HAR','HEN','HER','HIG',
                'HIL','HOL','IDR','JAC','JEF','LAF','LAK','LEE','LEO','LEV','LIB','MAD','MTE','MAO',
                'MRT','MON','NAS','OKA','OKE','ORA','OSC','PAL','PAS','PIN','POL','PUT','SAN','SAR',
                'SEM','STJ','STL','SUM','SUW','TAY','UNI','VOL','WAK','WAL','WAG']

COUNTIES['GA']=['APPL','ATKN','BACN','BAKR','BALD','BANK','BARR','BART','BENH','BERR','BIBB','BLEC',
                'BRAN','BROK','BRYN','BULL','BURK','BUTT','CALH','CMDN','CAND','CARR','CATO','CHAR',
                'CHTM','CHAT','CHGA','CHER','CLKE','CLAY','CLTN','CLCH','COBB','COFF','COLQ','COLU',
                'COOK','COWE','CRAW','CRIS','DADE','DAWS','DECA','DKLB','DODG','DOOL','DHTY','DOUG',
                'EARL','ECHO','EFFI','ELBE','EMAN','EVAN','FANN','FAYE','FLOY','FORS','FRAN','FULT',
                'GILM','GLAS','GLYN','GORD','GRAD','GREE','GWIN','HABE','HALL','HANC','HARA','HARR',
                'HART','HEAR','HNRY','HOUS','IRWI','JACK','JASP','JFDA','JEFF','JENK','JOHN','JONE',
                'LAMA','LANI','LAUR','LEE','LIBE','LINC','LONG','LOWN','LUMP','MCDU','MCIN','MACO',
                'MADI','MARI','MERI','MILL','MITC','MNRO','MONT','MORG','MURR','MUSC','NEWT','OCON',
                'OGLE','PAUL','PEAC','PICK','PIER','PIKE','POLK','PULA','PUTN','QUIT','RABU','RAND',
                'RICH','ROCK','SCHL','SCRE','SEMI','SPAL','STEP','STWT','SUMT','TLBT','TALI','TATT',
                'TAYL','TELF','TERR','THOM','TIFT','TOOM','TOWN','TREU','TROU','TURN','TWIG','UNIO',
                'UPSO','WLKR','WALT','WARE','WARR','WASH','WAYN','WEBS','WHEE','WHIT','WFLD','WCOX',
                'WILK','WKSN','WORT']

COUNTIES['HI']=['NII','KAU','LHN','WHN','PRL','HON','MOL','KAL','LNI','MAU','KOH','HIL','KON','VOL']

COUNTIES['IA']=['ADR','ADM','ALL','APP','AUD','BEN','BKH','BOO','BRE','BUC','BNV','BTL','CAL','CAR',
                'CAS','CED','CEG','CHE','CHI','CLR','CLA','CLT','CLN','CRF','DAL','DAV','DEC','DEL',
                'DSM','DIC','DUB','EMM','FAY','FLO','FRA','FRE','GRE','GRU','GUT','HAM','HAN','HDN',
                'HRS','HEN','HOW','HUM','IDA','IOW','JAC','JAS','JEF','JOH','JON','KEO','KOS','LEE',
                'LIN','LOU','LUC','LYN','MAD','MAH','MRN','MSL','MIL','MIT','MNA','MOE','MTG','MUS',
                'OBR','OSC','PAG','PLA','PLY','POC','POL','POT','POW','RIN','SAC','SCO','SHE','SIO',
                'STR','TAM','TAY','UNI','VAN','WAP','WAR','WAS','WAY','WEB','WNB','WNS','WOO','WOR',
                'WRI',]

COUNTIES['ID']=['ADA','ADM','BAN','BEA','BEN','BIN','BLA','BOI','BNR','BNV','BOU','BUT','CAM','CAN',
                'CAR','CAS','CLA','CLE','CUS','ELM','FRA','FRE','GEM','GOO','IDA','JEF','JER','KOO',
                'LAT','LEM','LEW','LIN','MAD','MIN','NEZ','ONE','OWY','PAY','POW','SHO','TET','TWI',
                'VAL','WAS']

COUNTIES['IL']=['ADAM','ALEX','BOND','BOON','BROW','BURO','CALH','CARR','CASS','CHAM','CHRS','CLRK',
                'CLAY','CLNT','COLE','COOK','CRAW','CUMB','DEKA','DEWT','DOUG','DUPG','EDGR','EDWA',
                'EFFG','FAYE','FORD','FRNK','FULT','GALL','GREE','GRUN','HAML','HANC','HARD','HNDR',
                'HENR','IROQ','JACK','JASP','JEFF','JERS','JODA','JOHN','KANE','KANK','KEND','KNOX',
                'LAKE','LASA','LAWR','LEE' ,'LIVG','LOGN','MACN','MCPN','MADN','MARI','MSHL','MASN',
                'MSSC','MCDN','MCHE','MCLN','MNRD','MRCR','MNRO','MNTG','MORG','MOUL','OGLE','PEOR',
                'PERR','PIAT','PIKE','POPE','PULA','PUTN','RAND','RICH','ROCK','SALI','SANG','SCHY',
                'SCOT','SHEL','STAR','SCLA','STEP','TAZW','UNIO','VERM','WABA','WARR','WASH','WAYN',
                'WHIT','WTSD','WILL','WMSN','WBGO','WOOD']

COUNTIES['IN']=['INADA','INALL','INBAR','INBEN','INBLA','INBOO','INBRO','INCAR','INCAS','INCLR',
                'INCLY','INCLI','INCRA','INDAV','INDEA','INDEC','INDEK','INDEL','INDUB','INELK',
                'INFAY','INFLO','INFOU','INFRA','INFUL','INGIB','INGRA','INGRE','INHAM','INHAN',
                'INHAR','INHND','INHNR','INHOW','INHUN','INJAC','INJAS','INJAY','INJEF','INJEN',
                'INJOH','INKNO','INKOS','INLAG','INLAK','INLAP','INLAW','INMAD','INMRN','INMRS',
                'INMRT','INMIA','INMNR','INMNT','INMOR','INNEW','INNOB','INOHI','INORA','INOWE',
                'INPAR','INPER','INPIK','INPOR','INPOS','INPUL','INPUT','INRAN','INRIP','INRUS',
                'INSCO','INSHE','INSPE','INSTA','INSTE','INSTJ','INSUL','INSWI','INTPP','INTPT',
                'INUNI','INVAN','INVER','INVIG','INWAB','INWRN','INWRK','INWAS','INWAY','INWEL',
                'INWHT','INWHL']

COUNTIES['KY']=['ADA','ALL','AND','BAL','BAR','BAT','BEL','BOO','BOU','BOY','BOL','BRA','BRE','BRK',
                'BUL','BUT','CAL','CAW','CAM','CAE','CRL','CTR','CAS','CHR','CLA','CLY','CLI','CRI',
                'CUM','DAV','EDM','ELL','EST','FAY','FLE','FLO','FRA','FUL','GAL','GAR','GRT','GRV',
                'GRY','GRE','GRP','HAN','HAR','HRL','HSN','HRT','HEN','HNY','HIC','HOP','JAC','JEF',
                'JES','JOH','KEN','KNT','KNX','LAR','LAU','LAW','LEE','LES','LET','LEW','LIN','LIV',
                'LOG','LYO','MCC','MCY','MCL','MAD','MAG','MAR','MSL','MAT','MAS','MEA','MEN','MER',
                'MET','MON','MOT','MOR','MUH','NEL','NIC','OHI','OLD','OWE','OWS','PEN','PER','PIK',
                'POW','PUL','ROB','ROC','ROW','RUS','SCO','SHE','SIM','SPE','TAY','TOD','TRI','TRM',
                'UNI','WAR','WAS','WAY','WEB','WHI','WOL','WOO']

COUNTIES['KS']=['ALL','AND','ATC','BAR','BRT','BOU','BRO','BUT','CHS','CHT','CHE','CHY','CLK','CLY','CLO',
                'COF','COM','COW','CRA','DEC','DIC','DON','DOU','EDW','ELK','ELL','ELS','FIN','FOR','FRA',
                'GEA','GOV','GRM','GRT','GRY','GLY','GRE','HAM','HPR','HVY','HAS','HOG','JAC','JEF','JEW',
                'JOH','KEA','KIN','KIO','LAB','LAN','LEA','LCN','LIN','LOG','LYO','MRN','MSH','MCP','MEA',
                'MIA','MIT','MGY','MOR','MTN','NEM','NEO','NES','NOR','OSA','OSB','OTT','PAW','PHI','POT',
                'PRA','RAW','REN','REP','RIC','RIL','ROO','RUS','RSL','SAL','SCO','SED','SEW','SHA','SHE',
                'SMN','SMI','STA','STN','STE','SUM','THO','TRE','WAB','WAL','WAS','WIC','WIL','WOO','WYA']

COUNTIES['LA']=['ACAD','ALLE','ASCE','ASSU','AVOY','BEAU','BIEN','BOSS','CADD','CALC','CALD','CAME','CATA',
                'CLAI','CONC','DESO','EBR' ,'ECAR','EFEL','EVAN','FRAN','GRAN','IBER','IBVL','JACK','JEFF',
                'JFDV','LASA','LAFA','LAFO','LINC','LIVI','MADI','MORE','NATC','ORLE','OUAC','PLAQ','PCP',
                'RAPI','REDR','RICH','SABI','SBND','SCHL','SHEL','SJAM','SJB' ,'SLAN','SMT' ,'SMAR','STAM',
                'TANG','TENS','TERR','UNIO','VERM','VERN','WASH','WEBS','WBR' ,'WCAR','WFEL','WINN']

COUNTIES['MD']=['ALY','ANA','BAL','BCT','CLV','CLN','CRL','CEC','CHS','DRC','FRD','GAR','HFD','HWD',
                'KEN','MON','PGE','QAN','STM','SMR','TAL','WAS','WIC','WRC','WDC']

COUNTIES['MA']=['BAR','BER','BRI','DUK','ESS','FRA','HMD','HMP','MID','NAN',
                'NOR','PLY','SUF','WOR']

COUNTIES['MB']=['BRS','CHA','CHR','DAU','ELM','KIL','POR','PRO','SEL','STB','WPC','WPN','WPS','WSC']

COUNTIES['ME']=['AND','ARO','CUM','FRA','HAN','KEN','KNO','LIN','OXF','PEN',
                'PIS','SAG','SOM','WAL','WAS','YOR']

COUNTIES['MI']=['ALCO',	'ALGE',	'ALLE',	'ALPE',	'ANTR',	'AREN',	'BARA',	'BARR',	'BAY',	'BENZ',	'BERR',
                'BRAN',	'CALH',	'CASS',	'CHAR',	'CHEB',	'CHIP',	'CLAR',	'CLIN',	'CRAW',	'DELT',	'DICK',
                'EATO',	'EMME',	'GENE',	'GLAD',	'GOGE',	'GRAT',	'GRTR',	'HILL',	'HOUG',	'HURO',	'INGH',
                'IONI',	'IOSC',	'IRON',	'ISAB',	'JACK',	'KALK',	'KENT',	'KEWE',	'KZOO',	'LAKE',	'LAPE',
                'LEEL',	'LENA',	'LIVI',	'LUCE',	'MACK',	'MACO',	'MANI',	'MARQ',	'MASO',	'MCLM',	'MECO',
                'MENO',	'MIDL',	'MISS',	'MONR',	'MTMO',	'MUSK',	'NEWA',	'OAKL',	'OCEA',	'OGEM',	'ONTO',
	        'OSCE',	'OSCO',	'OTSE',	'OTTA',	'PRES',	'ROSC',	'SAGI',	'SANI',	'SCHO',	'SHIA',	'STCL',
	        'STJO',	'TUSC',	'VANB',	'WASH',	'WAYN',	'WEXF']

COUNTIES['MN']=['AIT','ANO','BEC','BEL','BEN','BIG','BLU','BRO','CRL','CRV','CAS','CHP','CHS','CLA',
                'CLE','COO','COT','CRO','DAK','DOD','DOU','FAI','FIL','FRE','GOO','GRA','HEN','HOU',
                'HUB','ISA','ITA','JAC','KNB','KND','KIT','KOO','LAC','LAK','LKW','LES','LIN','LYO',
                'MCL','MAH','MRS','MRT','MEE','MIL','MOR','MOW','MUR','NIC','NOB','NOR','OLM','OTT',
                'PEN','PIN','PIP','POL','POP','RAM','RDL','RDW','REN','RIC','ROC','ROS','STL','SCO',
                'SHE','SIB','STR','STE','STV','SWI','TOD','TRA','WAB','WAD','WSC','WSH','WAT','WIL',
                'WIN','WRI','YEL']

COUNTIES['MO']=['ADR','AND','ATC','AUD','BAR','BTN','BAT','BEN','BOL','BOO','BUC','BTR','CWL','CAL',
                'CAM','CPG','CRL','CAR','CAS','CED','CHN','CHR','CLK','CLA','CLN','COL','COP','CRA',
                'DAD','DAL','DVS','DEK','DEN','DGL','DUN','FRA','GAS','GEN','GRN','GRU','HAR','HEN',
                'HIC','HLT','HOW','HWL','IRN','JAC','JAS','JEF','JON','KNX','LAC','LAF','LAW','LEW',
                'LCN','LIN','LIV','MAC','MAD','MRE','MAR','MCD','MER','MIL','MIS','MNT','MON','MGM',
                'MOR','NMD','NWT','NOD','ORE','OSA','OZA','PEM','PER','PET','PHE','PIK','PLA','POL',
                'PUL','PUT','RAL','RAN','RAY','REY','RIP','SAL','SCH','SCT','SCO','SHA','SHL','STC',
                'SCL','STF','STG','STL','SLC','STD','STN','SUL','TAN','TEX','VRN','WAR','WAS','WAY',
                'WEB','WOR','WRT']

COUNTIES['MS']=['ADA','ALC','AMI','ATT','BEN','BOL','CHI','CHO','CAL','CLB','CLA','CLK','COA','COP',
                'COV','CAR','DES','FOR','FRA','GEO','GRN','GRE','HAN','HAR','HIN','HOL','HUM','ISS',
                'ITA','JEF','JON','KEM','LAF','LAM','LAU','LAW','LEA','LEE','LEF','LIN','LOW','MRN',
                'MAD','MGY','MON','MAR','NES','NEW','NOX','OKT','PAN','PER','PIK','PEA','PON','PRE',
                'QUI','RAN','SMI','STO','SUN','TAL','TAT','TIP','TIS','TUN','UNI','WAL','WAS','WAY',
                'WEB','WIN','WIL','WAR','YAL','YAZ','SCO','JAC','JDV']

COUNTIES['MT']=['BEA','BIG','BLA','BRO','CRB','CRT','CAS','CHO','CUS','DAN','DAW','DEE','FAL','FER',
                'FLA','GAL','GAR','GLA','GOL','GRA','HIL','JEF','JUD','LAK','LEW','LIB','LIN','MAD',
                'MCC','MEA','MIN','MIS','MUS','PAR','PET','PHI','PON','PWD','PWL','PRA','RAV','RIC',
                'ROO','ROS','SAN','SHE','SIL','STI','SWE','TET','TOO','TRE','VAL','WHE','WIB','YEL']

COUNTIES['NB']=['ALB','CAR','CHA','GLO','KEN','KGS','MAD','NOR','QNS','RES','SJC','SUN','VIC','WES','YOR']

COUNTIES['NC']=['ALA','ALE','ALL','ANS','ASH','AVE','BEA','BER','BLA','BRU','BUN','BUR','CAB','CAL',
                'CAM','CAR','CAS','CAT','CHA','CHE','CHO','CLA','CLE','COL','CRA','CUM','CUR','DAR',
                'DVD','DAV','DUP','DUR','EDG','FOR','FRA','GAS','GAT','GRM','GRA','GRE','GUI','HAL',
                'HAR','HAY','HEN','HER','HOK','HYD','IRE','JAC','JOH','JON','LEE','LEN','LIN','MAC',
                'MAD','MAR','MCD','MEC','MIT','MON','MOO','NAS','NEW','NOR','ONS','ORA','PAM','PAS',
                'PEN','PEQ','PER','PIT','POL','RAN','RIC','ROB','ROC','ROW','RUT','SAM','SCO','STA',
                'STO','SUR','SWA','TRA','TYR','UNI','VAN','WAK','WAR','WAS','WAT','WAY','WLK','WIL',
                'YAD','YAN']

COUNTIES['ND']=['ADM','BRN','BSN','BLL','BOT','BOW','BRK','BUR','CSS','CAV','DIK','DIV','DUN','EDY',
                'EMN','FOS','GNV','GFK','GNT','GRG','HET','KDR','LMR','LOG','MCH','MCI','MCK','MCL',
                'MCR','MTN','MRL','NEL','OLR','PBA','PRC','RMY','RSM','REN','RLD','ROL','SGT','SRN',
                'SIX','SLP','STK','STL','STN','TWR','TRL','WLH','WRD','WLS','WLM ']

COUNTIES['NE']=['ADMS','ANTE','ARTH','BANN','BLAI','BOON','BOXB','BOYD','BRWN','BUFF','BURT','BUTL',
                'CASS','CEDA','CHAS','CHER','CHEY','CLAY','COLF','CUMI','CUST','DAKO','DAWE','DAWS',
                'DEUE','DIXO','DODG','DGLS','DUND','FILL','FRNK','FRON','FURN','GAGE','GARD','GARF',
                'GOSP','GRAN','GREE','HALL','HAMI','HRLN','HAYE','HITC','HOLT','HOOK','HOWA','JEFF',
                'JOHN','KEAR','KEIT','KEYA','KIMB','KNOX','LNCS','LINC','LOGA','LOUP','MDSN','MCPH',
                'MERR','MORR','NANC','NEMA','NUCK','OTOE','PAWN','PERK','PHEL','PIER','PLAT','POLK',
                'REDW','RICH','ROCK','SALI','SARP','SAUN','SCOT','SEWA','SHRD','SHRM','SIOU','STAN',
                'THAY','THOM','THUR','VLLY','WASH','WAYN','WEBS','WHEE','YORK']

COUNTIES['NH']=['BEL','CAR','CHE','COO','GRA','HIL','MER','ROC','STR','SUL']

COUNTIES['NJ']=['ATLA','BERG','BURL','CAPE','CMDN','CUMB','ESSE','GLOU','HUDS','HUNT','MERC','MID',
                'MONM','MORR','OCEA','PASS','SALE','SOME','SUSS','UNIO','WRRN']

COUNTIES['NL']=['ASJ','BMT','SCB','SGS','HCB','GFW','BTC','NDL','NSA','LGB','LNN']

COUNTIES['NM']=['BER','CAT','CHA','CIB','COL','CUR','DEB','DON','EDD','GRA',
                'GUA','HAR','HID','LEA','LIN','LOS','LUN','MCK','MOR','OTE',
                'QUA','RIO','ROO','SJU','SMI','SAN','SFE','SIE','SOC','TAO',
                'TOR','UNI','VAL']

COUNTIES['NS']=['ANP','ATG','CBR','COL','CMB','DIG','GUY','HRM','HNT','INV','KGS',
	        'LUN','PIC','QNS','RIC','SHL','VIC']

COUNTIES['NV'] = ['CAR','CHU','CLA','DOU','ELK','ESM','EUR','HUM','LAN','LIN','LYO','MIN','NYE','PER',
                  'STO','WAS','WHI']

COUNTIES['NY'] = ['ALB','ALL','BRX','BRM','CAT','CAY','CHA','CHE','CGO','CLI','COL','COR','DEL',
                  'DUT','ERI','ESS','FRA','FUL','GEN','GRE','HAM','HER','JEF','KIN','LEW','LIV',
                  'MAD','MON','MTG','NAS','NEW','NIA','ONE','ONO','ONT','ORA','ORL','OSW','OTS',
                  'PUT','QUE','REN','ROC','RIC','SAR','SCH','SCO','SCU','SEN','STL','STE','SUF',
                  'SUL','TIO','TOM','ULS','WAR','WAS','WAY','WES','WYO','YAT']

COUNTIES['OH'] = ['ADAM','ALLE','ASHL','ASHT','ATHE','AUGL','BELM','BROW','BUTL','CARR','CHAM','CLAR',
                  'CLER','CLIN','COLU','COSH','CRAW','CUYA','DARK','DEFI','DELA','ERIE','FAIR','FAYE',
                  'FRAN','FULT','GALL','GEAU','GREE','GUER','HAMI','HANC','HARD','HARR','HENR','HIGH',
                  'HOCK','HOLM','HURO','JACK','JEFF','KNOX','LAKE','LAWR','LICK','LOGA','LORA','LUCA',
                  'MADI','MAHO','MARI','MEDI','MEIG','MERC','MIAM','MONR','MONT','MORG','MORR','MUSK',
                  'NOBL','OTTA','PAUL','PERR','PICK','PIKE','PORT','PREB','PUTN','RICH','ROSS','SAND',
                  'SCIO','SENE','SHEL','STAR','SUMM','TRUM','TUSC','UNIO','VANW','VINT','WARR','WASH',
                  'WAYN','WILL','WOOD','WYAN']

COUNTIES['OK']=['ADA','DEL','LIN','PIT','ALF','DEW','LOG','PON','ATO','ELL','LOV','POT','BEA','GAR',
                'MCL','PUS','BEC','GRV','MCU','RGM','BLA','GRA','MCI','ROG','BRY','GNT','MAJ','SEM',
                'CAD','GRE','MAR','SEQ','CAN','HAR','MAY','STE','CAR','HRP','MUR','TEX','CHE','HAS',
                'MUS','TIL','CHO','HUG','NOB','TUL','CIM','JAC','NOW','WAG','CLE','JEF','OKF','WAS',
                'COA','JOH','OKL','WAT','COM','KAY','OKM','WOO','COT','KIN','OSA','WDW','CRA','KIO',
                'OTT','CRE','LAT','PAW','CUS','LEF','PAY']

COUNTIES['ON']=['ALG','BRA','BFD','BRU','CHK','COC','DUF','DUR','ELG','ESX','FRO','GRY','HAL','HLB',
                'HTN','HAM','HAS','HUR','KAW','KEN','LAM','LAN','LGR','LXA','MAN','MSX','MUS','NIA',
                'NIP','NFK','NOR','OTT','OXF','PSD','PEL','PER','PET','PRU','PED','RAI','REN','SIM',
                'SDG','SUD','TBY','TIM','TOR','WAT','WEL','YRK']

COUNTIES['OR'] = ['BAK','BEN','CLK','CLT','COL','COO','CRO','CUR','DES','DOU','GIL','GRA','HAR',
                  'HOO','JAC','JEF','JOS','KLA','LAK','LAN','LCN','LNN','MAL','MAR','MOR','MUL',
                  'POL','SHE','TIL','UMA','UNI','WAL','WCO','WSH','WHE','YAM']

COUNTIES['PA'] = ['ADA','ALL','ARM','BEA','BED','BER','BLA','BRA','BUX','BUT','CMB','CRN','CAR','CEN',
                  'CHE','CLA','CLE','CLI','COL','CRA','CUM','DAU','DCO','ELK','ERI','FAY','FUL','FOR',
                  'FRA','GRE','HUN','INN','JEF','JUN','LAC','LAN','LAW','LEB','LEH','LUZ','LYC','MCK',
                  'MER','MIF','MOE','MGY','MTR','NHA','NUM','PER','PHI','PIK','POT','SCH','SNY','SOM',
                  'SUL','SUS','TIO','UNI','VEN','WAR','WAS','WAY','WES','WYO','YOR']

COUNTIES['PEI'] = ['KGS','QNS','PRN']

COUNTIES['QC'] = ['BSA','SLS','QUE','MAU','ETE','MTL','OTS','ATE','CND','NDQ',
	          'GIM','CAS','LVL','LDE','LNS','MEE','CDQ']

COUNTIES['RI'] = ['BRI','KEN','NEW','PRO','WAS']

COUNTIES['SC'] = ['ABBE','AIKE','ALLE','ANDE','BAMB','BARN','BEAU','BERK','CHOU','CHAR','CHES',
                  'CHFD','CKEE','CLRN','COLL','DARL','DILL','DORC','EDGE','FAIR','FLOR','GEOR',
                  'GRWD','GVIL','HAMP','HORR','JASP','KERS','LAUR','LEE)','LEXI','LNCS','MARI',
                  'MARL','MCOR','NEWB','OCON','ORNG','PICK','RICH','SALU','SPAR','SUMT','UNIO',
                  'WILL','YORK']

COUNTIES['SD'] = ['AURO','BEAD','BENN','BONH','BROO','BRUL','BRWN','BUFF','BUTT','CAMP','CHAR',
                  'CLAY','CLRK','CODI','CORS','CUST','DAVI','DAY','DEUE','DEWY','DGLS','EDMU',
                  'FALL','FAUL','GRAN','GREG','HAAK','HAML','HAND','HNSN','HRDG','HUGH','HUTC',
                  'HYDE','JERA','JKSN','JONE','KING','LAKE','LAWR','LINC','LYMA','MCOO','MCPH',
                  'MEAD','MELL','MINE','MINN','MOOD','MRSH','PENN','PERK','POTT','ROBE','SANB',
                  'OGLA','SPIN','STAN','SULL','TODD','TRIP','TURN','UNIO','WALW','YANK','ZIEB']

COUNTIES['SK'] = ['BTL','CAR','CYP','DES','MOO','PRA','RGL','RGQ','RGW','SKG','SKU','SOU','YOR']

COUNTIES['TN'] = ['ANDE','BEDF','BENT','BLED','BLOU','BRAD','CAMP','CANN','CARR','CART','CHEA',
                  'CHES','CLAI','CLAY','COCK','COFF','CROC','CUMB','DAVI','DECA','DEKA','DICK',
                  'DYER','FAYE','FENT','FRAN','GIBS','GILE','GRAI','GREE','GRUN','HAMB','HAMI',
                  'HANC','HARD','HARN','HAWK','HAYW','HEND','HENR','HICK','HOUS','HUMP','JACK',
                  'JEFF','JOHN','KNOX','LAKE','LAUD','LAWR','LEWI','LINC','LOUD','MACO','MADI',
                  'MARI','MARS','MAUR','MCMI','MCNA','MEIG','MONR','MONT','MOOR','MORG','OBIO',
                  'OVER','PERR','PICK','POLK','PUTN','RHEA','ROAN','ROBE','RUTH','SCOT','SEQU',
                  'SEVI','SHEL','SMIT','STEW','SULL','SUMN','TIPT','TROU','UNIC','UNIO','VANB',
                  'WARR','WASH','WAYN','WEAK','WHIT','WILL','WILS']

COUNTIES['TX']=['ANDE','ANDR','ANGE','ARAN','ARCH','ARMS','ATAS','AUST','BAIL','BAND','BAST','BAYL',
                'BEE','BELL','BEXA','BLAN','BORD','BOSQ','BOWI','BZIA','BZOS','BREW','BRIS','BROO',
                'BROW','BURL','BURN','CALD','CALH','CALL','CMRN','CAMP','CARS','CASS','CAST','CHAM',
                'CHER','CHIL','CLAY','COCH','COKE','COLE','COLN','COLW','COLO','COML','COMA','CONC',
                'COOK','CORY','COTT','CRAN','CROC','CROS','CULB','DALM','DALS','DAWS','DSMI','DELT',
                'DENT','DEWI','DICK','DIMM','DONL','DUVA','EAST','ECTO','EDWA','EPAS','ELLI','ERAT',
                'FALL','FANN','FAYE','FISH','FLOY','FOAR','FBEN','FRAN','FREE','FRIO','GAIN','GALV',
                'GARZ','GILL','GLAS','GOLI','GONZ','GRAY','GRSN','GREG','GRIM','GUAD','HALE','HALL',
                'HAMI','HANS','HDMN','HRDN','HARR','HRSN','HART','HASK','HAYS','HEMP','HEND','HIDA',
                'HILL','HOCK','HOOD','HOPK','HOUS','HOWA','HUDS','HUNT','HUTC','IRIO','JACK','JKSN',
                'JASP','JDAV','JEFF','JHOG','JWEL','JOHN','JONE','KARN','KAUF','KEND','KENY','KENT',
                'KERR','KIMB','KING','KINN','KLEB','KNOX','LAMA','LAMB','LAMP','LSAL','LAVA','LEE',
                'LEON','LIBE','LIME','LIPS','LIVO','LLAN','LOVI','LUBB','LYNN','MADI','MARI','MART',
                'MASO','MATA','MAVE','MCUL','MLEN','MMUL','MEDI','MENA','MIDL','MILA','MILL','MITC',
                'MONT','MGMY','MOOR','MORR','MOTL','NACO','NAVA','NEWT','NOLA','NUEC','OCHI','OLDH',
                'ORAN','PPIN','PANO','PARK','PARM','PECO','POLK','POTT','PRES','RAIN','RAND','REAG',
                'REAL','RRIV','REEV','REFU','ROBE','RBSN','ROCK','RUNN','RUSK','SABI','SAUG','SJAC',
                'SPAT','SSAB','SCHL','SCUR','SHAC','SHEL','SHMN','SMIT','SOME','STAR','STEP','STER',
                'STON','SUTT','SWIS','TARR','TAYL','TERL','TERY','THRO','TITU','TGRE','TRAV','TRIN',
                'TYLE','UPSH','UPTO','UVAL','VVER','VZAN','VICT','WALK','WALL','WARD','WASH','WEBB',
                'WHAR','WHEE','WICH','WILB','WILY','WMSN','WLSN','WINK','WISE','WOOD','YOAK','YOUN',
                'ZAPA','ZAVA']

COUNTIES['UT'] = ['BEA','BOX','CAC','CAR','DAG','DAV','DUC','EME','GAR','GRA','IRO','JUA','KAN',
                  'MIL','MOR','PIU','RIC','SAL','SNJ','SNP','SEV','SUM','TOO','UIN','UTA','WST',
                  'WSH','WAY','WEB']

COUNTIES['VA']=['ACC','ALB','ALX','ALL','AME','AMH','APP','ARL','AUG','BAT','BED','BLA','BOT','BRX',
                'BRU','BCH','BHM','BVX','CAM','CLN','CRL','CCY','CHA','CHX','CPX','CHE','CLA','COX',
                'CVX','CRA','CUL','CUM','DAX','DIC','DIN','EMX','ESS','FFX','FXX','FCX','FAU','FLO',
                'FLU','FRA','FRX','FRE','FBX','GAX','GIL','GLO','GOO','GRA','GRN','GVL','HAL','HAX',
                'HAN','HCO','HBX','HRY','HIG','HOX','IOW','JAM','KQN','KGE','KWM','LAN','LEE','LEX',
                'LDN','LSA','LUN','LYX','MAD','MAT','MAX','MPX','MVX','MEC','MID','MON','NEL','NEW',
                'NNX','NFX','NHA','NUM','NRX','NOT','ORG','PAG','PAT','PBX','PIT','PQX','POX','POW',
                'PRE','PRG','PRW','PUL','RAX','RAP','RIC','RIX','ROA','ROX','RBR','RHM','RUS','SAX',
                'SCO','SHE','SMY','SHA','SPO','STA','STX','SUX','SUR','SUS','TAZ','VBX','WAR','WAS',
                'WAX','WES','WMX','WIX','WIS','WYT','YOR']

COUNTIES['VT']=['ADD','BEN','CAL','CHI','ESS','FRA','GRA','LAM','ORA','ORL','RUT','WAS','WNH','WNS']

# There is a different set of abbrevs for the 7QP and Salman Run (WA State QP)
COUNTIES['WA7QP'] = ['ADA','ASO','BEN','CHE','CLL','CLR','COL','COW','DOU','FER','FRA','GAR','GRN',
                  'GRY','ISL','JEF','KLI','KNG','KTP','KTT','LEW','LIN','MAS','OKA','PAC','PEN',
                  'PIE','SAN','SKG','SKM','SNO','SPO','STE','THU','WAH','WAL','WHA','WHI','YAK']

COUNTIES['WA'] = ['ADA','ASO','BEN','CHE','CLAL','CLAR','COL','COW','DOU','FER','FRA','GAR','GRAN',
                  'GRAY','ISL','JEFF','KING','KITS','KITT','KLI','LEW','LIN','MAS','OKA','PAC',
                  'PEND','PIE','SAN','SKAG','SKAM','SNO','SPO','STE','THU','WAH','WAL','WHA','WHI','YAK']

COUNTIES['WI'] = ['ADA','ASH','BAR','BAY','BRO','BUF','BUR','CAL','CHI','CLA','COL','CRA','DAN',
                  'DOD','DOO','DOU','DUN','EAU','FLO','FON','FOR','GRA','GRE','GRL','IOW','IRO',
                  'JAC','JEF','JUN','KEN','KEW','LAC','LAF','LAN','LIN','MAN','MAR','MRN','MRQ',
                  'MEN','MIL','MON','OCO','ONE','OUT','OZA','PEP','PIE','POL','POR','PRI','RAC',
                  'RIC','ROC','RUS','SAU','SAW','SHA','SHE','STC','TAY','TRE','VER','VIL','WAL',
                  'WSB','WAS','WAU','WAP','WSR','WIN','WOO']

COUNTIES['WV'] = ['BAR','BER','BOO','BRA','BRO','CAB','CAL','CLA','DOD','FAY','GIL','GRA','GRE',
                  'HAM','HAN','HDY','HAR','JAC','JEF','KAN','LEW','LIN','LOG','MRN','MAR','MAS',
                  'MCD','MER','MIN','MGO','MON','MRO','MOR','NIC','OHI','PEN','PLE','POC','PRE',
                  'PUT','RAL','RAN','RIT','ROA','SUM','TAY','TUC','TYL','UPS','WAY','WEB','WET',
                  'WIR','WOO','WYO']

COUNTIES['WY'] = ['ALB','BIG','CAM','CAR','CON','CRO','FRE','GOS','HOT','JOH','LAR','LIN','NAT',
                  'NIO','PAR','PLA','SHE','SUB','SWE','TET','UIN','WAS','WES']

# New England also has a combine QP
W1_STATES=['CT','ME','MA','NH','RI','VT']
COUNTIES['W1'] = []
for s in W1_STATES:
    for c in COUNTIES[s]:
        COUNTIES['W1'].append(s+c)

# As does the 7th call area (7QP)
W7_STATES=['AZ','ID','MT','NV','OR','UT','WA7QP','WY']
COUNTIES['7QP'] = []
COUNTIES_NV = []
for s in W7_STATES:
    for c in COUNTIES[s]:
        COUNTIES['7QP'].append(s[:2]+c)
        if s in ['NV']:
            COUNTIES_NV.append(s[:2]+c)

# NV Uses all 5-letters in their QSO Party            
COUNTIES['NV']=COUNTIES_NV

# They also combined the call history files for the IN, 7QP, DE and
# New England QPs since they happen on the same weekend
COUNTIES['IN7QPNEDE'] = COUNTIES['IN'] + COUNTIES['7QP'] + COUNTIES['W1'] + COUNTIES['DE'] 

# The Canadian prarie provinces have a combined QSO party 
CP_PROVINCES=['AB','MB','SK']
COUNTIES['CP'] = []
for s in CP_PROVINCES:
    for c in COUNTIES[s]:
        COUNTIES['CP'].append(s+c)

# As do the Atlantic provinces
AC_PROVINCES=['NL','PEI','NB','NS']
COUNTIES['AC'] = []
for s in AC_PROVINCES:
    for c in COUNTIES[s]:
        COUNTIES['AC'].append(s+c)

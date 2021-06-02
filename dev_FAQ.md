# FAQ - vývojáři

## Kde začít? 
Pěkný návod na rozchození projektu je v [README](./README.md) 

## Udělal jsem nějaké změny v kódu a chtěl bych je poslat do repo
Super, vytvoř pro změny novou větev a jakmile vývoj dané věci ukončíš, udělej pull request. Nepushuj přímo do masteru, jinak umře koťátko.

## Jak funguje deploy? 
V současnosti nemáme repo nijak propojený; jednou za čas se přihlásím na server, pullnu tam větev master a restartuju apache. 
Obvykle je to jednou za pár dní, pokud to hoří, tak rychleji. 
V případě potřeby piš na [admin@potrebujurousku.cz](mailto:admin@potrebujurousku.cz), nebo na discord

## Databáze? 

Máme databázi produkční, na kterou dáváme přístup jen vyvoleným. Pro vývoj je velmi doporučování využít lokální databáze. 
Návod na zprovoznění PostgreSQL databáze včetně naplnění daty nalezneš [zde](lokalni_databaze.md).

## Entity
Návrh DB, tabulky a jejich obsah a propojení

> Pozor! Došlo k přejmenování mnohých entit spolu s migrací do django.models. Myšlenka zůstává, názvy se změnily

### Opatření 
Hlavní jednotkou je OPATRENI. Většinou reflektuje jeden řádek v tabulce OPATRENI jedno vydané nařízení vlády, opatření KHS, či opatření MZDR.
Obsahuje sloupce jako 
- Název opatření (NAZEV)
- Zkratku názvu opatření (protože jsou dlouhé) (NAZEV_ZKR)
- Link na zdroj informací  (ZDROJ) 
- Platnost od (právníci tomu říkají účinnost) (PLATNOST_OD)
- Platnost do (je-li stanovena) (PLATNOST_DO) 
- identifikátor (pro dohledání u dané organizace, pokud existuje) (IDENTIFIKATOR) 
#### Interní
- PLATNOST (0 = "(nouzové) vypnutí, 1 = "aktivní", "2 = čeká na zpracování / probíhá zpracování") 
- PLATNOST_AUTOOPRAVA (místo, kde se projeví změny, když k nějakým na [mzdr](https://koronavirus.mzcr.cz/category/mimoradna-opatreni/)  dojde, default: null) 
- ROZSAH nic to nedělá, ale ušetří to spoustu času
- NAZEV_AUTOOPRAVA (zde se projeví změny v názvu, když k nějakým na [mzdr](https://koronavirus.mzcr.cz/category/mimoradna-opatreni/)  dojde, default: null) 

  - "nep" = nepotřebné, 
  - "rus" = prostě to jenom ruší něco jiného, 
  - "cr" celá ČR, "kraj" = Kraj, 
  - "okres", 
  - "nuts" = obec s rozšířenou působností, 
  - "obecmesto" = obec/město
- ZDROJ_AUTOOPRAVA - když se změní link, tak se tady objeví nový. Teď už takovéhle změny na [mzdr](https://koronavirus.mzcr.cz/category/mimoradna-opatreni/) nedělají

### Místní platnost opatření 
Návrh databáze pracoval s tím, že budou opatření stanovená na různých úrovních správy (třeba v rámci obce, nebo v rámci okresu). Pro to je zde spousta tabulek, které vyjadřují propojení daného opatření s konkrétním místem. 

#### OP_STAT
Nastavuje platnost opatření pro celou ČR. 
- ID_OPATRENI

#### OP_KRAJ
Nastavuje platnost opatření pro daný kraj (kraje podle jména k nalezení v tabulce KRAJ)  
- ID_OPATRENI
- ID_KRAJ

#### OP_OKRES
Nastavuje platnost opatření pro daný okres (okresy podle jména k nalezení v tabulce OKRES)  
- ID_OPATRENI
- ID_OKRES

#### OP_NUTS
Nastavuje platnost opatření pro obec s rozšířenou působností (podle jména k nalezení v tabulce NUTS3)  
- ID_OPATRENI
- ID_NUTS

#### OP_OM
Nastavuje platnost opatření pro obec/město (podle jména k nalezení v tabulce OBECMESTO)  
- ID_OPATRENI
- ID_OBECMESTO

### Položka
Jedno opatření se skládá většinou z více logických celků a k tomu slouží položka. 
Toto je vesměs samotný "text" logického celku z opatření 
- NAZEV
- KOMENTAR (výklad části opatření, jednoduchý, stručný)
- VYJIMKA (ideálně v bodech sepsané výjimky) 
- TYP ("doporuceni", "narizeni", "narizeninouzovy", "info"), podle toho se mění přiřazená class v bootstrapu 
- Propojení s kategorií  -> 
- Propojení s opatřním -> 
- ICON - název z fontaewsome, třeba "fas fa-exclamation-triangle" 

#### Interní 
- Extra link (občas je třeba "přilepit" více odkazů)
- Extra popis ("název" linku
- modal size (v bootstrapu určuje velikost vyskakujícího okna) 


### Kategorie 
Logické celky, jako třeba "Sport", "Kultura", "Hromadné akce" apod. Navázány na konkrétní položky opatření. 
Na [potrebujurousku.cz](https://potrebujurousku.cz/) se zobrazují setřízené právě podlě těchto kategorií 


Nedostatky tohoto návrhu: 
- Součásti jednoho opatření mohou mít více různých platností/účinností
- Občas je třeba připojit více než jeden odkaz, což se nyní řeší přímo v textu html <a href... 


### INFO 
Tady jsou vlastně jenom krákté výpisy z kontrol aktuálnosti 


## Vkládání dat do produkční databáze
S nejlepším vědomím a svědomím vlož data do db (máš-li přístup), commitni a zkontroluj vložené. 
Jestli je nějaké opatření "dobře zadné" (nebo pro takovou kontrolu) slouží [kontrola zadaného](https://potrebujurousku.cz/admin/kontrola-zadaneho/)

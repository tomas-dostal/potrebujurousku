# Postgresql dotabáze pro lokální vývoj

Vyskytla se potřeba přemigrovat Oracle databázi na něco lehčího. Časem se dostane i do produkce (až budou všechny sql dotazy přepsané do django.models). 

Pro vývoj je velmi žádoucí si rozběhnout lokální kopii databáze a nové funkce testovat právě na lokální kopii. 

Díky toho, že (budou) dotazy psány v django.models, tak nezáleží na tom, jaká dabáze je použita. Pro Postgresql jsem se rozhodl v podstatě jenom proto, že mi ji doporučovali v kurzu BI-DBS. 

## Instalace postgresql
```sh
sudo apt update
sudo apt install postgresql postgresql-contrib
```

Přepnu se na postgre server 

``` sh
sudo -i -u postgres

```
Udělám účet 

```sh
createuser --interactive

(username: potrebujurousku-admin) 
``` 

Udelám databázi 

```
createdb potrebujurousku
```

Potřebuju ještě udělat systémového uživatele se stejným jménem 

```sh 
sudo adduser potrebujurousku-admin

(set password: Password) 
``` 

## Nastavení připojení databáze

V souboru [secret.py.example](./projektrouska/secret.py.example) je example konfigurace pro lokální vývoj. Postačí ji přejmenovat na 
 ```secret.py``` 


## Naplnění databáze

Data jsou k dispozici v [insertscript](dbexport/) formátu.

Přes Datagrip (po přidání databáze) lze v následujícím pořadí naimportovat pomocí 
``` Databáze > postgres@localhost > databases > potrebujurousku > schemas > public > tables```
pravé tlačítko > ```RUN SQL script``` > vyber cestu k SQL insertscriptům. 

``` 
// disable integrity checks
SET session_replication_role = 'replica';

// enable integrity checks after import is done 
SET session_replication_role = 'origin';

``` 
na pořadí pak nezáleží. 

Popis jednotlivých entit (v češtině, databáze před migrací do django.models - myšlenka zůstala stejná, jen se to jinak jmenuje) naleznete 
[zde](./dev_FAQ.md#entity)
# Jak rozjet projekt pro lokální vývoj

## Stáhni kód
Naklonuj si kód z githubu do lokálního repozitáře.  
Nainstaluj si závislosti:  
  - buď `pip install -r requirements.txt`
  - nebo (doporučuju) `pipenv install`

## Doplň kód
Přejmenuj `secret.py.example` na `secret.py`

## Připoj databázi
Projekt aktuálně běží na oracle databázi.  
Pro používání si musíš zařídit přihlašovací údaje.  
Doplň přístupové údaje k databázi do `secret.py`  

Pokud nemáš, nainstaluj si oracle client  
  - Linux - [návod zde](https://help.ubuntu.com/community/Oracle Instant Client)


## Spusť projekt
Spusť pomocí
  - `python manage.py runserver`
  - nebo `pipenv run python manage.py runserver`, pokud instaluješ přes `pipenv`


# FAQ

## Když spouštím s DEV=False, tak se mi nenačítají static soubory
V produkční verzi Django defaultně neservuje static files, mělo by to být na webserveru (Apache, nginx,..).
Pokud chceš tyto soubory i bez toho, spusť aplikaci pomocí `python manage.py runserver --insecure`

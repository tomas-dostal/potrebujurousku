# Jak rozjet projekt pro lokální vývoj

## Stáhni kód
Naklonuj si kód z githubu do lokálního repozitáře.  
Nainstaluj si závislosti:  
  - buď `pip install -r requirements.txt`
  - nebo (doporučuju) `pipenv install`

## Doplň kód
Přejmenuj `secret.py.example` na `secret.py`

## Připoj databázi

1) Projekt aktuálně běží na PostgreSQL databázi. 
2) Pro připojení do ostré databáze musíš získat přístupové údaje. Pro lokální vývoj je velmi doporučeno vytvořit si
 [lokální kopii databáze](lokalni_databaze.md) a naplnit ji [daty](https://github.com/tomas-dostal/potrebujurousku/blob/master/dbexport/). 
Myšlenka za návrhem databáze [zde](https://github.com/tomas-dostal/potrebujurousku/blob/master/dev_FAQ.md)
3) Doplň přístupové údaje k databázi do `secret.py`


## Spusť projekt
Spusť pomocí
  - `python manage.py runserver`
  - nebo `pipenv run python manage.py runserver`, pokud instaluješ přes `pipenv`


# FAQ

## Když spouštím s DEV=False, tak se mi nenačítají static soubory
V produkční verzi Django defaultně neservuje static files, mělo by to být na webserveru (Apache, nginx,..).
Pokud chceš tyto soubory i bez toho, spusť aplikaci pomocí `python manage.py runserver --insecure`

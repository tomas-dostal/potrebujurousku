## Pár slov o projektu (Report)
Jak všechno vzniklo, proč to vůbec vzniklo a co by bylo pěkné dodělat. Toto, ale i pár pěkných grafíků s návštěvností.
- [![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://share.streamlit.io/tomas-dostal/potrebujurousku_streamlit/main/report.py)
- [Github repo reportu](https://github.com/tomas-dostal/potrebujurousku_streamlit)
- [Report (PDF)](https://github.com/tomas-dostal/potrebujurousku_streamlit/blob/main/potrebujurousku_report.pdf)

# Jak rozjet projekt pro lokální vývoj

## Stáhni kód
Naklonuj si kód z githubu do lokálního repozitáře.  
Nainstaluj si závislosti:  
  - buď `pip install -r requirements.txt`
  - nebo (doporučuju) `pipenv install`

## Doplň kód
Přejmenuj `secret.py.example` na `secret.py`

## Připoj databázi

1) Projekt aktuálně běží na oracle databázi. 
2) Pro používání si musíš zařídit přihlašovací údaje, alternativně si můžeš obsah databáze stáhnout jako [insertscript](https://github.com/tomas-dostal/potrebujurousku/blob/master/dbexport/) a vytvořit databázi vlastní. Co je v které tabulce a myšlenka za návrhem databáze [zde](https://github.com/tomas-dostal/potrebujurousku/blob/master/dev_FAQ.md)
3) Doplň přístupové údaje k databázi do `secret.py`  

Pokud nemáš, nainstaluj si oracle client  
  - Linux - [návod zde](https://help.ubuntu.com/community/Oracle%20Instant%20Client)


## Spusť projekt
Spusť pomocí
  - `python manage.py runserver`
  - nebo `pipenv run python manage.py runserver`, pokud instaluješ přes `pipenv`


# FAQ

## Když spouštím s DEV=False, tak se mi nenačítají static soubory
V produkční verzi Django defaultně neservuje static files, mělo by to být na webserveru (Apache, nginx,..).
Pokud chceš tyto soubory i bez toho, spusť aplikaci pomocí `python manage.py runserver --insecure`

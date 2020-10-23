#Jak rozjet projekt pro lokální vývoj

##Stáhni kód
Naklonuj si kód z githubu do lokálního repozitáře.
Nainstaluj si závislosti:
	- buď `pip install -r requirements.txt`
	- nebo (doporučuju) `pipenv install`

##Připoj databázi
Projekt aktuálně běží na oracle databázi.
Pro používání si musíš zařídit přihlašovací údaje.

Pokud nemáš, nainstaluj si oracle client
	- Linux - [návod zde](https://help.ubuntu.com/community/Oracle Instant Client)

Nastav si u sebe v Djangu parametry připojení k databázi:
	- buď v `base_settings.py` (ale pak pozor, abys změny nepřidal veřejně)
	- nebo přes `.env` soubor

##Spusť projekt
Spusť pomocí
	- `python manage.py runserver`
	- nebo `pipenv run python manage.py runserver`, pokud instaluješ přes `pipenv`
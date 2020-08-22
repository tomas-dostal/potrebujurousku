# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models


class Cast(models.Model):
    id_cast = models.BigIntegerField(primary_key=True)
    nazev_cast = models.CharField(max_length=50)
    obecmesto_id_obecmesto = models.ForeignKey('Obecmesto', models.DO_NOTHING, db_column='obecmesto_id_obecmesto')
    obecmesto_nuts3_id_nuts = models.ForeignKey('Obecmesto', models.DO_NOTHING, db_column='obecmesto_nuts3_id_nuts')
    obecmesto_nuts3_kraj_id_kraj = models.ForeignKey('Obecmesto', models.DO_NOTHING, db_column='obecmesto_nuts3_kraj_id_kraj')

    class Meta:
        managed = False
        db_table = 'cast'
        unique_together = (('id_cast', 'obecmesto_id_obecmesto', 'obecmesto_nuts3_id_nuts', 'obecmesto_nuts3_kraj_id_kraj'),)


class Kategorie(models.Model):
    id_kategorie = models.BigIntegerField(primary_key=True)
    nazev_kat = models.CharField(max_length=50)
    koment_kategorie = models.CharField(max_length=200, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'kategorie'


class Kraj(models.Model):
    id_kraj = models.BigIntegerField(primary_key=True)
    nazev_kraj = models.CharField(max_length=25)
    kod_kraj = models.BigIntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'kraj'


class Members(models.Model):
    member_id = models.FloatField(primary_key=True)
    first_name = models.CharField(max_length=50, blank=True, null=True)
    last_name = models.CharField(max_length=50, blank=True, null=True)
    birth_date = models.BigIntegerField()

    class Meta:
        managed = False
        db_table = 'members'


class Nuts3(models.Model):
    id_nuts = models.BigIntegerField(primary_key=True)
    nazev_nuts = models.CharField(max_length=50)
    kod_nuts = models.BigIntegerField(blank=True, null=True)
    kraj_id_kraj = models.ForeignKey(Kraj, models.DO_NOTHING, db_column='kraj_id_kraj')

    class Meta:
        managed = False
        db_table = 'nuts3'
        unique_together = (('id_nuts', 'kraj_id_kraj'),)


class Obecmesto(models.Model):
    id_obecmesto = models.BigIntegerField(primary_key=True)
    nazev_obecmesto = models.CharField(max_length=50)
    nuts3_id_nuts = models.ForeignKey(Nuts3, models.DO_NOTHING, db_column='nuts3_id_nuts')
    nuts3_kraj_id_kraj = models.ForeignKey(Nuts3, models.DO_NOTHING, db_column='nuts3_kraj_id_kraj')
    kod_obecmesto = models.BigIntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'obecmesto'
        unique_together = (('id_obecmesto', 'nuts3_id_nuts', 'nuts3_kraj_id_kraj'),)


class OpKraj(models.Model):
    opatreni_id_opatreni = models.OneToOneField('Opatreni', models.DO_NOTHING, db_column='opatreni_id_opatreni', primary_key=True)
    kraj_id_kraj = models.ForeignKey(Kraj, models.DO_NOTHING, db_column='kraj_id_kraj')

    class Meta:
        managed = False
        db_table = 'op_kraj'
        unique_together = (('opatreni_id_opatreni', 'kraj_id_kraj'),)


class OpNuts(models.Model):
    nuts3_id_nuts = models.OneToOneField(Nuts3, models.DO_NOTHING, db_column='nuts3_id_nuts', primary_key=True)
    nuts3_kraj_id_kraj = models.ForeignKey(Nuts3, models.DO_NOTHING, db_column='nuts3_kraj_id_kraj')
    opatreni_id_opatreni = models.ForeignKey('Opatreni', models.DO_NOTHING, db_column='opatreni_id_opatreni')

    class Meta:
        managed = False
        db_table = 'op_nuts'
        unique_together = (('nuts3_id_nuts', 'nuts3_kraj_id_kraj', 'opatreni_id_opatreni'),)


class OpOm(models.Model):
    opatreni_id_opatreni = models.OneToOneField('Opatreni', models.DO_NOTHING, db_column='opatreni_id_opatreni', primary_key=True)
    obecmesto_id_obecmesto = models.ForeignKey(Obecmesto, models.DO_NOTHING, db_column='obecmesto_id_obecmesto')
    obecmesto_nuts3_id_nuts = models.ForeignKey(Obecmesto, models.DO_NOTHING, db_column='obecmesto_nuts3_id_nuts')
    obecmesto_nuts3_kraj_id_kraj = models.ForeignKey(Obecmesto, models.DO_NOTHING, db_column='obecmesto_nuts3_kraj_id_kraj')

    class Meta:
        managed = False
        db_table = 'op_om'
        unique_together = (('opatreni_id_opatreni', 'obecmesto_id_obecmesto', 'obecmesto_nuts3_id_nuts', 'obecmesto_nuts3_kraj_id_kraj'),)


class Opatreni(models.Model):
    id_opatreni = models.BigIntegerField(primary_key=True)
    nazev_opatreni = models.CharField(max_length=200)
    platnost_od = models.DateField()
    je_platne = models.BigIntegerField()
    zdroj = models.CharField(max_length=500)
    nazev_zkr = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'opatreni'


class Polozka(models.Model):
    id_polozka = models.BigIntegerField(primary_key=True)
    nazev = models.CharField(max_length=40)
    komentar = models.CharField(max_length=500, blank=True, null=True)
    kategorie_id_kategorie = models.ForeignKey(Kategorie, models.DO_NOTHING, db_column='kategorie_id_kategorie')
    typ = models.CharField(max_length=20, blank=True, null=True)
    opatreni_id_opatreni = models.ForeignKey(Opatreni, models.DO_NOTHING, db_column='opatreni_id_opatreni')

    class Meta:
        managed = False
        db_table = 'polozka'
        unique_together = (('id_polozka', 'kategorie_id_kategorie', 'opatreni_id_opatreni'),)

from django.db import models

# Create your models here.
# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.


class AuthGroup(models.Model):
    name = models.CharField(unique=True, max_length=150, blank=True, null=True)

    class Meta:
        managed = False
        db_table = "auth_group"


class AuthGroupPermissions(models.Model):
    group = models.ForeignKey(AuthGroup, models.DO_NOTHING)
    permission = models.ForeignKey("AuthPermission", models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = "auth_group_permissions"
        unique_together = (("group", "permission"),)


class AuthPermission(models.Model):
    name = models.CharField(max_length=255, blank=True, null=True)
    content_type = models.ForeignKey("DjangoContentType", models.DO_NOTHING)
    codename = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        managed = False
        db_table = "auth_permission"
        unique_together = (("content_type", "codename"),)


class AuthUser(models.Model):
    password = models.CharField(max_length=128, blank=True, null=True)
    last_login = models.DateTimeField(blank=True, null=True)
    is_superuser = models.BooleanField()
    username = models.CharField(unique=True, max_length=150, blank=True, null=True)
    first_name = models.CharField(max_length=150, blank=True, null=True)
    last_name = models.CharField(max_length=150, blank=True, null=True)
    email = models.CharField(max_length=254, blank=True, null=True)
    is_staff = models.BooleanField()
    is_active = models.BooleanField()
    date_joined = models.DateTimeField()

    class Meta:
        managed = False
        db_table = "auth_user"


class AuthUserGroups(models.Model):
    user = models.ForeignKey(AuthUser, models.DO_NOTHING)
    group = models.ForeignKey(AuthGroup, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = "auth_user_groups"
        unique_together = (("user", "group"),)


class AuthUserUserPermissions(models.Model):
    user = models.ForeignKey(AuthUser, models.DO_NOTHING)
    permission = models.ForeignKey(AuthPermission, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = "auth_user_user_permissions"
        unique_together = (("user", "permission"),)


class DjangoAdminLog(models.Model):
    action_time = models.DateTimeField()
    object_id = models.TextField(blank=True, null=True)
    object_repr = models.CharField(max_length=200, blank=True, null=True)
    action_flag = models.IntegerField()
    change_message = models.TextField(blank=True, null=True)
    content_type = models.ForeignKey(
        "DjangoContentType", models.DO_NOTHING, blank=True, null=True
    )
    user = models.ForeignKey(AuthUser, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = "django_admin_log"


class DjangoContentType(models.Model):
    app_label = models.CharField(max_length=100, blank=True, null=True)
    model = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        managed = False
        db_table = "django_content_type"
        unique_together = (("app_label", "model"),)


class DjangoMigrations(models.Model):
    app = models.CharField(max_length=255, blank=True, null=True)
    name = models.CharField(max_length=255, blank=True, null=True)
    applied = models.DateTimeField()

    class Meta:
        managed = False
        db_table = "django_migrations"


class DjangoSession(models.Model):
    session_key = models.CharField(primary_key=True, max_length=40)
    session_data = models.TextField(blank=True, null=True)
    expire_date = models.DateTimeField()

    class Meta:
        managed = False
        db_table = "django_session"


"""
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
"""


class Info(models.Model):
    id = models.BigIntegerField(primary_key=True)
    checksum = models.CharField(max_length=50, blank=True, null=True)
    date_updated = models.DateField(blank=True, null=True)
    poznamka = models.CharField(max_length=200, blank=True, null=True)
    aktualnost = models.BigIntegerField(blank=True, null=True)
    chybi_pocet = models.BigIntegerField()
    chybi_pole = models.CharField(max_length=1000, blank=True, null=True)
    zmena_link_pocet = models.BigIntegerField(blank=True, null=True)
    zmena_link_pole = models.CharField(max_length=1000, blank=True, null=True)
    odstranit_pocet = models.BigIntegerField(blank=True, null=True)
    odstranit_pole = models.CharField(max_length=1000, blank=True, null=True)
    celk_zmen = models.BigIntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = "info"


"""
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


class Okres(models.Model):
    id_okres = models.BigIntegerField(primary_key=True)
    kraj_id_kraj = models.CharField(max_length=20, blank=True, null=True)
    nazev_okres = models.CharField(max_length=60, blank=True, null=True)
    nuts3_id_nuts = models.CharField(max_length=20, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'okres'


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


class OpOkres(models.Model):
    okres_id_okres = models.BigIntegerField(primary_key=True)
    kraj_id_kraj = models.BigIntegerField()
    nuts3_id_nuts = models.BigIntegerField()
    opatreni_id_opatreni = models.BigIntegerField()

    class Meta:
        managed = False
        db_table = 'op_okres'
        unique_together = (('okres_id_okres', 'nuts3_id_nuts', 'kraj_id_kraj', 'opatreni_id_opatreni'),)


class OpOm(models.Model):
    opatreni_id_opatreni = models.OneToOneField('Opatreni', models.DO_NOTHING, db_column='opatreni_id_opatreni', primary_key=True)
    obecmesto_id_obecmesto = models.ForeignKey(Obecmesto, models.DO_NOTHING, db_column='obecmesto_id_obecmesto')
    obecmesto_nuts3_id_nuts = models.ForeignKey(Obecmesto, models.DO_NOTHING, db_column='obecmesto_nuts3_id_nuts')
    obecmesto_nuts3_kraj_id_kraj = models.ForeignKey(Obecmesto, models.DO_NOTHING, db_column='obecmesto_nuts3_kraj_id_kraj')

    class Meta:
        managed = False
        db_table = 'op_om'
        unique_together = (('opatreni_id_opatreni', 'obecmesto_id_obecmesto', 'obecmesto_nuts3_id_nuts', 'obecmesto_nuts3_kraj_id_kraj'),)


class OpStat(models.Model):
    id_opatreni = models.BigIntegerField()

    class Meta:
        managed = False
        db_table = 'op_stat'


class Opatreni(models.Model):
    id_opatreni = models.BigIntegerField(primary_key=True)
    nazev_opatreni = models.CharField(max_length=200)
    platnost_od = models.DateField()
    je_platne = models.BigIntegerField()
    zdroj = models.CharField(max_length=500)
    nazev_zkr = models.CharField(max_length=150, blank=True, null=True)
    rozsah = models.CharField(max_length=20, blank=True, null=True)
    platnost_do = models.DateField(blank=True, null=True)
    zdroj_autooprava = models.CharField(max_length=500, blank=True, null=True)
    priorita = models.BigIntegerField()
    identifikator = models.CharField(max_length=50, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'opatreni'


class Polozka(models.Model):
    id_polozka = models.BigIntegerField(primary_key=True)
    nazev = models.CharField(max_length=60)
    komentar = models.CharField(max_length=2000, blank=True, null=True)
    kategorie_id_kategorie = models.ForeignKey(Kategorie, models.DO_NOTHING, db_column='kategorie_id_kategorie')
    typ = models.CharField(max_length=20, blank=True, null=True)
    opatreni_id_opatreni = models.ForeignKey(Opatreni, models.DO_NOTHING, db_column='opatreni_id_opatreni')
    vyjimka = models.CharField(max_length=800, blank=True, null=True)
    extra_link = models.CharField(max_length=500, blank=True, null=True)
    extra_popis = models.CharField(max_length=160, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'polozka'
        unique_together = (('id_polozka', 'kategorie_id_kategorie', 'opatreni_id_opatreni'),)
"""

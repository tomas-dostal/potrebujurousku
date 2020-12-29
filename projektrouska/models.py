# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
import datetime

from django.db import models


class AuthGroup(models.Model):
    name = models.CharField(unique=True, max_length=150, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'auth_group'


class AuthGroupPermissions(models.Model):
    group = models.ForeignKey(AuthGroup, models.DO_NOTHING)
    permission = models.ForeignKey('AuthPermission', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'auth_group_permissions'
        unique_together = (('group', 'permission'),)


class AuthPermission(models.Model):
    name = models.CharField(max_length=255, blank=True, null=True)
    content_type = models.ForeignKey('DjangoContentType', models.DO_NOTHING)
    codename = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'auth_permission'
        unique_together = (('content_type', 'codename'),)


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
        db_table = 'auth_user'


class AuthUserGroups(models.Model):
    user = models.ForeignKey(AuthUser, models.DO_NOTHING)
    group = models.ForeignKey(AuthGroup, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'auth_user_groups'
        unique_together = (('user', 'group'),)


class AuthUserUserPermissions(models.Model):
    user = models.ForeignKey(AuthUser, models.DO_NOTHING)
    permission = models.ForeignKey(AuthPermission, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'auth_user_user_permissions'
        unique_together = (('user', 'permission'),)


class DjangoAdminLog(models.Model):
    action_time = models.DateTimeField()
    object_id = models.TextField(blank=True, null=True)
    object_repr = models.CharField(max_length=200, blank=True, null=True)
    action_flag = models.IntegerField()
    change_message = models.TextField(blank=True, null=True)
    content_type = models.ForeignKey('DjangoContentType', models.DO_NOTHING, blank=True, null=True)
    user = models.ForeignKey(AuthUser, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'django_admin_log'


class DjangoContentType(models.Model):
    app_label = models.CharField(max_length=100, blank=True, null=True)
    model = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'django_content_type'
        unique_together = (('app_label', 'model'),)


class DjangoMigrations(models.Model):
    app = models.CharField(max_length=255, blank=True, null=True)
    name = models.CharField(max_length=255, blank=True, null=True)
    applied = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'django_migrations'


class DjangoSession(models.Model):
    session_key = models.CharField(primary_key=True, max_length=40)
    session_data = models.TextField(blank=True, null=True)
    expire_date = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'django_session'


# regional parts database
# https://cs.wikipedia.org/wiki/CZ-NUTS
# State (Czech Republic)
# \- Region (Moravskoslezský District)
#   \- NUTS (Bruntál)
#     \- City (Vrbno pod Pradědem) # city or village or whatever


"""
class Cast(models.Model):
    id_cast = models.BigIntegerField(primary_key=True)
    nazev_cast = models.CharField(max_length=50)
    obecmesto_id_obecmesto = models.ForeignKey('projektrouska.models.City', models.DO_NOTHING, db_column='obecmesto_id_obecmesto')
    obecmesto_nuts3_id_nuts = models.ForeignKey('projektrouska.models.City', models.DO_NOTHING, db_column='obecmesto_nuts3_id_nuts')
    obecmesto_nuts3_kraj_id_kraj = models.ForeignKey('projektrouska.models.City', models.DO_NOTHING, db_column='obecmesto_nuts3_kraj_id_kraj')

    class Meta:
        managed = False
        db_table = 'cast'
        unique_together = (('id_cast', 'obecmesto_id_obecmesto', 'obecmesto_nuts3_id_nuts', 'obecmesto_nuts3_kraj_id_kraj'),)
"""

# import order
# 1) state
# 2) region
# 3) nuts4
# 4) district
# 5) city

# State
class State(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=40)

    class Meta:
        db_table = 'state'

    def __str__(self):
        return self.name

# Kraj
class Region(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=25)

    code_index = models.IntegerField(blank=True, null=True)
    state = models.ForeignKey(State, on_delete=models.CASCADE)

    class Meta:
        db_table = 'region'
        unique_together = (('id', 'state'),)

    def __str__(self):
        return self.name

# nuts4, something like a part of Region that contains Districts
class Nuts4(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=50)

    code_index = models.BigIntegerField(blank=True, null=True)  # another code WTF
    code = models.CharField(max_length=50, null=True)  # CZ032

    # Foreign keys
    region = models.ForeignKey(Region, on_delete=models.CASCADE)
    state = models.ForeignKey(State, on_delete=models.CASCADE)

    class Meta:
        db_table = 'nuts4'
        unique_together = (('id', 'region', 'state'))

    def __str__(self):
        return self.name
# okres
class District(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=60, blank=True, null=True)
    code = models.CharField(max_length=50, null=True)

    # Foreign keys
    nuts4 = models.ForeignKey(Nuts4, on_delete=models.CASCADE)
    region = models.ForeignKey(Region, on_delete=models.CASCADE)
    state = models.ForeignKey(State, on_delete=models.CASCADE)

    class Meta:
        db_table = 'district'
        unique_together = (('id', 'nuts4', 'region', 'state'),)

    def __str__(self):
        return self.name

# obecmesto
class City(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=50)
    code = models.CharField(max_length=50, null=True)

    # Foreign keys
    district = models.ForeignKey(District, on_delete=models.CASCADE)
    nuts4 = models.ForeignKey(Nuts4, on_delete=models.CASCADE)
    region = models.ForeignKey(Region, on_delete=models.CASCADE)
    state = models.ForeignKey(State, on_delete=models.CASCADE)

    class Meta:
        db_table = 'city'
        unique_together = (('id', 'nuts4', 'district', 'region', 'state'),)

    def __str__(self):
        return self.name

# stores data from Update check
class UpdateLogs(models.Model):
    id = models.AutoField(primary_key=True)

    checksum = models.CharField(max_length=50, blank=False, null=True)
    date_updated = models.DateTimeField(default=datetime.datetime.now,  blank=False, null=False)

    comment = models.TextField(blank=True, null=True)

    up_to_date_percents = models.IntegerField(blank=True, null=True)

    missing_count = models.IntegerField(blank=True, null=True)
    missing_json = models.TextField(blank=True, null=True)

    change_link_count = models.IntegerField(blank=True, null=True)
    change_link_json = models.TextField(blank=True, null=True)

    outdated_count = models.IntegerField(blank=True, null=True)
    outdated_json = models.TextField(blank=True, null=True)

    total_changes = models.IntegerField(blank=True, null=True)

    class Meta:
        db_table = 'update_logs'

    def __str__(self):
        return str(self.id) + "_" + self.checksum
class ExternalContent(models.Model):
    id = models.AutoField(primary_key=True)

    date_inserted = models.DateTimeField(default=datetime.datetime.now,  blank=False, null=False)
    date_modified = models.DateTimeField(blank=True, null=True)

    GENERAL = 'URL'
    PDF = 'PDF'
    IMAGE = 'IMG'
    VIDEO = 'VID'

    TYPES = [
        (GENERAL, 'URL link to general content'),
        (PDF, 'URL link to PDF'),
        (IMAGE, 'URL link to IMAGE'),
        (VIDEO, 'URL link VIDEO'),
    ]

    #
    content_type = models.CharField(
        max_length=3,
        choices=TYPES,
        default=GENERAL,
    )

    NEW = 'NEW'
    REVISION = 'REV'

    STATUS = [
        (NEW, 'Brand new content, never changed'),
        (REVISION, 'URL link to PDF'),
        (IMAGE, 'URL link to IMAGE'),
        (VIDEO, 'URL link VIDEO'),
    ]

    # do you want to create a preview of content (if available)
    preview = models.BooleanField()

    # locally stored thumbnail of the content
    img_thumbnail = models.URLField( blank=True, null=True)

    # url to external file/content/site/whatever
    url_external = models.URLField()

    # local copy of the content
    url_local_copy = models.URLField(blank=True, null=True)
    # MD5 hash of local copy - to be able to detect changes
    content_hash = models.CharField(max_length=50, blank=True, null=True)

    # it might be very usefull to implement somehting like linked list of all previos versions
    #previous_version = models.OneToOneField(ExternalContent)
    class Meta:
        db_table = 'external_content'

    def __str__(self):
        return str(self.id) + "_" + self.content_type
class Cathegory(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=50)
    fa_icon = models.CharField(max_length=50)

    # Cathegories are ordered by priority
    priority = models.IntegerField()

    class Meta:
        db_table = 'cathegory'

    def __str__(self):
        return self.name

class Parts(models.Model):
    id = models.AutoField(primary_key=True)

    name = models.CharField(max_length=100)
    content = models.TextField(blank=True, null=True)

    # is there anyonw who does not need to fullfill this part of Precaution
    exceptions = models.TextField(blank=True, null=True)

    cathegory = models.ForeignKey(Cathegory, null=True,  on_delete=models.CASCADE)

    INFORMATION = 'info'
    RECOMMENDATION = 'warning'
    REGULATION = 'danger'
    EMERGENCY = 'black'

    TYPES = [
        (INFORMATION, 'Information, not requiered to be complienced'),
        (RECOMMENDATION, 'Recommendation, not requiered to be complienced'),
        (REGULATION, 'Regulation, requiered to be complienced'),
        (EMERGENCY, 'Emergency regulation, requiered to be complienced'),
    ]

    # bootstrap modal colors are generated based on this choice
    type = models.CharField(
        max_length=15,
        choices=TYPES,
        default=REGULATION,
    )

    SMALL = 'modal-sm'
    MEDIUM = 'modal-md'
    LARGE = 'modal-lg'

    MODALS = [
        (SMALL, 'Small'),
        (MEDIUM, 'Medium'),
        (LARGE, 'Large'),
    ]
    # bootstrap modals are generated based on this choice
    modal_size = models.CharField(
        max_length=15,
        choices=MODALS,
        default=MEDIUM,
    )
    # one to many
    external_contents = models.ForeignKey(ExternalContent, null=True, on_delete=models.CASCADE)

    icon = models.CharField(max_length=40, blank=True, null=True)

    created_date = models.DateTimeField(auto_now_add=True)
    modified_date = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'part'
        #unique_together = (('id', 'precaution'),)

    def __str__(self):
        return "ID={}_{}".format(self.id, self.name[:100])


# Opatření
class Precaution(models.Model):
    id = models.AutoField(primary_key=True)

    code_identificator = models.CharField(max_length=50, blank=True, null=True)

    full_name = models.CharField(max_length=400)
    short_name = models.CharField(max_length=400, blank=True, null=True)

    # it might be null because auto control can not find date
    valid_from = models.DateTimeField(blank=True, null=True)
    valid_to = models.DateTimeField(blank=True, null=True)

    # source URLs and all related images, pdfs and whatever moved here
    external_contents = models.ManyToManyField(ExternalContent)

    # Precautions are usually divided into several parts.
    # It is divided here for better orientation. Also, when precautions change, parts are usually just slightly modified.
    parts = models.ManyToManyField(Parts)

    # life_situations = models.ManyToManyField(LifeSituations)

    ENABLED_AUTO = 1
    DISABLED_AUTO = 0
    FORCE_ENABLE = 3
    FORCE_DISABLE = -1
    CHECK_REQUIRED = 2
    MAINTENANCE_IN_PROGRESS = -2

    STATUS_CHOICES = [
        (ENABLED_AUTO, 'Active (auto)'),
        (DISABLED_AUTO, 'Disabled (auto)'),
        (FORCE_ENABLE, 'Active (force)'),
        (FORCE_DISABLE, 'Disabled (force)'),
        (CHECK_REQUIRED, 'Active (check required)'),
        (MAINTENANCE_IN_PROGRESS, 'Disabled (maintenance in progress)'),
    ]
    # former "je_platne"
    status = models.IntegerField(
        choices=STATUS_CHOICES,
        default=ENABLED_AUTO,
    )

    NOT_FILLED = -1  # used when mass imported
    REDUNDANT = 0
    MIGHT_BE_USEFUL = 1
    GOOD_TO_KNOW = 10
    NEED_TO_KNOW = 100
    EXTREMELY_IMPORTANT = 1000

    PRIORITY_CHOICES = [
        (NOT_FILLED, 'Not filled'),
        (REDUNDANT, 'Redundant (it is here just to auto-check to be satisfied)'),
        (MIGHT_BE_USEFUL, 'It might be useful'),
        (GOOD_TO_KNOW, 'Slightly important information, good to know'),
        (NEED_TO_KNOW, 'Important information, have to know'),
        (EXTREMELY_IMPORTANT, 'Extremely important'),
    ]

    # former "je_platne"
    priority = models.IntegerField(
        choices=PRIORITY_CHOICES,
        default=NOT_FILLED,
    )

    state = models.ManyToManyField(State)
    region = models.ManyToManyField(Region)
    nuts4 = models.ManyToManyField(Nuts4)
    district = models.ManyToManyField(District)
    city = models.ManyToManyField(City)

    created_date = models.DateTimeField(auto_now_add=True)
    modified_date = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'precaution'
        #unique_together = (('id', 'parts'),)

    def __str__(self):
        return "ID={}_{}".format(self.id, self.short_name[:100])

class PES_general(models.Model):
    degree = models.AutoField(primary_key=True)
    min_value = models.IntegerField()
    max_value = models.IntegerField()
    description = models.TextField()

    color = models.CharField(max_length=10)

    parts = models.ManyToManyField(Parts)

    external_contents = models.ForeignKey(ExternalContent, on_delete=models.CASCADE)

    class Meta:
        db_table = 'pes_general'

    def __str__(self):
        return self.degree
class PES_history(models.Model):
    id = models.AutoField(primary_key=True)

    date_from = models.DateTimeField()
    date_to = models.DateTimeField(blank=True, null=True)

    # current index in selected region/country
    index = models.IntegerField()

    pes_general = models.ForeignKey(PES_general,  on_delete=models.CASCADE)

    state = models.ForeignKey(State, on_delete=models.CASCADE)
    region = models.ForeignKey(Region, on_delete=models.CASCADE)

    precautions = models.ManyToManyField(Precaution)

    class Meta:
        db_table = 'pes_history'



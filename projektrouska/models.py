import datetime
from django.db import models
from pytz import utc


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
    username = models.CharField(
        unique=True,
        max_length=150,
        blank=True,
        null=True)
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
    content_type = models.ForeignKey(
        'DjangoContentType',
        models.DO_NOTHING,
        blank=True,
        null=True)
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


# import order
# 1) state
# 2) region
# 3) nuts4
# 4) district
# 5) city

# precaution
# parts

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

    def all_regional_precautions(self):
        return self.precaution_set.all()

    def belongs_to(self, target: State) -> bool:
        return self.state == target


# okres
class District(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=60, blank=True, null=True)
    code = models.CharField(max_length=50, null=True)

    # Foreign keys
    nuts4 = models.ForeignKey('Nuts4', on_delete=models.CASCADE)
    region = models.ForeignKey(Region, on_delete=models.CASCADE)
    state = models.ForeignKey(State, on_delete=models.CASCADE)

    class Meta:
        db_table = 'district'
        unique_together = (('id', 'nuts4', 'region', 'state'),)

    def __str__(self):
        return self.name

    def belongs_to(self, target: State) -> bool:
        return self.region.belongs_to(State)


# nuts4, something like a part of Region that contains Districts
class Nuts4(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=50)

    code_index = models.BigIntegerField(
        blank=True, null=True)  # another code WTF
    code = models.CharField(max_length=50, null=True)  # CZ032

    # Foreign keys
    region = models.ForeignKey(Region, on_delete=models.CASCADE)
    state = models.ForeignKey(State, on_delete=models.CASCADE)

    class Meta:
        db_table = 'nuts4'
        unique_together = (('id', 'region', 'state'))

    def __str__(self):
        return self.name

    def belongs_to(self, target: District) -> bool:
        return target in self.district_set.all()


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

    def belongs_to(self, target: Nuts4) -> bool:
        return target == self.nuts4


# stores data from Update check
class UpdateLogs(models.Model):
    id = models.AutoField(primary_key=True)

    checksum = models.CharField(max_length=50, blank=False, null=True)
    date_updated = models.DateTimeField(
        default=datetime.datetime.now, blank=False, null=False)

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

    date_inserted = models.DateTimeField(
        default=datetime.datetime.now, blank=False, null=False)
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
    img_thumbnail = models.URLField(blank=True, null=True)

    # url to external file/content/site/whatever
    url_external = models.TextField()

    # local copy of the content
    url_local_copy = models.URLField(blank=True, null=True)
    # MD5 hash of local copy - to be able to detect changes
    content_hash = models.CharField(max_length=50, blank=True, null=True)

    # it might be very usefull to implement somehting like linked
    # list of all previos versions
    # previous_version = models.OneToOneField(ExternalContent)
    class Meta:
        db_table = 'external_content'

    def __str__(self):
        return str(self.id) + "_" + self.content_type


class Category(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=50)
    fa_icon = models.CharField(max_length=50)

    # Cathegories are ordered by priority
    priority = models.IntegerField()

    class Meta:
        db_table = 'category'

    def __str__(self):
        return self.name

    def get_precautions(self, active=False):
        return [p.get_parents(active_only=active)
                for p in self.parts_set.all()]

    def get_parts(self):
        return self.parts_set.all()


class Parts(models.Model):
    id = models.AutoField(primary_key=True)

    name = models.CharField(max_length=100)
    content = models.TextField(blank=True, null=True)

    # is there anyonw who does not need to fullfill this part of Precaution
    exceptions = models.TextField(blank=True, null=True)

    category = models.ForeignKey(Category, null=True, on_delete=models.CASCADE)

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
    # many to many
    external_contents = models.ManyToManyField(ExternalContent)

    icon = models.CharField(max_length=40, blank=True, null=True)

    created_date = models.DateTimeField(
        auto_now_add=True, blank=True, null=True)
    modified_date = models.DateTimeField(auto_now=True, blank=True, null=True)

    class Meta:
        db_table = 'part'
        # unique_together = (('id', 'precaution'),)

    def __str__(self):
        return "ID={}_{}".format(self.id, self.name[:100])

    def get_parents(self, active_only=False):
        if active_only:
            return self.precaution_set.all().filter(
                valid_from__lte=datetime.datetime.now(),
                valid_to__gte=datetime.datetime.now(),
                status__gt=0)
        return self.precaution_set.all()

    def get_category(self):
        return "%s" % self.category.name

    def get_external(self):
        return self.external_contents.all()

    def get_thumbnail_if_exists(self):
        thumbnails = self.external_contents.filter(
            img_thumbnail__isnull=False).all()
        if thumbnails.count() > 0:
            return thumbnails[0].img_thumbnail
        return


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
    # It is divided here for better orientation. Also, when precautions change,
    # parts are usually just slightly modified.
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
        default=CHECK_REQUIRED,
    )

    NOT_FILLED = -1  # used when mass imported
    REDUNDANT = 0
    MIGHT_BE_USEFUL = 1
    GOOD_TO_KNOW = 10
    NEED_TO_KNOW = 100
    EXTREMELY_IMPORTANT = 1000

    PRIORITY_CHOICES = [
        (NOT_FILLED, 'Not filled'),
        (REDUNDANT, 'Redundant (it is here just for auto-check)'),
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

    created_date = models.DateTimeField(
        auto_now_add=True, blank=True, null=True)
    modified_date = models.DateTimeField(auto_now=True, blank=True, null=True)

    class Meta:
        db_table = 'precaution'

    def __str__(self):
        return "ID={}_{}".format(self.id, self.short_name[:100])

    def get_parts(self):
        return self.parts.all()

    def get_locations_where_valid(self):
        """
        :return: Set of all places where precaution is active.
        Not recursive - if valid e.g. in Prague region and
        Moravskoslezský region, it return just those two regions,
        nothing "smaller"
        """
        tmp = list(self.state.all()) + list(self.region.all()) \
              + list(self.district.all()) + list(self.city.all()) \
              + list(self.nuts4.all())
        return tmp

    def is_active(self, now=datetime.datetime.now(), days_to_future=0):
        now = now.replace(tzinfo=utc)
        display_within = (
                now +
                datetime.timedelta(
                    days=days_to_future)).replace(
            tzinfo=utc)
        return self.status > 0 and self.valid_from <= display_within and self.valid_to and self.valid_to >= now

    # okay, it was a nice try to spicify data types etc. Python does not seems
    # to care.
    def is_valid_here(self, re: Region) -> bool:
        if (isinstance(re, Region)):
            return re in self.region.all()
        elif (isinstance(re, State)):
            return re in self.state.all()
        # todo


class PES_general(models.Model):
    degree = models.AutoField(primary_key=True)
    min_value = models.IntegerField()
    max_value = models.IntegerField()
    description = models.TextField()

    color = models.CharField(max_length=10)

    parts = models.ManyToManyField(Parts)

    external_contents = models.ForeignKey(
        ExternalContent, on_delete=models.CASCADE)

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
    pes_general = models.ForeignKey(PES_general, on_delete=models.CASCADE)

    state = models.ForeignKey(State, on_delete=models.CASCADE)
    region = models.ForeignKey(Region, on_delete=models.CASCADE)

    precautions = models.ManyToManyField(Precaution)

    class Meta:
        db_table = 'pes_history'

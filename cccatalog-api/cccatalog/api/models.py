from uuslug import uuslug
from django.db import models
from django.utils.safestring import mark_safe
from django.contrib.postgres.fields import JSONField, ArrayField


class OpenLedgerModel(models.Model):
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)

    def __iter__(self):
        for field_name in self._meta.get_fields():
            value = getattr(self, field_name, None)
            yield (field_name, value)

    class Meta:
        abstract = True


class Image(OpenLedgerModel):
    identifier = models.UUIDField(
        unique=True,
        db_index=True,
        help_text="A unique identifier that we assign on ingestion."
    )

    provider = models.CharField(
        max_length=80,
        blank=True,
        null=True,
        db_index=True,
        help_text="The content provider, e.g. Flickr, 500px...")

    source = models.CharField(
        max_length=80,
        blank=True,
        null=True,
        db_index=True,
        help_text="The source of the data, meaning a particular dataset. Source"
                  " and provider can be different: the Google Open Images "
                  "dataset is source=openimages., but provider=Flickr."
    )

    foreign_identifier = models.CharField(
        unique=True,
        max_length=1000,
        blank=True,
        null=True,
        db_index=True,
        help_text="The identifier provided by the upstream source."
    )

    foreign_landing_url = models.CharField(
        max_length=1000,
        blank=True,
        null=True,
        help_text="The landing page of the work."
    )

    url = models.URLField(
        unique=True,
        max_length=1000,
        help_text="The actual URL to the image."
    )

    thumbnail = models.URLField(
        max_length=1000,
        blank=True,
        null=True,
        help_text="The thumbnail for the image, if any."
    )

    width = models.IntegerField(blank=True, null=True)
    height = models.IntegerField(blank=True, null=True)

    filesize = models.IntegerField(blank=True, null=True)

    license = models.CharField(max_length=50)

    license_version = models.CharField(max_length=25, blank=True, null=True)

    creator = models.CharField(max_length=2000, blank=True, null=True)

    creator_url = models.URLField(max_length=2000, blank=True, null=True)

    title = models.CharField(max_length=2000, blank=True, null=True)

    tags = JSONField(blank=True, null=True)

    last_synced_with_source = models.DateTimeField(
        blank=True,
        null=True,
        db_index=True
    )

    removed_from_source = models.BooleanField(default=False)

    meta_data = JSONField(blank=True, null=True)

    view_count = models.IntegerField(default=0)

    watermarked = models.NullBooleanField(blank=True, null=True)

    def image_tag(self):
        return mark_safe('<img src="%s" width="150" />' % self.url)

    image_tag.short_description = 'Image'

    class Meta:
        db_table = 'image'
        ordering = ['-created_on']


class ContentProvider(models.Model):
    provider_identifier = models.CharField(max_length=50)
    provider_name = models.CharField(max_length=250, unique=True)
    created_on = models.DateTimeField(auto_now=False)
    domain_name = models.CharField(max_length=500)
    filter_content = models.BooleanField(null=False, default=False)
    notes = models.TextField(null=True)

    class Meta:
        db_table = 'content_provider'


class ImageTags(OpenLedgerModel):
    tag = models.ForeignKey(
        'Tag',
        on_delete=models.CASCADE,
        blank=True,
        null=True
    )
    image = models.ForeignKey(Image, on_delete=models.CASCADE, null=True)

    class Meta:
        unique_together = ('tag', 'image')
        db_table = 'image_tags'


class ImageList(OpenLedgerModel):
    title = models.CharField(max_length=2000, help_text="Display name")
    images = models.ManyToManyField(
        Image,
        related_name="lists",
        help_text="A list of identifier keys corresponding to images."
    )
    slug = models.CharField(
        max_length=200,
        help_text="A unique identifier used to make a friendly URL for "
                  "downstream API consumers.",
        unique=True,
        db_index=True
    )
    auth = models.CharField(
        max_length=64,
        help_text="A randomly generated string assigned upon list creation. "
                  "Used to authenticate updates and deletions."
    )

    class Meta:
        db_table = 'imagelist'

    def save(self, *args, **kwargs):
        self.slug = uuslug(self.title, instance=self)
        super(ImageList, self).save(*args, **kwargs)


class Tag(OpenLedgerModel):
    foreign_identifier = models.CharField(max_length=255, blank=True, null=True)
    name = models.CharField(max_length=1000, blank=True, null=True)
    # Source can be a provider/source (like 'openimages', or 'user')
    source = models.CharField(max_length=255, blank=True, null=True)
    slug = models.SlugField(blank=True, null=True, max_length=255)

    class Meta:
        db_table = 'tag'


class ShortenedLink(OpenLedgerModel):
    shortened_path = models.CharField(
        unique=True,
        max_length=10,
        help_text="The path to the shortened URL, e.g. tc3n834. The resulting "
                  "URL will be shares.cc/tc3n834.",
        db_index=True
    )
    full_url = models.URLField(unique=True, max_length=1000, db_index=True)
    created_on = models.DateTimeField(auto_now_add=True, db_index=True)

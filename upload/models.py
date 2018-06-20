from django.core.validators import RegexValidator
from django.utils import timezone
from django.db import models
import os

from .utils import get_zip_upload_path, validate_file_field
from .utils import get_image_upload_path, get_segmentation_plot_file_path
from .utils import get_segmentation_fixed_image_path, get_segmentation_plot_image_path


class Language(models.Model):
    """Model for language."""
    code = models.CharField(max_length=20)
    name = models.CharField(max_length=20, default='English')
    postprocessing_enabled = models.BooleanField(default=False)
    dict_file = models.CharField(max_length=255, blank=True)
    vocab_file = models.CharField(max_length=255, blank=True)
    editors = models.ManyToManyField('auth.User', related_name='languages')

    class Meta:
        ordering = ['code']

    def __str__(self):
        return self.name


class BookTag(models.Model):
    """Book Tag model."""
    tag = models.CharField(max_length=20)

    class Meta:
        verbose_name = 'Book Tag'

    def __str__(self):
        return self.tag


class Book(models.Model):
    """Storing books in the database."""
    code = models.CharField(max_length=20, default='')
    title = models.CharField(max_length=255, default='')
    author = models.CharField(max_length=255, blank=True)
    zip_file = models.FileField(upload_to=get_zip_upload_path, blank=True, max_length=500, validators=[validate_file_field])
    language = models.ForeignKey(Language, default=1)
    year = models.CharField(max_length=4, blank=True,
                            validators=[RegexValidator(regex=r'^\d{4}$',
                                        message='Enter 4 digit year.')])
    tags = models.ManyToManyField(BookTag, blank=True)
    details = models.CharField('Additional Info', max_length=2048, blank=True, null=True)
    created = models.DateTimeField(default=timezone.now)
    modified = models.DateTimeField(default=timezone.now)
    is_audio_required = models.BooleanField(default=False)
    completed = models.BooleanField(default=False)
    daisy_xml = models.TextField(blank=True)

    class Meta:
        ordering = ['-created']

    def get_display_name(self):
        return ' '.join(self.title.split("_"))

    def __str__(self):
        return '%s' % (self.title)


class AudioBook(models.Model):
    """Audio book model."""
    username = models.ForeignKey('auth.User', null=True)    # userid
    download_url = models.CharField(max_length=100)     # generate path based on op dir + bookname_bookid + filename.mp3
    book = models.ForeignKey(Book)   # bookid
    created = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-created']

    def split(self):
        return [x.strip() for x in self.download_url.split(',')]

    def __str__(self):
        return '%s' % (self.book.__str__())


class Upload(models.Model):
    """Uploaded Images."""
    STATUS_CHOICES = (
        ('', ''),
        ('new', 'New'),
        ('segmented', 'Segmented'),
        ('queued', 'Queued for manual fix'),
        ('fixed', 'Manually fixed'),
        ('processed', 'Processed (OCR + PP)'),
        ('corrected', 'Corrected'),
        ('unusable', 'Unusable')
    )
    image = models.FileField(upload_to=get_image_upload_path)
    xmldata = models.TextField(blank=True)
    language = models.ForeignKey(Language, default=1)
    book = models.ForeignKey(Book, default=1)
    page_number = models.PositiveSmallIntegerField(null=True)
    created = models.DateTimeField(default=timezone.now)
    modified = models.DateTimeField(default=timezone.now)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='new')
    processed = models.BooleanField(default=False)

    def __str__(self):
        return str(os.path.split(self.image.name)[-1].split('_', 1)[-1])


class SegmentationResult(models.Model):
    """Model to store Segmentation Results."""
    image = models.OneToOneField(Upload)
    manually_fixed = models.BooleanField(default=False)
    fixed_image = models.ImageField(upload_to=get_segmentation_fixed_image_path,
                                    null=True)
    segmentation_plot_file = models.FileField(upload_to=get_segmentation_plot_file_path, null=True)
    segmentation_plot_image = models.ImageField(
        upload_to=get_segmentation_plot_image_path, null=True)
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)


class OCRResult(models.Model):
    """Results for the OCR."""
    image = models.OneToOneField(Upload)
    result = models.TextField(verbose_name='Recognized Text', blank=True)
    start_time = models.DateTimeField()
    finish_time = models.DateTimeField()
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)
    corrected = models.BooleanField(default=False)
    check_out = models.BooleanField(default=False)
    check_out_by = models.ForeignKey('auth.User', null=True)
    check_out_time = models.DateTimeField(null=True)

    class Meta:
        verbose_name = 'OCR Result'

    def __str__(self):
        return self.image.__str__()


class ErrorWord(models.Model):
    """Error words."""
    ocr_result = models.ForeignKey(OCRResult)
    word = models.CharField(max_length=255)
    corrected = models.CharField(max_length=255)
    suggestion_number = models.PositiveSmallIntegerField(null=True)
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Error Word'

    def __str__(self):
        return self.word.strip()


class ErrorWordSuggestion(models.Model):
    """Suggestions for the Error words."""
    error_word = models.ForeignKey(ErrorWord)
    suggestion = models.CharField(max_length=255)
    suggestion_number = models.PositiveSmallIntegerField()
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Error Word Suggestion'

    def __str__(self):
        return self.suggestion.strip()


class CorrectedResult(models.Model):
    ocr_result = models.OneToOneField(OCRResult)
    result = models.TextField(verbose_name='Corrected Text', blank=True)
    editor = models.ForeignKey('auth.User')
    check_out_time = models.DateTimeField()
    check_in_time = models.DateTimeField()
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Corrected Result'

    def __str__(self):
        return self.ocr_result.__str__()


class Accuracy(models.Model):
    corrected_result = models.OneToOneField(CorrectedResult)
    word_accuracy = models.DecimalField(max_digits=5, decimal_places=2, null=True)
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

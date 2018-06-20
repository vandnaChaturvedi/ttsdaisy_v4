"""Forms for uploading."""
from django.forms import ModelForm

from .models import Book, Upload


class AddBookForm(ModelForm):
    """Form to add new book in zip."""
    class Meta:
        model = Book
        fields = ["zip_file", "title", "language", "author", "tags", "is_audio_required"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["is_audio_required"].label = "Is Audio book required"


class AddPageForm(ModelForm):
    """Form to add a single page book image."""
    class Meta:
        model = Upload
        fields = ["image", "language", "book"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class SinglePageBookForm(ModelForm):
    """Form to add a singel page."""
    class Meta:
        model = Upload
        fields = ["image", "language"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

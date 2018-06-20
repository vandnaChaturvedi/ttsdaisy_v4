"""Filter."""
from upload.models import Page
import django_filters


class BookFilter(django_filters.FilterSet):
    """Book filter."""
    class Meta:
        model = Page
        fields = ['book_name', 'text', 'image', ]

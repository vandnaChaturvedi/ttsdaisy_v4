"""Utility functions to perform small checks and operations."""
import random
import os
import datetime
import time

# TODO:
# - file validations
# - functions for file handling


def replace_space_with_underscore(string):
    """Replace space with underscore."""
    return '_'.join(string.split(' '))


def random_alpha_numeric_generator():
    """Random 8 character string."""
    return ''.join(random.choice('0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ') for i in range(8))


def get_current_timestamp():
    """Current time."""
    return datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d_%H%M%S')


def get_zip_upload_path(instance, filename):
    """Get the path of uploaded zip file."""
    print("Zip file uploaded to: `{}`".format(os.path.join('compressed_input', str(instance.language.id),
          str(get_current_timestamp()) + '_' + replace_space_with_underscore(instance.title),
          filename)))
    return os.path.join('compressed_input', str(instance.language.id),
                        str(get_current_timestamp()) + '_' + replace_space_with_underscore(instance.title),
                        filename)


def validate_file_field(value):
    """Incomplete function."""
    pass


def get_segmentation_fixed_image_path(instance, filename):
    """Segment image path."""
    return os.path.join(os.path.dirname(instance.image.image.name),
                        os.path.basename(instance.image.image.name)
                        + '.fixed' + os.path.splitext(filename)[1])


def get_segmentation_plot_file_path(instance, filename):
    """Segment plot file path."""
    return os.path.join(os.path.dirname(instance.image.image.name),
                        os.path.basename(instance.image.image.name)
                        + '.segmentation_plot_file'
                        + os.path.splitext(filename)[1])


def get_segmentation_plot_image_path(instance, filename):
    """Segment plot image path."""
    return os.path.join(os.path.dirname(instance.image.image.name),
                        os.path.basename(instance.image.image.name)
                        + '.segmentation_plot_image'
                        + os.path.splitext(filename)[1])


def get_image_upload_path(instance, filename):
    """Get the path for uploaded image."""
    print(os.path.join('uploaded_images', str(instance.language.name),
                       str(instance.book.id) or
                       random_alpha_numeric_generator() + '_uncatalogued',
                       filename))
    return os.path.join('uploaded_images', str(instance.language.name),
                        str(instance.book.id) or
                        random_alpha_numeric_generator() + '_uncatalogued',
                        filename)

# Redundant function
# def get_segmentation_plot_image_path_1(instance, filename):
#     return os.path.join(os.path.dirname(instance.image.image.name), filename)


def get_page_number(book_name):
    """Get the number of pages."""
    from .models import Upload
    page_number = Upload.objects.filter(book__title__exact=book_name).count() + 1
    return page_number


def single_page_book_id():
    """ID of book with Single Page."""
    from .models import Book
    try:
        id_ = Book.objects.filter(title__exact="Demo").values('id')[0]['id']
    except Exception:
        id_ = -1
    return id_

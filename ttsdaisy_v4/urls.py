from django.conf.urls import url, include
from django.contrib import admin
from . import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    url(r"^admin/", admin.site.urls),
    url(r"^$", views.HomePage.as_view(), name="home"),
    url(r"^accounts/", include("accounts.urls", namespace="accounts")),
    url(r"^accounts/", include("django.contrib.auth.urls")),
    url(r"^thanks/$", views.ThanksPage.as_view(), name="thanks"),

    url(r"^user_home/$", views.UserHomePage.as_view(), name="user_home"),
    url(r"^upload/", include("upload.urls", namespace="uploads")),
    url(r"^edit/(?P<pk>\d+)/$", views.EditorPage.as_view(), name="edit"),
    url(r"^edit/$", views.EditorPage.as_view(), name="editor"),
    url(r"^single_page/(?P<pk>\d+)", views.SingleEditorPage.as_view(), name="single_page"),

    url(r"^download/", views.download, name="download"),
    url(r"^download_success/", views.DownloadSuccess.as_view(), name="download_success"),

    url(r"^view_library/", views.ViewLibrary.as_view(), name="view_library"),
    url(r"^user_home/(?P<pk>\d+)/$", views.BookDetailsView.as_view(), name="book_details"),

    url(r"^api/get_books/", views.get_books, name="get_books"),
    url(r"^api/get_audiobooks/", views.get_audiobooks, name="get_audiobooks"),
    url(r"^api/load_image_and_text/", views.load_image_and_text, name="load_image_and_text"),
    url(r"^api/get_book_id_from_name/", views.get_book_id_from_name, name="get_book_id_from_name"),
    url(r"^api/get_audiobook_id_from_name/", views.get_audiobook_id_from_name, name="get_audiobook_id_from_name"),
    url(r"^api/save_audio_to_db/", views.save_audio_to_db, name="save_audio_to_db"),
    url(r"^api/mark_page_as_processed/", views.mark_page_as_processed, name="mark_page_as_processed"),
    url(r"^api/load_full_xml_to_editor/", views.load_full_xml_to_editor, name="load_full_xml_to_editor"),
    url(r"^api/update_daisy_xml/", views.update_daisy_xml, name="update_daisy_xml"),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

if settings.DEBUG:
    import debug_toolbar
    urlpatterns = [
        url(r'^__debug__/', include(debug_toolbar.urls))
    ] + urlpatterns

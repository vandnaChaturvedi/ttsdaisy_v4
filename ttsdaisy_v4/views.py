from django.shortcuts import render, get_object_or_404, render_to_response, redirect
from django.views.generic import TemplateView, ListView, DetailView
from django.views.decorators.csrf import csrf_exempt, csrf_protect
from upload.models import Book, Upload, OCRResult, AudioBook
from django.core.urlresolvers import reverse, reverse_lazy
from django.http import HttpResponseRedirect, HttpResponse
from django.core.paginator import Paginator
from django.contrib.auth.models import User
from django.contrib import messages
from django.template import RequestContext
from django.db.models import Count
import json, requests, os, zipfile, shutil, pathlib as pl
from urllib.parse import urlencode
from httplib2 import Http
from . import settings
import time, datetime, logging, sys

logger = logging.getLogger(__name__)
LOGGING = {
    'handlers': {
            'console': {
                'level': 'DEBUG',
                'class': 'logging.StreamHandler',
                'stream': sys.stdout,
            },
        },
    'loggers': {
        'myApp.page_processors': {
            'handlers': ['console'],
            'level': 'DEBUG',
        }
    }
}


class HomePage(TemplateView):
    template_name = "index.html"

    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated():
            return HttpResponseRedirect(reverse_lazy("user_home"))
        return super().get(request, *args, **kwargs)


class BookDetailsView(DetailView):
    template_name = 'book_details.html'
    model = Book

    def get_queryset(self):
        return Book.objects.all()


class UserHomePage(ListView):
    model = Book
    template_name = 'user_home.html'
    paginate_by = 10

    def get_queryset(self):
        try:
            book = Book.objects.all()
        except Exception:
            print("No book is present.")
            book = []
        return book


class ViewLibrary(ListView):
    model = AudioBook
    template_name = 'my_library.html'
    paginate_by = 10

    def get_queryset(self):
        return AudioBook.objects.filter(username__exact=self.request.user.id)


class EditorPage(TemplateView):
    template_name = 'editor.html'

    def get_context_data(self):
        context = {}
        bookid = self.request.GET.get('bookid')
        title = Book.objects.get(id=bookid).title

        try:
            if Upload.objects.filter(book__id=bookid, processed=False).count():
                pages = Upload.objects.filter(book__id=bookid,
                                              processed=False).order_by('page_number')
                page_number = pages.values()[0]['page_number']
            else:
                page_number = Upload.objects.filter(book__id=bookid).count()
        except Exception as e:
            print("An error occured when finding the page number, taking default: ", e)
            page_number = Upload.objects.filter(book__id=bookid).count()
        count = Upload.objects.filter(book__id=bookid).count()
        if page_number == 1:
            page_position = 'first'
        elif page_number == count:
            page_position = 'last'
        else:
            page_position = 'intermediate'
        all_processed = int(Upload.objects.filter(book__id=bookid, processed=False).count() == 0)
        context['title'] = title
        context['bookid'] = bookid
        context['page_number'] = page_number
        pages = Upload.objects.filter(book__id=bookid, processed=False)
        context['pages'] = pages
        context['all_processed'] = all_processed
        context['page_position'] = page_position
        if all_processed:
            context['is_final_page'] = 1

        return context


class SingleEditorPage(TemplateView):
    template_name = 'single_page_editor.html'

    def get_context_data(self, pk):
        context = {}
        title = Book.objects.get(id=pk).title
        context['title'] = title
        context['bookid'] = pk
        return context


class ThanksPage(TemplateView):
    template_name = 'thanks.html'


class DownloadSuccess(TemplateView):
    template_name = 'download_success.html'


def get_mp3_files(bookname):
    # ts = time.time()
    # now = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d_%H:%M:%S')
    p = pl.Path(settings.MEDIA_ROOT + '/archive/' + bookname + '/daisy202/')
    allfiles = [settings.MEDIA_URL + 'archive/' + bookname + '/daisy202/' + os.path.basename(x)
                for x in [str(x) for x in list(p.glob('**/*.mp3'))] if 'tpbnarrator_res.mp3' not in x]
    allfiles = ','.join(allfiles)
    return allfiles


def save_audio_to_db(request):
    bookid = request.GET.get('data', '')
    audiobook = AudioBook()
    book = Book.objects.get(id=bookid)
    audiobook.book = book
    user = User.objects.get(id=request.user.id)
    audiobook.username = user
    # string = ''
    bookname = '_'.join(book.title.split(' '))
    audiobook.download_url = get_mp3_files(bookname)
    audiobook.save()
    mimetype = 'application/json'
    return HttpResponse(json.dumps({"status": 200}), mimetype)


def get_books(request):
    if request.is_ajax():
        q = request.GET.get('term', '')
        books = Book.objects.filter(title__icontains=q)[:20]
        results = []
        for book in books:
            book_json = {}
            book_json['id'] = book.id
            book_json['label'] = book.title
            book_json['value'] = book.title
            results.append(book_json)
        data = json.dumps(results)
    else:
        data = 'fail'
    mimetype = 'application/json'
    return HttpResponse(data, mimetype)


def get_audiobooks(request):
    if request.is_ajax():
        q = request.GET.get('term', '')
        audiobooks = AudioBook.objects.filter(book__title__icontains=q)[:20]
        results = []
        for book in audiobooks:
            book_json = {}
            book_json['id'] = book.id
            book_json['label'] = book.title
            book_json['value'] = book.title
            results.append(book_json)
        data = json.dumps(results)
    else:
        data = 'fail'
    mimetype = 'application/json'
    return HttpResponse(data, mimetype)


def get_book_id_from_name(request):
    bookname = request.POST.get('bookname', '')
    book_id = Book.objects.filter(title__exact=bookname).values('id')[0]['id']
    context = {}
    context['book_id'] = book_id
    mimetype = 'application/json'
    return HttpResponse(json.dumps(context), mimetype)


def get_audiobook_id_from_name(request):
    bookname = request.POST.get('audiobook_name', '')
    audiobook_id = AudioBook.objects.filter(book__title__exact=audiobook_name).values('id')[0]['id']
    context = {}
    context['audiobook_id'] = audiobook_id
    mimetype = 'application/json'
    return HttpResponse(json.dumps(context), mimetype)


def get_pre_loaded_xml(ocrtext, page_position, bookname, page_number=1):
    xmlpage_1_start = """<?xml version="1.0" encoding="UTF-8"?>
    <!DOCTYPE dtbook PUBLIC "-//NISO//DTD dtbook 2005-3//EN" "http://www.daisy.org/z3986/2005/dtbook-2005-3.dtd">
    <dtbook xmlns="http://www.daisy.org/z3986/2005/dtbook/" version="2005-3" xml:lang="ml">
    <head>
        <meta name="dtb:uid" content="AUTO-UID-0239"/>
        <meta name="dt:version" content="2.0.0.0 Beta"/>
        <meta name="dc:Title" content="{}"/>
        <meta name="dc:Creator" content="Vikram"/>
        <meta name="dc:Date" content="2018-05-08"/>
        <meta name="dc:Publisher" content="IIIT"/>
        <meta name="dc:Identifier" content="AUTO-UID-0239"/>
        <meta name="dc:Language" content="en"/>
    </head>
    <book showin="blp">
        <frontmatter>
          <doctitle>{}</doctitle>
          <docauthor>Vikram</docauthor>
        </frontmatter>
        <bodymatter id="bodymatter_0239">
        <level1>
        <pagenum page="normal" id="page000{}">{}</pagenum>
            <p>
    """.format(bookname, bookname, page_number, page_number)

    xmlpage_1_end = """</p>
    """

    xmlpage_last_start = """
        <pagenum page="normal" id="page000{}">{}</pagenum>
            <p>
    """.format(page_number, page_number)

    xmlpage_last_end = """</p>
    </level1>
    </bodymatter>
    </book>
    </dtbook>
    """

    xmlpage_int_start = """<pagenum page="normal" id="page000{}">{}</pagenum>
        <p>
    """.format(page_number, page_number)

    xmlpage_int_end = """
        </p>
    """

    if page_position == 'first':
        xmltext = xmlpage_1_start + "\n" + ocrtext + "\n" + xmlpage_1_end
    elif page_position == 'last':
        xmltext = xmlpage_last_start + "\n" + ocrtext + "\n" + xmlpage_last_end
    elif page_position == 'intermediate':
        xmltext = xmlpage_int_start + "\n" + ocrtext + "\n" + xmlpage_int_end
    return xmltext


def get_text_data_of_the_image(image, page_number, bookname, page_position='intermediate', media_url=''):
    print("image: {} and media_url: {} ".format(image, media_url))
    input_image = media_url + image
    output_path = "/home/iiit/data/tts_out"
    payload = {"input_image": input_image, "output_path": output_path}
    j = {"xml": "The OCR could not be completed, there has been some error. "}
    print("The payload is: ", payload)
    # url = "http://127.0.0.1:5000/get_ocr_output"
    url = "http://10.2.16.111:5000/get_ocr_output"
    session = requests.Session()
    session.trust_env = False
    try:
        print("Got the request. ")
        r = session.post(url, data=payload)
        print("Response: ", r.content.decode())
        j = json.loads(r.text)
        print(j)
        j["xml"] = get_pre_loaded_xml(j["ocr_text"], page_position, bookname, page_number)
    except Exception as e:
        print("Error message is: " + str(e))
    return j["xml"]


def append_xml_data(bookid, data):
    print("Appending data to daisy xml. ")
    book = Book.objects.get(id=bookid)
    if book.daisy_xml == '' or book.daisy_xml is None:
        daisy_xml = data
    else:
        daisy_xml = book.daisy_xml + "\n" + data
    book.daisy_xml = daisy_xml
    book.save()
    return daisy_xml


def get_full_daisy_xml(bookid):
    daisy_xml = ''
    try:
        book = Book.objects.get(id=bookid)
        daisy_xml = book.daisy_xml
    except Exception:
        print("The book id could not be found. ", bookid)
        daisy_xml = None
    return daisy_xml


def get_bookname_from_id(bookid):
    bookname = ''
    try:
        book = Book.objects.get(id=bookid)
        bookname = book.title
    except Exception:
        print("The book could not be found. ", bookid)
        bookname = None
    return bookname


def load_image_and_text(request):
    data = {}
    bookid = request.GET.get('bookid', '')
    save_option = request.GET.get('saveOption', '')
    print("SAVE OPTION", save_option)
    page_number = int(request.GET.get('page_number', ''))
    logger.debug("The current page loaded is: ", page_number)
    if page_number == '' or page_number is None:
        page_number = 1
    logger.debug("The book id in the request is: {}".format(bookid))
    context = {}

    # There is a need to check if more pages are present
    page_id = Upload.objects.filter(book__id=bookid, processed=False).order_by('page_number').values()[0]['id']
    logger.debug("The corresponding page_id is: {}".format(page_id))
    image = Upload.objects.filter(id=page_id).values('image')[0]['image']
    media_url = settings.MEDIA_URL
    media_root = settings.MEDIA_ROOT + "/"
    logger.debug("The image path is: {}".format(image))
    if OCRResult.objects.filter(image_id=page_id):
        text = OCRResult.objects.filter(image_id=page_id).values('result')[0]['result']
    else:
        text = "OCR is not complete. "
    count = Upload.objects.filter(book__id=bookid).count()
    if page_number == 1:
        page_position = 'first'
    elif page_number == count:
        page_position = 'last'
    else:
        page_position = 'intermediate'
    print("This page is: ", page_position)
    print("page number: {}, count: {}".format(page_number, count))
    bookname = get_bookname_from_id(bookid)
    test_text = get_text_data_of_the_image(image, page_number, bookname, page_position)
    print("Finished getting the text data for the image. ")

    if len(test_text):
        text = test_text

    context['bookid'] = bookid
    context['text'] = text
    context['title'] = get_bookname_from_id(bookid)
    context['daisy_xml'] = get_full_daisy_xml(bookid)
    context["img"] = image
    context["media_url"] = media_url
    context["page_position"] = page_position
    context["all_processed"] = '0'

    mimetype = 'application/json'
    return HttpResponse(json.dumps(context), mimetype)


def get_page_xml(bookid, page_number):
    page_xml = ''
    try:
        page = Upload.objects.get(book__id=bookid, page_number=page_number)
        page_xml = page.xmldata
    except Exception as e:
        print("The book id could not be found. ", bookid)
    return page_xml


def load_full_xml_to_editor(request):
    bookid = request.GET.get('bookid', '')
    page_number = request.GET.get('page_number', '')
    save_option = request.GET.get('saveOption', '')

    context = {}
    context["all_processed"] = '1'
    context["daisy_xml"] = get_full_daisy_xml(bookid)

    mimetype = 'application/json'
    return HttpResponse(json.dumps(context), mimetype)


def zipdir(path, ziph):
    all_files = []
    for root, dirs, files in os.walk(path):
        for f in files:
            # ziph.write(os.path.basename(os.path.join(root, f)))
            ziph.write(os.path.join(root, f), os.path.join("daisy202", os.path.basename(os.path.join(root, f))))
    del all_files


def zipdir2(output_filename, input_dir):
    shutil.make_archive(output_filename, 'zip', input_dir)


@csrf_exempt
def update_daisy_xml(request):
    bookid = request.POST.get('bookid', '')
    data = request.POST.get('data', '')
    try:
        book = Book.objects.get(id=bookid)
        book.completed = True
        book.save()
    except Exception as e:
        print("The book could not be saved. " + str(e))
    mimetype = 'application/json'
    return HttpResponse(json.dumps({"status": "200", "message": "success"}), mimetype)


@csrf_exempt
def download(request):
    title = request.GET.get("title")
    zipf = zipfile.ZipFile(settings.MEDIA_ROOT + '/archive/' + title + '.zip', 'w', zipfile.ZIP_DEFLATED)
    zipdir(settings.MEDIA_ROOT + '/archive/' + title + "/daisy202/", zipf)
    zipf.close()
    messages.info(request, 'The file has been downloaded. ')
    return HttpResponse({"status": "success"})


@csrf_exempt
def mark_page_as_processed(request):
    print("Marking this page as processed and saving the xmldata. ")
    book_id = request.POST.get('bookid', '')
    page_number = request.POST.get('pagenumber', '')
    xml_data = request.POST.get('xmldata', '')
    try:
        print("Page number from request is: ", page_number)
        upload = Upload.objects.get(book__id=book_id, page_number=page_number)
        upload.processed = True
        upload.xmldata = xml_data
        upload.save()
        append_xml_data(book_id, xml_data)
    except Exception as e:
        print("The record for book_id='{}' and page_number='{}' does not exist. "
              .format(book_id, page_number))
        print("Error message for saving book is", str(e))
    print("The page '{}' has been saved successfully. ".format(page_number))
    mimetype = 'application/json'
    return HttpResponse(json.dumps({"url": "/edit/?bookid="+book_id}), mimetype)


# References
# File download
# https://stackoverflow.com/questions/36392510/django-download-a-file
#
# Serve mp3 files
# https://stackoverflow.com/questions/28113220/django-how-to-serve-mp3-files
#
# General archive
# https://simpleisbetterthancomplex.com/archive/

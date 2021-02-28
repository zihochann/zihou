from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse

from core.mod_user import user_login, user_logout
from core.scheduler import *
from core.vtuber import *
from core.notification import *

NAV_ITEMS = ['index', 'new_live', 'vtb_list', 'notify', 'user_edit']

STD_ERROR_404 = HttpResponse('HARUTARO', status=404)


def render_navbar(request, nav_item):
    # Generate the id.
    flags = {'username': request.user.username}
    for ii in range(len(NAV_ITEMS)):
        flags['item_{}'.format(ii)] = ' active' if nav_item == NAV_ITEMS[ii] \
            else ''
    return loader.render_to_string('navbar.html', flags, request)


def render_page(request, title, nav_item, content):
    # Fill the content and nav bar.
    return render(request, 'global_frame.html',
                  {'title': title,
                   'navbar': render_navbar(request, nav_item),
                   'content': content})


# Create your views here.
def vtb_list(request):
    # Check login first.
    if not request.user.is_authenticated:
        return redirect('/login/')
    # Logic codes.
    if request.method == 'GET':
        # Render the vtuber page.
        return render_page(request, '全出席者管理', 'vtb_list',
                           render_vtbs(request))
    return STD_ERROR_404


def vtb_add(request):
    # Check login first.
    if not request.user.is_authenticated:
        return redirect('/login/')
    # Logic codes.
    if request.method == 'GET':
        # Render the create page.
        return render_page(request, '新しい出席者を登録する', '',
                           render_add_vtb(request))
    if request.method == 'POST':
        # Add a new item for the Vtuber.
        # Provide as json response
        return JsonResponse(add_vtuber(request))
    return STD_ERROR_404


def vtb_edit(request):
    # Check login first.
    if not request.user.is_authenticated:
        return redirect('/login/')
    # Logic codes.
    if request.method == 'GET':
        # Render the edit page.
        return render_page(request, '出席者を編集', '',
                           render_edit_vtb(request))
    if request.method == 'POST':
        # Edit an exist vtuber.
        # Provide as json response.
        return JsonResponse(edit_vtuber(request))
    return STD_ERROR_404


def notify(request):
    # Check login first.
    if not request.user.is_authenticated:
        return redirect('/login/')
    # Logic codes.
    if request.method == 'GET':
        return render_page(request, '通知システム', 'notify',
                           render_notify_status(request))
    if request.method == 'POST':
        result = notify_operate(request)
        print('Notify result is', result)
        return JsonResponse(result)
    return STD_ERROR_404


def vtb_remove(request):
    # Check login first.
    if not request.user.is_authenticated:
        return redirect('/login/')
    # Logic codes.
    if request.method == 'POST':
        # Remove an exist vtuber.
        return JsonResponse(remove_vtuber(request))
    return STD_ERROR_404


def new_live(request):
    # Check login first.
    if not request.user.is_authenticated:
        return redirect('/login/')
    # Logic codes.
    if request.method == 'GET':
        return render_page(request, '新しい予約', 'new_live',
                           render_new_live(request))
    if request.method == 'POST':
        # Add a new live to database.
        return JsonResponse(add_new_live(request))
    return STD_ERROR_404


def edit_live(request):
    # Check login first.
    if not request.user.is_authenticated:
        return redirect('/login/')
    # Logic codes.
    if request.method == 'GET':
        return render_page(request, '予約編集', '', render_edit_live(request))
    if request.method == 'POST':
        # Edit an existed live info.
        return JsonResponse(edit_live_by_id(request))
    return STD_ERROR_404


def remove_live(request):
    # Check login first.
    if not request.user.is_authenticated:
        return redirect('/login/')
    # Logic codes.
    if request.method == 'POST':
        # Edit an existed live info.
        return JsonResponse(remove_live_by_id(request))
    return STD_ERROR_404


def index(request):
    if request.method != 'GET':
        return STD_ERROR_404
    # Check login first.
    if not request.user.is_authenticated:
        return redirect('/login/')
    # Get the url year and month.
    url_year = request.GET.get('year')
    url_month = request.GET.get('month')

    # Get the default.
    def get_current():
        # Get the current year and month.
        current = datetime.now().date()
        return current.year, current.month

    if url_year is None or url_month is None:
        # Get the current year and month.
        url_year, url_month = get_current()
    # Try to transfer the data into int.
    try:
        if not isinstance(url_year, int):
            url_year = int(url_year)
            url_month = int(url_month)
    except:
        url_year, url_month = get_current()
    # Or else, we have to render the scheduler.
    return render_page(request, '時報システム', 'index',
                       render_scheduler(request, url_year, url_month))


def login(request):
    # Check login first.
    if request.user.is_authenticated:
        return redirect('/')
    # When doing get, it request for the login page.
    if request.method == 'GET':
        return render(request, 'login.html', {})
    # When doing post, it is login.
    if request.method == 'POST':
        # Check the username and password.
        if user_login(request, request.POST.get('id'), request.POST.get('ck')):
            return JsonResponse({'status': 'ok'})
        # Or else, return an error json.
        return JsonResponse({'error': '無効なユーザー名またはパスワード。'})
    # For all the other request.
    return STD_ERROR_404


def logout(request):
    if request.method == 'GET':
        user_logout(request)
        return redirect('/')
    # For all the other request.
    return STD_ERROR_404

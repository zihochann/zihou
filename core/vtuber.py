from django.template import loader
from core.models import Vtuber

BILI_PREFIX = 'https://space.bilibili.com/'


def get_bilibili_url(bili_id: str):
    return 'https://space.bilibili.com/{}/'.format(bili_id) if len(bili_id) >\
                                                               0 else ''


def render_vtbs(request):
    def generate_row(vtb):
        # Check the twitter is empty or not.
        if len(vtb.twitter) == 0:
            twitter = ''
        else:
            twitter = '<a href="https://twitter.com/{}">@{}</a>'.format(
                vtb.twitter, vtb.twitter)
        if len(vtb.bili_id) == 0:
            bili = ''
        else:
            bili_link = get_bilibili_url(vtb.bili_id)
            bili = '<a href="{}">{}</a>'.format(bili_link, bili_link)
        return ['<tr>',
                '<td>{}</td>'.format(vtb.name),
                '<td>{}</td>'.format(twitter),
                '<td>{}</td>'.format(bili),
                '<td><a class="btn-a" href="/vtbedit/?name={}">編集</a> <a '
                'class="btn-a" href="#" onclick="removeVtuber(\'{}\');">削除</td>'.format(
                    vtb.name, vtb.name),
                '</tr>']

    vtb_list = []
    for vtuber in Vtuber.objects.all():
        vtb_list += generate_row(vtuber)
    return loader.render_to_string('vtb_list.html',
                                   {'vtblist': '\n'.join(vtb_list)},
                                   request)


def render_vtb_edit(request, name='', twitter='', bili=BILI_PREFIX):
    return loader.render_to_string('vtb_edit_panel.html',
                                   {'vtbname': name,
                                    'vtbtwitter': twitter,
                                    'vtbbili': bili},
                                   request)


def render_add_vtb(request):
    return loader.render_to_string('vtb_editor.html',
                                   {'vtbedit': render_vtb_edit(request),
                                    'originalname': '',
                                    'buttonname': '出席者を追加する',
                                    'buttonaction': 'addVtuber();',
                                    'title': '新しい出席者を登録する'},
                                   request)


def vtb_checkboxs(selected=[]):
    def html_code(label: str, id: int, checked):
        return [
            '<div class="form-check form-check-inline">',
            '  <input class="form-check-input" type="checkbox" id="vtb{}" '
            'value="{}"{}>'.format(id, label, ' checked' if checked else ''),
            '  <label class="form-check-label" for="vtb{}">{}</label>'.format(id, label),
            '</div>']
    box_codes = []
    vtb_counter = 0
    for ii, vtb in enumerate(Vtuber.objects.all()):
        box_codes += html_code(vtb.name, ii, vtb.name in selected)
        vtb_counter = ii
    return '\n'.join(box_codes), vtb_counter


def render_edit_vtb(request):
    target = Vtuber.objects.filter(name=request.GET.get('name'))
    if not target.exists():
        return None
    target = target.first()
    # Render the target edit widget.
    bili_url = get_bilibili_url(target.bili_id)
    if bili_url == '':
        bili_url = BILI_PREFIX
    return loader.render_to_string('vtb_editor.html',
                                   {'title': '出席者を編集',
                                    'originalname': target.name,
                                    'buttonname': '出席者を編集する',
                                    'buttonaction': 'editVtuber();',
                                    'vtbedit': render_vtb_edit(
                                       request, target.name, target.twitter,
                                       bili_url)},
                                   request)


def extract_bili_id(src: str):
    if not src.startswith(BILI_PREFIX):
        return ''
    # Now we have to parse it.
    src = src[len(BILI_PREFIX):]
    # Find the first character which is not number.
    for ii in range(len(src)):
        if not src[ii].isnumeric():
            return src[:ii]
    return src


def remove_vtuber(request):
    # Find the target.
    target = Vtuber.objects.filter(name=request.POST.get('name'))
    if target.exists():
        target.first().delete()
    return {'status': 'ok'}


def edit_vtuber(request):
    origin_name = request.POST.get('origin')
    # Find the target.
    target = Vtuber.objects.filter(name=origin_name)
    if not target.exists():
        return {'status': 'error', 'info': 'not existed.'}
    target = target.first()
    # Now change the content.
    update_name = request.POST.get('name')
    # Extract the bilibili id
    update_bili_id = extract_bili_id(request.POST.get('bilibili'))
    if update_name != origin_name:
        # Check whether the update name existed.
        update_check = Vtuber.objects.filter(name=update_name)
        if update_check.exists():
            return {'status': 'error', 'info': '{}はすでに存在しています。'.format(
                update_name)}
        # Remove the original data.
        target.delete()
        # Create a new one.
        Vtuber.objects.create(name=update_name, twitter=request.POST.get('twitter'),
                              bili_id=update_bili_id)
    else:
        # Okay, now it is free to update.
        target.twitter=request.POST.get('twitter')
        target.bili_id=update_bili_id
        target.save()
    # Done.
    return {'status': 'ok'}


def add_vtuber(request):
    # First we check the bilibili url.
    vtb_bili_id = extract_bili_id(request.POST.get('bilibili'))
    # Fetch the name and twitter id.
    vtb_name = request.POST.get('name')
    if len(vtb_name) == 0:
        return {'status': 'error', 'info': '名前がありません。'}
    vtb_twitter = request.POST.get('twitter')
    # Check whether existed before.
    exist_check = Vtuber.objects.filter(name=vtb_name)
    if exist_check.exists():
        return {'status': 'error', 'info': '{}はすでに存在しています。'.format(
            vtb_name)}
    # Create the model.
    Vtuber.objects.create(name=vtb_name, twitter=vtb_twitter,
                          bili_id=vtb_bili_id)
    return {'status': 'ok'}

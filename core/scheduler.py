import pytz
from datetime import datetime
from calendar import monthrange

from django.template import loader

from core.models import Live
from core.vtuber import vtb_checkboxs
from core.notification import Notifier, live_data

JAPAN_STD_UTC = pytz.timezone('Asia/Tokyo')


def live_card(live):
    return ['<a href="/editlive/?liveid={}">'.format(live.id),
            '<div class="card w-100">',
            '<span>{} {}</span>'.format(
                ', '.join(live.vtbs.split('|')),
                live.dt.strftime("%I:%M %p"),
            ),
            '<span>{}</span>'.format(
                ', '.join(live.platform.split('|'))),
            '</div>',
            '</a>']


class MonthView:
    def __init__(self):
        self.codes = []
        self.row = -1
        self.day_left = 0

    def __indent(self, codes: list):
        return list(('    ' + x) for x in codes)

    def __add_day_code(self, codes: list):
        if self.day_left == 0:
            if self.row > -1:
                self.codes.append('</tr>')
            # Increase a new row.
            self.row += 1
            self.day_left = 7
            # Add the row code.
            self.codes.append('<tr>')
        # Add the day item to the codes.
        self.codes += self.__indent(['<td>', *codes, '</td>'])
        # Reduce the day left.
        self.day_left -= 1

    def add_empty_days(self, days: int):
        for _ in range(days):
            self.__add_day_code([])

    def complete(self):
        if self.row > -1:
            self.codes.append('</tr>')

    def render(self, indent=1):
        space = '    ' * indent
        render_codes = []
        for ii, x in enumerate(self.codes):
            if ii == 0:
                render_codes.append(x.strip())
            else:
                render_codes.append(space + x)
        return '\n'.join(render_codes)

    def add_day(self, date: int, content: list):
        # Generate the day code.
        date_codes = ['<span>{}</span>'.format(date)]
        # Sort the content based on the time.
        content.sort(key=lambda x: x.dt)
        # Check the content.
        for live in content:
            date_codes += live_card(live)
        # TODO: Add codes here.
        self.__add_day_code(self.__indent(date_codes))


def seperate(src: str):
    return list(filter(lambda x: x, src.split('|')))


def extract_name_platform(request):
    # Extract names.
    names = seperate(request.POST.get('vtbs'))
    if len(names) == 0:
        return None, None, {'status': 'error', 'info': '出席者なし。'}
    platform = seperate(request.POST.get('platform'))
    if len(platform) == 0:
        return None, None, {'status': 'error',
                            'info': '配信プラットフォームなし。'}
    return names, platform, None


def add_new_live(request):
    # Extract names.
    names, platform, error = extract_name_platform(request)
    if error is not None:
        return error
    # Record the live time.
    parsed_time = datetime.strptime(request.POST.get('dt'),
                                    '%Y-%m-%d %I:%M %p')
    # Add the live to database.
    live_obj = Live.objects.create(dt=parsed_time,
                                   vtbs='|'.join(names),
                                   platform='|'.join(platform))
    # Fetch the system.
    notify_sys = Notifier()
    notify_sys.add_live(live_data(live_obj))
    return {'status': 'ok'}


def edit_live_by_id(request):
    # Extract the live object.
    target = Live.objects.filter(id=int(request.POST.get('live_id')))
    if not target.exists():
        return {'status': 'error', 'info': 'No existed.'}
    target = target.first()
    # Now get the name and platform.
    names, platform, error = extract_name_platform(request)
    if error is not None:
        return error
    # Record the live time.
    parsed_time = datetime.strptime(request.POST.get('dt'),
                                    '%Y-%m-%d %I:%M %p')
    # Update the target.
    target.dt = parsed_time
    target.vtbs = '|'.join(names)
    target.platform = '|'.join(platform)
    target.save()
    # Update the notify system.
    notify_sys = Notifier()
    notify_sys.update_live(live_data(target))
    return {'status': 'ok'}


def remove_live_by_id(request):
    # Extract the live object.
    target = Live.objects.filter(id=int(request.POST.get('live_id')))
    if not target.exists():
        return {'status': 'error', 'info': 'No existed.'}
    target = target.first()
    # Remove the live from notification system.
    notify_sys = Notifier()
    notify_sys.remove_live(target.id)
    # Remove from the system.
    target.delete()
    return {'status': 'ok'}


def render_new_live(request):
    vtb_codes, vtb_num = vtb_checkboxs()
    current = datetime.now()
    return loader.render_to_string(
        'live_editor.html',
        {'title': '新しい予約',
         'live_date': current.strftime("%Y-%m-%d"),
         'live_time': '8:00 PM',
         'vtbs': vtb_codes,
         'vtbcount': vtb_num + 1,
         'remove_hide': ' d-none',
         'apply': '予約を追加',
         'apply_code': 'addLive();',
         'youtube_checked': '',
         'bilibili_checked': '',
         'liveid': -1,
         'backy': current.year,
         'backm': current.month,
         },
        request)


def render_edit_live(request):
    # Extract the request number.
    target = Live.objects.filter(id=request.GET.get('liveid'))
    if not target.exists():
        return None
    # Extract the update information.
    target = target.first()
    # Update platforms status.
    platforms = target.platform.split('|')
    # Update the live date.
    vtb_codes, vtb_num = vtb_checkboxs(target.vtbs.split('|'))
    return loader.render_to_string(
        'live_editor.html',
        {'title': '予約編集',
         'live_date': target.dt.strftime("%Y-%m-%d"),
         'live_time': target.dt.strftime("%I:%M %p"),
         'vtbs': vtb_codes,
         'vtbcount': vtb_num + 1,
         'remove_hide': '',
         'apply': '予約を更新',
         'apply_code': 'updateLive();',
         'youtube_checked': ' checked' if 'youtube' in platforms else '',
         'bilibili_checked': ' checked' if 'bilibili' in platforms else '',
         'liveid': request.GET.get('liveid'),
         'backy': target.dt.year,
         'backm': target.dt.month,
         },
        request)


def render_scheduler(request, year: int, month: int):
    # Extract the live within the month.
    lives = Live.objects.filter(dt__year=year,
                                dt__month=month)
    # Get the week day, now we are allowed to render the calender.
    view = MonthView()
    # Add empty days.
    first_day, day_range = monthrange(year, month)
    view.add_empty_days(first_day)
    # Prepare the buckets.
    live_buckets = [[] for _ in range(day_range)]
    for live in lives:
        live_buckets[live.dt.day - 1].append(live)
    for day_num in range(day_range):
        # Insert the day to calender.
        view.add_day(day_num + 1, live_buckets[day_num])
    view.complete()
    # Calculate the previous year and month.
    if month == 1:
        prev_year = year - 1
        prev_month = 12
    else:
        prev_year = year
        prev_month = month - 1
    if month == 12:
        next_year = year + 1
        next_month = 1
    else:
        next_year = year
        next_month = month + 1
    # Render the title.
    return loader.render_to_string(
        'schedule.html',
        {'year': year,
         'month': month,
         'monthset': view.render(5),
         'prev_y': prev_year,
         'prev_m': prev_month,
         'next_y': next_year,
         'next_m': next_month,
        },
        request)
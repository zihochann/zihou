from django.template import loader
from core.notify_proc import Notifier, now_jp_time, jp_time

from core.models import Live


def live_data(live):
    # Generate as Japan time.
    return [live.id,
            jp_time(live.dt.year, live.dt.month, live.dt.day,
                    live.dt.hour, live.dt.minute, live.dt.second),
            live.vtbs, live.platform]


def notify_operate(request):
    # Fetch the system.
    notify_sys = Notifier()
    # Check the operation.
    if request.POST.get('op') == 'start':
        tuser = request.POST.get('tuser')
        tpass = request.POST.get('tpass')
        # Check the empty first.
        if len(tuser) == 0 or len(tpass) == 0:
            return {'status': 'error',
                    'info': 'ユーザー名またはパスワードがありません。'}
        # Start the system first.
        notify_sys.start()
        # Try to login with the username and password.
        if not notify_sys.login(tuser, tpass):
            # Stop the system right now.
            notify_sys.stop()
            # Return the error.
            return {'status': 'error',
                    'info': 'Twitterアカウント「{}」へのログインに失敗しました。'.format(tuser)}
        # Prepare the initial notify lives.
        live_info = []
        for live in Live.objects.filter(dt__gte=now_jp_time()):
            live_info.append(live_data(live))
        notify_sys.init_lives(live_info)
    else:
        notify_sys.stop()
    return {'status': 'ok'}


def render_notify_status(request):
    notify_sys = Notifier()
    status = notify_sys.running
    # Now renderting the page.
    return loader.render_to_string(
        'notify.html',
        {'rstatus': '実行中' if status else '未実行',
         'buttonmode': ' btn-danger' if status else ' btn-success',
         'buttontext': '終止' if status else '起動',
         'operate': 'stop' if status else 'start',
         'runhide': ' d-none' if status else '',
         },
        request)

import threading
import time
import pytz
from multiprocessing import Process, Queue
from datetime import datetime, timedelta

from core.msg_sender import MessageSender


JAPAN_STD_UTC = pytz.timezone('Asia/Tokyo')
# NOTIFY_RANGE = timedelta(minutes=5)
NOTIFY_RANGE = timedelta(hours=12)
WAIT_MARGIN = 6
HEARTBEAT_MARGIN = 2

# Forcast strings.
TEST_MESSAGE = 'このツイートは自動ボットから送信されるテストツイートです。後で削除されます。\n'
LIVE_FORECAST = 'この後{}から{}で{}の配信が開始になります。'
NAME_DOT = '・'
HASH_TAG = '\n\n#時報組'

# Const enum.
ID_LIVEID = 0
ID_TIME = 1
ID_VTBS = 2
ID_PLATFORM = 3


def text_time(time: datetime):
    result = '{}時'.format(time.hour)
    if time.minute != 0:
        result += '{}分'.format(time.minute)
    return result


def text_vtb(vtb: str):
    vtb_list = vtb.split('|')
    if len(vtb_list) < 3:
        return 'と'.join(vtb_list)
    return NAME_DOT.join(vtb_list)


def text_platforms(platform: str):
    p_list = platform.split('|')
    for ii, p_text in enumerate(p_list):
        p_list[ii] = p_text.capitalize()
    return p_list


def generate_live_forecast(live):
    time_text = text_time(live[ID_TIME])
    vtb_text = text_vtb(live[ID_VTBS])
    platform_list = text_platforms(live[ID_PLATFORM])
    # Generate the forecast text.
    tweets = []
    for platform in platform_list:
        tweets.append(TEST_MESSAGE +
                      LIVE_FORECAST.format(time_text, platform, vtb_text) +
                      HASH_TAG)
    return tweets


def jp_time(year, month, day, hour, minute, second):
    return datetime(year, month, day, hour, minute, second,
                    tzinfo=JAPAN_STD_UTC)


def now_jp_time():
    # Transfer to local time zone first, then to the std Japan time.
    return datetime.now().astimezone().astimezone(JAPAN_STD_UTC)


class NotifierTasks:
    _task_lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        # Singleton check.
        if not hasattr(cls, '_instance'):
            with NotifierTasks._task_lock:
                if not hasattr(cls, '_instance'):
                    NotifierTasks._instance = super().__new__(cls)
        return NotifierTasks._instance

    def __init__(self):
        if hasattr(self, 'initialized'):
            return
        self.initialized = True
        self.stop_flag = False
        self.conn = None
        # Live queues.
        self.lives = []
        self.sender = MessageSender()

    def init(self, lives):
        # Update the lives.
        self.lives = lives
        # Sort the live based on the date and time.
        self.lives.sort(key=lambda x: x[ID_TIME])

    def add(self, live):
        live_time = live[ID_TIME]
        # Check whether the live time is less than the target time, then insert.
        for ii, queue_live in enumerate(self.lives):
            # Extract queue time.
            queue_time = queue_live[ID_TIME]
            # Compare the live time and queue time.
            if live_time < queue_time:
                # Insert the live here.
                self.lives.insert(ii, live)
                return
        # Or else, append at the end of the queue.
        self.lives.append(live)

    def remove(self, live_id):
        # Go through the lives, remove the id.
        for ii, queue_live in enumerate(self.lives):
            # Check whether the live id matches.
            if live_id == queue_live[ID_LIVEID]:
                self.lives.pop(ii)
                return

    def update_live(self, live):
        # We should remove old data from the list.
        self.remove(live[ID_LIVEID])
        # Check whether should we insert the live.
        if live[ID_TIME] > now_jp_time():
            self.add(live)

    def pop_forecast(self, current_time: datetime):
        # Calculate the start time.
        check_time = current_time + NOTIFY_RANGE
        # Check the live is in the range or not.
        forecast_live = []
        while len(self.lives) > 0:
            # Check the head of the queue.
            id, time, vtbs, platform = self.lives[0]
            if time < check_time:
                forecast_live.append(self.lives.pop(0))
            else:
                break
        return forecast_live

    def clear_flag(self):
        self.stop_flag = False


def launch_notify(queue: Queue, reflect: Queue):
    # Reset the tasks flags.
    tasks = NotifierTasks()
    tasks.clear_flag()
    # Create the loop.
    while True:
        exit_flag = False
        # Wait during the margin, process the command queue.
        for _ in range(WAIT_MARGIN):
            # Check whether we have any command.
            while not queue.empty():
                # Fetch the data.
                cmd, args = queue.get()
                if cmd == 'init':
                    tasks.init(args)
                elif cmd == 'add':
                    # Insert the live to queue.
                    tasks.add(args)
                elif cmd == 'update':
                    # Update the task information.
                    tasks.update_live(args)
                elif cmd == 'remove':
                    # Remove from the tasks.
                    tasks.remove(args)
                elif cmd == 'login':
                    tuser, tpass = args
                    reflect.put(tasks.sender.login(tuser, tpass))
                elif cmd == 'exit':
                    exit_flag = True
                    # Shutdown the driver here.
                    tasks.sender.shutdown()
                    break
                else:
                    print('Unknown command {}.'.format(cmd))
            # Sleep for heartbeat.
            time.sleep(HEARTBEAT_MARGIN)
            if exit_flag:
                break
        # Before forecast, we check the flag.
        if exit_flag:
            break
        # Task - notification check.
        coming_lives = tasks.pop_forecast(now_jp_time())
        if len(coming_lives) == 0:
            continue
        # Got works!
        # Generate all the tweet text.
        tweets = []
        for live in coming_lives:
            tweets += generate_live_forecast(live)
        # Send the forecast.
        for tweet_text in tweets:
            # Print debug message.
            print('Notify: \n{}'.format(tweet_text))
            tasks.sender.send_message(tweet_text)


class Notifier:
    _driver_lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        # Singleton check.
        if not hasattr(cls, '_instance'):
            with Notifier._driver_lock:
                if not hasattr(cls, '_instance'):
                    Notifier._instance = super().__new__(cls)
        return Notifier._instance

    def __init__(self):
        if hasattr(self, 'initialized'):
            return
        self.initialized = True
        self.running = False
        self.queue = Queue()
        self.reflect = Queue()
        self.proc = None

    def start(self):
        if self.running:
            return
        # Mark the running state.
        self.running = True
        self.proc = Process(target=launch_notify, args=(self.queue,
                                                        self.reflect, ))
        self.proc.start()

    def remove_live(self, live_id):
        # Check the time of the live.
        if self.running:
            # Check whether the time of the live is after current time.
            self.send(['remove', live_id])

    def update_live(self, live):
        # Check the time of the live.
        if self.running:
            # Update the live.
            self.send(['update', live])

    def add_live(self, live):
        # Check the time of the live.
        if self.running:
            # Check whether the time of the live is after current time.
            if live[ID_TIME] > now_jp_time():
                self.send(['add', live])

    def init_lives(self, lives):
        # Check running status.
        if self.running:
            self.send(['init', lives])

    def login(self, tuser, tpass):
        if self.running:
            # Send the command.
            self.send(['login', [tuser, tpass]])
            # Now hold and wait for the result.
            return self.reflect.get(timeout=60)
        return False

    def send(self, command):
        if self.running:
            # Just send the data to queue.
            self.queue.put(command)

    def is_running(self):
        return self.running

    def stop(self):
        if not self.running:
            return
        # Send the exit flag here.
        self.queue.put(['exit', None])
        # Wait for proc end.
        self.proc.join(30)
        # Check whether it is still alive.
        if self.proc.is_alive():
            # WTF... something bad happens here.
            self.proc.kill()
        # Finish the running.
        self.running = False

import functools
import logging
import random
import time

import requests
from gevent.lock import RLock
from locust import HttpLocust, TaskSet

# ramnes: see UserBehavior
login_lock = RLock()
available_clients = []

available_users = []
for i in range(0, 10):
    name = "user{}".format(i)
    available_users.append({"name": name, "password": name})

available_sentences = [
    "Hey lads, what's up?",
    "I'm feeling good today! #sunshine",
    "weeeeeeeeeeeeeee!",
    "Locusts are going to take over the world, I promise",
    "Are you sure? #LocustsGate",
    "I'M SUPER HUNGRY YOU FK",
    "Please help, this queue is getting rather long",
    "This server needs more CPUs"
]


def api_login(l):
    data = random.choice(available_users)
    l.client.post("/api/login", data)
    l.logged = True


def ui_login(l):
    data = random.choice(available_users)
    l.client.post("/", data)
    l.logged = True


def login_required(task):
    @functools.wraps(task)
    def wrapper(l):
        if l.logged is False:
            ui_login(l)
        return task(l)
    return wrapper


def index(l):
    l.client.get("/")


@login_required
def follow(l):
    user_id = random.choice(range(1, 10))
    l.client.get("/tweets/follow/{}/".format(user_id))


@login_required
def unfollow(l):
    user_id = random.choice(range(1, 10))
    l.client.get("/tweets/unfollow/{}/".format(user_id))


@login_required
def tweet(l):
    tweet = random.choice(available_sentences)
    l.client.post("/tweets/post/", {"tweet": tweet})


@login_required
def tweets(l):
    l.client.get("/tweets/")


@login_required
def users(l):
    l.client.get("/users/")


@login_required
def logout(l):
    l.client.get("/logout/")
    l.logged = False


class UserBehavior(TaskSet):
    tasks = {logout: 1, users: 5,
             follow: 5, unfollow: 5,
             tweet: 20, tweets: 200}

    # ramnes: this overload exists for two reasons:
    # 1/ to do all the logins synchronously, so that we are sure to avoid any
    # kind of fail (e.g. the server is overloaded and thus can not authentify);
    # 2/ and to wait all the logins to be done before running the tasks,
    # because otherwise it would slow down logins, and their stats wouldn't
    # make any sense anyway (on the other way, logins would slow down tasks).
    def __init__(self, *args, **kwargs):
        from locust.runners import locust_runner as runner

        super().__init__(*args, **kwargs)

        with login_lock:
            if available_clients:
                self.locust.client = available_clients.pop()
                self.logged = True
            else:
                api_login(self)

        if not hasattr(runner, "num_ready"):
            runner.num_ready = 0
        runner.num_ready += 1
        logging.info("{}: Locust {}/{} ready".format(runner.client_id,
                                                     runner.num_ready,
                                                     runner.num_clients))
        if runner.num_ready == runner.num_clients:
            logging.info("{}: Let's go!".format(runner.client_id))
        while runner.num_ready < runner.num_clients:
            time.sleep(0.01)

    # ramnes: keep our precious logged clients aside so that new locusts
    # can use them, and avoid useless login requests.
    def on_stop(self):
        from locust.runners import locust_runner

        available_clients.append(self.client)
        locust_runner.num_ready -= 1


class WebsiteUser(HttpLocust):
    task_set = UserBehavior
    min_wait = 500
    max_wait = 1500

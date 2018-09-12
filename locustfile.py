import functools
import logging
import time

import requests
from gevent.lock import RLock
from locust import HttpLocust, TaskSet

# ramnes: see UserBehavior
login_lock = RLock()
available_clients = []


def login(l):
    data = {"name": "tototo", "password": "tototo"}
    l.client.post("/", data)
    l.logged = True


def login_required(task):
    @functools.wraps(task)
    def wrapper(l):
        if l.logged is False:
            login(l)
        return task(l)
    return wrapper


def index(l):
    l.client.get("/")


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
    tasks = {index: 1, users: 2, tweets: 4, logout: 1}

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
                login(self)

        if not hasattr(runner, "num_ready"):
            runner.num_ready = 0
        runner.num_ready += 1
        logging.info("{}: Locust {}/{} ready".format(runner.client_id,
                                                     runner.num_ready,
                                                     runner.num_clients))
        while runner.num_ready < runner.num_clients:
            time.sleep(0.01)
        logging.info("{}: Locusts ready, let's go!".format(runner.client_id))

    # ramnes: keep our precious logged clients aside so that new locusts
    # can use them, and avoid useless login requests.
    def on_stop(self):
        from locust.runners import locust_runner

        available_clients.append(self.client)
        locust_runner.num_ready -= 1


class WebsiteUser(HttpLocust):
    task_set = UserBehavior
    min_wait = 1000
    max_wait = 3000

    def setup(self):
        logging.info("Reset database")
        requests.get(self.host + "/reset-database")

        logging.info("Register user")
        data = {"name": "tototo", "email": "tototo@yopmail.com",
                "password": "tototo", "confirm": "tototo"}
        requests.post(self.host + "/register/", data=data)

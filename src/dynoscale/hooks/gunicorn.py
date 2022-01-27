from dynoscale.agent import DynoscaleAgent

dynoscale = DynoscaleAgent()


def on_starting(server):
    dynoscale.on_starting(server)


def on_reload(server):
    dynoscale.on_reload(server)


def when_ready(server):
    dynoscale.when_ready(server)


def pre_fork(server, worker):
    dynoscale.pre_fork(server, worker)


def post_fork(server, worker):
    dynoscale.post_fork(server, worker)


def post_worker_init(worker):
    dynoscale.post_worker_init(worker)


def worker_int(worker):
    dynoscale.worker_int(worker)


def worker_abort(worker):
    dynoscale.worker_abort(worker)


def pre_exec(server):
    dynoscale.pre_exec(server)


def pre_request(worker, req):
    worker.log.debug("%s %s" % (req.method, req.path))
    dynoscale.pre_request(worker, req)


def post_request(worker, req, environ, resp):
    dynoscale.post_request(worker, req, environ, resp)


def child_exit(server, worker):
    dynoscale.child_exit(server, worker)


def worker_exit(server, worker):
    dynoscale.worker_exit(server, worker)


def nworkers_changed(server, new_value, old_value):
    dynoscale.nworkers_changed(server, new_value, old_value)


def on_exit(server):
    dynoscale.on_exit(server)

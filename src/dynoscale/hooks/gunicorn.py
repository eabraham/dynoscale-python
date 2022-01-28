from dynoscale.agent import DynoscaleAgent

dynoscale_agent = DynoscaleAgent()


def on_starting(server):
    dynoscale_agent.on_starting(server)


def on_reload(server):
    dynoscale_agent.on_reload(server)


def when_ready(server):
    dynoscale_agent.when_ready(server)


def pre_fork(server, worker):
    dynoscale_agent.pre_fork(server, worker)


def post_fork(server, worker):
    dynoscale_agent.post_fork(server, worker)


def post_worker_init(worker):
    dynoscale_agent.post_worker_init(worker)


def worker_int(worker):
    dynoscale_agent.worker_int(worker)


def worker_abort(worker):
    dynoscale_agent.worker_abort(worker)


def pre_exec(server):
    dynoscale_agent.pre_exec(server)


def pre_request(worker, req):
    worker.log.debug("%s %s" % (req.method, req.path))
    dynoscale_agent.pre_request(worker, req)


def post_request(worker, req, environ, resp):
    dynoscale_agent.post_request(worker, req, environ, resp)


def child_exit(server, worker):
    dynoscale_agent.child_exit(server, worker)


def worker_exit(server, worker):
    dynoscale_agent.worker_exit(server, worker)


def nworkers_changed(server, new_value, old_value):
    dynoscale_agent.nworkers_changed(server, new_value, old_value)


def on_exit(server):
    dynoscale_agent.on_exit(server)

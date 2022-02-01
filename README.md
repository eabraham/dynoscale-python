# Dynoscale Agent

#### Simple yet efficient scaling agent for Python apps on Heroku

# 🚀🚀🚀TL;DR🚀🚀🚀

1. Add __dynoscale__ to your app on Heroku: `heroku addons:create dscale`
2. Install __dynoscale__:  `python -m pip install dynoscale`
3. In your `gunicorn.conf.py` import request hooks:
   ```python
    from dynoscale.hooks.gunicorn import *
    
    # ... or if you have your own hooks, remember to call our hook
    # aftewards otherwise dynoscale agent will not be notified when
    # this hook is hit!
   
    def pre_request(worker, req):
        print(f"GUNICORN: worker about to be handed a request")
        dynoscale.agent.pre_request(worker, req)
   
    def when_ready(server):
        print(f"GUNICORN: server is ready")
        dynoscale.agent.when_ready(server)
        
    def post_fork(server, worker):
        print(f"GUNICORN: worker was just forked")
        dynoscale.agent.post_fork(server, worker)
    ```
4. Profit! (Literally, this will save you money 😏

# 📖 Usage

Long form of the above... with screenshots and such, maybe less emojis.
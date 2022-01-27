# Dynoscale Agent

#### Simple yet efficient scaling agent for Python apps on Heroku

# 🚀🚀🚀TL;DR🚀🚀🚀

1. Add dynoscale.net on Heroku.
2. install `dynoscale` package:
    1. `python -m pip install dynoscale`
3. In your `gunicorn.conf.py` import request hooks:
    1. ```python
       from dynoscale.hook.gunicorn import *
       
       # If you have your own hooks, remember to call our hook aftewards
       # otherwise dynoscale agent will not be notified when this hook is hit
       def pre_request(worker, req):
          print(f"GUNICORN: pre_request worker:{worker} req: {req}")
          dynoscale.agent.pre_request(worker, req)
       ```
4. Profit! (Literally, this will save you money 😏

# 📖 Usage

Long form of the above... with screenshots and such, maybe less emojis.
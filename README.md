# simple llama wrapper
#### basically makes RPC to groq.com API on each /llama command call (you should get your groq api_key and tg bot token)  

## USAGE
### run locally:
```commandline
pip install -r requirements.txt
```

```commandline
GROQ_API_KEY=some_groq_key TG_BOT_TOKEN=some_TG_BOT_token python main.py
```

### run with `docker compose` (yeah without dash in-between):

#### set up .env file with 
```txt
GROQ_API_KEY=some_groq_key
TG_BOT_TOKEN=some_TG_BOT_token 
```

#### after everything is set up run:

```commandline
docker-compose up -d sota_bot
```

#### if build **FAILS** (for some reason you messed up with packages or smth) you can rebuild stuff with `--build` flag 

```commandline
docker-compose up --build -d  sota_bot
```
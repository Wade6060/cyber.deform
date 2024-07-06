import json

try:
    with open("data/cached_user_agents.json", "r") as f:
        CACHED_USER_AGENTS = json.load(f)
except FileNotFoundError:
    CACHED_USER_AGENTS = {}

THREADS = 100

referal_code = 'r41VGY8jdLnc' # если без него то None без ''
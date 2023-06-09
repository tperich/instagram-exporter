#!/usr/bin/env python
import os
import time

import redis
from dotenv import load_dotenv
from prometheus_client import start_http_server, Gauge

from custom_types import FollowerStats

load_dotenv()
REDIS_HOST = os.getenv("REDIS_HOST")
REDIS_PORT = os.getenv("REDIS_PORT")
METRICS_HOST = os.getenv("METRICS_HOST")
METRICS_PORT = os.getenv("METRICS_PORT")
REFRESH_INTERVAL_SECONDS = 5

redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT)

def read_from_db() -> FollowerStats:
    if not redis_client.ping():
        print("[ERROR] Could not connect to redis, please check your credentials")
        return

    follower_count = redis_client.get("instagram_followers").decode()
    following_count = redis_client.get("instagram_following").decode()

    return {"followers": follower_count, "following": following_count}


def serve_metrics() -> None:
    follower_stats: FollowerStats = read_from_db()

    # Create gauge metrics
    instagram_followers = Gauge("instagram_followers", "Number of Instagram followers")
    instagram_following = Gauge("instagram_following", "Number of Instagram followees")

    # Set the initial values of the gauges
    instagram_followers.set(follower_stats["followers"])
    instagram_following.set(follower_stats["following"])

    # Start the server
    start_http_server(METRICS_PORT, METRICS_HOST)
    print(f"[+] Serving metrics on http://{METRICS_HOST}:{METRICS_PORT}")

    # Keep the script running
    while True:
        # Update the metrics
        follower_stats = read_from_db()
        instagram_followers.set(follower_stats["followers"])
        instagram_following.set(follower_stats["following"])
        time.sleep(REFRESH_INTERVAL_SECONDS)


if __name__ == "__main__":
    try:
        serve_metrics()
    except KeyboardInterrupt:
        exit(0)

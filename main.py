#!/usr/bin/env python
import os
import re
import time
import argparse

import redis
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.firefox import GeckoDriverManager

from custom_types import FollowerStats

load_dotenv()

IG_USERNAME = os.getenv("IG_USERNAME")
IG_PASSWORD = os.getenv("IG_PASSWORD")
IG_TARGET_USER = os.getenv("IG_TARGET_USER")
REDIS_HOST = os.getenv("REDIS_HOST")
REDIS_PORT = os.getenv("REDIS_PORT")


parser = argparse.ArgumentParser()
parser.add_argument("--headless", action="store_true")
args = parser.parse_args()

service = Service(GeckoDriverManager().install())
options = webdriver.FirefoxOptions()
options.add_argument("--headless") if args.headless else None
driver = webdriver.Firefox(service=service, options=options)


def login() -> None:
    """Logs into Instagram account in order to gather necessary cookies."""
    print("[+] Logging in...")
    driver.get("https://www.instagram.com/accounts/login")
    time.sleep(1)

    # Get rid of cookies popup
    cookies_btn = driver.find_element(
        By.XPATH, "//button[text()='Only allow essential cookies']"
    )
    cookies_btn.click()

    time.sleep(1)

    # Log in
    username_input = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, "input[name='username']"))
    )
    password_input = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, "input[name='password']"))
    )

    username_input.clear()
    username_input.send_keys(IG_USERNAME)
    password_input.clear()
    password_input.send_keys(IG_PASSWORD)

    login_btn = (
        WebDriverWait(driver, 2)
        .until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button[type='submit']")))
        .click()
    )


def get_follower_stats() -> FollowerStats:
    """Scrapes follower stats from IG_TARGET_USER's account."""
    print("[+] Getting follower stats...")
    driver.get(f"https://www.instagram.com/{IG_TARGET_USER}")
    time.sleep(3)

    followers_wrapper = driver.find_element(
        By.XPATH, "//a[contains(@href, '/followers')]"
    )
    followers_html = followers_wrapper.get_attribute("innerHTML")

    following_wrapper = driver.find_element(
        By.XPATH, "//a[contains(@href, '/following')]"
    )
    following_html = following_wrapper.get_attribute("innerHTML")

    followers_count = re.findall(r"[0-9,]{2,9}", followers_html)[0].replace(",", "")
    following_count = re.findall(r"[0-9,]{2,9}", following_html)[0].replace(",", "")

    return {"followers": followers_count, "following": following_count}


def write_to_db(follower_stats: FollowerStats) -> None:
    """Writes stats to Redis DB."""
    print("[+] Writing to DB...")
    redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT)

    if not redis_client.ping():
        print("[ERROR] Could not connect to redis, please check your credentials")
        return

    redis_client.set("instagram_followers", follower_stats["followers"])
    redis_client.set("instagram_following", follower_stats["following"])


if __name__ == "__main__":
    follower_stats: FollowerStats = {}

    # Try fetching stats first if the session hasn't expired
    try:
        login()
        time.sleep(3)

        follower_stats = get_follower_stats()
        write_to_db(follower_stats)

        print("[$] Success!")
        driver.quit()
    except KeyboardInterrupt:
        print("Exiting...")
        driver.quit()
        exit(0)

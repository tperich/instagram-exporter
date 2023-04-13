# Instagram Exporter and Scraper for Prometheus

## Why

None of the scrapers I found online currently work (this one probably won't work too unless I keep it updated, check the time of the latest commits). It's currently set up to read from a Redis DB once I figure out Instagram's login threshold (you might get logged out and requested to change your account password).

## What

There are two main scripts:

 - `main.py` scrapes the number of followers and followees and saves them to a Redis database
 - `serve-metrics.py` reads from Redis and serves metrics on port 3000

## Getting started

### Prerequisites

 - python3 and pip
 - firefox
 - redis up and running

### Setting up

 1. Copy [.env.example](./.env.example) to `.env` and add necessary info
 2. Run `pip install -r requirements.txt` to install dependencies
 3. Run `./main.py` to fetch follower stats
 4. Run `./serve-metrics.py` to serve metrics

 ## Metrics

 | Name                | Description         | Example value |
 | ------------------- | ------------------- | ------------- |
 | instagram_followers | Number of followers | 50            |
 | instagram_following | Number of followees | 100           |


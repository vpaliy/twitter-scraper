#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import argparse
import getpass
import queue
import threading

import _base

DEFAULT_RETWEETED_CONTESTS = 30
DEFAULT_BLEND_IN_TWEETS = 10
DEFAULT_TIME_INTERVAL = 1440 # 24 hours

parser = argparse.ArgumentParser()

parser.add_argument(
  '-a', '--agents',
  help='File containing user-agents',
  dest='agents_file'
)
parser.add_argument(
  '--contests',
  help='Number of contests',
  dest='contests'
)
parser.add_argument(
  '-d', '--delay',
  help='Delay between retweeting contests'
)
parser.add_argument(
  '-t', '--time',
  help='For how long we should be executing'
)
parser.add_argument(
  '-ed', '--err-delay',
  help='Delay between errors',
  dest='error_delay'
)
parser.add_argument(
  '-l', '--limit',
  help='How many tweets we can fetch',
  dest='tweet_limit'
)

args = parser.parse_args()

tweets_limit = args.tweet_limit
time_interval = args.time or DEFAULT_TIME_INTERVAL
error_delay = args.error_delay
req_delay = args.delay
user_agents = []

if args.agents_file:
  try:
    with open(args.agents_file, encoding='UTF-8') as fp:
      for agent in fp:
        user_agents.append(agent)
  except Exception as ex:
    exit(f'Failed to open/read the user-agents file.\n({ex})')

while True:
  username = input('Twitter username: ')
  if not _base._is_logged(username):
    password = getpass.getpass(prompt='Twitter password: ')
    try:
      _base.login(username, password)
    except _base.InvalidCredentials:
      _base.logger.error('Invalid credentials.Try again')
      continue
  os.environ['username'] = username
  break

tweet_queue = queue.Queue()
action_queue = queue.Queue()

searcher = _base.TweetSearcher(tweet_queue)
handler = _base.TweetHandler(
  tweet_queue, action_queue, 'win winner'.split()
)
executor = _base.ActionExecutor(action_queue, delay=1)

query = ['rt to win','contest alert']

threading.Thread(target=handler.handle).start()
threading.Thread(target=executor.execute).start()

for tag in query:
  threading.Thread(
    target=searcher.search, args=(tag,)
  ).start()

tweet_queue.join()
action_queue.join()

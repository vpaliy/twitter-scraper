#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import json
import shutil
import argparse
import getpass
import _base
import queue
import threading
import collections


def _get_searchers(queue, config):
  count = config.get('count', 1)
  result = {'query': config['search-queries']}
  while count > 0:
    searcher = _base.TweetSearcher(queue, **config)
    result.setdefault('searchers', []).append(searcher)
    count -= 1
  return result


def _get_handlers(tweet_queue, action_queue, config):
  count = config.get('count', 1)
  handlers = []
  while count > 0:
    handlers.append(_base.ContestTweetHandler(
      tweet_queue, action_queue, **config
    ))
    count -= 1
  return handlers


def _spin_handlers(handlers):
  for handler in handlers:
    threading.Thread(
      target=handler.handle
    ).start()


def _spin_searchers(queries, searchers):
  if not isinstance(queries, collections.Iterable):
    queries = (queries, )
  for query in queries:
    for searcher in searchers:
      threading.Thread(
        target=searcher.search, args=(query,)
      ).start()


def _spin_executors(executors):
  if not isinstance(executors, collections.Iterable):
    executors = (executors, )
  for executor in executors:
    threading.Thread(
      target=executor.execute
    ).start()


parser = argparse.ArgumentParser()

parser.add_argument(
  '-a', '--agents',
  help='File containing user-agents',
  dest='agents_file',
  default='user-agents.txt'
)
parser.add_argument(
  '-i', '--invalidate',
  help='Invalidate all saved sessions',
  dest='invalidate',
  action='store_true'
)
parser.add_argument(
  '-c', '--config',
  help='Configuration file',
  dest='config',
  default='config.json'
)
parser.add_argument(
  '-e', '--executor-count',
  help='How many executors should we have running',
  dest='executor_count',
  default=2
)

args = parser.parse_args()

if not args.config:
  _base.logger.error('You need to provide the path to the config.json file')
  exit()

config = {}
user_agents = []

try:
  with open(args.config, encoding='UTF-8') as fp:
    config = json.loads(fp.read())
    config['searchers']; config['handlers'] # quick check
except Exception as ex:
  exit(f'Failed to read config.json .\n {ex}')

if args.invalidate:
  cache = _base._get_cache_fs()
  dir = cache.getsyspath('/')
  for the_file in os.listdir(dir):
    file_path = os.path.join(dir, the_file)
    try:
      if os.path.isfile(file_path):
        os.unlink(file_path)
    except Exception as e:
      pass
    else:
      _base.logger.info('All stored data has been cleared')

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

for searcher in config['searchers']:
  searcher = _get_searchers(tweet_queue, searcher)
  _spin_searchers(searcher['query'], searcher['searchers'])

for handler in config['handlers']:
  handler = _get_handlers(tweet_queue, action_queue, handler)
  _spin_handlers(handler)

_spin_executors(_base.ActionExecutor(action_queue, delay=2))

tweet_queue.join(); action_queue.join()

#!/usr/bin/env python3
# -*- coding: future_fstrings -*-
import os
import sys
import json
import shutil
import argparse
import getpass
import queue
import threading
import collections
import _base
from handlers import ContestTweetHandler
from tweebot import logger, ua_provider

if sys.version_info[0] < 3:
  logger.error('Python 3 or a more recent version is required.')
  exit()

parser = argparse.ArgumentParser()
default_config_path = os.path.join(
  os.path.dirname(__file__), 'config/'
)

parser.add_argument(
  '-a', '--agents',
  help='File containing user-agents',
  dest='agents_file',
  default=f'{default_config_path}/user-agents.txt'
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
  default=f'{default_config_path}/config.json'
)
parser.add_argument(
  '-e', '--executor-count',
  help='How many executors should we have running',
  dest='executor_count',
  default=2
)

args = parser.parse_args()

if args.invalidate:
  _base.clear()

if args.agents_file:
  ua_provider.load(args.agents_file)

if not args.config:
  logger.error('You need to provide the path to the config.json file')
  exit()

config = {}

try:
  with open(args.config, encoding='UTF-8') as fp:
    config = json.loads(fp.read())
    config['searchers']; config['handlers'] # quick check
except Exception as ex:
  exit(f'Failed to read config.json .\n {ex}')

if not 'executors' in config:
  if not args.executor_count:
    logger.error(
      '''You will need to provide configurations
      for the executor object. Check the docs for more info.'''
    )
    exit()
  config['executors'] = [{
    'count': args.executor_count,
    'request-delay': 2
  }]

while True:
  username = input('Twitter username: ')
  if not _base._is_logged(username):
    password = getpass.getpass(prompt='Twitter password: ')
    try:
      _base.login(username, password)
    except _base.InvalidCredentials:
      logger.error('Invalid credentials.Try again')
      continue
  os.environ['username'] = username
  break


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
    handlers.append(ContestTweetHandler(
      tweet_queue, action_queue, **config
    ))
    count -= 1
  return handlers


def _get_executors(action_queue, **config):
  count = config.get('count', 1)
  executors = []
  while count > 0:
    executors.append(_base.ActionExecutor(
      action_queue, config['request-delay']
    ))
    count -= 1
  return executors


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
        target=searcher.search,
        args=(query,)
      ).start()


def _spin_executors(executors):
  if not isinstance(executors, collections.Iterable):
    executors = (executors, )
  for executor in executors:
    threading.Thread(
      target=executor.execute
    ).start()


tweet_queue = queue.Queue()
action_queue = queue.Queue()

for params in config['searchers']:
  searcher = _get_searchers(tweet_queue, params)
  _spin_searchers(searcher['query'], searcher['searchers'])

for params in config['handlers']:
  handler = _get_handlers(tweet_queue, action_queue, params)
  _spin_handlers(handler)

for params in config['executors']:
  executors = _get_executors(action_queue, **params)
  _spin_executors(executors)

tweet_queue.join(); action_queue.join()

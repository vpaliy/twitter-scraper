# -*- coding: future_fstrings -*-
import re
from tweebot import logger
from _base import BaseTweetHandler
from actions import *


class ContestTweetHandler(BaseTweetHandler):
  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    self._follow_re = re.compile('follow', re.IGNORECASE)
    self._like_re = re.compile('|'.join(['like', 'fav']), re.IGNORECASE)
    self._retweet_re = re.compile('|'.join(['rt', 'retweet']), re.IGNORECASE)

  def process_tweet(self, tweet):
    text, user = tweet.text, tweet.user
    actions = []
    if self._retweet_re.search(text):
      actions.append(LikeAction(tweet))
      actions.append(RetweetAction(tweet))
      if not user.is_followed:
        actions.append(FollowAction(tweet))
      else:
        logger.warning(f'already following @{user.username}')
    else:
      if self._follow_re.search(text):
        if not user.is_followed:
          actions.append(FollowAction(tweet))
          actions.append(LikeAction(tweet))
        else:
          logger.warning(f'already following @{user.username}')
          if self._like_re.search(text):
            actions.append(LikeAction(tweet))
    if len(actions) > 0:
      self._action_queue.put(actions)

# -*- coding: future_fstrings -*-
import requests
import time
import constants
from tweebot import logger
from tweebot._base import Action


class FollowAction(Action):
  def execute(self, delay):
    user = self.tweet.user
    res = self.make_request(constants.FOLLOW_URL, error_delay=delay)
    if res.status_code != 200:
      logger.error(f'failed to follow {user.username}')
    else:
      logger.info(f'followed: {user.username}')

  @property
  def payload(self):
    user = self.tweet.user
    return {
      'user_id': user.id,
      'skip_status': False
    }


class RetweetAction(Action):
  __slots__ = Action.__slots__ + ('comment', )

  def __init__(self, tweet, comment=None):
    super().__init__(tweet)
    self.comment = comment

  def execute(self, delay):
    time.sleep(delay)

    res = self.make_request(url=constants.RETWEET_URL, error_delay=delay)

    if res.status_code != 200:
      logger.error(f'failed to retweet: {self.tweet}')
    else:
      logger.info(f'retweeted: {self.tweet}')

  @property
  def payload(self):
    return {
      'id': self.tweet.id,
      'tweet_stat_count': self.tweet.retweet_count
    }


class LikeAction(Action):
  def execute(self, delay):
    time.sleep(delay)

    res = self.make_request(url=constants.LIKE_URL, error_delay=delay)

    if res.status_code != 200:
      logger.error(f'failed to like: {self.tweet}')
    else:
      logger.info(f'liked: {self.tweet}')

  @property
  def payload(self):
    return {
      'id': self.tweet.id,
      'tweet_stat_count': self.tweet.retweet_count
    }

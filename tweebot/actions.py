import os
import _base
import requests
import time
import fake_useragent
import _thread
import constants
from tweebot import logger
from abc import ABC, abstractmethod


class Action(ABC):
  __slots__ = ('tweet', )

  def __init__(self, tweet):
    self.tweet = tweet

  def get_session(self):
    username = os.environ['username']
    session = _base.create_session(username)
    cookies = requests.utils.dict_from_cookiejar(session.cookies)

    if 'ct0' not in cookies:
      logger.error(f'{username} session has expired. Log in again')
      _thread.interrupt_main()

    session.headers['User-Agent'] = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) snap Chromium/70.0.3538.77 Chrome/70.0.3538.77 Safari/537.36'
    session.headers['Authorization'] = constants.BEARER
    session.headers['X-Twitter-Auth-Type'] = 'OAuth2Session'
    session.headers['X-Twitter-Active-User'] = 'yes'
    session.headers['Origin'] = constants.BASE_URL
    session.headers['x-csrf-token'] = cookies['ct0']

    return session

  def make_request(self, url, method='post',
                   error_delay=5, tries=10, allow_redirects=False):
    with self.get_session() as session:
      while tries > 0:
        try:
          request = getattr(session, method.lower())
          res = request(
            url = url,
            data = self.payload,
            allow_redirects = allow_redirects
          )
          return res
        except Exception as ex:
          time.sleep(error_delay)
          tries -= 1

  @abstractmethod
  def execute(self, delay):
    """Do the action """

  @property
  @abstractmethod
  def payload(self):
    pass


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
      logger.error(f'failed to retweet: {self.tweet.id}')
    else:
      logger.info(f'retweeted: {self.tweet.id}')

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
      logger.error(f'failed to like: {self.tweet.id}')
    else:
      logger.info(f'liked: {self.tweet.id}')

  @property
  def payload(self):
    return {
      'id': self.tweet.id,
      'tweet_stat_count': self.tweet.retweet_count
    }

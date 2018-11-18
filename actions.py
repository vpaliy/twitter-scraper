import os
import _base
import requests
import time
import fake_useragent

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
      _base.logger(f'{username} session has expired. Log in again')
      exit()

    session.headers['user-agent'] = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) snap Chromium/70.0.3538.77 Chrome/70.0.3538.77 Safari/537.36'
    session.headers['authorization'] = _base.BEARER
    session.headers['x-twitter-auth-type'] = 'OAuth2Session'
    session.headers['x-twitter-active-user'] = 'yes'
    session.headers['origin'] = 'https://twitter.com'
    session.headers['x-csrf-token'] = cookies['ct0']

    return session

  def make_request(self, url, method='post', payload=None,
                   params=None, error_delay=5, tries=10, allow_redirects=False):
    with self.get_session() as session:
      while tries > 0:
        try:
          request = getattr(session, method)
          res = request(url, data=payload, params=params, allow_redirects=allow_redirects)
          return res
        except Exception as ex:
          _base.logger.error(f'request has failed {ex}')
          time.sleep(error_delay)
          tries -= 1

  @abstractmethod
  def execute(self, delay):
    """Do the action """


class FollowAction(Action):
  def execute(self, delay):
    user = self.tweet.user

    payload = {
      'user_id': user.id,
      'skip_status': False
    }

    res = self.make_request(
      _base.FOLLOW_URL, error_delay=delay, payload=payload
    )
    if res.status_code != 200:
      _base.logger.error(f'failed to follow {user.username}')
    else:
      _base.logger.info(f'followed: {user.username}')


class RetweetAction(Action):
  __slots__ = Action.__slots__ + ('comment', )

  def __init__(self, tweet, comment=None):
    super().__init__(tweet)
    self.comment = comment

  def execute(self, delay):
    time.sleep(delay)
    payload = {
      'id': self.tweet.id,
      'tweet_stat_count': self.tweet.retweet_count
    }

    res = self.make_request(
      url=_base.RETWEET_URL, error_delay=delay, payload=payload
    )

    if res.status_code != 200:
      _base.logger.error(f'failed to retweet: {self.tweet.id}')
    else:
      _base.logger.info(f'retweeted: {self.tweet.id}')


class MessageAction(Action):
  def __init__(self, id, message):
    self._id = id
    self._message = message

  def execute(self, delay):
    pass


class LikeAction(Action):
  def execute(self, delay):
    time.sleep(delay)

    payload = {
      'id': self.tweet.id,
      'tweet_stat_count': self.tweet.retweet_count
    }

    res = self.make_request(
      url=_base.LIKE_URL, error_delay=delay, payload=payload
    )

    if res.status_code != 200:
      _base.logger.error(f'failed to like: {self.tweet.id}')
    else:
      _base.logger.info(f'liked: {self.tweet.id}')

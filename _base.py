import os
import time
import datetime
import logging
import json
import random
import collections
import requests
import fake_useragent
import typing
import fs
import re
import coloredlogs
import abc
import dateutil.relativedelta

from actions import FollowAction, RetweetAction, LikeAction, Action
from six.moves.http_cookiejar import FileCookieJar, LWPCookieJar
from abc import abstractmethod, ABC
from bs4 import BeautifulSoup
from bs4.element import NavigableString, Tag

__version__ = "0.0.1"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
coloredlogs.install(level='INFO', logger=logger)
coloredlogs.install(fmt='%(asctime)s | %(message)s')

BASE_URL = 'https://twitter.com'
TIMELINE_SEARCH_URL = 'https://twitter.com/i/search/timeline'
SEARCH_URL = 'https://twitter.com/search/'
LOGIN_URL = 'https://twitter.com/login'
SESSIONS_URL = 'https://twitter.com/sessions'
RETWEET_URL = 'https://api.twitter.com/1.1/statuses/retweet.json'
FOLLOW_URL = 'https://api.twitter.com/1.1/friendships/create.json'
LIKE_URL = 'https://api.twitter.com/1.1/favorites/create.json'

COOKIES_FILE = 'cookies.txt'
BEARER = 'Bearer AAAAAAAAAAAAAAAAAAAAAPYXBAAAAAAACLXUNDekMxqa8h%2F40K4moUkGsoc%3DTYfbDKbT3jJPCEVnMYqilB28NHfOPqkca3qaAxGfsyKCs0wRbw'

_sentinel = object()


class TimeoutSession(requests.Session):
  def request(self, *args, **kwargs):
    if kwargs.get('timeout') is None:
      kwargs['timeout'] = os.environ.get('timeout', 10)
    return super(TimeoutSession, self).request(*args, **kwargs)


class User(object):
  __slots__ = ('id', 'username', 'is_followed')

  def __init__(self, id, username, is_followed):
    self.id = id
    self.username = username
    self.is_followed = is_followed


class AtLink(object):
  __slots__ = ('user_id', 'username', 'link')

  def __init__(self, user_id, username):
    self.user_id = user_id
    self.username = username
    self.link = BASE_URL + username


class Tweet(object):
  __slots__ = ('id', 'user', 'text', 'links', 'retweet_count')

  def __init__(self, id, user, text, links, retweet_count):
    self.id = id
    self.user = user
    self.text = text
    self.links = links
    self.retweet_count = retweet_count


class TweetHandler(abc.ABC):
  _AVOID_KEYWORDS = {'bot', 'fake', 'RT @./S'}
  _AVOID_USERNAMES = {'bot', 'bot spotter'}

  def __init__(self, queue, action_queue, **kwargs):
    if not queue or not action_queue:
      raise RuntimeError('Queues should be provided')
    self._queue = queue
    self._action_queue = action_queue
    self._keywords = kwargs['keywords']
    self._avoid_keywords = kwargs.get('avoid-keywords', self._AVOID_KEYWORDS)
    self._avoid_usernames = kwargs.get('avoid-usernames', self._AVOID_USERNAMES)

  def handle(self):
    pattern = re.compile(
      r'^((.*? )?({find})([ ,.!?]|$)){{3}}.*$'.format(
      find='|'.join(self._keywords),
    ), re.IGNORECASE)

    avoid_keywords = re.compile(
      r'(?i)\b({avoid})\b[^a-z\s]*'.format(
      avoid='|'.join(self._avoid_keywords)
    ))

    avoid_usernames = re.compile(
      r'(?i)\b({avoid})\b[^a-z\s]*'.format(
      avoid='|'.join(self._avoid_usernames)
    ))

    while True:
      tweet = self._queue.get()
      if tweet is _sentinel:
        self._queue.put(_sentinel)
        break
      user = tweet.user
      if avoid_usernames.search(user.username):
        logger.warning(f'tweet from forbidden {user.username}, skipping')
        continue
      if avoid_keywords.search(tweet.text):
        continue
      if pattern.search(tweet.text):
        self.process_tweet(tweet)

  @abstractmethod
  def process_tweet(self, tweet):
    raise NotImplemented


class ContestTweetHandler(TweetHandler):
  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    self._follow_re = re.compile('follow', re.IGNORECASE)
    self._like_re = re.compile('|'.join(['like', 'fav']), re.IGNORECASE)
    self._rt_re = re.compile('|'.join(['rt', 'retweet']), re.IGNORECASE)

  def process_tweet(self, tweet):
    text, user = tweet.text, tweet.user
    actions = []
    if self._rt_re.search(text):
      actions.append(LikeAction(tweet))
      actions.append(RetweetAction(tweet))
      if not user.is_followed:
        actions.append(FollowAction(tweet))
      else:
        logger.warning(f'already following {user.username}')
    else:
      if self._follow_re.search(text):
        if not user.is_followed:
          actions.append(FollowAction(tweet))
          actions.append(LikeAction(tweet))
        else:
          logger.warning(f'already following {user.username}')
          if self._like_re.search(text):
            actions.append(LikeAction(tweet))
    if len(actions) > 0:
      self._action_queue.put(actions)


class ActionExecutor(object):
  def __init__(self, queue, delay=30):
    self._queue = queue
    self._delay = delay

  def execute(self):
    while True:
      actions = self._queue.get()
      if actions is _sentinel:
        self._queue.put(_sentinel)
        break
      if not isinstance(actions, collections.Iterable):
        actions = (actions, )
      for action in actions:
        if not isinstance(action, Action):
          logger.error(f'expected object of Action type, got {type(action)}')
          continue
        action.execute(self._delay)


class InvalidCredentials(Exception):
  """Gets raised when the user enters invalid credentials."""


def _get_cache_fs():
  url = f'usercache://twitter-bot:{__name__}:{__version__}'
  return fs.open_fs(url, create=True)


def create_session(username):
  session = TimeoutSession()
  session.cookies = LWPCookieJar(
    _get_cache_fs().getsyspath(f'{username}-{COOKIES_FILE}')
  )
  try:
    typing.cast(FileCookieJar, session.cookies).load()
  except IOError:
    pass
  typing.cast(FileCookieJar, session.cookies).clear_expired_cookies()
  return session


def _is_logged(username):
  session, expired = create_session(username), False
  if session is not None:
    for cookie in session.cookies:
      if cookie.is_expired():
        expired = True
        break
      if cookie.name == 'auth_token':
        logger.info(f'You are signed in as {username}')
        return True
  if expired:
    # remove cookies for that user
    file = _get_cache_fs().getsyspath(f'{username}-{COOKIES_FILE}')
    os.remove(file)
    logger.warning(f'{username} session has expired. Please sign in.')
  else:
    logger.warning(f'No sessions found for {username}.')
  return False


def login(username, password, tries=10, delay=2):
  with create_session(username) as session:
    res = session.get(LOGIN_URL)
    soup = BeautifulSoup(res.text,"html.parser")
    token = soup.select_one("[name='authenticity_token']")['value']

    payload = {
      'session[username_or_email]':username,
      'session[password]': password,
      'authenticity_token':token,
      'ui_metrics':'{"rf":{"c6fc1daac14ef08ff96ef7aa26f8642a197bfaad9c65746a6592d55075ef01af":3,"a77e6e7ab2880be27e81075edd6cac9c0b749cc266e1cea17ffc9670a9698252":-1,"ad3dbab6c68043a1127defab5b7d37e45d17f56a6997186b3a08a27544b606e8":252,"ac2624a3b325d64286579b4a61dd242539a755a5a7fa508c44eb1c373257d569":-125},"s":"fTQyo6c8mP7d6L8Og_iS8ulzPObBOzl3Jxa2jRwmtbOBJSk4v8ClmBbF9njbZHRLZx0mTAUPsImZ4OnbZV95f-2gD6-03SZZ8buYdTDkwV-xItDu5lBVCQ_EAiv3F5EuTpVl7F52FTIykWowpNIzowvh_bhCM0_6ReTGj6990294mIKUFM_mPHCyZ    xkIUAtC3dVeYPXff92alrVFdrncrO8VnJHOlm9gnSwTLcbHvvpvC0rvtwapSbTja-cGxhxBdekFhcoFo8edCBiMB9pip-VoquZ-ddbQEbpuzE7xBhyk759yQyN4NmRFwdIjjedWYtFyOiy_XtGLp6zKvMjF8QAAAWE468LY"}',
      'authenticity_token':token,
      'remember_me':1
    }

    session.headers['Origin'] = BASE_URL
    session.headers['Referer'] = LOGIN_URL
    session.headers['Upgrade-Insecure-Requests'] = '1'

    time.sleep(5) # pause a bit

    while tries > 0:
      try:
        # random user-agent
        session.headers['User-Agent'] = fake_useragent.UserAgent().firefox
        res = session.post(SESSIONS_URL, data=payload, allow_redirects=False)
        res.raise_for_status()
        if 'location' in res.headers:
          url = res.headers['location']
          if 'locked' in url:
            logger.error('Too many attempts. Your account has been locked (60 mins).')
            exit()
          elif 'error' in url:
            raise InvalidCredentials
        if 'auth_token' in res.cookies.get_dict():
          typing.cast(FileCookieJar, session.cookies).save()
          logger.info(f'You have signed in as {username}')
          return
      except Exception as ex:
        if isinstance(ex, InvalidCredentials):
          raise
        logger.error(f'Error while signing in:\n{ex}')
        pass
      time.sleep(delay)
      tries -= 1
    # Twitter won't provide auth_token in cookies or ban
    logger.error(
    '''Failed to sign in. Your IP address (or account) may have been banned (yikes).
       Try logging in through your browser. If you can't log in, then you've been banned.'''
     )
    exit()


def _convert_to_bool(condition):
  try:
    result = json.loads(condition.lower())
  except:
    result = False
  return result


def _create_user(raw_content):
  if not raw_content:
    return None
  id = raw_content.get('data-user-id')
  if not id:
    return None
  username = raw_content.get('data-screen-name')
  if raw_content.has_attr('data-you-follow'):
    is_followed = _convert_to_bool(raw_content.get('data-you-follow'))
  else:
    is_followed = False
  return User(id, username, is_followed)


def _create_tweet(id, user, raw_tweet):
  raw_content = raw_tweet.find(class_='js-tweet-text')
  count = raw_tweet.find(class_='ProfileTweet-actionCount')
  if not raw_content:
    return None
  text, links = str(), set()
  for child in raw_content.contents:
    if isinstance(child, NavigableString):
      text += str(child)
    elif child.has_attr('href'):
      cls, href = child.get('class'), child.get('href')
      if 'twitter-atreply' in cls:
        user_id = child.get('data-mentioned-user-id')
        links.add(AtLink(user_id, href))
        text += child.text
  return Tweet(id, user, text, links, count)


def is_original_tweet(raw_content):
  if raw_content.has_attr('data-has-parent-tweet'):
    if _convert_to_bool(raw_content.get('data-has-parent-tweet')):
      return False
  if raw_content.has_attr('data-is-reply-to'):
    return not _convert_to_bool(raw_content.get('data-is-reply-to'))
  return True


def is_retweeted(raw_content):
  if raw_content.has_attr('data-my-retweet-id'):
    return True
  return 'retweeted' in raw_content.get('class')


def has_picture(raw_content):
  return 'has-cards' in raw_content.get('class')


class TweetSearcher(object):
  def __init__(self, queue, **kwargs):
    if not queue:
      raise ValueError('Queue should be provided')
    if 'scan-time' in kwargs:
      kwargs['scan-time'] = time.time() + kwargs['scan-time']
    if 'month-diff' in kwargs:
      delta = dateutil.relativedelta.relativedelta(months=kwargs['month-diff'])
      kwargs['month-diff'] = datetime.datetime.now() - delta
    self._endtime = kwargs.get('scan-time', time.time() + 60 * 25)
    self._req_delay = kwargs.get('request-delay', 5)
    self._error_delay = kwargs.get('error-request-delay', 5)
    self._empty_delay = kwargs.get('empty-request-delay', 15)
    self._error_tries = kwargs.get('error-tries', 5)
    self._empty_tries = kwargs.get('empty-tries', 5)
    self._tweets_limit = kwargs.get('tweets-limit')
    self._with_pics_only = kwargs.get('pictures-only', True)
    self._verified_only = kwargs.get('verified-accounts-only')
    self._month_diff = kwargs.get('month-diff')
    self._queue = queue
    self._cache = set()

  def _make_request(self, query, limit=None):
    params = {
      'vertical': 'default',
      'src': 'typd',
      'include_available_features': '1',
      'include_entities': '1',
      'q': query
    }

    if bool(random.getrandbits(1)):
      params['f'] = 'tweets' # this will fetch the latest

    if limit is not None:
      params['max_position'] = limit

    tries = self._error_tries
    with create_session(os.environ['username']) as session:
      # set headers
      session.headers['Accept'] = 'application/json, text/javascript, */*; q=0.01'
      session.headers['Accept-Language'] = 'en-US,en;q=0.5'
      session.headers['Referer'] = SEARCH_URL
      session.headers['X-Requested-With'] = 'XMLHttpRequest'
      session.headers['X-Twitter-Active-User'] = 'yes'
      while tries > 0:
        try:
          session.headers['User-Agent'] = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) snap Chromium/70.0.3538.77 Chrome/70.0.3538.77 Safari/537.36'
          res = session.get(TIMELINE_SEARCH_URL, params=params)
          data = res.json()
          # check if we have what we need
          data['inner']['items_html']
          return data['inner']
        except Exception as e:
          logger.error(f'{self._error_tries - tries }-search request has failed:\n{e}')
          time.sleep(self._error_delay)
          tries -= 1
    logger.error(f'failed to make the search request: {query}')
    exit()

  def _is_date_valid(self, raw_tweet):
    if self._month_diff is not None:
      date = raw_tweet.find(class_='tweet-timestamp')
      date = datetime.datetime.strptime(date.get('title'), '%I:%M %p - %d %b %Y')
      return self._month_diff <= date
    return True

  def search(self, query):
    if not query:
      raise TypeError('search takes a query param')
    tweet_count, limit = 0, None
    empty_tries = self._empty_tries
    while time.time() < self._endtime and empty_tries > 0:
      data = self._make_request(query, limit)
      soup = BeautifulSoup(data['items_html'], 'html.parser')
      tweets = soup.findAll('li',
        id = lambda id: id and id.startswith('stream-item-tweet-')
      )
      # nothing has been found
      if not tweets or len(tweets) == 0:
        empty_tries -= 1
        time.sleep(self._empty_delay)
        continue
      # fetch tweet data
      for tweet in tweets:
        id = tweet.get('data-item-id')
        raw = tweet.find(class_='js-stream-tweet')
        # skip if too old
        if not self._is_date_valid(raw):
          continue
        # filter retweeted
        if id in self._cache or is_retweeted(raw):
          username = raw.get('data-screen-name')
          logger.warning(f'already retweeted {id} by @{username}')
          continue
        elif len(self._cache) == 500:
          self._cache.clear()
        # pics only
        if self._with_pics_only and not has_picture(raw):
          continue
        # check if it's original
        if not is_original_tweet(raw):
          continue
        self._cache.add(id)

        user = _create_user(raw)
        tweet = _create_tweet(id, user, tweet)

        if tweet is not None:
          self._queue.put(tweet)
          tweet_count += 1

        if self._tweets_limit is not None:
          if self._tweets_limit <= tweet_count:
            self._finish(query, tweet_count)
            return

      max = tweets[-1].get('data-item-id')
      min = tweets[0].get('data-item-id')

      if max is not min:
        limit = f'TWEET-{max}-{min}'
      time.sleep(self._req_delay)
    self._finish(query, tweet_count)

  def _finish(self, query, tweet_count):
    logger.info(f'{query} | Total tweets found:{tweet_count}')
    self._queue.put(_sentinel)

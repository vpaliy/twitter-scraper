# -*- coding: future_fstrings -*-
import random
import fake_useragent

class UserAgentProvider(object):
  def __init__(self, agents=None):
    self._agents = agents or []

  def fetch(self):
    if self._agents and len(self._agents) > 0:
      return random.choice(self._agents)
    # TODO: not sure
    return fake_useragent.random

  def load(self, agents_file):
    try:
      with open(agents_file, encoding='utf-8') as fp:
        for agent in fp:
          self._agents.append(agent.strip())
    except Exception as ex:
      exit(f'Failed to open/read the user-agents file.\n({ex})')

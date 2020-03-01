# twitter-scraper

<img src="https://github.com/vpaliy/twitter-santa/blob/master/art/final.jpg" />

## Why?
This [Def Con talk](https://www.youtube.com/watch?v=iAOOdYsK7MM) was my motivation behind creating this project. I built a more general version of the bot discussed in the talk;

Use this bot for educational purposes only.

## Basics
Before we get started, you need to know that this bot uses Python >= 3 only.

This bot contains a small number of command line arguments that you can pass in.
Here is the complete list of them:
- `-a` or `--agents` (file containing user agents to be used while making HTTP requests to Twitter)
- `-i` or `--invalidate` (erase all saved sessions; this includes cookies or any other data saved from previous web requests)
- `-c` or `--config` (file containing the configurations for the bot; if not provided, we will used the default configurations in the config directory)
- `-e` or `--executor-count` (specifies how many executors - explained below - we need to launch)

Speaking of interface design, I would define three important abstractions here:
- Searchers (primary responsibility is to search for the desired tweets and pass them along to handlers)

- Handlers (responsible for filtering out and parsing tweets to determine appropriate actions that should be applied to those tweets. When finished, pass the actions to executors)

- Actions (many tweets request different actions to participate in a contest - retweet, like, follow, comment, etc. You can also customize it and add yours)

- Executors (receive a list of actions from handlers and execute them. Plain and simple)

Let's dive into the configuration of those objects. Here's a sample JSON file:

```json
{
    "searchers": [{
        "count": 1,
        "search-queries": ["rt to win", "#contest"],
        "scan-time": 560,
        "month-diff": 1,
        "request-delay": 5,
        "error-delay": 5,
        "empty-request-delay": 20,
        "error-tries": 5,
        "empty-tries": 5
    },{
        "count": 2,
        "search-queries": ["rt to donate", "#donation", "RT", "donation"],
        "scan-time": 560,
        "month-diff": 1,
        "tweet-limit": 500
    }],

    "handlers": [{
        "count": 5,
        "keywords": ["win", "winner", "lucky"],
        "avoid-usernames": ["bot", "bot spotter", "bot spotting"]
    },{
        "count": 2,
        "keywords": ["charity", "donate", "donation"],
        "avoid-usernames": ["bot", "bot spotter", "bot spotting"]
    }],

    "executors": [{
      "count": 2,
      "request-delay": 5
    }]
}
```

**Searchers**:
 - `count` (defines how many searchers with the same configuration we need to create. **Optional**)

 - `search-queries` (an array of strings that should be used for searching tweets. **Required**)

 - `scan-time` (specifies for how long this searcher should be scrapping Twitter. **Optional**)

 - `month-diff` (defines the "expiration date" for tweets in terms of months. For instance, if 1 is specified, then we would only accept tweets that have been tweeted within last month. **Optional**)

 - `request-delay` (specifies for how long this searcher should wait before making an HTTP request. **Optional**)

 - `error-delay` (specifies for how long this searcher should wait before retrying an HTTP request after an error has occurred. **Optional**)

 - `empty-request-delay` (specifies for how long this searcher should wait before making another HTTP request after getting an empty list of tweets. **Optional**)

 - `error-tries` (specifies how many error tries are allowed before terminating the bot. **Optional**)

 - `empty-tries` (specifies how many "empty" tries are allowed before terminating the current searcher. **Optional**)

 - `pictures-only` (true/false values. Should every tweet contain an image? **Optional**)

 - `verified-accounts-only` (true/false values. Should we search for tweets from verified accounts only? **Optional**)


**Handlers**:
  - `count` (defines how many handlers with the same configuration we need to create. **Optional**)

  - `keywords` (an array of strings that every tweet should contain in order to be processed. **Required**)

  - `avoid-usernames` (an array of usernames that we should avoid - bot spotters as an example. **Optional**)

  - `avoid-keywords` (an array of usernames that we should avoid - bot spotters as an example. **Optional**)


Mostly all of the optional configuration fields have a default value. You can look at the source code for more information.

# Installation

### Option 1: Install via git clone

This would be the easiest way to play around with this bot:
```
$ git clone https://github.com/vpaliy/twitter-santa.git
$ cd twitter-santa/
$ python3 tweebot/
```

### Option 2: Download with pip3
 Coming soon...

# Disclaimer
This bot has been written only for educational purposes.
I hold no liability for what you do with this bot or what happens to you by using this bot.
Abusing this bot may result in a permanent ban from Twitter (your account or IP address).

# License
```
MIT License

Copyright (c) 2018 Vasyl Paliy

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

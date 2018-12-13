# twitter-santa

## Why?
This [Def Con talk](https://www.youtube.com/watch?v=iAOOdYsK7MM) was the motivation behind creating this project. In short, a guy built a bot to retweet twitter contests and won a lot of random stuff. He's never released the source code, so I decided that implementing a bot like this would be a great way to spend weekends. Consequently, I built a more general version of the bot discussed in the talk; you can configure the bot and use it for different purposes than retweeting contests (RT to make donations, for instance). However, I encourage you to use this bot for educational purposes only.

## Basics
Before we get started, you need to know that this bot uses Python 3 only (I just couldn't restrain myself from using f-Strings).

This bot contains a small number of command line arguments that you can pass in.
Here is the complete list of them:
- `-a` or `--agents` (file containing user agents to be used while making HTTP requests to Twitter)
- `-i` or `--invalidate` (erase all saved sessions; this includes cookies or any other data saved from previous web requests)
- `-c` or `--config` (file containing the configurations for the bot; if not provided, we will used the default configurations in the config directory)
- `-e` or `--executor-count` (specifies how many executors - explained below - we need to launch)

Speaking of interface design, I would define three important abstractions here:
- Searchers (main responsibility is to search for the desired tweets and pass them along to handlers)

- Handlers (responsible for filtering out and parsing tweets to determine appropriate actions that should be applied to those tweets. When finished, pass the actions to executors)

- Actions (many tweets request different actions to participate in a contest - retweet, like, follow, comment, etc. You can also customize it and add yours)

- Executors (receive a list of actions from handlers and execute them. Plain and simple)

Let's dive into configuration of those objects. Here's a sample JSON file:

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

`Searchers`:
 - count (defines how many searchers with the exact same configuration we need to create. Optional)

 - search-queries (an array of strings that should be used for searching tweets. Required)

 - scan-time (specifies for how long this searcher should be scrapping Twitter. Optional)

 - month-diff (defines the "expiration date" for tweets in terms of months. For instance, if 1 is specified, then we would only accept tweets that have been tweeted within last month. Optional)

 - request-delay (


# Disclaimer
This bot has been written only for educational purposes.
I hold no liability for what you do with this bot or what happens to you by using this bot.
Abusing this bot may result in a permanent ban from Twitter (your account or IP address).

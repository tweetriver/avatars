# TweetRiver Avatar service

The service is located [at AppSpot][1]

The URL pattern is:
    GET http://http://tweetriver-avatars.appspot.com/SCREEN_NAME
and
    GET http://http://tweetriver-avatars.appspot.com/SCREEN_NAME/GUESSED_URL

## Running it locally

1. Install the [Google App Engine SDK][2] (and make sure you install the 
   commandline tools)
2. Run `rake run`

## Deploying it

1. Make sure you have access to the application (ask someone)
2. Run `rake deploy` and provide your credentials

[1]: http://tweetriver-avatars.appspot.com
[2]: http://code.google.com/appengine/downloads.html
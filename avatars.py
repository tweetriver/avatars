import logging
from base64 import b64encode

from google.appengine.api import memcache
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.api import urlfetch 

from BeautifulSoup import BeautifulSoup

DEFAULT_PROFILE_IMAGE_URL = "http://static.twitter.com/images/default_profile_normal.png"

# We pretend to be the iPhone for the Twitter mobile site
IPHONE = "Mozilla/5.0 (iPhone; U; CPU like Mac OS X; en) AppleWebKit/420+ (KHTML, like Gecko) Version/3.0 Mobile/1A543a Safari/419.3"

class Avatar(object):
  
  def __init__(self, screen_name, guessed_url=None):
    self.screen_name = screen_name
    self.key = "avatar_" + screen_name
    self.guessed_url = guessed_url
    self.profile_url = "http://m.twitter.com/%s" % screen_name
    
  @property
  def url(self):
    """
    Retrieve the URL for the given screen_name
    Try to get it from memcache first, otherwise try the guess URL
    or actually go retrieve it (and store it in memcache for 15 minutes)
    """
    try:
      url = memcache.get(self.key)
    except Exception, e:
      logging.error('Error retrieving information from memcache (%s)' % e)
    if url:
      logging.debug("[%s] Retrieved URL from memcache" % self.screen_name)
      return url
    else:
      url = self._verified_guess() or self._url()
      if url:
        try:
          logging.debug("[%s] Adding URL to memcache" % self.screen_name)
          memcache.add(self.key, url, 60 * 15)
        except Exception, e:
          logging.error('Error adding information to memcache (%s)' % e)
      return url
  
  def _verified_guess(self):
    """
    Verify (with a HEAD) that the "guessed" URL actually exists
    """
    try:
      urlfetch.fetch(self.guessed_url, method='HEAD', follow_redirects=False)
      logging.debug("[%s] Verified URL" % self.screen_name)
      return self.guessed_url
    except:
      logging.debug("[%s] Could not verify URL" % self.screen_name)
      return None
  
  def _url(self):
    """
    Retrieve the profile image URL
    """
    retrievers = [
      ProfileRetriever("mobile", "http://m.twitter.com/%s" % self.screen_name, lambda soup: soup.find("td", {"class": "g"}).img['src']),
      ProfileRetriever("normal", "http://twitter.com/%s" % self.screen_name, lambda soup: soup.find("img", {"id": "profile-image"})['src'])
    ]
    for retriever in retrievers:
      url = retriever.retrieve()
      if url:
        return url
    else:
      logging.debug("[%s] Could not find profile image, storing default" % self.screen_name)
      return DEFAULT_PROFILE_IMAGE_URL 
      
class ProfileRetriever(object):
  
  def __init__(self, name, profile_url, finder_func):
    self.name = name
    self.profile_url = profile_url
    self.finder_func = finder_func
    
  def retrieve(self):
    profile = self._get()
    if profile:
      try:
        logging.debug("Parsing '%s' profile" % self.profile_url)
        # logging.debug(repr("%s" % profile))
        soup = BeautifulSoup(profile)
      except Exception, e:
        logging.warn("Could not parse profile (%s)" % e)
        return None
      try:
        return self.finder_func(soup)
      except Exception, e:
        logging.warn("Could not find URL in profile (%s)" % e)
        return None
    else:
      return None
    
  def _get(self):
    try:
      logging.debug("Retrieving '%s' profile" % self.name)
      return urlfetch.fetch(self.profile_url, headers={'User-Agent': IPHONE}, follow_redirects=False).content
    except Exception, e:
      logging.debug("Could not retrieve '%s' profile (%s for %s)" % (self.name, e, self.profile_url))
      return None

class App(webapp.RequestHandler):  
  def get(self, screen_name, guessed_url=None):
    if len(screen_name):
      if guessed_url:
        guessed_url = b64encode(guessed_url)
      avatar = Avatar(screen_name, guessed_url)
      if avatar.url and len(avatar.url):
        self.redirect(avatar.url)
      else:
        logging.debug("[%s] No avatar URL found" % screen_name)
        self.response.set_status(500, "Error")
    else:
      logging.debug("Screen name not provided")
      self.response.set_status(500, "Error")

application = webapp.WSGIApplication([(r'/(.*)/(.*)', App),
                                      (r'/(.*)', App)])
def main():
  """
  Starts the app
  """
  logging.getLogger().setLevel(logging.INFO)
  run_wsgi_app(application)

if __name__ == "__main__":
  main()
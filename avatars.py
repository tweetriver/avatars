import logging

from google.appengine.api import memcache
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.api import urlfetch 

from BeautifulSoup import BeautifulSoup

DEFAULT_PROFILE_IMAGE_URL = "http://static.twitter.com/images/default_profile_normal.png"

class Avatar:
  
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
      if url is not None:
        logging.debug("[%s] Retrieved URL from memcache" % self.screen_name)
        return url
      else:
        url = self._verified_guess() or self._url()
        if url:
          logging.debug("[%s] Adding URL to memcache" % self.screen_name)
          memcache.add(self.key, url, 60 * 15)
        return url
    except:
      logging.error('There was an error retrieving information from memcache')
      
  
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
    try:
      profile = self._profile()
      if profile:
        logging.debug("[%s] Parsing profile" % self.screen_name)
        soup = BeautifulSoup(profile)
        image = soup.find("img", {"alt": self.screen_name})
        image_url = image['src']
        logging.debug("[%s] Found profile image, %s" % (self.screen_name, image_url))
        return image_url
      else:
        logging.debug("[%s] Could not find profile image" % self.screen_name)
        return DEFAULT_PROFILE_IMAGE_URL
    except:
      return DEFAULT_PROFILE_IMAGE_URL
    
  def _profile(self):
    """
    Retrieve the contents of the user profile
    """
    try:
      logging.debug("[%s] Retrieving profile" % self.screen_name)
      return urlfetch.fetch(self.profile_url, follow_redirects=False).content
    except Exception, e:
      logging.debug("[%s] Could not retrieve profile (%s for %s)" % (self.screen_name, e, self.profile_url))
      return None
      
class App(webapp.RequestHandler):
  def get(self, screen_name, guessed_url=None):
    if len(screen_name):
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
  logging.getLogger().setLevel(logging.DEBUG)
  run_wsgi_app(application)

if __name__ == "__main__":
  main()
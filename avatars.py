from google.appengine.api import memcache
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app

import urllib2
from BeautifulSoup import BeautifulSoup

class Avatar:
  
  def __init__(self, screen_name, guessed_url=None):
    self.screen_name = screen_name
    self.key = "avatar_" + screen_name
    self.guessed_url = guessed_url
    
  @property
  def url(self):
    url = memcache.get(self.key)
    if url is not None:
      return url
    else:
      url = self._verified_guess() or self._url()
      if url:
        memcache.add(self.key, url, 60 * 15)
      return url
  
  def _verified_guess(self):
      try:
        request = urllib2.Request(self.guessed_url)
        request.get_method = lambda: "HEAD"
        urllib2.urlopen(request)
        return self.guess_url
      except:
        return None
  
  def _url(self):
    try:
      profile = self._profile()
      if profile:
        soup = BeautifulSoup(self._profile())
        image = soup.find("img", {"alt": self.screen_name})
        return image['src']
      else:
        return None
    except:
      return None
    
  def _profile(self):
    try:
      return urllib2.urlopen("http://m.twitter.com/%s" % self.screen_name).read()
    except:
      return None
      
class App(webapp.RequestHandler):
  def get(self, screen_name, guessed_url=None):
    if len(screen_name):
      avatar = Avatar(screen_name, guessed_url)
      if avatar.url and len(avatar.url):
        self.response.out.write(avatar.url)
      else:
        self.response.set_status(404, "Not Found")
    else:
      self.response.set_status(500, "Error")

application = webapp.WSGIApplication([(r'/(.*)/(.*)', App),
                                      (r'/(.*)', App)])
def main():
  run_wsgi_app(application)

if __name__ == "__main__":
  main()
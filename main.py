import webapp2
import views
import models

config = {
  'webapp2_extras.sessions': {
    'secret_key': models.SiteConfig.get().secret_key
  }
}

app = webapp2.WSGIApplication(views.routes, config=config, debug=True)

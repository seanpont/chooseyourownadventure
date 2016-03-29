import webapp2
import views

config = {
  'webapp2_extras.sessions': {
    'secret_key': 'Made for Cedric and Alexia'
  }
}

app = webapp2.WSGIApplication(views.routes, config=config, debug=True)

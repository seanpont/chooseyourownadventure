# -*- coding: utf-8 -*-
"""
views.py

URL route handlers

Note that any handler params must match the URL route params.
For example the *say_hello* handler, handling the URL route '/hello/<username>',
  must be passed *username* as the argument.

"""
import json

import jinja2
import webapp2
from google.appengine.api import users
from webapp2_extras import sessions
from models import Story, Page, Choice
import logging
routes = []

def route(path):
  """Use to annotate handlers. eg @route('/path')"""
  def wrap(handler):
    routes.append((path, handler))
    return handler
  return wrap

jinja_env = jinja2.Environment(loader=jinja2.FileSystemLoader('templates'),
                               extensions=['jinja2.ext.autoescape',
                                           'jinja2.ext.loopcontrols',
                                           'jinja2.ext.with_'])

class BaseHandler(webapp2.RequestHandler):

  def dispatch(self):
    self.session_store = sessions.get_store(request=self.request)
    try:
      webapp2.RequestHandler.dispatch(self)
    finally:
      self.session_store.save_sessions(self.response)

  @webapp2.cached_property
  def session(self):
    return self.session_store.get_session()

  def initialize(self, request, response):
    super(BaseHandler, self).initialize(request, response)
    self.session = sessions.get_store().get_session()
    self.user = users.get_current_user()

  def render_html(self, template, **kwargs):
    jinja_template = jinja_env.get_template(template)
    html = jinja_template.render(user=self.user,
                                 **kwargs)
    self.response.out.write(html)

  def render_json(self, d):
    json_txt = json.dumps(d)
    self.response.headers['Content-Type'] = 'application/json; charset=UTF-8'
    self.response.out.write(json_txt)

  def params(self, *args):
    """get request parameter(s)"""
    if len(args) == 1:
      return self.request.get(args[0])
    return (self.request.get(arg) for arg in args)

@route('/')
class Home(BaseHandler):
  def get(self):
    self.render_html('home.html')

@route('/create')
class Create(BaseHandler):
  def get(self):
    if not self.user:
      self.redirect(users.create_login_url(self.request.uri))
      return
    story, page1 = Story.create(self.user)
    self.redirect(Edit.path_for(story, page1))

@route('/edit/story/(\d+)/page/(\d+)')
class Edit(BaseHandler):
  def get(self, story_id, page_id):
    story = Story.get_by_id(int(story_id))
    if not story:
      self.abort(404)
    page = Page.get_by_id(int(page_id), parent=story.key)
    if not page:
      self.abort(404)
    pages = list(Page.query(ancestor=story.key))
    logging.info("page % summary: %s", pages[0].key.id(), pages[0].summary())
    self.render_html('edit.html',
                     story=story,
                     page=page,
                     pages=pages,
                     path_for=Edit.path_for)

  @classmethod
  def path_for(cls, story, page):
    return '/edit/story/%s/page/%s' % (story.key.id(), page.key.id())



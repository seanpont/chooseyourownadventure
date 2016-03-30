# -*- coding: utf-8 -*-
"""
views.py

URL route handlers

Note that any handler params must match the URL route params.
For example the *say_hello* handler, handling the URL route '/hello/<username>',
  must be passed *username* as the argument.

"""
import json
import cgi
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
    self.render_html('home.html',
                     show_create=True)

@route('/edit/story')
class EditStory(BaseHandler):
  def post(self):
    if not self.user:
      self.redirect(users.create_login_url(self.request.uri))
      return
    story = Story.create(self.user)
    self.redirect(EditPage.path(story.key, story.page1_key))

@route('/edit/story/(\d+)/page/(\d+)')
class EditPage(BaseHandler):
  def get(self, story_id, page_id):
    story = Story.get_by_id(int(story_id))
    if not story:
      self.abort(404)
    page = Page.get_by_id(int(page_id), parent=story.key)
    if not page:
      self.abort(404)
    pages = list(Page.query(ancestor=story.key))
    self.render_html('edit.html',
                     story=story,
                     page=page,
                     pages=pages,
                     edit_page_path=EditPage.path,
                     add_page_path=AddPage.path)

  def post(self, story_id, page_id):
    story = Story.get_by_id(int(story_id))
    if not story:
      self.abort(404)
    page = Page.get_by_id(int(page_id), parent=story.key)
    if not page:
      self.abort(404)
    page.text = cgi.escape(self.request.get('text'))
    page.put()
    self.redirect(EditPage.path(story.key, page.key))

  @classmethod
  def path(cls, story_key, page_key):
    return '/edit/story/%s/page/%s' % (story_key.id(), page_key.id())

@route('/edit/story/(\d+)/page')
class AddPage(BaseHandler):
  def post(self, story_id):
    story = Story.get_by_id(int(story_id))
    if not story:
      self.abort(404)
    story, page = story.add_page()
    logging.info('add page %s %s', story, page)
    self.redirect(EditPage.path(story.key, page.key))

  @classmethod
  def path(cls, story_key):
    return '/edit/story/%s/page' % story_key.id()



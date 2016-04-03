# -*- coding: utf-8 -*-
"""
views.py

URL route handlers

Note that any handler params must match the URL route params.
For example the *say_hello* handler, handling the URL route '/hello/<username>',
  must be passed *username* as the argument.

"""
import cgi
import json
import logging
import re

import jinja2
import webapp2
from google.appengine.api import users
from google.appengine.ext import ndb

from models import Story, Page

routes = []
handler_path = {}

def route(path):
  """Use to annotate handlers. eg @route('/path')"""
  def wrap(handler):
    routes.append((path, handler))
    handler_path[handler.__name__] = '%s'.join(re.compile('\(.+?\)').split(path))
    return handler
  return wrap


def path_for(handler_name, *args):
  """ Cheat code for getting path for a handler """
  return handler_path[handler_name] % args


jinja_env = jinja2.Environment(loader=jinja2.FileSystemLoader('templates'),
                               extensions=['jinja2.ext.autoescape',
                                           'jinja2.ext.loopcontrols',
                                           'jinja2.ext.with_'])


class BaseHandler(webapp2.RequestHandler):

  def initialize(self, request, response):
    super(BaseHandler, self).initialize(request, response)
    self.user = users.get_current_user()

  def render_html(self, template, **kwargs):
    jinja_template = jinja_env.get_template(template)
    html = jinja_template.render(user=self.user,
                                 path_for=path_for,
                                 **kwargs)
    self.response.out.write(html)

  @staticmethod
  def json_serializer(obj):
    if isinstance(obj, users.User):
      return obj.email()
    if isinstance(obj, ndb.Key):
      return obj.urlsafe()
    raise TypeError('%s is not serializable and has no default' % obj)

  def render_json(self, d):
    json_txt = json.dumps(d, default=BaseHandler.json_serializer)
    self.response.headers['Content-Type'] = 'application/json; charset=UTF-8'
    self.response.out.write(json_txt)

  def story(self, story_id, is_author=False):
    story = Story.get_by_id(int(story_id))
    if not story:
      self.abort(404)
    if is_author and story.author != self.user:
      self.abort(401)
    return story

  def story_page(self, story_id, page_id, is_author=False):
    story = self.story(story_id, is_author)
    page = Page.get_by_id(int(page_id), parent=story.key)
    if not page:
      self.abort(404)
    return story, page


@route('/')
class Home(BaseHandler):
  def get(self):
    stories = Story.query().fetch()
    self.render_html('home.html',
                     show_create=(self.user is not None),
                     stories=stories)


@route('/sign-in')
class SignIn(BaseHandler):
  def get(self):
    if not self.user:
      self.redirect(users.create_login_url('/'))
    else:
      self.redirect('/#account')


@route('/read/story/(\d+)/page/(\d+)')
class ReadPage(BaseHandler):
  def get(self, story_id, page_id):
    story, page = self.story_page(story_id, page_id)
    self.render_html('read.html',
                     story=story,
                     page=page)


@route('/edit/story')
class CreateStory(BaseHandler):
  def post(self):
    if not self.user:
      self.redirect(users.create_login_url(path_for('Home')))
      return
    story = Story.create(self.user)
    self.redirect(path_for('EditPage', story.key.id(), story.page1_key.id()))


@route('/edit/story/(\d+)')
class EditStory(BaseHandler):
  def put(self, story_id):
    story = self.story(story_id, is_author=True)
    field_mask = self.request.get('field_mask')
    if 'title' in field_mask:
      story.title = cgi.escape(self.request.get('title'))
    story.put()
    self.render_json(story.to_dict())


@route('/edit/story/(\d+)/page/(\d+)')
class EditPage(BaseHandler):
  def get(self, story_id, page_id):
    story, page = self.story_page(story_id, page_id, is_author=True)
    pages = list(Page.query(ancestor=story.key))
    self.render_html('edit.html',
                     story=story,
                     page=page,
                     pages=pages)

  def put(self, story_id, page_id):
    story, page = self.story_page(story_id, page_id, is_author=True)
    field_mask = self.request.get('field_mask')
    if 'text' in field_mask:
      page.text = cgi.escape(self.request.get('text'))
    page.put()
    self.render_json(page.to_dict())

@route('/edit/story/(\d+)/page')
class AddPage(BaseHandler):
  def post(self, story_id):
    story = self.story(story_id, is_author=True)
    page = story.add_page()
    page_id = self.request.get('current_page', page.key.id())
    self.redirect(path_for('EditPage', story.key.id(), page_id))


@route('/edit/story/(\d+)/page:delete')
class DeletePage(BaseHandler):
  def post(self, story_id):
    story = self.story(story_id, is_author=True)
    story = story.remove_page()
    if story:
      self.redirect(path_for('EditPage', story.key.id(), story.page1_key.id()))
    else:
      self.redirect(path_for('Home'))


@route('/edit/story/(\d+)/page/(\d+)/choice')
class AddChoice(BaseHandler):
  def post(self, story_id, page_id):
    story, page = self.story_page(story_id, page_id, is_author=True)
    page.add_choice()
    self.redirect(path_for('EditPage', story_id, page_id))


@route('/edit/story/(\d+)/page/(\d+)/choice:delete')
class DeleteChoice(BaseHandler):
  def post(self, story_id, page_id):
    story, page = self.story_page(story_id, page_id, is_author=True)
    page.remove_choice()
    self.redirect(path_for('EditPage', story_id, page_id))


@route('/edit/story/(\d+)/page/(\d+)/choice/(\d+)')
class EditChoice(BaseHandler):
  def put(self, story_id, page_id, choice_id):
    story, page = self.story_page(story_id, page_id, is_author=True)
    choice = page.choices[int(choice_id)]
    field_mask = self.request.get('field_mask')
    if 'text' in field_mask:
      choice.text = cgi.escape(self.request.get('text'))
    if 'page' in field_mask:
      choice.page = int(self.request.get('page'))
    page.put()
    self.render_json(choice.to_dict())

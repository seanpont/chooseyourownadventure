from google.appengine.ext import ndb
import logging

class Story(ndb.Model):
  author = ndb.UserProperty(required=True)
  title = ndb.TextProperty(default="")
  pages = ndb.IntegerProperty(default=1)
  page1_key = ndb.KeyProperty()

  @staticmethod
  @ndb.transactional()
  def create(user):
    story = Story(author=user)
    story.put()
    page1 = Page.create(story, story.pages)
    story.page1_key = page1.key
    story.put()
    return story

  @ndb.transactional()
  def add_page(self):
    self.pages += 1
    page = Page.create(self, self.pages)
    self.put()
    return page

  @ndb.transactional()
  def remove_page(self):
    ndb.Key(Story, self.key.id(), Page, self.pages).delete()
    self.pages -= 1
    if self.pages > 0:
      self.put()
      return self
    else:
      self.key.delete()
      return None

  def summary(self):
    page1 = self.page1_key.get()
    return page1.html_text() if page1 else ""


class Choice(ndb.Model):
  # parent = Page
  id = ndb.IntegerProperty()
  text = ndb.TextProperty(default="")
  page = ndb.IntegerProperty(default=1)


class Page(ndb.Model):
  # parent = Story
  text = ndb.TextProperty(default="")
  choices = ndb.StructuredProperty(Choice, repeated=True)

  def summary(self, character_limit=100):
    return "%s. %s%s" % (
      self.key.id(),
      self.text[:character_limit],
      "..." if len(self.text) > character_limit else ""
    )

  def html_text(self):
    return (self.text
            .replace('\n', '<br>')
            .replace('&lt;b&gt;', '<b>')
            .replace('&lt;/b&gt;', '</b>')
            .replace('&lt;i&gt;', '<i>')
            .replace('&lt;/i&gt;', '</i>')
            .replace('&lt;em&gt;', '<em>')
            .replace('&lt;/em&gt;', '</em>')
            .replace('&lt;u&gt;', '<u>')
            .replace('&lt;/u&gt;', '</u>'))

  def add_choice(self):
    self.choices.append(Choice(id=len(self.choices)))
    self.put()

  def remove_choice(self):
    self.choices.pop()
    self.put()

  @staticmethod
  def create(story, page_number):
    page = Page(parent=story.key, id=page_number)
    page.put()
    return page


class SiteConfig(ndb.Model):
  secret_key = ndb.StringProperty(required=True)

  @staticmethod
  def get():
    site_config = ndb.Key('SiteConfig', 1).get()
    if not site_config:
      logging.info('Creating SiteConfig entry -- CHANGE SECRET KEY')
      site_config = SiteConfig(id=1, secret_key="Change Me!")
      site_config.put_async()
    return site_config

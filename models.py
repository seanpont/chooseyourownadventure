from google.appengine.ext import ndb
import logging

class Story(ndb.Model):
  author = ndb.UserProperty(required=True)
  title = ndb.TextProperty(required=True)
  pages = ndb.IntegerProperty(default=1)
  page1_key = ndb.KeyProperty()

  @ndb.transactional()
  def add_page(self):
    self.pages += 1
    page = Page.create(self, self.pages)
    self.put()
    return self, page

  def summary(self, char_limit=300):
    text = self.page1_key.get().text
    return "%s%s" % (
        text[:char_limit],
        "..." if len(text) > char_limit else ""
    )

  @classmethod
  def create(cls, user):
    story = Story(author=user, title="Title of the Story", pages=1)
    story.put()
    page1 = Page.create(story, story.pages)
    story.page1_key = page1.key
    story.put()
    return story


class Choice(ndb.Model):
  # parent = Page
  id = ndb.IntegerProperty()
  text = ndb.TextProperty(default="")
  page = ndb.IntegerProperty(default=0)


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
            .replace('&lt;/u&gt;', '</u>')
    )

  def add_choice(self):
    self.choices.append(Choice(id=len(self.choices)))
    self.put()


  @classmethod
  def create(cls, story, page_number):
    page = Page(parent=story.key,
                id=page_number,
                text="It was a dark and stormy night...")
    page.put()
    return page


class SiteConfig(ndb.Model):
  secret_key = ndb.StringProperty(required=True)

  @classmethod
  def get(cls):
    site_config = ndb.Key('SiteConfig', 1).get()
    if not site_config:
      logging.info('Creating SiteConfig entry -- CHANGE SECRET KEY')
      site_config = SiteConfig(id=1, secret_key="Change Me!")
      site_config.put_async()
    return site_config

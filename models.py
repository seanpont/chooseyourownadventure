from google.appengine.ext import ndb


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
  text = ndb.TextProperty()
  page = ndb.KeyProperty()


class Page(ndb.Model):
  # parent = Story
  text = ndb.TextProperty(required=True)
  choices = ndb.StructuredProperty(Choice, repeated=True)

  def summary(self, character_limit=100):
    return "%s. %s%s" % (
      self.key.id(),
      self.text[:character_limit],
      "..." if len(self.text) > character_limit else ""
    )

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
    site_config = ndb.Key('SiteConfig', 'key').get()
    if not site_config:
      site_config = SiteConfig(secret_key="Change Me!")
      site_config.put_async()
    return site_config

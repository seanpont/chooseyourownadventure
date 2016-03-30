from google.appengine.ext import ndb


class Story(ndb.Model):
  author = ndb.UserProperty(required=True)
  title = ndb.TextProperty(required=True)
  page_1 = ndb.KeyProperty()

  @classmethod
  def create(cls, user):
    story = Story(author=user, title="")
    story.put()
    page_1 = Page.create(story)
    story.page_1 = page_1.key
    story.put()
    return story, page_1

  @classmethod
  def find_by_key_string(cls, urlsafe_story_key):
    ndb.Key(urlsafe=story_key_string)


class Choice(ndb.Model):
  # parent = Page
  text = ndb.TextProperty()
  page = ndb.KeyProperty()


class Page(ndb.Model):
  # parent = Story
  text = ndb.TextProperty(required=True)
  choices = ndb.StructuredProperty(Choice, repeated=True)

  def summary(self, character_limit=100):
    return self.text[:character_limit] + (
      "..." if len(self.text) > character_limit else "")

  @classmethod
  def create(cls, story):
    page = Page(parent=story.key,
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

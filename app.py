"""
@filename: app.py
@description: this script sets up the web application
@author: Daniele Di Mitri
@date: 15-10-2015


@Run 
cd /usr/local/google_appengine/
dev_appserver.py /Users/Daniele/Documents/LearningPulse/webapp/
appcfg.py -A learningpulse-1096 update /Users/Daniele/Documents/LearningPulse/webapp/
"""

import os
import urllib
import httplib2
import jinja2
import webapp2

from google.appengine.api import users
from google.appengine.ext import ndb
from google.appengine.ext.webapp import template

from apiclient.discovery import build
from oauth2client.appengine import AppAssertionCredentials

url = 'https://www.googleapis.com/auth/bigquery'
PROJECT_NUMBER = '815835684542'

credentials = AppAssertionCredentials(scope=url)
httpss = credentials.authorize(httplib2.Http())
bigquery_service = build('bigquery','v2',http=httpss)


JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)

DEFAULT_DASHBOARD_NAME = 'default_dashboard'


# We set a parent key on the 'Ratings' to ensure that they are all
# in the same entity dashboard. Queries across the single entity dashboard
# will be consistent. However, the write rate should be limited to
# ~1/second.

def dashboard_key(dashboard_name=DEFAULT_DASHBOARD_NAME):
    #Constructs a Datastore key for a Dashboard entity.
    #We use dashboard_name as the key.
    return ndb.Key('Dashboard', dashboard_name)

class Author(ndb.Model):
    """Sub model for representing an author."""
    identity = ndb.StringProperty(indexed=False)
    email = ndb.StringProperty(indexed=False)


class Rating(ndb.Model):
    """A main model for representing an individual Dashboard entry."""
    author = ndb.StructuredProperty(Author)
    productivity = ndb.StringProperty(indexed=False)
    stress = ndb.StringProperty(indexed=False)
    activity = ndb.StringProperty(indexed=False)
    date = ndb.DateTimeProperty(auto_now_add=True)


class MainPage(webapp2.RequestHandler):

    def get(self):
        dashboard_name = self.request.get('user', DEFAULT_DASHBOARD_NAME)
        
        ratings_query = Rating.query(ancestor=dashboard_key(dashboard_name)).order(-Rating.date)
        ratings = ratings_query.fetch(10)

        user = users.get_current_user()
        if user:
            url = users.create_logout_url(self.request.uri)
            url_linktext = 'Logout'
        else:
            url = users.create_login_url(self.request.uri)
            url_linktext = 'Login'

        template_values = {
            'user': user,
            'ratings': ratings,
            'dashboard_name': urllib.quote_plus(dashboard_name),
            'url': url,
            'url_linktext': url_linktext,
        }

        template = JINJA_ENVIRONMENT.get_template('index.html')
        #template = JINJA_ENVIRONMENT.get_template('templates/index.html')
        self.response.write(template.render(template_values))


class Dashboard(webapp2.RequestHandler):

    def post(self):
        # We set the same parent key on the 'Rating' to ensure each
        # Rating is in the same entity dashboard. Queries across the
        # single entity dashboard will be consistent. However, the write
        # rate to a single entity dashboard should be limited to
        # ~1/second.
        dashboard_name = self.request.get('dashboard_name',
                                          DEFAULT_DASHBOARD_NAME)
        rating = Rating(parent=dashboard_key(dashboard_name))

        if users.get_current_user():
            rating.author = Author(
                    identity=users.get_current_user().user_id(),
                    email=users.get_current_user().email())

        rating.productivity = self.request.get('productivity')
        rating.stress = self.request.get('stress')
        rating.activity = self.request.get('activity')
        rating.put()

        query_params = {'dashboard_name': dashboard_name}
        self.redirect('/?' + urllib.urlencode(query_params))


app = webapp2.WSGIApplication([
    ('/', MainPage),
    ('/rate', Dashboard),
], debug=True)

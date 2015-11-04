"""
@filename: app.py
@description: this script sets up the web application
@author: Daniele Di Mitri
@date: 15-10-2015


@Run 
cd /usr/local/google_appengine/
dev_appserver.py C:\Users\DDM\Documents\LearningPulse\webapp\learning-pulse-python-app 
appcfg.py -A learningpulse-1096 update /Users/Daniele/Documents/LearningPulse/webapp/
"""

import os
import urllib
import httplib2
import jinja2
import webapp2
from datetime import datetime, timedelta

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

working_time = [8,9,10,11,12,13,14,15,16,17,18]

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
    challenge = ndb.StringProperty(indexed=False)
    abilities = ndb.StringProperty(indexed=False)
    activity = ndb.StringProperty(indexed=False)
    date = ndb.DateTimeProperty(auto_now_add=True)
    timeframe = ndb.StringProperty(indexed=True)


class MainPage(webapp2.RequestHandler):


    def get(self):
        dashboard_name = self.request.get('user', DEFAULT_DASHBOARD_NAME)
        
        ratings_query = Rating.query(ancestor=dashboard_key(dashboard_name)).order(-Rating.date)
        ratings = ratings_query.fetch(10)
        timeframes = [7,8,9,10,11,12,13,14,15,16,17,18]  
        to = 1 #offset UTC+1 s      
        currentHour = int(datetime.utcnow().strftime('%H')) #e.g. 9 
        todayNice = datetime.utcnow().strftime('%A %d, %b %Y') #e.g. Tuesday 03, Nov 2015
        user = users.get_current_user() 
        listTimeframes = ""
        if user:
            url = users.create_logout_url(self.request.uri)
            url_linktext = 'Logout' 
            
            for i in timeframes:
                if i < currentHour:
                    """
                    timeframe = datetime.utcnow().strftime('%Y-%m-%d '+ str(i) +':00:00')
                    date_object = datetime.strptime(timeframe, '%Y-%m-%d %H:%M:%S')
                    query = Rating.query(
                        ndb.AND(Rating.date >= date_object),
                                Rating.date < date_object + timedelta(hours=1))
                    """
                    query = Rating.query(Rating.timeframe == str(i+to))
                    if not query.get():
                        listTimeframes += "<li class='list-group-item'><span class='badge'>"+str(i+to)+ \
                        " - "+str(i+to+1)+" </span> <a href='#"+str(i+to)+"' class='timeframe-rating'>Rate this timeframe</a></li>"
                    else:
                        listTimeframes += "<li class='list-group-item list-group-item-success'>"+"<span class='badge'>"+ \
                        str(i+to)+" - "+str(i+to+1)+" </span> You rated this timeframe already</li>"
                elif i==currentHour:
                    listTimeframes += "<li class='list-group-item list-group-item-warning'>"+"<span class='badge'>"+ \
                        str(i+to)+" - "+str(i+to+1)+" </span> Ongoing timeframe</li>"
                        
        else:
            url = users.create_login_url(self.request.uri)
            url_linktext = 'Login'

        template_values = {
            'user': user,
            'ratings': ratings,
            'dashboard_name': urllib.quote_plus(dashboard_name),
            'url': url,
            'url_linktext': url_linktext,
            'listTimeframes': listTimeframes,
            'today': todayNice
        }

        template = JINJA_ENVIRONMENT.get_template('index.html')
        self.response.write(template.render(template_values))

    def post(self):
        dashboard_name = self.request.get('dashboard_name', DEFAULT_DASHBOARD_NAME)
        rating = Rating(parent=dashboard_key(dashboard_name))

        if users.get_current_user():
            rating.author = Author(
                    identity=users.get_current_user().user_id(),
                    email=users.get_current_user().email())

        rating.productivity = self.request.get('productivity')
        rating.stress = self.request.get('stress')
        rating.challenge = self.request.get('challenge')
        rating.abilities = self.request.get('abilities')
        rating.activity = self.request.get('activity')
        rating.timeframe = self.request.get('timeframe')
        rating.put()

        query_params = {'dashboard_name': dashboard_name}
        self.redirect('/?' + urllib.urlencode(query_params))



class Visualisation(webapp2.RequestHandler):
    def get(self):
        dashboard_name = self.request.get('user', DEFAULT_DASHBOARD_NAME)
        ratings_query = Rating.query(ancestor=dashboard_key(dashboard_name)).order(-Rating.date)
        ratings = 
        for r in ratings_query.fetch():
        #    
        dailychart = "['data1', 30, 200, 100, 400, 150, 250],"
        template_values = {
            'user': user,
            'dailychart': dailychart,
        }

        template = JINJA_ENVIRONMENT.get_template('vis.html')
        self.response.write(template.render(template_values))

class Login(webapp2.RequestHandler):
    def get(self):
        user = users.get_current_user()
        if user:
            self.redirect('/rate')
        else:
            self.redirect(users.create_login_url(self.request.uri))

app = webapp2.WSGIApplication([
    ('/', Login),
    ('/rate', MainPage),
], debug=True)

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
from google.appengine.api import mail

import pandas as pd

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

timeframes = [7,8,9,10,11,12,13,14,15,16,17,18]  
todayNice = datetime.utcnow().strftime('%A %d, %b %Y') #e.g. Tuesday 03, Nov 2015]
to = 1 # Time offset UTC+1 
today = datetime.now() # dateobject 
participants = ['ddm@ou.nl']
user = users.get_current_user() #current user


def dashboard_key(dashboard_name=DEFAULT_DASHBOARD_NAME):
    #Constructs a Datastore key for a Dashboard entity.
    #We use dashboard_name as the key.
    return ndb.Key('Dashboard', dashboard_name)

class Author(ndb.Model):
    identity = ndb.StringProperty(indexed=False)
    email = ndb.StringProperty(indexed=True)


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
        currentHour = int(datetime.utcnow().strftime('%H')) #e.g. 9 
        listTimeframes = ""
        if user:
            url = users.create_logout_url(self.request.uri)
            url_linktext = 'Logout' 
            
            for i in timeframes:
                if i < currentHour:
                    today = datetime.utcnow().strftime('%Y-%m-%d')
                    date_object = datetime.strptime(today, '%Y-%m-%d')
                    query = Rating.query(
                        ancestor=dashboard_key(dashboard_name),
                        filters=ndb.AND(Rating.date >= date_object,
                                        Rating.date < date_object + timedelta(days=1),
                                        Rating.timeframe == str(i+to),
                                        Rating.author.email == user.email())
                    )
                    
                    if not query.get():
                        listTimeframes += "<a href='#"+str(i+to)+"' class='list-group-item timeframe-rating'><span class='badge'>"+str(i+to)+ \
                        " - "+str(i+to+1)+" </span> Rate this timeframe</a>"
                    else:
                        listTimeframes += "<a href='#"+str(i+to)+"' class='list-group-item list-group-item-success'>"+"<span class='badge'>"+ \
                        str(i+to)+" - "+str(i+to+1)+"</span> You rated this timeframe already</>"
                elif i==currentHour:
                    listTimeframes += "<a href='#"+str(i+to)+"' class='list-group-item list-group-item-warning disabled'>"+"<span class='badge'>"+ \
                        str(i+to)+" - "+str(i+to+1)+"</span> Ongoing timeframe</a>"
                        
        else:
            url = users.create_login_url(self.request.uri)
            url_linktext = 'Login'

        template_values = {
            'user': user,
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
        if user:
            url = users.create_logout_url(self.request.uri)
            url_linktext = 'Logout' 
            today = datetime.utcnow().strftime('%Y-%m-%d')
            date_object = datetime.strptime(today, '%Y-%m-%d')
            query = Rating.query(
                ancestor=dashboard_key(dashboard_name),
                filters=ndb.AND(Rating.date >= date_object,
                                Rating.date < date_object + timedelta(days=1),
                                Rating.author.email == user.email())
            )
            chart_x_label = "['x',"
            chart_productivity = "['Productivity',"
            chart_stress = "['Stress',"
            chart_challenge = "['Challenge',"
            chart_abilities = "['Abilities',"
            for r in query.fetch():
                chart_x_label += r.timeframe + ","
                chart_productivity += r.productivity + ","
                chart_stress += r.stress + ","
                chart_challenge += r.challenge + "," 
                chart_abilities += r.abilities + ","
            chart_x_label += "]"
            chart_productivity += "]"
            chart_stress += "]"
            chart_challenge += "]"
            chart_abilities += "]"

            chart_data = chart_x_label + "," + chart_productivity + "," + chart_stress + "," + chart_challenge + "," + chart_abilities
            template_values = {
                'user': user,
                'chart_data': chart_data,
                'url_linktext': url_linktext,
                'today': todayNice,
            }
        else:
            url = users.create_login_url(self.request.uri)
            url_linktext = 'Login'

        template = JINJA_ENVIRONMENT.get_template('vis.html')
        self.response.write(template.render(template_values))

class Reminder(webapp2.RequestHandler):
    def get(self):

        message = mail.EmailMessage(sender="Learning Pulse <dnldimitri@gmail.com>", #"daniele.dimitri@ou.nl",
                        subject="It's time to rate your activity!")
        message.html = """
        <html>
        <body style="font-family: Arial, sans-serif; font-size:11px; text-align:center;">
        <p>
            <a href="http://learningpulse-1096.appspot.com/rate">
                <img src="http://learningpulse-1096.appspot.com/static/itstimetorate.jpg" alt="It's time to rate!" style="width:500px;" width="500" />
            </a>
        </p>
        <p>
            http://learningpulse-1096.appspot.com/rate <br />
            Reply to this email in case of issue. <br />
            LearningPulse - Welten Institute 2015
        </p>
        </body>
        """
        for email in participants:
            message.to = email
            message.send()
            print "email sent to "+email
            #message.to = user.email() # This would send it to the logged user

class Login(webapp2.RequestHandler):
    def get(self): 
        if user:
            self.redirect('/rate')
        else:
            self.redirect(users.create_login_url(self.request.uri))

class Process(webapp2.RequestHandler):
    def get(self):
        data_frame = pd.read_gbq('SELECT * FROM [xAPIStatements.xapiTable]', PROJECT_NUMBER)
        print data_frame

app = webapp2.WSGIApplication([
    ('/', Login),
    ('/rate', MainPage),
    ('/vis', Visualisation),
    ('/process', Process),
    ('/joDKskOKufkwl39a3jwghga240ckaJEKRmcairtsDK', Reminder),
], debug=True)

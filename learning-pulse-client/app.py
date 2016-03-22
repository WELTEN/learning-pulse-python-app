"""
@filename: app.py
@description: This script sets up the GAE web application 
@author: Daniele Di Mitri
@date: 15-10-2015
"""

import os, json
import urllib, urllib2, httplib2
import jinja2, webapp2
import base64
from datetime import datetime, timedelta

from google.appengine.api import users
from google.appengine.ext import ndb
from google.appengine.ext.webapp import template
from google.appengine.api import mail
from google.appengine.api import urlfetch

from apiclient.discovery import build
from oauth2client.appengine import AppAssertionCredentials

url = 'https://www.googleapis.com/auth/bigquery'
PROJECT_NUMBER = '815835684542'

credentials = AppAssertionCredentials(scope=url)
httpss = credentials.authorize(httplib2.Http())
bigquery_service = build('bigquery','v2',http=httpss)
    
#Google Big Query credential
dataProxyURL = 'http://learning-pulse.appspot.com/data-proxy/xAPI/statement/origin/rating'
dataProxyHeader = {"Content-Type": "application/json", "X-Experience-API-Version": "1.0.0","Authorization": \
                         "Basic %s" % base64.b64encode("test:test")}

JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)

DEFAULT_DASHBOARD_NAME = 'default_dashboard'

timeframes = [7,8,9,10,11,12,13,14,15,16,17,18]  
to = 1 # Time offset UTC+1 
today = datetime.now() # dateobject 
participants = ['ddm@ou.nl','katerina.riviou@ou.nl','asu@ou.nl','mhx@ou.nl','gsv@ou.nl','zai@ou.nl','jkh@ou.nl','xjs@ou.nl','xai@ou.nl']
defaultLat = 50
defaultLong = 5

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
    latitude = ndb.FloatProperty(indexed=False)
    longitude = ndb.FloatProperty(indexed=False)    


class MainPage(webapp2.RequestHandler):
    def get(self):
        dashboard_name = self.request.get('user', DEFAULT_DASHBOARD_NAME)  
        currentHour = int(datetime.now().strftime('%H')) #e.g. 9 
        todayNice = datetime.now().strftime('%A %d, %b %Y') #e.g. Tuesday 03, Nov 2015]
        user = users.get_current_user()
        listTimeframes = ""
        if user:
            url = users.create_logout_url(self.request.uri)
            url_linktext = 'Logout' 
            
            for i in timeframes:
                if i < currentHour:
                    today = datetime.now().strftime('%Y-%m-%d')
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
                        listTimeframes += "<a href='' class='list-group-item list-group-item-success' >"+"<span class='badge'>"+ \
                        str(i+to)+" - "+str(i+to+1)+"</span> You rated this timeframe already</a>"
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
        user = users.get_current_user()
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
        if self.request.get('latitude')!='':
            rating.latitude = float(self.request.get('latitude'))
        else:  
            rating.latitude = defaultLat
        if self.request.get('longitude')!='':
            rating.longitude = float(self.request.get('longitude'))
        else:  
            rating.longitude = defaultLong
        rating.put()

        #xAPI statement generation
        #-------------------------
        # xAPI statement Productivity

        # I convert the Timestamp to the corresponding timeframe
        hr = str(int(rating.timeframe)+1).zfill(2)
        dt = '{0.year}-{0.month}-{0.day}'.format(rating.date)

        dateXApi = dt + "T" + hr + ":00:00.000Z" 

        #xAPI statement productivity
        xAPI = [None] * 5
        xAPI[0] = '{ "timestamp":  "'+dateXApi+'",  "actor": \
        { "objectType": "Agent", "name": "%s", "mbox": "mailto:%s" }, \
        "verb": { "id": "http://id.tincanapi.com/verb/rated", \
        "display": { "en-US": "indicates the user rated something"\
        } }, "object": { "objectType": "Activity", "id": "Productivity", \
        "definition": { "name": { "en-US": "rated activity" }, \
        "description": { "en-US": "rated activity" }, "type": \
        "http://adlnet.gov/expapi/activities/performance" } }, "result":\
        { "response": "%s" }, "context": { "extensions": { \
        "http://activitystrea.ms/schema/1.0/place": { "definition": \
        { "type": "http://activitystrea.ms/schema/1.0/place", "name":\
        { "en-US": "Place" }, "description": { "en-US": \
        "Represents a physical location." } }, "id": \
        "http://vocab.org/placetime/geopoint/wgs84/X-15.416497Y28.079203.html", \
        "geojson": { "type": "FeatureCollection", "features": [ \
        { "geometry": { "type": "Point", "coordinates": [ \
        %s,%s] }, "type": "Feature" } ] }, "objectType": "Place" } } } }' \
         % (rating.author.email,rating.author.email,rating.productivity,rating.latitude,rating.longitude)

        # xAPI statement Stress
        xAPI[1] = '{ "timestamp":  "'+dateXApi+'", "actor": \
        { "objectType": "Agent", "name": "%s", "mbox": "mailto:%s" }, \
        "verb": { "id": "http://id.tincanapi.com/verb/rated", \
        "display": { "en-US": "indicates the user rated something"\
        } }, "object": { "objectType": "Activity", "id": "Stress", \
        "definition": { "name": { "en-US": "rated activity" }, \
        "description": { "en-US": "rated activity" }, "type": \
        "http://adlnet.gov/expapi/activities/performance" } }, "result":\
        { "response": "%s" }, "context": { "extensions": { \
        "http://activitystrea.ms/schema/1.0/place": { "definition": \
        { "type": "http://activitystrea.ms/schema/1.0/place", "name":\
        { "en-US": "Place" }, "description": { "en-US": \
        "Represents a physical location." } }, "id": \
        "http://vocab.org/placetime/geopoint/wgs84/X-15.416497Y28.079203.html", \
        "geojson": { "type": "FeatureCollection", "features": [ \
        { "geometry": { "type": "Point", "coordinates": [ \
        %s,%s] }, "type": "Feature" } ] }, "objectType": "Place" } } } }' \
         % (rating.author.email,rating.author.email,rating.stress,rating.latitude,rating.longitude)


        # xAPI statement Challenge
        xAPI[2]  = '{ "timestamp":  "'+dateXApi+'", "actor": \
        { "objectType": "Agent", "name": "%s", "mbox": "mailto:%s" }, \
        "verb": { "id": "http://id.tincanapi.com/verb/rated", \
        "display": { "en-US": "indicates the user rated something"\
        } }, "object": { "objectType": "Activity", "id": "Challenge", \
        "definition": { "name": { "en-US": "rated activity" }, \
        "description": { "en-US": "rated activity" }, "type": \
        "http://adlnet.gov/expapi/activities/performance" } }, "result":\
        { "response": "%s" }, "context": { "extensions": { \
        "http://activitystrea.ms/schema/1.0/place": { "definition": \
        { "type": "http://activitystrea.ms/schema/1.0/place", "name":\
        { "en-US": "Place" }, "description": { "en-US": \
        "Represents a physical location." } }, "id": \
        "http://vocab.org/placetime/geopoint/wgs84/X-15.416497Y28.079203.html", \
        "geojson": { "type": "FeatureCollection", "features": [ \
        { "geometry": { "type": "Point", "coordinates": [ \
        %s,%s] }, "type": "Feature" } ] }, "objectType": "Place" } } } }' \
         % (rating.author.email,rating.author.email,rating.challenge,rating.latitude,rating.longitude)

        # xAPI statement Ability
        xAPI[3]  = '{ "timestamp":  "'+dateXApi+'",  "actor": \
        { "objectType": "Agent", "name": "%s", "mbox": "mailto:%s" }, \
        "verb": { "id": "http://id.tincanapi.com/verb/rated", \
        "display": { "en-US": "indicates the user rated something"\
        } }, "object": { "objectType": "Activity", "id": "Abilities", \
        "definition": { "name": { "en-US": "rated activity" }, \
        "description": { "en-US": "rated activity" }, "type": \
        "http://adlnet.gov/expapi/activities/performance" } }, "result":\
        { "response": "%s" }, "context": { "extensions": { \
        "http://activitystrea.ms/schema/1.0/place": { "definition": \
        { "type": "http://activitystrea.ms/schema/1.0/place", "name":\
        { "en-US": "Place" }, "description": { "en-US": \
        "Represents a physical location." } }, "id": \
        "http://vocab.org/placetime/geopoint/wgs84/X-15.416497Y28.079203.html", \
        "geojson": { "type": "FeatureCollection", "features": [ \
        { "geometry": { "type": "Point", "coordinates": [ \
        %s,%s] }, "type": "Feature" } ] }, "objectType": "Place" } } } }' \
         % (rating.author.email,rating.author.email,rating.abilities,rating.latitude,rating.longitude)

        # xAPI statement Activity
        xAPI[4]  = '{ "timestamp":  "'+dateXApi+'", "actor": \
        { "objectType": "Agent", "name": "%s", "mbox": "mailto:%s" }, \
        "verb": { "id": "http://adlnet.gov/expapi/verbs/experienced", \
        "display": { "en-US": "indicates the user experienced something"\
        } }, "object": { "objectType": "Activity", "id": "MainActivity"\
        , "definition": { "name": { "en-US": "main activity" }, \
        "description": { "en-US": "main activity" }, "type": \
        "http://activitystrea.ms/schema/1.0/event" } }, "result": \
        { "response": "%s" }, "context": { "extensions": { \
        "http://activitystrea.ms/schema/1.0/place": { "definition":\
        { "type": "http://activitystrea.ms/schema/1.0/place", \
        "name": { "en-US": "Place" }, "description": { "en-US":\
        "Represents a physical location." } }, "id": \
        "http://vocab.org/placetime/geopoint/wgs84/X-15.416497Y28.079203.html",\
        "geojson": { "type": "FeatureCollection", "features": \
        [ { "geometry": { "type": "Point", "coordinates":[ \
        %s,%s] }, "type": "Feature" } ] }, "objectType": "Place" } } } }' \
        % (rating.author.email,rating.author.email,rating.activity,rating.latitude,rating.longitude)

        message = mail.EmailMessage(sender="Learning Pulse <dnldimitri@gmail.com>", #"daniele.dimitri@ou.nl",
                            subject="xAPI")
        
        emailbody = ""
        for statement in xAPI:
            #emailbody += statement + "--------------------------------- "
            parsed_json = json.loads(statement)
            result = urlfetch.fetch(url=dataProxyURL, headers=dataProxyHeader, payload = statement, method=urlfetch.POST)
        #message.body = emailbody
        #message.to = "dnldimitri@gmail.com"
        #message.send()
        query_params = {'dashboard_name': dashboard_name}
        self.redirect('/?' + urllib.urlencode(query_params))
 
class Visualisation(webapp2.RequestHandler):
    def get(self):
        dashboard_name = self.request.get('user', DEFAULT_DASHBOARD_NAME)
        todayNice = datetime.now().strftime('%A %d, %b %Y') #e.g. Tuesday 03, Nov 2015]
        user = users.get_current_user()
        if user:
            url = users.create_logout_url(self.request.uri)
            url_linktext = 'Logout' 
            today = datetime.now().strftime('%Y-%m-%d')
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
                t0 = r.timeframe 
                t1 = 1+int(r.timeframe) 
                chart_x_label += "'" + str(t0) + "-" + str(t1) + "',"
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

        template = JINJA_ENVIRONMENT.get_template('viz.html')
        self.response.write(template.render(template_values))

class Reminder(webapp2.RequestHandler):
    def get(self):
        # Random Joke generator Tambal
        weekday = datetime.today().weekday()
        
        if (weekday<5): #This control limits blocks the emails on Sat and Sun
            
            #fetching a random joke 
            req = urllib2.Request("http://api.icndb.com/jokes/random?exclude=[nerdy,explicit]")
            full_json = urllib2.urlopen(req).read()
            full = json.loads(full_json)
            joke = full['value']['joke']

            currentHour = int(datetime.now().strftime('%H')) #e.g. 9 
            
            # Compse the message 
            message = mail.EmailMessage(sender="Learning Pulse <dnldimitri@gmail.com>", #"",
                            subject="It's time to rate your activity")
            message.html = "<html> \
            <body style='font-family: Arial, sans-serif; font-size:11px; text-align:center;'> \
            <p style='font-family: Courier new, sans-serif; font-size:12px; margin:20px 0; \
            text-align:center; line-height:1.3em;'>" + joke + "</p><p> \
                <a href='http://learningpulse-1096.appspot.com/rate#"+str(currentHour)+"'> \
                    <img src='http://learningpulse-1096.appspot.com/static/itstimetorate.jpg' \
                    alt='It s time to rate!'  style='width:500px;' width='500' /> \
                </a></p> \
            <p><a href='http://learningpulse-1096.appspot.com/rate#"+str(currentHour)+"'> \
                learningpulse-1096.appspot.com</a> <br /> <br /> \
                Reply to this email in case of issue. <br /><br /> \
                LearningPulse - Welten Institute 2015 \
            </p></body>"

            # Loop through the email array Participants and send an email
            for email in participants:
                message.to = email
                message.send()

class Login(webapp2.RequestHandler):
    def get(self): 
        user = users.get_current_user()
        if user:
            self.redirect('/rate')
        else:
            self.redirect(users.create_login_url(self.request.uri))

class ErrorHandler(webapp2.RequestHandler):
    def get(self): 
        user = users.get_current_user()
        todayNice = datetime.now().strftime('%A %d, %b %Y') #e.g. Tuesday 03, Nov 2015]
        if user:
            self.redirect('/rate')            
        template_values = {
                'user': user,
                'url_linktext': url_linktext,
                'today': todayNice,
            }
        template = JINJA_ENVIRONMENT.get_template('error.html')
        self.response.write(template.render(template_values))


class DeleteHandler(webapp2.RequestHandler):
    def get(self):
        key = self.request.get('t')
        dashboard_name = self.request.get('user', DEFAULT_DASHBOARD_NAME)
        user = users.get_current_user()
        if user:
            timeframes_keys = Rating.query(
                ancestor=dashboard_key(dashboard_name),
                filters=ndb.AND(Rating.timeframe == key,
                                 Rating.author.email == user.email())
                        ).fetch(keys_only=True)
            ndb.delete_multi(timeframes_keys)
        self.redirect('/rate')   

app = webapp2.WSGIApplication([
    ('/', Login),
    ('/rate', MainPage),
    ('/viz', Visualisation),
    ('/delete', DeleteHandler),
    ('/error', ErrorHandler),
    ('/joDKskOKufkwl39a3jwghga240ckaJEKRmcairtsDK', Reminder),
], debug=True)

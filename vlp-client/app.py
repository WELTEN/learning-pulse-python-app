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
import unirest

from google.appengine.api import users
from google.appengine.ext import ndb
from google.appengine.ext.webapp import template
from google.appengine.api import mail
from google.appengine.api import urlfetch

from apiclient.discovery import build
from oauth2client.appengine import AppAssertionCredentials

url = 'https://www.googleapis.com/auth/bigquery'
PROJECT_NUMBER = 'xxxxx'

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

timeframes = [6,7,8,9,10,11,12,13,14,15,16,17]  
to = 1 # Time offset UTC+1 
today = datetime.now() # dateobject 
#participants = ['xxxxx']

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

class Weather(ndb.Model):
    user = ndb.StringProperty(indexed=False)
    status = ndb.StringProperty(indexed=False)
    date = ndb.DateTimeProperty(auto_now_add=True) 

class MainPage(webapp2.RequestHandler):
    def get(self):
        dashboard_name = self.request.get('user', DEFAULT_DASHBOARD_NAME)  
        currentHour = int(datetime.now().strftime('%H'))+1 #e.g. 9 
        today = datetime.now().strftime('%Y-%m-%d')
        todayNice = datetime.now().strftime('%A %d, %b %Y') #e.g. Tuesday 03, Nov 2015]
        user = users.get_current_user()
        listTimeframes = ""
        if user:
            url = users.create_logout_url(self.request.uri)
            url_linktext = '<i class="fa fa-sign-out"></i> Logout' 
            
            for i in timeframes:
                act_i = i+1
                if i < currentHour:
                    date_object = datetime.strptime(today, '%Y-%m-%d')
                    query = Rating.query(
                        ancestor=dashboard_key(dashboard_name),
                        filters=ndb.AND(Rating.date >= date_object,
                                        Rating.date < date_object + timedelta(days=1),
                                        Rating.timeframe == str(act_i),
                                        Rating.author.email == user.email())
                    )
                    
                    if not query.get():
                        listTimeframes += "<a href='#"+str(act_i)+"' class='list-group-item timeframe-rating'><span class='badge'>"+str(act_i)+ \
                        " - "+str(act_i+1)+" </span> Rate this timeframe</a>"
                    else:
                        listTimeframes += "<a href='/delete?t="+str(act_i)+"' class='list-group-item list-group-item-success' onclick='confirm_delete()' >"+"<span class='badge'>"+ \
                        str(act_i)+" - "+str(act_i+1)+"</span> You rated this timeframe already</a>"
                elif i==currentHour:
                    listTimeframes += "<a href='#"+str(act_i)+"' class='list-group-item list-group-item-warning disabled'>"+"<span class='badge'>"+ \
                        str(act_i)+" - "+str(act_i+1)+"</span> Ongoing timeframe</a>"
            
            # VIZ
            #************************************************
            date_object = datetime.strptime(today, '%Y-%m-%d')
            query = Rating.query(
                ancestor=dashboard_key(dashboard_name),
                filters=ndb.AND(Rating.date >= date_object,
                                Rating.date < date_object + timedelta(days=1),
                                Rating.author.email == user.email())
            )
            chart_x_label = "['x'"
            chart_productivity = "['Productivity'"
            chart_stress = "['Stress'"
            chart_challenge = "['Challenge'"
            chart_abilities = "['Abilities'"
            for r in query.fetch():
                t0 = r.timeframe 
                t1 = 1+int(r.timeframe) 
                chart_x_label += ",'" + str(t0) + "-" + str(t1) + "'"
                chart_productivity +=  "," + r.productivity 
                chart_stress += "," + r.stress
                chart_challenge += "," + r.challenge
                chart_abilities += "," + r.abilities
            chart_x_label += "]"
            chart_productivity += "]"
            chart_stress += "]"
            chart_challenge += "]"
            chart_abilities += "]"

            chart_data = chart_x_label + "," + chart_productivity + "," + chart_abilities + "," +  chart_challenge + "," + chart_stress
            #************************************************
                

        else:
            url = users.create_login_url(self.request.uri)
            chart_data = ''
            url_linktext = '<i class="fa fa-sign-in"></i> Login'

        
        template_values = {
            'user': user,
            'dashboard_name': urllib.quote_plus(dashboard_name),
            'url': url,
            'url_linktext': url_linktext,
            'listTimeframes': listTimeframes,
            'chart_data': chart_data,
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

        message = mail.EmailMessage(sender="Visual Learning Pulse <xxxx@xxxx.xx>", 
                            subject="xAPI")
        
        emailbody = ""
        for statement in xAPI:
            #emailbody += statement + "--------------------------------- "
            parsed_json = json.loads(statement)
            result = urlfetch.fetch(url=dataProxyURL, headers=dataProxyHeader, payload = statement, method=urlfetch.POST)
        query_params = {'dashboard_name': dashboard_name}
        self.redirect('/?' + urllib.urlencode(query_params))

class Reminder(webapp2.RequestHandler):
    def get(self):
        weekday = datetime.today().weekday()
        if (weekday<5): #This control limits blocks the emails on Sat and Sun
            # These code snippets use an open-source library. http://unirest.io/python
            
            response = unirest.get("https://webknox-jokes.p.mashape.com/jokes/oneLiner",
              headers={
                "X-Mashape-Key": "CC9qExPz1xmshMlClnCaQArQh3nip1PTsqYjsnP2aOar9pQfTx"
              }
            )
            joke = response.body['text']
            #joke = "na"
            
            currentHour = int(datetime.now().strftime('%H'))+1 #e.g. 9
            # Compse the message 
            message = mail.EmailMessage(sender="Visual Learning Pulse <xxxx@xx.xx>", #"",
                            subject="It's time to rate your activity")
            message.html = "<!DOCTYPE html><html><body style='font-family: Arial, sans-serif; font-size:11px; text-align:center;'> \
                <p>"+joke+"</p><br /><p>Please remember to submit your ratings.</p><br />  \
                Visual Learning Pulse - Welten Institute 2016</p></body></html>"

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

class WeatherDownload(webapp2.RequestHandler):
    def get(self):
        weekday = datetime.today().weekday()

        if (weekday<5): #This control limits blocks the emails on Sat and Sun
            owa_key = "0d68f7a39b4bbc47ac1d14ffadcbe17a"
            dashboard_name = self.request.get('dashboard_name', DEFAULT_DASHBOARD_NAME)           
            authors = ndb.gql("SELECT DISTINCT author.email FROM Rating")
            for a in authors.fetch(): 
                lastRatings = ndb.gql("SELECT * FROM Rating WHERE author.email = :1 ORDER by date desc LIMIT 1", a.author.email)
                #today = datetime.strptime(datetime.now().strftime('%Y-%m-%d') , '%Y-%m-%d')  
                #lastRatings = lastRatings.filter("date =", today)     
                if lastRatings.get():
                    owa_lat = str(lastRatings.get().latitude)
                    owa_lon = str(lastRatings.get().longitude)
                else:
                    owa_lat = "50.877861"
                    owa_lon = "5.958490"

                page =  urllib2.urlopen('http://api.openweathermap.org/data/2.5/weather?lat='+owa_lat 
                       +'&lon=' + owa_lon + '&APPID=' + owa_key)
                wjson = page.read()
                statement = json.loads(wjson)
                weather = Weather(parent=dashboard_key(dashboard_name))
                weather.status = str(statement)
                weather.user = a.author.email
                weather.put() 


class Dashboard(webapp2.RequestHandler):
    def get(self):
        dashboard_name = self.request.get('user', DEFAULT_DASHBOARD_NAME) 
        #@todo start here
        today = datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ')
        todayNice = datetime.now().strftime('%A %d, %b %Y') #e.g. Tuesday 03, Nov 2015]
        user = users.get_current_user()
        if user:
            xAPI  = '{ "timestamp":  "'+today+'",  "actor": \
            { "objectType": "Agent", "name": "%s", "mbox": "mailto:%s" }, \
            "verb": { "id": "http://activitystrea.ms/schema/1.0/access", \
            "display": { "en-US": "Indicates the learner accessed something"\
            } }, "object": { "objectType": "Activity", "id": "dashboard", \
            "definition": { "name": { "en-US": "Learner Dashboard" }, \
            "description": { "en-US": "this is a page" }, "type": \
            "http://activitystrea.ms/schema/1.0/page" } }, "result":\
            { "response": "http://visual-learning-pulse.appspot.com/dashboard" },\
             "context": { "extensions": { \
            "http://activitystrea.ms/schema/1.0/place": { "definition": \
            { "type": "http://activitystrea.ms/schema/1.0/place", "name":\
            { "en-US": "Place" }, "description": { "en-US": \
            "Represents a physical location." } }, "id": \
            "http://vocab.org/placetime/geopoint/wgs84/X50.877861Y5.958490.html", \
            "geojson": { "type": "FeatureCollection", "features": [ \
            { "geometry": { "type": "Point", "coordinates": [ \
            50.877861,5.958490] }, "type": "Feature" } ] }, "objectType": "Place" } } } }' \
            % (users.get_current_user().email(),user.email())

            result = urlfetch.fetch(url=dataProxyURL, headers=dataProxyHeader, payload = xAPI, method=urlfetch.POST)

            url = users.create_logout_url(self.request.uri)
            url_linktext = '<i class="fa fa-sign-out"></i> Logout'
            dash_dict = {
                "xxx@xxxx": 
                "https://app.redash.io/"
                }
            url_dashboard = dash_dict[user.email()]
            template_values = {
                'user': user,
                'url_linktext': url_linktext,
                'today': todayNice,
                'url_dashboard': url_dashboard,
            }
            template = JINJA_ENVIRONMENT.get_template('dashboard.html')
            self.response.write(template.render(template_values))
        else:
            self.redirect(users.create_login_url(self.request.uri))

app = webapp2.WSGIApplication([
    ('/', Login),
    ('/rate', MainPage),
    ('/delete', DeleteHandler),
    ('/error', ErrorHandler),
    ('/weather', WeatherDownload),
    ('/dashboard', Dashboard),
    ('/joDKskOKufkwl39a3jwghga240ckaJEKRmcairtsDK', Reminder),
], debug=True)

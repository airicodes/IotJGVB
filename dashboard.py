import dash
from dash.dependencies import Input, Output
import dash_daq as daq
import dash_core_components as dcc
import dash_html_components as html
import time
import base64
import board
from dash.exceptions import PreventUpdate
import RPi.GPIO as GPIO
import adafruit_dht
import paho.mqtt.client as mqtt
import smtplib, ssl
import email
import imaplib
from datetime import datetime
import easyimap
from tinydb import TinyDB, Query

db = TinyDB('acountdb.json')

#For the motor
GPIO.setmode(GPIO.BCM)
GPIO.setup(12,GPIO.OUT)
GPIO.setup(23,GPIO.OUT)

port = 465
smtp_server = "smtp.gmail.com"
sender_email = "vincentjeremie53@gmail.com"
receiver_email = "vincebry0803@yahoo.com"
password = "VincentJeremie123"
headers  = "From: From Home System \n"
headers += "To: To Person \n"
headers += "Subject: "
headers += "Home system alert!"

now = datetime.now()
current_time = now.strftime("%d/%m/%Y %H:%M:%S")
body = "The light has been turned on.\n Time: " + current_time
body2 = "Do you want to turn on the fan? \n Yes or No"
body3 = "User Logged in!\n Time: " + current_time

#This message is for the light
message = (headers + '\n' + body)
#This message is for the fan
message2 = (headers + '\n' + body2)
#This message is for the user
message3 = (headers + '\n' + body3)

#This part is for receiving email
imap_ssl_host = 'imap.gmail.com'  # imap.mail.yahoo.com
imap_ssl_port = 993

#This function returns the first block of the message
def get_first_text_block(msg):
    type = msg.get_content_maintype()

    if type == 'multipart':
        for part in msg.get_payload():
            if part.get_content_maintype() == 'text':
                return part.get_payload()
    elif type == 'text':
        return msg.get_payload()

dhtDevice = adafruit_dht.DHT11(board.D17, use_pulseio=False)


app = dash.Dash(__name__)

#To connect to mqtt server
def connectClient() -> mqtt.Client:
    def on_connect(client, userdata, flags, rc):
     print("Connected with result code " + str(rc))

    client = mqtt.Client()
    client.on_connect = on_connect
    client.connect("172.20.10.8", 1883, 60)
    return client

#To subscribe to all of the topics
def subscribe(client: mqtt.Client):
    def on_message(client, userdata, msg):
        if msg.payload.decode("utf-8").isdigit():
          global lightIntensity
          lightIntensity = msg.payload.decode("utf-8")
        elif msg.payload.decode("utf-8").isalnum():
          global rfidValue
          rfidValue = msg.payload.decode("utf-8")
          # Getting the active user from the database
          global activeUser
          activeUser = (db.get(Query()['rfidTag'] == rfidValue))
          # Send the email to inform that a user has scanned
          context = ssl.create_default_context()
          with smtplib.SMTP_SSL(smtp_server, port, context = context) as server:
                server.login(sender_email, password)
                server.sendmail(sender_email, receiver_email, message3)

    client.subscribe("light")
    client.subscribe("rfid")
    client.on_message = on_message


client = connectClient()
subscribe(client)

client.loop_start()


#This callback is for sending the email when the light is on
@app.callback(Output('light', 'src'), Input('interval-component', 'n_intervals'))
def update_output(value):

    if int(lightIntensity) > 2200:
        value = app.get_asset_url('lightbulboff.png')
    else:
        # Uncomment this to send the email for the light status
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(smtp_server, port, context = context) as server:
           server.login(sender_email, password)
           server.sendmail(sender_email, receiver_email, message)
        value = app.get_asset_url('lightbulbon.png')

    return value

#This callback is for the notification alert!
@app.callback(Output('confirm-danger', 'displayed'),
              Input('button', 'on'))
def display_confirm(value):
    if value == True:
        return True
    return False

#This callback display the current Intensity of the light
@app.callback(Output('lightIntensity', 'children'), Input('interval-component', 'n_intervals'))
def update_output(value):
    value = "Light Intensity: " + str(lightIntensity)

    return value

#This callback is for the fan
@app.callback(Output('fan', 'src'), Input('interval-component', 'n_intervals'))
def update_output(value):
    imapper = easyimap.connect('imap.gmail.com', sender_email, password)
    for mail_id in imapper.listids(limit=1):
        mail = imapper.mail(mail_id)
        print(mail.body)
        if 'yes' in mail.body.lower():
            GPIO.output(12, True)
            GPIO.output(23, False)
            value = app.get_asset_url('fanOn.png')
        elif 'no' in mail.body.lower():
            value = app.get_asset_url('fanOff.png')
            GPIO.output(12, False)
            GPIO.output(23, False)

    return value

#This callback is for active user profile picture
@app.callback(Output('profilePic', 'src'), Input('interval-component', 'n_intervals'))
def update_output(value):
    value = app.get_asset_url(activeUser.get('profilePic'))
    return value

#This callback is for name of the active user
@app.callback(Output('profilename', 'children'), Input('interval-component', 'n_intervals'))
def update_output(value):
    value = "Name: "+ activeUser.get('name')

    return value

#This callback is for temperature of the active user
@app.callback(Output('profileTemp', 'children'), Input('interval-component', 'n_intervals'))
def update_output(value):
    value = "Temperature: "+ activeUser.get('temp')
    return value

#This callback is for light intensity of the active user
@app.callback(Output('profileLightInt', 'children'), Input('interval-component', 'n_intervals'))
def update_output(value):
    value = "Light Intensity: "+ activeUser.get('lightInt')
    return value


#callback for the humidity
@app.callback(Output('my-gauge-2', 'value'), Input('interval-component', 'n_intervals'))
def update_output(value):
    value = dhtDevice.humidity
    return value

#callback for the temperature
@app.callback(Output('my-gauge-1', 'value'), Input('interval-component', 'n_intervals'))
def update_output(value):
    value = dhtDevice.temperature
    if value > 20:
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(smtp_server, port, context = context) as server:
            server.login(sender_email, password)
            server.sendmail(sender_email, receiver_email, message2)

    return value

while True:
    app.layout = html.Center([ html.Div([
    html.H1('IoT Dashboard', style={'color':'white'}),
    html.Div([
        html.P(""),
    ])]),
    html.Br(),
    daq.Gauge(
        id='my-gauge-1',
        label="Temperature",
        #replace the value with dhtDevice.tempature
        value= 0,
        color='pink',
        size=300,
        max = 100,
        style={'margin-left': '1000px', 'color':'white', 'float': 'right', 'position' : 'relative', 'right': '100px', 'height': '400px'},
        showCurrentValue=True,
    ),
    daq.Gauge(
        id='my-gauge-2',
        label="Humidity",
        #replace the value with dhtDevice.humidity
        value= 0,
        max = 2000,
        size=300,
        style={'margin-right': '100px', 'margin-bottom': '100px', 'color':'white', 'height': '400px'},
        showCurrentValue=True,
    ),
    html.Div(children=[
    html.H2('Light Status', style={'color':'white'}),
    html.P("Light Intensity: ", id="lightIntensity", style={'color':'white'}),
    html.Img(id="light", src=app.get_asset_url('lightbulboff.png'), style={'height':'150px', 'width':'150px'})
    ], style={'float': 'right', 'position' : 'relative', 'right': '200px'}),
    html.Div(children=[
    html.H2('Fan Status', style={'color':'white'}),
    html.Img(id="fan", src=app.get_asset_url('fanOff.png'), style={'height':'200px', 'width':'200px'})
    ], style={'margin-left': '-1250px'}),
    dcc.ConfirmDialog(
        id='confirm-danger',
        message='The email has been sent!',
    ),
    html.Div(children=[
    html.H2('Profile:', style={'color':'white'}),
    html.Img(id="profilePic", src=app.get_asset_url('defualtAccount.png'), style={'height':'100px', 'width':'100px'}),
    html.P("Name: ", id="profilename", style={'color':'white'}),
    html.P("Temperature: ", id="profileTemp", style={'color':'white'}),
    html.P("Light Intensity: ", id="profileLightInt", style={'color':'white'})
    ], style={'bottom': '700px', 'margin-left': '30px', 'float': 'flex','position': 'relative'}),
    dcc.Interval(
            id='interval-component',
            interval=5*1000, # in milliseconds
            n_intervals=0
    ),

], style={'backgroundColor':'rgb(26, 23, 35)'})



    if __name__ == '__main__':
        app.run_server(debug=True)

    time.sleep(2.0)
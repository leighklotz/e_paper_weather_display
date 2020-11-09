# This little program is for the Waveshare 7.5
# inch Version 2 black and white only epaper display
# It uses OpenWeatherMap API to display weather info
import sys
import os
picdir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'pic')
icondir = os.path.join(picdir, 'icon')
fontdir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'font')

# Search lib folder for display driver modules
sys.path.append('lib')
from waveshare_epd import epd7in5_V2
epd = epd7in5_V2.EPD()

from datetime import datetime
import time
from PIL import Image,ImageDraw,ImageFont
import traceback

import requests, json
from io import BytesIO
import csv
from collections import namedtuple

from settings import *

import dateutil.parser
from datetime import datetime, timezone

# Set the fonts
font22 = ImageFont.truetype(os.path.join(fontdir, 'Font.ttc'), 22)
font30 = ImageFont.truetype(os.path.join(fontdir, 'Font.ttc'), 30)
font35 = ImageFont.truetype(os.path.join(fontdir, 'Font.ttc'), 35)
font50 = ImageFont.truetype(os.path.join(fontdir, 'Font.ttc'), 50)
font60 = ImageFont.truetype(os.path.join(fontdir, 'Font.ttc'), 60)
font100 = ImageFont.truetype(os.path.join(fontdir, 'Font.ttc'), 100)
font160 = ImageFont.truetype(os.path.join(fontdir, 'Font.ttc'), 160)
# Set the colors
black = 'rgb(0,0,0)'
white = 'rgb(255,255,255)'
grey = 'rgb(235,235,235)'

SIMULATE=True

def write_to_screen(image):
    print('Writing to screen.')
    if SIMULATE:
        print("SIMULATED")
        return
    # Write to screen
    h_image = Image.new('1', (epd.width, epd.height), 255)
    # Open the template
    screen_output_file = Image.open(os.path.join(picdir, image))
    # Initialize the drawing context with template as background
    h_image.paste(screen_output_file, (0, 0))
    epd.display(epd.getbuffer(h_image))

def display_error(error_source):
    # Display an error
    print('Error in the', error_source, 'request.')
    if SIMULATE:
        print("SIMULATED ERROR")
        return
    # Initialize drawing
    error_image = Image.new('1', (epd.width, epd.height), 255)
    # Initialize the drawing
    draw = ImageDraw.Draw(error_image)
    draw.text((100, 150), error_source +' ERROR', font=font50, fill=black)
    draw.text((100, 300), 'Retrying in 30 seconds', font=font22, fill=black)
    current_time = datetime.now().strftime('%H:%M')
    draw.text((300, 365), 'Last Refresh: ' + str(current_time), font = font50, fill=black)
    # Save the error image
    error_image_file = 'error.png'
    error_image.save(os.path.join(picdir, error_image_file))
    # Close error image
    error_image.close()
    # Write error to screen 
    write_to_screen(error_image_file, 30)

def screen_sleep(sleep_seconds):
    # Sleep
    time.sleep(1)
    if not SIMULATE:
        epd.sleep()
    print(f'Sleeping for {sleep_seconds}.')
    time.sleep(sleep_seconds)

def iso86901_datetime_age(n):
    now = datetime.now(timezone.utc)
    diff = now - dateutil.parser.parse(n)
    return diff.total_seconds()

def process_loop():
    while True:
        # Get the PM 2.5 value from thingspeak first, but don't error out.
        for http_try in range(3):
            try:
                # HTTP request
                print(f'Try #{http_try} to connect to Thingspeak.')
                thingspeak_response = requests.get(THINGSPEAK_URL)
                print('Connection to Thingspeak successful.')
                if thingspeak_response.status_code == 200:
                    thingspeak_feeds = thingspeak_response.json()['feeds']
                    response_pm_2_5 = thingspeak_feeds[-1]['field2']
                    response_pm_2_5_date = thingspeak_feeds[-1]['created_at']
                    response_pm_2_5_dates = [f['created_at'] for f in thingspeak_feeds]
                    response_pm_2_5_history = [f['field2'] for f in thingspeak_feeds]
                    break
                else:
                    response_pm_2_5 = ''
                    response_pm_2_5_date = None
                    response_pm_2_5_history = []
                    print(f'Thingspeak failed s={response.status_code}')
            except:
                print('Thingspeak connection error.')
                response_pm_2_5 = ''
                response_pm_2_5_date = None
                response_pm_2_5_history = []

        # Ensure there are no errors with connection
        error_connect = True
        while error_connect == True:
            try:
                # HTTP request
                print('Attempting to connect to OWM.')
                response = requests.get(OWM_URL)
                print('Connection to OWM successful.')
                error_connect = None
            except:
                # Call function to display connection error
                print('Connection error.')
                display_error('CONNECTION') 

        error = None
        while error == None:
            # Check status of code request
            if response.status_code == 200:
                print('Connection to Open Weather successful.')
                # get data in jason format
                data = response.json()

                # get current dict block
                current = data['current']
                # get current
                temp_current = current['temp']
                # get feels like
                feels_like = current['feels_like']
                # get humidity
                humidity = current['humidity']
                # get pressure
                wind = current['wind_speed']
                # get description
                weather = current['weather']
                report = weather[0]['description']
                # get icon url
                icon_code = weather[0]['icon']
                #icon_URL = 'http://openweathermap.org/img/wn/'+ icon_code +'@4x.png'

                # get daily dict block
                daily = data['daily']
                # get daily precip
                daily_precip_float = daily[0]['pop']
                #format daily precip
                daily_precip_percent = daily_precip_float * 100
                # get min and max temp
                daily_temp = daily[0]['temp']
                temp_max = daily_temp['max']
                temp_min = daily_temp['min']

                # Append weather data to CSV if csv_option == True
                if CSV_OPTION == True:
                    # Get current year, month, date, and time
                    current_year = datetime.now().strftime('%Y')
                    current_month = datetime.now().strftime('%m')
                    current_date = datetime.now().strftime('%d')
                    current_time = datetime.now().strftime('%H:%M')
                    #open the CSV and append weather data
                    with open('records.csv', 'a', newline='') as csv_file:
                        writer = csv.writer(csv_file, delimiter=',')
                        writer.writerow([current_year, current_month, current_date, current_time,
                                         LOCATION,temp_current, feels_like, temp_max, temp_min,
                                         humidity, daily_precip_float, wind])
                    print('Weather data appended to CSV.')

                # Set strings to be printed to screen
                r = namedtuple('r', 'location temp_current feels_like pm_2_5 humidity wind report temp_max temp_min precip_percent icon_code')
                r.location = LOCATION
                r.temp_current = format(temp_current, '.0f') + u'\N{DEGREE SIGN}F'
                r.feels_like = 'Feels like: ' + format(feels_like, '.0f') +  u'\N{DEGREE SIGN}F'
                r.humidity = 'Humidity: ' + str(humidity) + '%'
                r.wind = 'Wind: ' + format(wind, '.1f') + ' MPH'
                r.report = 'Now: ' + report.title()
                r.temp_max = 'High: ' + format(temp_max, '>.0f') + u'\N{DEGREE SIGN}F'
                r.temp_min = 'Low:  ' + format(temp_min, '>.0f') + u'\N{DEGREE SIGN}F'
                r.precip_percent = 'Precip: ' + str(format(daily_precip_percent, '.0f'))  + '%'
                r.icon_code = icon_code
                if response_pm_2_5_date is None:
                    r.pm_2_5 = f'PM 2.5: ---'
                elif iso86901_datetime_age(response_pm_2_5_date) < 1000:
                    r.pm_2_5 = 'PM 2.5: ' + str(response_pm_2_5) + u'\N{GREEK SMALL LETTER MU}' + 'g/m' + u'\N{SUPERSCRIPT THREE}'
                else:
                    age = int(iso86901_datetime_age(response_pm_2_5_date))
                    r.pm_2_5 = f'PM 2.5: stale {age}s'

                # Set error code to false
                error = False

                '''
                print('Location:', LOCATION)
                print('Temperature:', format(temp_current, '.0f'), u'\N{DEGREE SIGN}F') 
                print('Feels Like:', format(feels_like, '.0f'), 'F') 
                print('Humidity:', humidity)
                print('Wind Speed:', format(wind_speed, '.1f'), 'MPH')
                print('Report:', report.title())

                print('High:', format(temp_max, '.0f'), 'F')
                print('Low:', format(temp_min, '.0f'), 'F')
                print('Probabilty of Precipitation: ' + str(format(daily_precip_percent, '.0f'))  + '%')
                '''    
                display_results(r)

            else:
                # Call function to display HTTP error
                display_error('HTTP')

def display_results(r):
    # Open template file
    template = Image.open(os.path.join(picdir, 'template.png'))
    # Initialize the drawing context with template as background
    draw = ImageDraw.Draw(template)
    
    ## Open icon file
    icon_file = r.icon_code + '.png' 
    icon_image = Image.open(os.path.join(icondir, icon_file))

    # Draw top left box
    ## Paste the image
    template.paste(icon_image, (40, 15))
    ## Place a black rectangle outline
    draw.rectangle((25, 20, 225, 180), outline=black)
    ## Draw Text
    draw.text((30, 200), r.report, font=font22, fill=black)
    draw.text((30, 240), r.precip_percent, font=font30, fill=black)

    # Draw top middle box
    draw.text((285, 35), r.temp_current, font=font100, fill=black)
    draw.text((285, 210), r.feels_like, font=font35, fill=black)

    # Draw top right box
    # (x0, y0,  x1, y1)
    # Debug Outline
    LEFT_EDGE = 520
    LEFT_OFFSET = 520
    TOP_EDGE = 10
    TOP_OFFSET = 20
    BOTTOM_EDGE = 295
    RIGHT_EDGE = 789
    YMAX = 300
    draw.rectangle((LEFT_EDGE, TOP_EDGE, RIGHT_EDGE, BOTTOM_EDGE), fill=white)
    data = [4,5,1,4,4]
    x = 0
    for i in data:
        x = x + 10
        y = YMAX + TOP_OFFSET + TOP_EDGE - i
        # x0,y0 x1,y1
        draw.line((x+LEFT_OFFSET,BOTTOM_EDGE,x+LEFT_OFFSET,y-40), width=5, fill=black)
    
    # Draw bottom left box
    draw.text((35, 325), r.temp_max, font=font50, fill=black)
    draw.rectangle((170, 385, 265, 387), fill=black)
    draw.text((35, 390), r.temp_min, font=font50, fill=black)

    # Draw bottom middle box
    draw.text((345, 320), r.pm_2_5, font=font30, fill=black)
    draw.text((345, 360), r.humidity, font=font30, fill=black)
    draw.text((345, 400), r.wind, font=font30, fill=black)

    # Draw bottom right box
    draw.text((627, 330), 'UPDATED', font=font35, fill=white)
    current_time = datetime.now().strftime('%H:%M')
    draw.text((627, 375), current_time, font = font60, fill=white)
    ## Add a reminder to take out trash on Mon
    weekday = datetime.today().weekday()
    if weekday == 0:
        draw.rectangle((345, 13, 705, 55), fill =black)
        draw.text((355, 15), 'TAKE OUT TRASH TONIGHT!', font=font30, fill=white)
        
    # Save the image for display as PNG
    screen_output_file = os.path.join(picdir, 'screen_output.png')
    template.save(screen_output_file)
    # Close the template file
    template.close()
    
    # Refresh clear screen to avoid burn-in at 3:00 AM
    if datetime.now().strftime('%H') == '03':
    	print('Clearning screen to avoid burn-in.')
    	epd.Clear()
    
    # Write to screen
    write_to_screen(screen_output_file)
    # Sleep
    screen_sleep(600)

if __name__ == "__main__":
    # Initialize and clear screen
    print('Initializing and clearing screen.')
    if not SIMULATE:
        epd.init()
        epd.Clear()
    process_loop()

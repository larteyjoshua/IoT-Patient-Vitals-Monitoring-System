'''


Usage:
    run <python app.py> 
    follow url given

Created : July 2019

Author(s) :

'''


from flask import*
# from aquaLite import *
import datetime
import json
import sqlite3
import time
import statistics as stat
from config import credential
import generator
from flask_toastr import Toastr     # toastr module import
import create_database
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session,sessionmaker
from passlib.hash import sha256_crypt


app = Flask(__name__)

# python notification toaster
toastr = Toastr(app)

# Set the secret_key on the application to something unique and secret.
app.config['SECRET_KEY'] = '5791628bb0b13ce0c676dfde280ba245'

@app.route('/')
def index():
    return render_template("index.html")

@app.route('/records')
def records():
    return render_template("records.html")


# home route....landing page
engine = create_engine('sqlite:///iot_wqms_data.db')
db=scoped_session(sessionmaker(bind=engine))

@app.route("/register",methods=["GET","POST"])
def registered():
    if request.method=="POST":
        name=request.form.get("name")
        email=request.form.get("email")
        ml_number =request.form.get("ml_number")
        password=request.form.get("password")
        confirm=request.form.get("confirm")
        secure_password=sha256_crypt.encrypt(str(password))

        print(name)

        usernamedata=db.execute("SELECT email FROM users WHERE email=:email",{"email":email}).fetchone()
        #usernamedata=str(usernamedata)
        if usernamedata==None:
            if password==confirm:
                db.execute("INSERT INTO users(name,email, ml_number, password) VALUES(:name,:email,:ml_number, :password)",
                    {"name":name,"email":email,"ml_number":ml_number, "password":secure_password})
                db.commit()
                flash("You are registered and can now login","success")
                return redirect(url_for('index'))
            else:
                flash("password does not match","danger")
                return render_template('register.html')
        else:
            flash("user already existed, please login or contact admin","danger")
            return redirect(url_for('login'))

    return render_template('register.html')

@app.route("/login",methods=["GET","POST"])
def login():
    if request.method=="POST":
        email=request.form.get("email")
        password=request.form.get("password")
        usernamedata=db.execute("SELECT email FROM users WHERE email=:email",{"email":email}).fetchone()
        passworddata=db.execute("SELECT password FROM users WHERE email=:email",{"email":email}).fetchone()

        if usernamedata is None:
            flash("No User","danger")
            return render_template('register.html')
        else:
            for passwor_data in passworddata:
                if sha256_crypt.verify(password,passwor_data):
                    session["log"]=True
                    flash("You are now logged in!!","success")
                    return redirect(url_for('dashboard'))
                else:
                    return render_template('index.html')
                    flash("incorrect password","danger")

    return render_template('index.html')



@app.route('/add_data')
def add_data():
    temperature = request.args.get('temperature')
    pulse = request.args.get('pulse')
    respiration = request.args.get('respiration')
    print(temperature)
    print(pulse)
    print(respiration)
    add_to_db(temperature,pulse,respiration)
    return redirect(url_for('dashboard')) 


def add_to_db(temperature, pulse, respiration):
    con = sqlite3.connect('iot_wqms_data.db')
    c = con.cursor()
    c.execute(""" INSERT INTO iot_wqms_table( temperature, turbidity, ph) 
                         VALUES (?, ?, ?) """,
                   (temperature,pulse, respiration))
    flash("data inserted SUCCESSFULLY", "success")
    con.commit()
    print("Data inserted SUCCESSFULLY")


# empty list to be used for all parameter route
time = []
ph=[]
temp= []
turbidity= []
waterlevel=[]

# initial temps
average_temp = 0
min_temp=0
max_temp=0
range_temp = 0

@app.route("/tempChart/<x>")
def temperature(x):
    print(">>> temperature page running ...")
    # connecting to datebase
    con = sqlite3.connect('iot_wqms_data.db')
    cursor = con.cursor()

    #  30secs time interval for pushing data from sensor to database, that the limit of data to be determined  
    
    # data processing for an hour 
    if x == '1h':
        name = '1 Hour'
        label = 'Minute'

        # with 30 seconds interval, ...2,880 temperature data will be posted within an hour
        cursor.execute(" SELECT time,temperature FROM ( SELECT * from iot_wqms_table ORDER BY id DESC LIMIT 120 ) order by id asc ") 
        data = cursor.fetchall()
        
        # emptying list 
        del time[:]
        del temp[:]
    
        for datum in data:
            # temperature data extraction
            datum_float = float(datum[1])
            temp.append(datum_float)
            # time extraction
            t = str(datum[0][14:])
            time.append(t)
        
        # analysis
        mean_temp = stat.mean(temp)
        average_temp = round(mean_temp, 2)
        min_temp = round(min(temp), 2) # assigned to global min_temp
        max_temp = round(max(temp), 2)
        range_temp = max_temp - min_temp


    # data processing for a day
    
    if x == '1d':
        name = '1 Day'
        label = 'Hour'
    
        cursor.execute(" SELECT time,temperature FROM iot_wqms_table ORDER BY id ASC LIMIT 2880 ") 
        data = cursor.fetchall()

        del time[:] # time on the x-axis
        del temp[:]
    
        for datum in data:
            # print(datum)
            datum_float = float(datum[1])
            temp.append(datum_float)
            t = str(datum[0][11:16])
            time.append(t)
        
        # analysis
        mean_temp = stat.mean(temp)
        average_temp = round(mean_temp, 2)
        min_temp = round(min(temp), 2) # assigned to global min_temp
        max_temp = round(max(temp), 2)
        range_temp = max_temp - min_temp


    # weekly data processing ,,,,,

    if x == '1w':
        name = '1 Week'
        label = 'Day'

        # fetching data from database
        cursor.execute(" SELECT time,temperature FROM iot_wqms_table ORDER BY id ASC LIMIT 20160") 
        data = cursor.fetchall()
        
        # converting timestamp from database to day in string like Mon, Tue
        def date_to_day(year, month, day):
            time = datetime.datetime(year, month, day)
            return (time.strftime("%a"))

        # emptying time and temperature container list
        del time[:]
        del temp[:]

        # retrieving weekly time and temp from database data
        for datum in data:
            # collecting temperature
            datum_float = float(datum[1])   # temp data in float
            temp.append(datum_float)        # pushing to temp list

            # string day processing from full timestamp
            tm = str(datum[0][:10])
            tm_split = tm.split("-")
            year = int(tm_split[0])
            month = int(tm_split[1])
            day = int(tm_split[2])

            # using full_date to day_string function defined 
            current_day = date_to_day(year, month, day)
            time.append(current_day)
            
        # analysis
        mean_temp = stat.mean(temp)
        average_temp = round(mean_temp, 2)
        min_temp = round(min(temp), 2) # assigned to global min_temp
        max_temp = round(max(temp), 2)
        range_temp = max_temp - min_temp


    # monthly data processing

    if x == '1m':
        name = '1 Month'
        label = 'Month-Date'

        # fetching data from database.....change number of data to fetch
        cursor.execute(" SELECT time,temperature FROM iot_wqms_table ORDER BY id ASC LIMIT 87600") 
        data = cursor.fetchall()
        
        # retreiving month string from timestamp of database to get sth like January, Febuary
        def string_month_from_full_date(year, month, day):
            time = datetime.datetime(year, month, day)
            return (time.strftime("%b")) # %B for fullname

        # emptying time and temperature container list
        del time[:]
        del temp[:]

        # retrieving monthly time and temp from database data
        for datum in data:
            # collecting temperature
            # print(datum)
            datum_float = float(datum[1])   # temp data in float
            temp.append(datum_float)        # pushing to temp list

            # string month processing from full date timestamp
            tm = str(datum[0][5:10])
            time.append(tm)

         # analysis
        mean_temp = stat.mean(temp)
        average_temp = round(mean_temp, 2)
        min_temp = round(min(temp), 2) # assigned to global min_temp
        max_temp = round(max(temp), 2)
        range_temp = max_temp - min_temp


    # yearly data processing

    if x == '1y':
        name = '1 Year'
        label = 'Month'

        # fetching data from database.....change number of data to fetch
        cursor.execute(" SELECT time,temperature FROM iot_wqms_table ORDER BY id ASC LIMIT 1051333") 
        data = cursor.fetchall()
        
         # retreiving month string from timestamp of database to get sth like January, Febuary
        def string_month_from_full_date(year, month, day):
            time = datetime.datetime(year, month, day)
            return (time.strftime("%b")) # %B for fullname

        # emptying time and temperature container list
        del time[:]
        del temp[:]

        # retrieving monthly time and temp from database data
        for datum in data:
            # collecting temperature
            # print(datum)
            datum_float = float(datum[1])   # temp data in float
            temp.append(datum_float)        # pushing to temp list

            # string month processing from full date timestamp
            tm = str(datum[0][:10])
            tm_split = tm.split("-")
            year = int(tm_split[0])
            month = int(tm_split[1])
            day = int(tm_split[2])

            # using full_date to day_string function defined 
            current_month = string_month_from_full_date(year, month, day)
            time.append(current_month)
            # time.append(year)
            
         # analysis
        mean_temp = stat.mean(temp)
        average_temp = round(mean_temp, 2)
        min_temp = round(min(temp), 2) # assigned to global min_temp
        max_temp = round(max(temp), 2)
        range_temp = max_temp - min_temp


    # all data processing

    if x == 'all':
        name = 'All'
        label = 'Time'

        # fetching data from database.....change number of data to fetch
        # cursor.execute(" SELECT time,temperature FROM iot_wqms_table ORDER BY id DESC LIMIT 1440") 
        cursor.execute(" SELECT time,temperature FROM ( SELECT * from iot_wqms_table ORDER BY id DESC ) order by id asc") 
        data = cursor.fetchall()

        # emptying time and temperature container list
        del time[:]
        del temp[:]

        # retrieving monthly time and temp from database data
        for datum in data:
            # collecting temperature
            # print(datum)
            datum_float = float(datum[1])   # temp data in float
            temp.append(datum_float)        # pushing to temp list
            # string month processing from full date timestamp
            tm = str(datum[0][:7])
            time.append(tm)
            
         # analysis
        mean_temp = stat.mean(temp)
        average_temp = round(mean_temp, 2)
        min_temp = round(min(temp), 2) # assigned to global min_temp
        max_temp = round(max(temp), 2)
        range_temp = max_temp - min_temp

    return render_template("tempChart.html", temp=temp, time=time, label=label, name=name, mean=average_temp, max_temp=max_temp, min_temp=min_temp, range_temp=range_temp)


@app.route("/phChart/<x>")
def powerOfHydrogen(x):
    print(">>> ph page running ...")
    # connecting to datebase
    con = sqlite3.connect('iot_wqms_data.db')
    cursor = con.cursor()

    # data processing for an hour 
    if x == '1h':
        name = '1 Hour'
        label = 'Minute'

        # selecting ph data
        cursor.execute(" SELECT time, ph FROM ( SELECT * from iot_wqms_table ORDER BY id DESC LIMIT 120 ) order by id asc ") 
        data = cursor.fetchall()
        # print(data)

        # emptying list 
        del time[:]
        del ph[:]

        # data extraction
        for datum in data:
            # print(datum)
            # extracting ph data
            datum_float = float(datum[1])
            ph.append(datum_float)
            # extracting minutes and seconds
            t = str(datum[0][14:])
            time.append(t)
        
        # analysis
        average_ph = round(stat.mean(ph), 2)
        min_ph = round(min(ph), 2)
        max_ph = round(max(ph), 2)
        range_ph = float( round((max_ph - min_ph), 2) )

    # data processing for day 
    if x == '1d':
        name = '1 Day'
        label = 'Hour'

        # selecting ph data
        cursor.execute(" SELECT time, ph FROM iot_wqms_table ORDER BY id ASC LIMIT 2880 ") 
        data = cursor.fetchall()

        # emptying list 
        del time[:]
        del ph[:]

        # data extraction
        for datum in data:
            # print(datum)
            # extracting ph data
            datum_float = float(datum[1])
            ph.append(datum_float)
            # extracting minutes and seconds
            t = str(datum[0][11:16])
            time.append(t)

        # analysis
        average_ph = round(stat.mean(ph), 2)
        min_ph = round(min(ph), 2)
        max_ph = round(max(ph), 2)
        range_ph = float( round((max_ph - min_ph), 2) )


     # weekly data processing ,,,,,

    if x == '1w':
        name = '1 Week'
        label = 'Day'

        # fetching data from database
        cursor.execute(" SELECT time, ph FROM iot_wqms_table ORDER BY id ASC LIMIT 20160") 
        data = cursor.fetchall()
        
        # converting timestamp from database to day in string like Mon, Tue
        def date_to_day(year, month, day):
            time = datetime.datetime(year, month, day)
            return (time.strftime("%a"))

        # emptying time and ph container list
        del time[:]
        del ph[:]

        # retrieving weekly time and ph from database data
        for datum in data:
            # collecting ph
            # print(datum)
            datum_float = float(datum[1])   # ph data in float
            ph.append(datum_float)        # pushing to ph list

            # string day processing from full timestamp
            tm = str(datum[0][:10])
            tm_split = tm.split("-")
            year = int(tm_split[0])
            month = int(tm_split[1])
            day = int(tm_split[2])

            # converting full_date to day_string function defined 
            current_day = date_to_day(year, month, day)
            time.append(current_day)
            
        # analysis
        average_ph = round(stat.mean(ph), 2)
        min_ph = round(min(ph), 2)
        max_ph = round(max(ph), 2)
        range_ph = float( round((max_ph - min_ph), 2) )

    
     # monthly data processing

    if x == '1m':
        name = '1 Month'
        label = 'Month-Date'

        # fetching data from database.....change number of data to fetch
        cursor.execute(" SELECT time, ph FROM iot_wqms_table ORDER BY id ASC LIMIT 87600") 
        data = cursor.fetchall()

        # emptying list
        del time[:]
        del ph[:]

        # extracting monthly time and ph data to empty list
        for datum in data:
            # collecting ph
            # print(datum)
            datum_float = float(datum[1])   # ph data to float
            ph.append(datum_float)       

            # extracting month from full timestamp
            tm = str(datum[0][5:10])
            time.append(tm)
        
         # analysis
        average_ph = round(stat.mean(ph), 2)
        min_ph = round(min(ph), 2)
        max_ph = round(max(ph), 2)
        range_ph = float( round((max_ph - min_ph), 2) )


    # yearly data processing

    if x == '1y':
        name = '1 Year'
        label = 'Month'

        cursor.execute(" SELECT time, ph FROM iot_wqms_table ORDER BY id ASC LIMIT 1051333") 
        data = cursor.fetchall()

         # retreiving month in string from timestamp of database to get sth like January, Febuary
        def string_month_from_full_date(year, month, day):
            time = datetime.datetime(year, month, day)
            return (time.strftime("%b")) # %B for fullname

        # emptying
        del time[:]
        del ph[:]

        # retrieving monthly time and ph to emptied list above
        for datum in data:
            # collecting ph
            datum_float = float(datum[1])   # temp data in float
            ph.append(datum_float)        # pushing to temp list

            # string month processing from full date timestamp
            tm = str(datum[0][:10])
            tm_split = tm.split("-")
            year = int(tm_split[0])
            month = int(tm_split[1])
            day = int(tm_split[2])

            # using full_date to day_string function to get month in string 
            current_month = string_month_from_full_date(year, month, day)
            time.append(current_month)

        # analysis
        average_ph = round(stat.mean(ph), 2)
        min_ph = round(min(ph), 2)
        max_ph = round(max(ph), 2)
        range_ph = float( round((max_ph - min_ph), 2) )

    
    # all data processing

    if x == 'all':
        name = 'All'
        label = "Time"
        cursor.execute(" SELECT time, ph FROM ( SELECT * from iot_wqms_table ORDER BY id DESC ) order by id asc") 
        data = cursor.fetchall()
        
        # emptying 
        del time[:]
        del ph[:]
        # retrieving monthly time and ph to emptied list
        for datum in data:
            # collecting temperature
            datum_float = float(datum[1])   # ph data in float
            ph.append(datum_float)        # pushing to ph list

            # string month processing from full date timestamp
            tm = str(datum[0][:7])
            time.append(tm)
            
        # analysis
        average_ph = round(stat.mean(ph), 2)
        min_ph = round(min(ph), 2)
        max_ph = round(max(ph), 2)
        range_ph = float( round((max_ph - min_ph), 2) )

    return render_template("phChart.html", ph=ph, time=time, label=label, name=name, average_ph=average_ph, min_ph=min_ph, max_ph=max_ph, range_ph=range_ph)


@app.route("/turbChart/<x>")
def turb(x):
    print(">>> turbidity page running ...")
    con = sqlite3.connect('iot_wqms_data.db')
    cursor = con.cursor()
    if x == '1h':
        name = '1 Hour'
        label = 'Minute'
        cursor.execute(" SELECT time, turbidity FROM ( SELECT * from iot_wqms_table ORDER BY id DESC LIMIT 120 ) order by id asc ") 
        data = cursor.fetchall()
        del time[:]
        del turbidity[:]
        for datum in data:
            datum_float = float(datum[1])
            turbidity.append(datum_float)
            t = str(datum[0][14:])
            time.append(t)
        average_turbidity = round(stat.mean(turbidity), 2)
        min_turbidity = round(min(turbidity), 2)
        max_turbidity = round(max(turbidity), 2)
        range_turbidity = float( round((max_turbidity - min_turbidity), 2) )
        print("range", range_turbidity)
    
    # data processing for day 
    if x == '1d':
        name = '1 Day'
        label = 'Hour'
        cursor.execute(" SELECT time, turbidity FROM iot_wqms_table ORDER BY id ASC LIMIT 2880 ") 
        data = cursor.fetchall()
        del time[:]
        del turbidity[:]
        # appending data to emptied list
        for datum in data:
            datum_float = float(datum[1])
            turbidity.append(datum_float)
            t = str(datum[0][11:16])
            time.append(t)
        # to 2 decimal places
        average_turbidity = round( stat.mean(turbidity) , 2)
        min_turbidity = round(min(turbidity), 2)
        max_turbidity = round(max(turbidity), 2)
        range_turbidity = float( round((max_turbidity - min_turbidity), 2) )

    if x == '1w':
        name = '1 Week'
        label = 'Day'
        cursor.execute(" SELECT time, turbidity FROM iot_wqms_table ORDER BY id ASC LIMIT 20160") 
        data = cursor.fetchall()
        def date_to_day(year, month, day):
            time = datetime.datetime(year, month, day)
            return (time.strftime("%a"))
        del time[:]
        del turbidity[:]
        for datum in data:
            # print(datum)
            datum_float = float(datum[1])   # ph data in float
            turbidity.append(datum_float)        # pushing to ph list
            tm = str(datum[0][:10])
            tm_split = tm.split("-")
            year = int(tm_split[0])
            month = int(tm_split[1])
            day = int(tm_split[2])
            current_day = date_to_day(year, month, day)
            time.append(current_day)
        average_turbidity = round( stat.mean(turbidity) , 2)
        min_turbidity = round(min(turbidity), 2)
        max_turbidity = round(max(turbidity), 2)
        range_turbidity = float( round((max_turbidity - min_turbidity), 2) )

    if x == '1m':
        name = '1 Month'
        label = 'Month-Date'
        cursor.execute(" SELECT time, turbidity FROM iot_wqms_table ORDER BY id ASC LIMIT 87600") 
        data = cursor.fetchall()
        del time[:]
        del turbidity[:]
        for datum in data:
            datum_float = float(datum[1])   # ph data to float
            turbidity.append(datum_float)       
            tm = str(datum[0][5:10])
            time.append(tm)
        average_turbidity = round( stat.mean(turbidity) , 2)
        min_turbidity = round(min(turbidity), 2)
        max_turbidity = round(max(turbidity), 2)
        range_turbidity = float( round((max_turbidity - min_turbidity), 2) )
    
    if x == '1y':
        name = '1 Year'
        label = 'Month'
        cursor.execute(" SELECT time, turbidity FROM iot_wqms_table ORDER BY id ASC LIMIT 1051333") 
        data = cursor.fetchall()
        def string_month_from_full_date(year, month, day):
            time = datetime.datetime(year, month, day)
            return (time.strftime("%b")) # %B for fullname
        del time[:]
        del turbidity[:]
        for datum in data:
            datum_float = float(datum[1])   # temp data in float
            turbidity.append(datum_float)        # pushing to temp list
            tm = str(datum[0][:10])
            tm_split = tm.split("-")
            year = int(tm_split[0])
            month = int(tm_split[1])
            day = int(tm_split[2])
            current_month = string_month_from_full_date(year, month, day)
            time.append(current_month)
        average_turbidity = round( stat.mean(turbidity) , 2)
        min_turbidity = round(min(turbidity), 2)
        max_turbidity = round(max(turbidity), 2)
        range_turbidity = float( round((max_turbidity - min_turbidity), 2) )

    if x == 'all':
        name = 'All'
        label = "Time"
        cursor.execute(" SELECT time, turbidity FROM ( SELECT * from iot_wqms_table ORDER BY id DESC ) order by id asc") 
        data = cursor.fetchall()
        del time[:]
        del turbidity[:]
        for datum in data:
            datum_float = float(datum[1])   # ph data in float
            turbidity.append(datum_float)        # pushing to ph list
            tm = str(datum[0][:7])
            time.append(tm)
        average_turbidity = round( stat.mean(turbidity) , 2)
        min_turbidity = round(min(turbidity), 2)
        max_turbidity = round(max(turbidity), 2)
        range_turbidity = float( round((max_turbidity - min_turbidity), 2) )

    return render_template("turbChart.html", turbidity=turbidity, time=time, label=label, name=name, average_turbidity=average_turbidity, min_turbidity=min_turbidity, max_turbidity=max_turbidity, range_turbidity=range_turbidity)



@app.route("/dashboard", methods=["GET"])
def dashboard():
    print(">>> dashboard running ...")
    con = sqlite3.connect('iot_wqms_data.db')
    cursor = con.cursor()

    # selecting current hour data ...ie, 120 for every 30 seconds of posting
    cursor.execute(" SELECT * FROM iot_wqms_table ORDER BY id DESC LIMIT 120") 
    data = cursor.fetchall()
    data = list(data)

    print(".........Page refreshed at", datetime.datetime.now())

    # data collector
    temp_data = []
    turbidity_data = []
    ph_data = []


    # collecting individual data to collectors
    for row in data:
        temp_data.append(row[2])   
        turbidity_data.append(row[3])
        ph_data.append(row[4])


    # last value added to database...current data recorded 
    last_temp_data = temp_data[0]
    last_turbidity_data = turbidity_data[0]
    last_ph_data = ph_data[0]


    # message toasting 
    if (last_temp_data < 34) | (last_temp_data > 37):
        flash("Abnormal Temperatures", 'warning')
    if (last_turbidity_data < 12) | (last_turbidity_data > 16):
        flash("Abnormal Respiration", 'warning')
    if (last_ph_data < 60) | (last_ph_data > 100):
        flash("Abnormal Pulse Rate", 'warning')


    # current sum of 1hour data rounded to 2dp
    current_temp_sum = round(sum(temp_data), 2)
    current_turbidity_sum = round(sum(turbidity_data), 2)
    current_ph_sum = round( sum(ph_data), 2 )
    
    # fetching 240 data from db to extract the penultimate 120 data to calculate percentage change
    cursor.execute(" SELECT * FROM iot_wqms_table ORDER BY id DESC LIMIT 240") 
    data = list(cursor.fetchall())

    # collecting individual data
    prev_temp_data = []  # collecting temp values
    prev_turbidity_data = []
    prev_ph_data = []
    for row in data:
        prev_temp_data.append(row[2])
        prev_turbidity_data.append(row[3])
        prev_ph_data.append(row[4])

    # slicing for immediate previous 120 data 
    prev_temp_data = prev_temp_data[120:240]
    prev_temp_sum = round( sum(prev_temp_data), 2 )

    prev_turbidity_data = prev_turbidity_data[120:240]
    prev_turbidity_sum = round( sum(prev_turbidity_data), 2 )

    prev_ph_data = prev_ph_data[120:240]
    prev_ph_sum = round( sum(prev_ph_data), 2 )


    # temp, getting the percentage change
    temp_change = prev_temp_sum - current_temp_sum
    temp_change = round(temp_change, 2)
    percentage_temp_change = (temp_change/current_temp_sum) * 100
    percentage_temp_change = round(percentage_temp_change, 1)
    
    # ph, getting the percentage change
    ph_change = prev_ph_sum - current_ph_sum
    ph_change = round(ph_change, 2)
    percentage_ph_change = (ph_change/current_ph_sum) * 100
    percentage_ph_change = round(percentage_ph_change,1)

    # turbidity, getting the percentage change
    turbidity_change = prev_turbidity_sum - current_turbidity_sum
    turbidity_change = round(turbidity_change, 2)
    percentage_turbidity_change = (turbidity_change/current_turbidity_sum) * 100
    percentage_turbidity_change = round(percentage_turbidity_change,1)

    # waterlevel, getting the percentage change
   


    # notification toast 
    # flash("Not So OK", 'error')

    return render_template("dashboard.html", data=data, percentage_temp_change=percentage_temp_change, percentage_ph_change=percentage_ph_change, percentage_turbidity_change=percentage_turbidity_change, temp_change=temp_change, ph_change=ph_change, turbidity_change=turbidity_change,last_temp_data=last_temp_data, last_ph_data=last_ph_data, last_turbidity_data=last_turbidity_data)




@app.route("/download/<prop>")
def get_CSV(prop):
    print(">>> csv file downloaded")

    if prop == 'temperature':
        # prepare data in csv format
        generator.generate_csv_file(prop)

        # opens, reads, closes csv file for download 
        with open(f'data/wqms_{prop}_data.csv', 'r') as csv_file:
            csv_reader = csv_file.read().encode('latin-1')
        csv_file.close()

        # routes function returning the file download
        return Response(
            csv_reader,
            mimetype="text/csv",
            headers={"Content-disposition": "attachment; filename=wqms_%s.csv" %prop}
        )
    

    if prop == 'turbidity':
        generator.generate_csv_file(prop)
        with open(f'data/wqms_{prop}_data.csv', 'r') as csv_file:
            csv_reader = csv_file.read().encode('latin-1')
        csv_file.close()

        return Response(
            csv_reader,
            mimetype="text/csv",
            headers={"Content-disposition": "attachment; filename=wqms_%s.csv" %prop}
        )


    if prop == 'ph':
        generator.generate_csv_file(prop)
        with open(f'data/wqms_{prop}_data.csv', 'r') as csv_file:
            csv_reader = csv_file.read().encode('latin-1')
        csv_file.close()

        return Response(
            csv_reader,
            mimetype="text/csv",
            headers={"Content-disposition": "attachment; filename=wqms_%s.csv" %prop}
        )
    

    if prop == 'water_level':
        generator.generate_csv_file(prop)
        with open(f'data/wqms_{prop}_data.csv', 'r') as csv_file:
            csv_reader = csv_file.read().encode('latin-1')
        csv_file.close()

        return Response(
            csv_reader,
            mimetype="text/csv",
            headers={"Content-disposition": "attachment; filename=wqms_%s.csv" %prop}
        )
       


# main function
if  __name__ == "__main__":
    try:
        # using local ip address and auto pick up changes
        app.run(debug=True)

        # create database for the system if on not created
        create_database.create_table()

        # using static ip
        # app.run(debug=True, host='192.168.43.110 ', port=5050)   # setting your own ip

    except Exception as rerun:
        print(">>> Failed to run main program : ",rerun)

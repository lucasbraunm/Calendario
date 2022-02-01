from flask import Flask, flash, jsonify, redirect, render_template, request, session
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash
from flask_session import Session
from tempfile import mkdtemp
import sqlite3 

from helpers import login_required
import datetime
import calendar

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Important global variables
date_now = datetime.datetime.now()
current_date = date_now
state = "day"
name = ""

@app.route("/login", methods=["GET", "POST"])
def login():
    # Log in

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        # Query database for username
        # Create SQL cursor
        connection = sqlite3.connect("database.db")
        db = connection.cursor()

        username = request.form.get("username")
        rows = db.execute("SELECT * FROM users WHERE username = ?",
                          [username]).fetchall()

        connection.commit()
        connection.close()

        # Ensure username exists and password is correct
        if len(rows) == 1:
            id_user, username, password = rows[0]
            if not check_password_hash(password, request.form.get("password")):
                alert_message = "Invalid password"
                return render_template("login.html", alert=1, alert_message=alert_message)   
        else:
            alert_message = "Invalid username"
            return render_template("login.html", alert=1, alert_message=alert_message)

        # Remember which user has logged in
        session["user_id"] = id_user

        global name
        name = username

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")

@app.route("/logout")
def logout():
    # Log out

    # Forget any user_id
    session.clear()

    current_date = date_now
    state = "day"

    # Redirect user to login form
    return redirect("/")

@app.route("/register", methods=["GET", "POST"])
def register():
    # Register

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        # Ensure that password and confirmation are equal
        if request.form.get("password") != request.form.get("confirmation"):
            alert_message = "Password and confirmation must be the same"
            return render_template("register.html", alert=1, alert_message=alert_message)

        # Query database for username
        # Create SQL cursor
        connection = sqlite3.connect("database.db")
        db = connection.cursor()

        username = request.form.get("username")
        rows = db.execute("SELECT * FROM users WHERE username = ?", [username]).fetchall()

        # Check if user name already exists
        if len(rows) == 1:
            alert_message = "Username already exists"
            return render_template("register.html", alert=1, alert_message=alert_message)

        # Insert username and hashed password into database
        username = request.form.get("username")
        password = request.form.get("password")
        hashed_password = generate_password_hash(password)

        db.execute(
            "INSERT INTO users (username, hash) VALUES ( ?, ? )",
            (username, hashed_password)
        )


        connection.commit()
        connection.close()

        # Redirect user to home page
        return redirect("/login")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("register.html")

@app.route("/", methods=["GET", "POST"])
# @login_required
@login_required
def home():
    # Index page

    # Declare global variables to change calendar
    global state
    global current_date
    
    # Change state if button was pressed
    if request.method == "POST":
        if request.form.get("change-to-year") != None:
            state = "year"
            return redirect("/")
        elif request.form.get("change-to-month") != None:
            state = "month"
            return redirect("/")
        elif request.form.get("change-to-week") != None:
            state = "week"
            return redirect("/")
        elif request.form.get("change-to-day") != None:
            state = "day"
            return redirect("/")
        elif request.form.get("change-to-today") != None:
            current_date = datetime.datetime.now()
            return redirect("/")

    # Render calendar month by month
    if state == "day":
        # If button was pressed, change day
        if request.method == "POST":
            current_day = current_date.day + int(request.form.get("button_calendar"))
            current_month = current_date.month
            current_year = current_date.year
            x, last_day = calendar.monthrange(current_year, current_month)

            # If day is less than 1
            if current_day < 1:
                # If between two years
                if current_month == 1:
                    current_month = 12
                    current_year -= 1
                    x, last_day = calendar.monthrange(current_year, current_month)
                    current_day = last_day                   
                else:
                    current_month -= 1
                    x, last_day = calendar.monthrange(current_year, current_month)
                    current_day = last_day

            # If day is higher than last day of month
            elif current_day > last_day:
                # If between two years
                if current_month == 12:
                    current_month = 1
                    current_year += 1
                    current_day = 1
                else:
                    current_month += 1
                    current_day = 1

            current_date = datetime.datetime(current_year, current_month, current_day)

        month = current_date.month
        date = "{}, {} {}, {}".format(current_date.strftime("%A"), current_date.strftime("%B"), current_date.strftime("%d"), current_date.strftime("%Y"))

        events = get_day_events()
        reminders = get_day_reminders()

        return render_template("calendar-day.html", name=name, date=date, month=month, events=events, reminders=reminders)
    
    elif state == "month": 
        # If button was pressed, change month
        if request.method == "POST":
            current_month = current_date.month + int(request.form.get("button_calendar"))
            current_year = current_date.year

            # If month less than 0 or over than 12
            if current_month == 0:
                current_month = 12
                current_year -= 1
            elif current_month == 13:
                current_month = 1
                current_year += 1

            current_date = datetime.datetime(current_year, current_month, current_date.day)
        
        current_date = datetime.datetime(current_date.year, current_date.month, align_datetime())

        # Create date dictionary
        month = generate_month(current_date.year, current_date.month)

        events = get_events(current_date.year, current_date.month)

        reminders = get_reminders(current_date.year, current_date.month)

        return render_template("calendar-month.html", name=name, date=month, events=events, reminders=reminders)

    # Render calendar year by year
    elif state == "year":
        
        # If button was pressed, change year
        if request.method == "POST":
            current_year =  current_date.year + int(request.form.get("button_calendar"))
            current_date = datetime.datetime(current_year, current_date.month, current_date.day)
        
        current_date = datetime.datetime(current_date.year, current_date.month, align_datetime())

        months = []
        for i in range(1, 13):
            x = generate_month(current_date.year, i)
            months.append(x)

        return render_template("calendar-year.html", name=name, year=current_date.year, months=months)

    # Render calendar week by week
    elif state =="week":
        # If button was pressed, change year
        if request.method == "POST":
            current_year = current_date.year
            current_month = current_date.month
            current_day = current_date.day

            # If next week
            if request.form.get("button_calendar") == "next-week":
                # Number of days in current month
                x, last_day = calendar.monthrange(current_date.year, current_date.month)

                # If between next year and current year
                if current_month == 12 and current_day + 7 > last_day:
                    current_year += 1
                    current_month = 1
                    current_day = 7 - (last_day - current_day)
                # If between next month and current month
                elif current_month != 12 and current_day + 7 > last_day:
                    current_month += 1
                    current_day = 7 - (last_day - current_day)
                # If simply adding 7
                else:
                    current_day += 7
            # If past week
            elif request.form.get("button_calendar") == "prev-week":
                # Number of days in past month
                if current_month == 1:
                    x, last_day = calendar.monthrange(current_year - 1, 12)
                else:
                    x, last_day = calendar.monthrange(current_year, current_month - 1)

                # If between last year and current year
                if current_month == 1 and current_day <= 7:
                    current_year -= 1
                    current_month = 12
                    current_day = last_day - (7 - current_day)
                # If between last month and current month
                elif current_month != 1 and current_day <= 7:
                    current_month -= 1
                    current_day = last_day - (7 - current_day)
                # If simply subtracting 7
                else:
                    current_day -= 7

            current_date = datetime.datetime(current_year, current_month, current_day)
        
        else:
            current_date = datetime.datetime(current_date.year, current_date.month, align_datetime())

        # Create dict with all information needed to HTML
        date = generate_week()

        events = get_week_events(date["days"])

        reminders = get_week_reminders(date["days"])

        return render_template("calendar-week.html", name=name, date=date, events=events, reminders=reminders)

@app.route("/settings", methods=["GET", "POST"])
# @login_required
@login_required
def settings():
    if request.method == "POST":
        # ensures user provided all password changing information
        if (not request.form.get("old_password")) or (not request.form.get("password")) or (not request.form.get("confirmation")):
            alert_message = "You must provide all information required"
            return render_template("settings.html", name=name, alert=2, alert_message=alert_message)

        # Query database for username
        # Create SQL cursor
        connection = sqlite3.connect("database.db")
        db = connection.cursor()

        # Query database for username
        x, y, hashed = db.execute("SELECT * FROM users WHERE id = ?", [session["user_id"]]).fetchone()

        # Ensure username exists and password is correct
        if not check_password_hash(hashed, request.form.get("old_password")):
            alert_message = "Invalid old password"
            return render_template("settings.html", name=name, alert=2, alert_message=alert_message)

        # ensure password and confirmation are equal
        elif request.form.get("password") != request.form.get("confirmation"):
            alert_message = "New password and confirmation must be the same"
            return render_template("settings.html", name=name, alert=2, alert_message=alert_message)

        # ensure new password and old password are different
        elif request.form.get("password") == request.form.get("old_password"):
            alert_message = "Old password must be different from new password"
            return render_template("settings.html", name=name, alert=2, alert_message=alert_message)

        hashed_password = generate_password_hash(request.form.get("password"))

        # change password
        db.execute("UPDATE users SET hash = ? WHERE id = ?", (hashed_password, session["user_id"]))

        connection.commit()
        connection.close()
        
        alert_message = "Password changed successfully!"
        return render_template("settings.html", name=name, alert=1, alert_message=alert_message)

    else:
        # render settings page
        return render_template("settings.html", alert=0)

@app.route("/events", methods=["GET", "POST"])
# @login_required
@login_required
def events():
    # If form submitted
    if request.method == "POST":
        # Get event information
        title = request.form.get("title")
        text = request.form.get("text")
        start_time = request.form.get("start-time")
        end_time = request.form.get("end-time")
        date = request.form.get("date")

        # Create SQL cursor
        connection = sqlite3.connect("database.db")
        db = connection.cursor()

        db.execute(
            "INSERT INTO events (user_id, title, text, date, start_time, end_time) VALUES (?, ?, ?, ?, ?, ?)",
            (session["user_id"], title, text, date, start_time, end_time)
        )
            
        connection.commit()
        connection.close()

        # Return to index page
        return redirect("/")
    
    # If request method is GET
    return render_template("events.html", name=name)

@app.route("/reminders", methods=["GET", "POST"])
# @login_required
@login_required
def reminders():
    # If form submitted
    if request.method == "POST":
        # Get reminder information
        title = request.form.get("title")
        date = request.form.get("time")

        # Create SQL cursor
        connection = sqlite3.connect("database.db")
        db = connection.cursor()

        db.execute(
            "INSERT INTO reminders (user_id, title, date) VALUES (?, ?, ?)",
            (session["user_id"], title, date)
        )
            
        connection.commit()
        connection.close()

        # Return to index page
        return redirect("/")
    
    # If request method is GET
    return render_template("reminders.html", name=name)

@app.route("/redirect-month", methods=["POST"])
# @login_required
@login_required
def redirect_month():
    global current_date
    global state
    
    # Change global variables
    if request.method == "POST":
        if request.form.get("redirect-month") != None:
            current_date = datetime.datetime(current_date.year, int(request.form.get("redirect-month")), current_date.day)
            current_date = datetime.datetime(current_date.year, current_date.month, align_datetime())
            state = "month"

    # Return to index page
    return redirect("/")

@app.route("/myappointments")
# @login_required
@login_required
def myappointments():
    # Create class for event
    class Event:
        def __init__(self, title, text, date, start_time, end_time):
            self.title = title
            self.text = text
            self.date = date
            self.start_time = start_time
            self.end_time = end_time
        
    # Create class for reminder
    class Reminder:
        def __init__(self, title, date):
            self.title = title
            self.date = date
    
    # Create SQL cursor
    connection = sqlite3.connect("database.db")
    db = connection.cursor()

    eventrows = db.execute("SELECT * FROM events WHERE user_id = ? ORDER BY date,start_time ASC",
                          [session["user_id"]]).fetchall()

    reminderrows = db.execute("SELECT * FROM reminders WHERE user_id = ? ORDER BY date ASC",
                          [session["user_id"]]).fetchall()

    connection.commit()
    connection.close()

    events = []
    for row in eventrows:
        lst = row[4].split("-")
        datetm = datetime.datetime(int(lst[0]), int(lst[1]), int(lst[2]))
        date = "{}, {} {}, {}".format(datetm.strftime("%A"), datetm.strftime("%B"), datetm.strftime("%d"), datetm.strftime("%Y"))
        evnt = Event(row[2], row[3], date, row[5], row[6])
        events.append(evnt)

    reminders = []
    for row in reminderrows:
        lst = row[3].split("-")
        datetm = datetime.datetime(int(lst[0]), int(lst[1]), int(lst[2]))
        date = "{}, {} {}, {}".format(datetm.strftime("%A"), datetm.strftime("%B"), datetm.strftime("%d"), datetm.strftime("%Y"))
        rmndr = Reminder(row[2], date)
        reminders.append(rmndr)


    return render_template("appointments.html", name=name, events=events, reminders=reminders)


# Create month dictionary
def generate_month(year, month):
    # Create datetime object
    date_time = datetime.datetime(year, month, 1)
    
    # Set number of days
    days = []
    cal = calendar.Calendar(6) 
    for day in cal.itermonthdays(year, month): 
        if day != 0:
            days.append(day)

    # Set today only if in the correct month
    if year == date_now.year and month == date_now.month:
        today = date_now.day
    else:
        today = ""

    # Calculate number of white spaces for each month
    x = int(datetime.datetime(date_time.year, date_time.month, 1).strftime("%w"))
    blank_spaces = list(range(0, x))

    list_days = cal.monthdayscalendar(current_date.year, current_date.month)

    # Create dictionary of useful information
    date = {
        "year": year,
        "month": date_time.strftime("%B"),
        "days": days,
        "blank_spaces": blank_spaces,
        "today": today,
        "month_num": date_time.strftime("%m"),
        "total_spaces": len(days) + len(blank_spaces),
        "list_days": list_days,
    }
    
    return date

# Create week dictionary
def generate_week():
    # calendar object
    cal = calendar.Calendar(6) 

    # Create current variables
    current_year = current_date.year
    current_month = current_date.month
    current_day = current_date.day

    # creating week list with all day numbers
    week = []
    weeks = cal.monthdayscalendar(current_date.year, current_date.month)
    for num, item in enumerate(weeks):
        if current_date.day in item:
            week = weeks[num]
    
    for num, day in enumerate(week):
        if day != 0:
            week[num] = "{}/{}".format(current_date.month, day)

    # if week between last month and current month
    if week[0] == 0:
        if current_month != 1:
            current_month -= 1
            past_week = cal.monthdayscalendar(current_year, current_month)[-1]
        else:
            current_year -= 1
            current_month = 12
            past_week = cal.monthdayscalendar(current_year, current_month)[-1]

        for num, day in enumerate(week):
            if day == 0:
                week[num] = "{}/{}".format(current_month, past_week[num])

    # If between next month and current
    elif week[-1] == 0:
        if current_month != 12:
            current_month += 1
            next_week = cal.monthdayscalendar(current_year, current_month)[0] 
        else:
            current_year += 1
            current_month = 1
            next_week = cal.monthdayscalendar(current_year, current_month)[0]

        for num, day in enumerate(week):
            if day == 0:
                week[num] = "{}/{}".format(current_month, next_week[num])

    # Set today only if in the correct month
    if current_date.year == date_now.year and current_date.month == date_now.month:
        today = "{}/{}".format(date_now.month, date_now.day)
    else:
        today = ""

    iterator = {}
    i = 1
    for day in week:
        iterator[day] = i
        i += 1

    # Create dictionary of useful information
    date = {
        "year": current_date.year,
        "month": current_date.strftime("%B"),
        "today": today,
        "month_num": current_date.strftime("%m"),
        "days": week,
        "iterator": iterator
    }

    return date

# Get events
def get_events(year, month):
    # Create class for event
    class Event:
        def __init__(self, title, text, date, start_time, end_time):
            self.title = title
            self.text = text
            self.date = date
            self.start_time = start_time
            self.end_time = end_time
    
    # Set list of days
    days = []
    cal = calendar.Calendar() 
    for day in cal.itermonthdays(year, month): 
        if day != 0:
            days.append(day)
    
    events = {}

    # Create SQL cursor
    connection = sqlite3.connect("database.db")
    db = connection.cursor()

    # Create dictionary with key days and events as value
    for day in days:
        date = str(datetime.datetime(year, month, day)).split()[0]
        
        # Get event from database
        rows = db.execute("SELECT * FROM events WHERE user_id = ? AND date = ? ORDER BY start_time ASC",
                          (session["user_id"], date)).fetchall()
        day_event_list = []
        for row in rows:
            lst = row[4].split("-")
            datetm = datetime.datetime(int(lst[0]), int(lst[1]), int(lst[2]))
            date = "{}, {} {}, {}".format(datetm.strftime("%A"), datetm.strftime("%B"), datetm.strftime("%d"), datetm.strftime("%Y"))
            evnt = Event(row[2], row[3], date, row[5], row[6])
            day_event_list.append(evnt)
        
        events[day] = day_event_list

    connection.commit()
    connection.close()

    return events

# Get events for week
def get_week_events(days):
    # Create class for event
    class Event:
        def __init__(self, title, text, date, start_time, end_time):
            self.title = title
            self.text = text
            self.date = date
            self.start_time = start_time
            self.end_time = end_time
    
    events = {}

    # Create SQL cursor
    connection = sqlite3.connect("database.db")
    db = connection.cursor()

    dates = []
    lst_days = []
    for day in days:
        x = day.split("/")
        x[0] = int(x[0])
        x[1] = int(x[1])
        lst_days.append(x)
    
    # If between two years
    if [1, 1] in lst_days:
        index = lst_days.index([1, 1])
        # if current year if starting
        if index <= 3:
            other_year = current_date.year - 1
            for day in lst_days:
                if day[0] == 12:
                    date = str(datetime.datetime(other_year, day[0], day[1])).split()[0]
                    
                else:
                    date = str(datetime.datetime(current_date.year, day[0], day[1])).split()[0]
                dates.append(date)
                             
        # If current year is ending 
        else:
            other_year = current_date.year + 1
            for day in lst_days:
                if day[0] == 12:
                    date = str(datetime.datetime(current_date.year, day[0], day[1])).split()[0]
                else:
                    date = str(datetime.datetime(other_year, day[0], day[1])).split()[0]
                dates.append(date)
    # If not between two years
    else:
        for day in lst_days:
            date = str(datetime.datetime(current_date.year, day[0], day[1])).split()[0]
            dates.append(date)

    # Create dictionary with key days and events as value
    for num, date in enumerate(dates):
        # Get event from database
        rows = db.execute("SELECT * FROM events WHERE user_id = ? AND date = ? ORDER BY start_time ASC",
                          (session["user_id"], date)).fetchall()
        day_event_list = []
        for row in rows:
            lst = row[4].split("-")
            datetm = datetime.datetime(int(lst[0]), int(lst[1]), int(lst[2]))
            date = "{}, {} {}, {}".format(datetm.strftime("%A"), datetm.strftime("%B"), datetm.strftime("%d"), datetm.strftime("%Y"))
            evnt = Event(row[2], row[3], date, row[5], row[6])
            day_event_list.append(evnt)
        
        events[days[num]] = day_event_list

    connection.commit()
    connection.close()

    return events

# Get events for current day
def get_day_events():
    date = str(datetime.datetime(current_date.year, current_date.month, current_date.day)).split()[0]
    
    # Create class for event
    class Event:
        def __init__(self, title, text, date, start_time, end_time):
            self.title = title
            self.text = text
            self.date = date
            self.start_time = start_time
            self.end_time = end_time
    
    # Create SQL cursor
    connection = sqlite3.connect("database.db")
    db = connection.cursor()

    # Get event from database
    rows = db.execute("SELECT * FROM events WHERE user_id = ? AND date = ? ORDER BY start_time ASC",
                        (session["user_id"], date)).fetchall()
    events = []
    for row in rows:
        lst = row[4].split("-")
        datetm = datetime.datetime(int(lst[0]), int(lst[1]), int(lst[2]))
        date = "{}, {} {}, {}".format(datetm.strftime("%A"), datetm.strftime("%B"), datetm.strftime("%d"), datetm.strftime("%Y"))
        evnt = Event(row[2], row[3], date, row[5], row[6])
        events.append(evnt)
        

    connection.commit()
    connection.close()

    return events

# Get reminders
def get_reminders(year, month):
    # Set list of days
    days = []
    cal = calendar.Calendar() 
    for day in cal.itermonthdays(year, month): 
        if day != 0:
            days.append(day)
    
    reminders = {}

    # Create SQL cursor
    connection = sqlite3.connect("database.db")
    db = connection.cursor()

    # Create dictionary with key days and reminders as value
    for day in days:
        date = str(datetime.datetime(year, month, day)).split()[0]
        rows = db.execute("SELECT * FROM reminders WHERE user_id = ? AND date = ?",
                          (session["user_id"], date)).fetchall()
        day_reminders_list = []
        for row in rows:
            day_reminders_list.append(row[2])
        
        reminders[day] = day_reminders_list

    connection.commit()
    connection.close()

    return reminders

# Get week reminders
def get_week_reminders(days):

    reminders = {}

    dates = []
    lst_days = []
    for day in days:
        x = day.split("/")
        x[0] = int(x[0])
        x[1] = int(x[1])
        lst_days.append(x)
    
    # If between two years
    if [1, 1] in lst_days:
        index = lst_days.index([1, 1])
        # if current year if starting
        if index <= 3:
            other_year = current_date.year - 1
            for day in lst_days:
                if day[0] == 12:
                    date = str(datetime.datetime(other_year, day[0], day[1])).split()[0]
                    
                else:
                    date = str(datetime.datetime(current_date.year, day[0], day[1])).split()[0]
                dates.append(date)
                             
        # If current year is ending 
        else:
            other_year = current_date.year + 1
            for day in lst_days:
                if day[0] == 12:
                    date = str(datetime.datetime(current_date.year, day[0], day[1])).split()[0]
                else:
                    date = str(datetime.datetime(other_year, day[0], day[1])).split()[0]
                dates.append(date)
    # If not between two years
    else:
        for day in lst_days:
            date = str(datetime.datetime(current_date.year, day[0], day[1])).split()[0]
            dates.append(date)
    
    # Create SQL cursor
    connection = sqlite3.connect("database.db")
    db = connection.cursor()

    # Create dictionary with key days and reminders as value
    for num, date in enumerate(dates):
        rows = db.execute("SELECT * FROM reminders WHERE user_id = ? AND date = ?",
                          (session["user_id"], date)).fetchall()
        day_reminders_list = []
        for row in rows:
            day_reminders_list.append(row[2])
        
        reminders[days[num]] = day_reminders_list

    connection.commit()
    connection.close()

    return reminders

# Get reminders for current day
def get_day_reminders():
    date = str(datetime.datetime(current_date.year, current_date.month, current_date.day)).split()[0]
    
    # Create SQL cursor
    connection = sqlite3.connect("database.db")
    db = connection.cursor()

    # Create dictionary with key days and reminders as value
    rows = db.execute("SELECT * FROM reminders WHERE user_id = ? AND date = ?",
                        (session["user_id"], date)).fetchall()
    reminders = []
    for row in rows:
        reminders.append(row[2])

    connection.commit()
    connection.close()

    return reminders

# Align current day to be a wednesday
def align_datetime():
    datetimeday = current_date.day - (-3 + int(current_date.strftime("%w")))
    x, last_day = calendar.monthrange(current_date.year, current_date.month)

    if datetimeday < 1:
        datetimeday += 7
    elif datetimeday > last_day:
        datetimeday -= 7

    return datetimeday

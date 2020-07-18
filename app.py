import numpy as np
import sqlalchemy
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func
import datetime as dt
from flask import Flask, jsonify

#################################################
# Database Setup
#################################################
engine = create_engine("sqlite:///Resources/hawaii.sqlite")

# reflect an existing database into a new model
Base = automap_base()

# reflect the tables
Base.prepare(engine, reflect=True)

# Save reference to the table
Measurement = Base.classes.measurement
Station = Base.classes.station

#################################################
# Flask Setup
#################################################
app = Flask(__name__)


#################################################
# Flask Routes
#################################################

# Home route
@app.route("/")
def welcome():
    # Create session (link) from Python to the DB
    session = Session(engine)

    """List all available api routes."""

    # Query to call the last date supported
    last_date = session.query(Measurement.date).order_by(Measurement.date.desc()).first()
    last_date_unpacked= last_date[0]

    return (
        f"Available Routes:<br/>"

        f"1. Precipitation records per date<br/>"
        f"/api/v1.0/precipitation<br/>"

        f"2. List of Hawaii Stations<br/>"
        f"/api/v1.0/stations<br/>"

        f"3. Most active station temperature observations during the last year<br/>"
        f"/api/v1.0/tobs<br/>"

        f"4. Temperature normals (TMIN, TMAX, TAVG) from a specific date<br/>"
        f"/api/v1.0/start_date<br/>"

        f"5. Temperature normals (TMIN, TMAX, TAVG) in date range<br/>"
        f"/api/v1.0/start_date/end_date<br/>"

        f" Important Note: Dates must be submitted in yyyy-mm-dd<br/>"

        f"Last date supported is {last_date_unpacked}"
    )

# Precipitation date:prcp data
@app.route("/api/v1.0/precipitation")
def precipitation():
    # Create session (link) from Python to the DB
    session = Session(engine)

    """Return a dictionary of precipitation records"""

    # Query date, precipitation, and order by date
    sel = [Measurement.date, Measurement.prcp]
    measurement_data = session.query(*sel).order_by(Measurement.date).all()

    session.close()

    # Create a dictionary from the row data and append to a all_prcp_dates
    all_prcp_dates = []
    for date, prcp in measurement_data:
        prcp_dates_dict = {}
        prcp_dates_dict[date] = prcp 
        all_prcp_dates.append(prcp_dates_dict)

    return jsonify(all_prcp_dates)

# Station List
@app.route("/api/v1.0/stations")
def stations():
    # Create session (link) from Python to the DB
    session = Session(engine)

    """Return a list of stations id and names"""

    # Query all stations name and id
    station_data = session.query(Station.name, Station.station).all()

    session.close()

    # Creating a list of dictionaries
    station_list = []
    for name, station in station_data:
        station_dict = {}
        station_dict["Name"] = name
        station_dict["id"] = station
        station_list.append(station_dict)

    return jsonify(station_list)

# Most active analysis
@app.route("/api/v1.0/tobs")
def tobs():
    # Create session (link) from Python to the DB
    session = Session(engine)

    """Return a list of tobs"""

    # Query to find the most active station
    sel = [Measurement.station, func.count(Measurement.station)]
    most_active_stations = session.query(*sel).group_by(Measurement.station).\
                        order_by(func.count(Measurement.station).desc()).all()

    most_active_st = most_active_stations[0][0]

    # Query to find the last date recorded across the dataset
    last_date_most_active_st = session.query(Measurement.date).order_by(Measurement.date.desc()).first()
    last_date_unpacked_most_active= last_date_most_active_st[0]

    # Calculating the date one year before the last date recorded
    one_year_before_date_most_active_st = dt.datetime.strptime(last_date_unpacked_most_active, '%Y-%m-%d').date()\
                                    - dt.timedelta(days = 365)
    print( f" Date from one year ago is : {one_year_before_date_most_active_st}")

    # Query TOBS for the most active station during the last year
    last_year_most_active_st = session.query(Measurement.date, Measurement.tobs).\
                        filter(Measurement.date >= one_year_before_date_most_active_st).\
                        filter(Measurement.station == most_active_st).order_by(Measurement.date).all()
    session.close()

    # Creating a list of dictionaries
    active_sts_list = []
    for date, tobs in last_year_most_active_st:
        active_sts_dict = {}
        active_sts_dict[date] = tobs
        active_sts_list.append(active_sts_dict)

    return jsonify(active_sts_list)

#TOBS normals from specific date
@app.route("/api/v1.0/<start>")
def startdate(start):

     #Ensuring date format
    try:
        initial_date = dt.datetime.strptime(start, '%Y-%m-%d').date()
    except ValueError:

        raise ValueError("Incorrect data format, should be YYYY-MM-DD")
    # Create our session (link) from Python to the DB
    session = Session(engine)

    """Return a list for temperature normals records"""
    
    # Defining first date in dataset
    
    first_date = session.query(Measurement.date).order_by(Measurement.date).first()
    first_date_unpacked= dt.datetime.strptime(first_date[0], '%Y-%m-%d').date()

    last_date = session.query(Measurement.date).order_by(Measurement.date.desc()).first()
    last_date_unpacked = dt.datetime.strptime(last_date[0], '%Y-%m-%d').date()

    # Condition if user define a date that is outside of the dataset scope:
    if initial_date < first_date_unpacked:
        return jsonify({"error": f"Date not found, first date supported is: {first_date_unpacked} ."}), 404
    elif initial_date > last_date_unpacked:
        return jsonify({"error": f"Date not found, last date supported is: {last_date_unpacked} ."}), 404

    
    else:

        # Query temperature normals from a specific date

        sel = [func.min(Measurement.tobs), func.max(Measurement.tobs), func.avg(Measurement.tobs)]

        temp_records_onedate = session.query(*sel).filter(Measurement.date >= initial_date).all()

        session.close()

        # Create a dictionary from the row data and append to a list of temperature_list
        temperature_list = []
        for tmin, tavg, tmax in temp_records_onedate:
            temperature_dict = {}
            temperature_dict["TMIN"] = tmin
            temperature_dict["TAVG"] = tavg
            temperature_dict["TMAX"] = tmax
            temperature_list.append(temperature_dict)

        return jsonify(temperature_list)
    
           
#TOBS normals from specific dates
@app.route("/api/v1.0/<start_date>/<end_date>")
def start_end_date(start_date, end_date):

    #Ensuring date format
    try:
        start_date_mod = dt.datetime.strptime(start_date, '%Y-%m-%d').date()
        end_date_mod = dt.datetime.strptime(end_date, "%Y-%m-%d").date()

    except ValueError:
        raise ValueError("Incorrect data format, should be YYYY-MM-DD")

    # Create session (link) from Python to the DB
    session = Session(engine)

    """Return a list for temperature normals records in a specific range of time"""

        # Defining first date in dataset
    
    start_date = session.query(Measurement.date).order_by(Measurement.date).first()
    start_date_unpacked = dt.datetime.strptime(start_date[0], '%Y-%m-%d').date()

    last_date = session.query(Measurement.date).order_by(Measurement.date.desc()).first()
    last_date_unpacked = dt.datetime.strptime(last_date[0], '%Y-%m-%d').date()

    # Condition if user define dates that are outside of the dataset scope:

    if end_date_mod > last_date_unpacked and start_date_mod < start_date_unpacked:
        return jsonify({"error": f"Start and End Date not found, first and last date supported are: {start_date_unpacked} and {last_date_unpacked}."}), 404

    elif start_date_mod < start_date_unpacked:
        return jsonify({"error": f"Start Date not found, first date supported is: {start_date_unpacked} ."}), 404

    elif end_date_mod > last_date_unpacked:
        return jsonify({"error": f"Last Date not found, first date supported is: {last_date_unpacked} ."}), 404

    else:
    
        # Query tobs normals bewteen a defined dates range
        sel_dates = [func.min(Measurement.tobs), func.max(Measurement.tobs), func.avg(Measurement.tobs)]

        temp_records_betwdates = session.query(*sel_dates).filter(Measurement.date >= start_date_mod).\
                                filter(Measurement.date <= end_date_mod).all()

        session.close()

        # Create a dictionary from the row data and append to a temperature_list_dates
        temperature_list_dates = []
        for t_min, t_avg, t_max in temp_records_betwdates:
            temperature_dict_dates = {}
            temperature_dict_dates["TMIN"] = t_min
            temperature_dict_dates["TAVG"] = t_avg
            temperature_dict_dates["TMAX"] = t_max
            temperature_list_dates.append(temperature_dict_dates)

        return jsonify(temperature_list_dates)

if __name__ == '__main__':
    app.run(debug=True)

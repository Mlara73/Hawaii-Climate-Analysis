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

@app.route("/")
def welcome():

    session = Session(engine)

    last_date_most_active_st = session.query(Measurement.date).order_by(Measurement.date.desc()).first()
    last_date_unpacked_most_active= last_date_most_active_st[0]

    session.close()

    """List all available api routes."""
    return (
        f"Available Routes:<br/>"
        f"/api/v1.0/precipitation<br/>"
        f"/api/v1.0/stations<br/>"
        f"/api/v1.0/tobs<br/>"
        f"/api/v1.0/start_date<br/>"
        f"/api/v1.0/start_date/end_date<br/>"

        f" Important Note: Dates must be submitted in yyyy-mm-dd<br/>"
        f"Last date supported is {last_date_unpacked_most_active}"
    )

@app.route("/api/v1.0/precipitation")
def precipitation():
    # Create our session (link) from Python to the DB
    session = Session(engine)

    # Query all passengers
    sel = [Measurement.date, Measurement.prcp]
    measurement_data = session.query(*sel).order_by(Measurement.date).all()

    session.close()

    # Create a dictionary from the row data and append to a list of all_passengers
    all_prcp_dates = []
    for date, prcp in measurement_data:
        prcp_dates_dict = {}
        prcp_dates_dict[date] = prcp 
        all_prcp_dates.append(prcp_dates_dict)

    return jsonify(all_prcp_dates)

#Return a JSON list of stations from the dataset
@app.route("/api/v1.0/stations")
def stations():
    # Create our session (link) from Python to the DB
    session = Session(engine)

    """Return a list of all passenger names"""
    # Query all passengers
    station_data = session.query(Station.name, Station.station).all()

    session.close()

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
    # Create our session (link) from Python to the DB
    session = Session(engine)

    ###
    sel = [Measurement.station, func.count(Measurement.station)]
    most_active_stations = session.query(*sel).group_by(Measurement.station).\
                        order_by(func.count(Measurement.station).desc()).all()

    most_active_st = most_active_stations[0][0]

    last_date_most_active_st = session.query(Measurement.date).order_by(Measurement.date.desc()).first()
    last_date_unpacked_most_active= last_date_most_active_st[0]

    one_year_before_date_most_active_st = dt.datetime.strptime(last_date_unpacked_most_active, '%Y-%m-%d').date()\
                                    - dt.timedelta(days = 365)
    print( f" Date from one year ago is : {one_year_before_date_most_active_st}")

    last_year_most_active_st = session.query(Measurement.date, Measurement.tobs).\
                        filter(Measurement.date >= one_year_before_date_most_active_st).\
                        filter(Measurement.station == most_active_st).order_by(Measurement.date).all()
    active_sts_list = []

    for date, tobs in last_year_most_active_st:
        active_sts_dict = {}
        active_sts_dict[date] = tobs
        active_sts_list.append(active_sts_dict)

    session.close()

    return jsonify(active_sts_list)


@app.route("/api/v1.0/<start>")
def startdate(start):
    # Create our session (link) from Python to the DB
    session = Session(engine)

    initial_date = dt.datetime.strptime(start, '%Y-%m-%d')

    """Return a list of passenger data including the name, age, and sex of each passenger"""
    print(initial_date)
    # Query all passengers
    sel = [func.min(Measurement.tobs), func.max(Measurement.tobs), func.avg(Measurement.tobs)]

    temp_records_onedate = session.query(*sel).filter(Measurement.date >= initial_date).all()

    session.close()

    # Create a dictionary from the row data and append to a list of all_passengers
    temperature_list = []
    for tmin, tavg, tmax in temp_records_onedate:
        temperature_dict = {}
        temperature_dict["TMIN"] = tmin
        temperature_dict["TAVG"] = tavg
        temperature_dict["TMAX"] = tmax
        temperature_list.append(temperature_dict)

    return jsonify(temperature_list)                

@app.route("/api/v1.0/<start_date>/<end_date>")
def start_end_date(start_date, end_date):
    # Create our session (link) from Python to the DB
    session = Session(engine)

    start_date_mod = dt.datetime.strptime(start_date, '%Y-%m-%d')
    end_date_mod = dt.datetime.strptime(end_date, "%Y-%m-%d")
    """Return a list of passenger data including the name, age, and sex of each passenger"""
    # Query all passengers
    sel_dates = [func.min(Measurement.tobs), func.max(Measurement.tobs), func.avg(Measurement.tobs)]

    temp_records_betwdates = session.query(*sel_dates).filter(Measurement.date >= start_date_mod).\
                            filter(Measurement.date <= end_date_mod).all()

    session.close()

    # Create a dictionary from the row data and append to a list of all_passengers
    temperature_list_dates = []
    for t_min, t_avg, t_max in temp_records_betwdates:
        temperature_dict_dates = {}
        temperature_dict_dates["TMIN"] = t_min
        temperature_dict_dates["TAVG"] = t_avg
        temperature_dict_dates["TMAX"] = t_max
        temperature_list_dates.append(temperature_dict_dates)

    return jsonify(temperature_list_dates)

@app.route("/api/names/<name_1>")
def names(name_1):
    return "HI"

if __name__ == '__main__':
    app.run(debug=True)

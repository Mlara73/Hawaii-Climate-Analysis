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
    """List all available api routes."""
    return (
        f"Available Routes:<br/>"
        f"/api/v1.0/precipitation<br/>"
        f"/api/v1.0/stations<br/>"
        f"/api/v1.0/tobs<br/>"
        f"/api/v1.0/start<br/>"
        f"/api/v1.0/start/end<br/>"
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
        all_prcp_dates.append(prcp_dates_dict )

    return jsonify(all_prcp_dates)

#Return a JSON list of stations from the dataset
@app.route("/api/v1.0/stations")
def stations():
    # Create our session (link) from Python to the DB
    session = Session(engine)

    """Return a list of all passenger names"""
    # Query all passengers
    station_data = session.query(Station.station).all()
    station_list = list(np.ravel(station_data))
    session.close()

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

    last_year_most_active_st = session.query(Measurement.tobs).filter(Measurement.date >= one_year_before_date_most_active_st).\
                        filter(Measurement.station == most_active_st).all()
    list_active_st_ly= list(np.ravel(last_year_most_active_st))

    session.close()

    return jsonify(list_active_st_ly)


# @app.route("/api/v1.0/passengers")
# def passengers():
#     # Create our session (link) from Python to the DB
#     session = Session(engine)

#     """Return a list of passenger data including the name, age, and sex of each passenger"""
#     # Query all passengers
#     results = session.query(Passenger.name, Passenger.age, Passenger.sex).all()

#     session.close()

#     # Create a dictionary from the row data and append to a list of all_passengers
#     all_passengers = []
#     for name, age, sex in results:
#         passenger_dict = {}
#         passenger_dict["name"] = name
#         passenger_dict["age"] = age
#         passenger_dict["sex"] = sex
#         all_passengers.append(passenger_dict)

#     return jsonify(all_passengers)


if __name__ == '__main__':
    app.run(debug=True)

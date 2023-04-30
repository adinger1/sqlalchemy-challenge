# Import the dependencies.
import numpy as np

import sqlalchemy
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func
import pandas as pd
from flask import Flask, jsonify

#################################################
# Database Setup
#################################################
engine = create_engine("sqlite:///Resources/hawaii.sqlite")

# reflect an existing database into a new model
Base = automap_base()
# reflect the tables
Base.prepare(autoload_with=engine)

# Save references to each table
measurements = Base.classes.measurement
stations = Base.classes.station

# Create our session (link) from Python to the DB
session = Session(engine)

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
        f"/api/v1.0/tobs"
        f"/api/v1.0/<start>"
        #f"/api/v1.0/<start>/<end>"
    )

@app.route("/api/v1.0/precipitation")
def precipitation():
    most_recent = session.query(measurements.date).\
        order_by(measurements.date.desc()).first()
    #most_recent_string just equals the string '2017-08-23'
    most_recent_string = most_recent[0]
    #convert to datetime
    most_recent_dt = pd.to_datetime(most_recent_string)

    # Calculate the date one year from the last date in data set.
    one_year_before = most_recent_dt - pd.DateOffset(years=1)

    start_date = str(one_year_before)[0:10]
    data = session.query(measurements.date,measurements.prcp).\
        filter(measurements.date >= str(one_year_before)[0:10])
        
    data_rows = {}
    for row in data:
        data_rows[row[0]]=row[1]
    return jsonify(data_rows)

@app.route("/api/v1.0/stations")
def get_stations():
    station_query = session.query(stations.station).all()
    stations_list = []
    for station in station_query:
        stations_list.append(station[0])
    return jsonify(stations_list)

@app.route("/api/v1.0/tobs")
def tobs():
    station_query_count = session.query(measurements.station,func.count(measurements.station))\
    .group_by(measurements.station).order_by(func.count(measurements.station).desc()).all()
    
    most_active = station_query_count[0]
    
    #Pulling the most recent date in table
    most_recent = session.query(measurements.date).\
        order_by(measurements.date.desc()).first()
    #most_recent_string just equals the string '2017-08-23'
    most_recent_string = most_recent[0]
    #convert to datetime
    most_recent_dt = pd.to_datetime(most_recent_string)

    # Calculate the date one year from the last date in data set.
    one_year_before = most_recent_dt - pd.DateOffset(years=1)

    start_date = str(one_year_before)[0:10]
    
    twelve_month_query = session.query(measurements.tobs).filter(measurements.station == most_active[0]).\
    filter(measurements.date >= start_date).all()
    #List elements have extra commas
    #Cleaning up data elements in list
    temperature_data = []
    for temp in twelve_month_query:
        temperature_data.append(temp[0])
        
    return temperature_data

@app.route("/api/v1.0/<start>")
def start_date():
    first_date = session.query(measurements.date).order_by(measurements.date).first()
    search_date = input("Enter a date in YYYY/MM/DD format")
    return("Hang on not done yet")
if __name__ == '__main__':
    app.run(debug=True)
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
        f"/api/v1.0/tobs<br/>"
        f"Enter a start date after the '/' in YYYY-MM-DD format: <br/>"
        f"/api/v1.0/<start><br/>"
        f"Enter a date range in the following format for the below link: 'api/v1.0/YYYY-MM-DD/YYYY-MM-DD':<br/>"
        f"/api/v1.0/<start>/<end>"
    )

@app.route("/api/v1.0/precipitation")
def precipitation():
    session = Session(engine)

    most_recent = session.query(measurements.date).\
        order_by(measurements.date.desc()).first()
    #most_recent_string just equals the string '2017-08-23'
    most_recent_string = most_recent[0]
    #convert to datetime
    most_recent_dt = pd.to_datetime(most_recent_string)

    # Calculate the date one year from the last date in data set.
    one_year_before = most_recent_dt - pd.DateOffset(years=1)

    start = str(one_year_before)[0:10]
    data = session.query(measurements.date,measurements.prcp).\
        filter(measurements.date >= str(one_year_before)[0:10])
        
    data_rows = {}
    for row in data:
        data_rows[row[0]]=row[1]
    
    session.close()
    return jsonify(data_rows)

@app.route("/api/v1.0/stations")
def get_stations():
    session = Session(engine)

    station_query = session.query(stations.station).all()
    stations_list = []
    for station in station_query:
        stations_list.append(station[0])
    
    session.close()
    return jsonify(stations_list)

@app.route("/api/v1.0/tobs")
def tobs():
    session = Session(engine)

    station_query_count = session.query(measurements.station,func.count(measurements.station))\
    .group_by(measurements.station).order_by(func.count(measurements.station).desc()).all()
    
    most_active = station_query_count[0]
    
    #Pulling the most recent date in table
    most_recent_string = session.query(measurements.date).\
        order_by(measurements.date.desc()).first()[0]
    
    #convert to datetime
    most_recent_dt = pd.to_datetime(most_recent_string)

    # Calculate the date one year from the last date in data set.
    one_year_before = most_recent_dt - pd.DateOffset(years=1)

    #Removes hours and minutes portion of datetime value and converts to string for query
    start_date = str(one_year_before)[0:10]
    
    twelve_month_query = session.query(measurements.tobs).filter(measurements.station == most_active[0]).\
    filter(measurements.date >= start_date).all()
    
    #List elements have extra commas
    #Cleaning up data elements in list
    temperature_data = []
    for temp in twelve_month_query:
        temperature_data.append(temp[0])
    
    session.close()    
    return temperature_data

@app.route("/api/v1.0/<start>")
def start_date(start):
    try:
        start_in_dt = pd.to_datetime(start)
    except:
        return f"That is not a valid date"
    
    session = Session(engine)
    
    #Query returns the tuple ('2010-01-01',). Adding [0] just returns the string
    first_date = session.query(measurements.date).order_by(measurements.date).first()[0]
    
    most_recent = session.query(measurements.date).order_by(measurements.date.desc()).first()[0]
    
    if (start < first_date) or (start > most_recent):
        session.close()
        return jsonify({"error": f"We do not have data for that date."}), 404
    
    data = session.query(func.min(measurements.tobs),\
                                  func.max(measurements.tobs),\
                                  func.avg(measurements.tobs))\
                                .filter(measurements.date >= start).all()
    
    session.close()
    
    tmin = data[0][0]
    tmax = data[0][1]
    tavg = data[0][2]
    date_summary = f"Stats from {start} to {most_recent}:<br/>"
    date_summary += f"Minimum temperature: {tmin}<br/>Maximum temperature: {tmax}<br/>Average temperature: {tavg}" 
    return(date_summary)

@app.route("/api/v1.0/<start>/<end>")
def start_end_range(start,end):
    
    try:
        start_in_dt = pd.to_datetime(start)
        start_in_dt = pd.to_datetime(end)
    except:
        return f"One of those dates is not a valid date"
    
    if end < start:
        return "That is not a valid date range."
    
    session = Session(engine)
    
    #Query returns the tuple in the form ('2010-01-01',). Adding [0] just returns the string
    first_date = session.query(measurements.date).order_by(measurements.date).first()[0]
    end_date = session.query(measurements.date).order_by(measurements.date.desc()).first()[0]
    

    #Verifies valid date range
    if (start < first_date) or (start > end_date) or (end < first_date) or (end > end_date):
        session.close()
        return jsonify({"error": f"We do not have data for that date range."}), 404
    
    #This executes if the start and end dates are equal and within the available dates in the data.
    #IF the start and end dates are equal, data is returned for only that date
    elif end == start:
        data = session.query(func.min(measurements.tobs),\
                                  func.max(measurements.tobs),func.avg(measurements.tobs))\
                                .filter(measurements.date == start).all()
    
        session.close()
    
        tmin = data[0][0]
        tmax = data[0][1]
        tavg = data[0][2]
        date_summary = f"Stats for {start}:<br/>"
        date_summary += f"Minimum temperature: {tmin}<br/>Maximum temperature: {tmax}<br/>Average temperature: {tavg}" 
        return(date_summary)
    
    else: 
        data = session.query(func.min(measurements.tobs),func.max(measurements.tobs),func.avg(measurements.tobs))\
                .filter(measurements.date >= start).filter(measurements.date <= end).all()
    
    session.close()
    
    tmin = data[0][0]
    tmax = data[0][1]
    tavg = data[0][2]
    date_summary = f"Stats from {start} to {end}:<br/>"
    date_summary += f"Minimum temperature: {tmin}<br/>Maximum temperature: {tmax}<br/>Average temperature: {tavg}" 
    return(date_summary)
    
    
if __name__ == '__main__':
    app.run(debug=True)
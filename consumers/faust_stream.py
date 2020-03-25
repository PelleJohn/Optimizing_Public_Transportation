"""Defines trends calculations for stations"""
import logging

import faust


logger = logging.getLogger(__name__)


# Faust will ingest records from Kafka in this format
class Station(faust.Record):
    stop_id: int
    direction_id: str
    stop_name: str
    station_name: str
    station_descriptive_name: str
    station_id: int
    order: int
    red: bool
    blue: bool
    green: bool

# Faust will produce records to Kafka in this format
class TransformedStation(faust.Record):
    station_id: int
    station_name: str
    order: int
    line: str

# Define a Faust Stream that ingests data from the Kafka Connect stations topic and
#   places it into a new topic with only the necessary information.
app = faust.App("stations-stream", broker="kafka://localhost:9092", store="memory://")
# Define the input Kafka Topic. Hint: What topic did Kafka Connect output to?
topic = app.topic("org.chicago.cta.stations.arrivals", value_type=Station)
# Define the output Kafka Topic
out_topic = app.topic("org.chicago.cta.stations.table", partitions=1)
# Define a Faust Table
table = app.Table(
    name = "org.chicago.cta.stations.table",
    default=int,
    partitions=1,
    changelog_topic=out_topic,
)

#
# Using Faust, transform input `Station` records into `TransformedStation` records. Note that
# "line" is the color of the station. So if the `Station` record has the field `red` set to true,
# then you would set the `line` of the `TransformedStation` record to the string `"red"`
#

@app.agent(topic)
async def transform_records(arrivals):
    async for arrival in arrivals:
    
        if arrivals.red:
            linecolor = "red"
        elif arrivals.blue:
            linecolor = "blue"
        else:
            linecolor = "green"

        transformed_station = TransformedStation(
            station_id = arrival.station_id,
            station_name = arrival.station_descriptive_name,
            order = arrival.order,
            line = linecolor
        )    

        table[transformed_station.station_id] = transformed_station

        logger.info(f"Station element updated successfully in table")
        
        pass

if __name__ == "__main__":
    app.main()
import datetime as dttm
import requests
from typing import Union
 
BASE_URL = 'https://api.tidesandcurrents.noaa.gov/api/prod/datagetter?'
 
# Station ID for Washington Narrows at Warren Bridge
STATION_ID = 'PUG1510'

class TidalCurrentRequester:
    def __init__(self) -> None:
        self._base_url = BASE_URL
        self.station_id = STATION_ID
        self._plus_time_delta = dttm.timedelta(3)
        self._minus_time_delta = dttm.timedelta(1)

    def get_current_predictions_for_now(self) -> tuple[list[str], list[str]]:
        now = dttm.datetime.now()
        time_series = self._parse_time_series(
            self._query_current_predictions(
                now - self._minus_time_delta, now + self._plus_time_delta
            )
        )
        time_series["Relationship"] = [
            "Past" if time <= now else "Future" for time in time_series["Time"]
        ]
        return time_series
 
    def _build_and_query(
        self,
        begin_date: Union[dttm.datetime, str],
        end_date: Union[dttm.datetime, str],
        product: str
    ) -> dict:
        
        # Convert datetime objects to strings for API query
        if isinstance(begin_date, dttm.datetime):
            begin_date = begin_date.strftime('%Y%m%d %H:%M')
            
        if isinstance(end_date, dttm.datetime):
            end_date = end_date.strftime('%Y%m%d %H:%M')
        
        # Configure query dates, data product, and station # options
        options = 'begin_date={}&end_date={}'.format(begin_date, end_date)
        options+= '&product={}&station={}'.format(product, self.station_id)
        
        # Configure units of measure, time zone, format options
        options += '&units=english&time_zone=lst&application=RawdogRob&format=json'
        
        # Send http request
        r = requests.get(self._base_url + options)
        return r.json()

    def _query_current_predictions(
        self,
        begin_date: Union[dttm.datetime, str],
        end_date: Union[dttm.datetime, str]
    ) -> dict:
        return self._build_and_query(begin_date, end_date, 'currents_predictions')
    
    def _parse_time_series(self, response: dict) -> dict[str, list]:
        predictions = response['current_predictions']['cp']
        t, pred_current= [], []
        
        for pred in predictions:
            t.append(dttm.datetime.strptime(pred["Time"], "%Y-%m-%d %H:%M"))
            pred_current.append(pred['Velocity_Major'])
            
        return {"Time": t, "Current" : pred_current}

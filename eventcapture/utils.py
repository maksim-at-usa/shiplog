import os
import pandas as pd
from django.conf import settings
from eventcapture.models import Cruise, Device, Event, GPS, ShipLog

def _to_df(log):
    columns = list(log.values('timestamp', 'device_id', 'event_id', 'gps'))
    df = pd.DataFrame(columns)
    df['device_id'] = df['device_id'].apply(lambda x: Device.objects.get(pk=x))
    df['event_id'] = df['event_id'].apply(lambda x: Event.objects.get(pk=x))
    df['gps'] = df['gps'].apply(lambda x: GPS.objects.get(pk=x))
    df = df.set_index('timestamp')
    df = df.rename(columns={'device_id': 'device', 'event_id': 'event'})
    return df

def to_csv(cruise_id):
    cruise_id = int(cruise_id)
    if cruise_id > 0:
        cruise = Cruise.objects.get(pk=cruise_id)
        cruise_number = cruise.number
        log = ShipLog.get_log(cruise)
    else:
        cruise_number = 'All'
        log = ShipLog.get_all_logs()
    filename = settings.EVENT_LOG_FILENAME.format(cruise_number)
    df = _to_df(log)
    outfile = os.path.join(settings.MEDIA_ROOT, filename)
    df.to_csv(outfile)
    return outfile


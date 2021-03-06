import os
import pytz
from datetime import datetime
from django.shortcuts import render
from django.http import HttpResponseRedirect, HttpResponse
from django.urls import reverse
from django.conf import settings
from eventcapture import utils
from eventcapture.models import Cruise, Device, Event, ShipLog, Cast, CastReport, GPS

def index(request):
    context = {}
    try:
        cruise = Cruise.get_active_cruise()
    except ValueError:
        return render(request, 'index.html', context)
    try:
        context['devices'] = cruise.get_parent_devices()
    except AttributeError:
        pass
    if request.method != 'POST':
        return render(request, 'index.html', context)
    cruise_id = request.POST.get('cruise', None)
    device_id = request.POST.get('device', None)
    event_id = request.POST.get('event', None)
    if cruise_id is None or device_id is None or event_id is None:
        return render(request, 'index.html', {'error': 'Unknown cruise, device, or event'})
    cruise = Cruise.objects.get(pk=int(cruise_id))
    device = Device.objects.get(pk=int(device_id))
    event = Event.objects.get(pk=int(event_id))
    timestamp = datetime.now(pytz.utc)
    gps = GPS()
    gps.save(timestamp=timestamp)
    shiplog = ShipLog(cruise=cruise, device=device, event=event, gps=gps, timestamp=timestamp)
    shiplog.save()
    context['event_was_logged'] = True
    return render(request, 'index.html', context)

def device(request, device_id):
    context = {}
    device = Device.objects.get(pk=int(device_id))
    if any(device.events.all()):
        return HttpResponseRedirect(reverse('event', args=[device_id]))
    try:
        cruise = Cruise.get_active_cruise()
    except ValueError:
        return render(request, 'device.html', context)
    context['children'] = device.get_child_devices(cruise)
    context['device'] = device
    context['parents'] = device.get_lineage()
    return render(request, 'device.html', context)

def event(request, device_id):
    context = {}
    device = Device.objects.get(pk=int(device_id))
    context['device'] = device
    context['parents'] = device.get_lineage()
    return render(request, 'event.html', context)

def download(request, log, cruise_id):
    if log == 'eventlog':
        csv_path = utils.to_csv(ShipLog, cruise_id, settings.EVENT_LOG_FILENAME)
    elif log == 'wirelog':
        csv_path = utils.to_csv(CastReport, cruise_id, settings.WIRE_LOG_FILENAME)
    else:
        raise ValueError('Unknown log type')
    with open(csv_path, 'rb') as f:
        response = HttpResponse(f.read(), content_type='text/csv')
        response['Content-Disposition'] = 'inline; filename=' + os.path.basename(csv_path)
        return response

def eventlog(request):
    try:
        cruise = Cruise.get_active_cruise()
    except ValueError:
        return render(request, 'eventlog.html')
    if not cruise:
        return render(request, 'eventlog.html')
    context = {}
    context['log'] = ShipLog.get_log(cruise)
    if request.method != 'POST':
        return render(request, 'eventlog.html', context)
    action = request.POST.get('action', None)
    if action == 'download':
        return HttpResponseRedirect(reverse('download', args=['eventlog', cruise.id]))

def wirelog(request):
    cruise = Cruise.get_active_cruise()
    if not cruise:
        return render(request, 'wirelog.html')
    context = {}
    context['log'] = CastReport.get_log(cruise)
    if request.method != 'POST':
        return render(request, 'wirelog.html', context)
    action = request.POST.get('action', None)
    if action == 'download':
        return HttpResponseRedirect(reverse('download', args=['wirelog', cruise.id]))


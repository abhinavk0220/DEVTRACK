from django.shortcuts import render

# Create your views here.
import json

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from . import storage
from .models import Reporter

REPORTERS_FILE = 'reporters.json'


def error(message, status):
    return JsonResponse({'error': message}, status=status)


@csrf_exempt
@require_http_methods(['GET', 'POST'])
def reporters(request):
    if request.method == 'POST':
        return create_reporter(request)
    return get_reporters(request)


def get_reporters(request):
    records = storage.load(REPORTERS_FILE)
    raw_id = request.GET.get('id')

    if raw_id is None:
        return JsonResponse(records, safe=False)

    try:
        reporter_id = int(raw_id)
    except ValueError:
        return error('id must be an integer', 400)

    for record in records:
        if record['id'] == reporter_id:
            return JsonResponse(record)
    return error('Reporter not found', 404)


def create_reporter(request):
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return error('Invalid JSON body', 400)
    if not isinstance(data, dict):
        return error('Body must be a JSON object', 400)

    for field in ('name', 'email', 'team'):
        if not isinstance(data.get(field), str):
            return error(f'{field} is required and must be a string', 400)

    records = storage.load(REPORTERS_FILE)
    reporter = Reporter(
        id=storage.next_id(records),
        name=data['name'],
        email=data['email'],
        team=data['team'],
    )

    try:
        reporter.validate()
    except ValueError as e:
        return error(str(e), 400)

    records.append(reporter.to_dict())
    storage.save(REPORTERS_FILE, records)
    return JsonResponse(reporter.to_dict(), status=201)
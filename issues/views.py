from django.shortcuts import render


import json

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from . import storage
from .models import (
    VALID_STATUSES,
    CriticalIssue,
    Issue,
    LowPriorityIssue,
    Reporter,
)

REPORTERS_FILE = 'reporters.json'
ISSUES_FILE = 'issues.json'

PRIORITY_CLASSES = {
    'critical': CriticalIssue,
    'low': LowPriorityIssue,
}


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

@csrf_exempt
@require_http_methods(['GET', 'POST'])
def issues(request):
    if request.method == 'POST':
        return create_issue(request)
    return get_issues(request)


def get_issues(request):
    records = storage.load(ISSUES_FILE)
    raw_id = request.GET.get('id')
    status = request.GET.get('status')

    if raw_id is not None:  # id takes precedence over status
        try:
            issue_id = int(raw_id)
        except ValueError:
            return error('id must be an integer', 400)
        for record in records:
            if record['id'] == issue_id:
                return JsonResponse(record)
        return error('Issue not found', 404)

    if status is not None:
        if status not in VALID_STATUSES:
            return error(f"Invalid status. Allowed: {', '.join(VALID_STATUSES)}", 400)
        records = [r for r in records if r['status'] == status]

    return JsonResponse(records, safe=False)


def create_issue(request):
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return error('Invalid JSON body', 400)
    if not isinstance(data, dict):
        return error('Body must be a JSON object', 400)

    for field in ('title', 'description', 'status', 'priority'):
        if not isinstance(data.get(field), str):
            return error(f'{field} is required and must be a string', 400)

    reporter_id = data.get('reporter_id')
    # bool is a subclass of int in Python, so True would pass a plain isinstance check
    if not isinstance(reporter_id, int) or isinstance(reporter_id, bool):
        return error('reporter_id is required and must be an integer', 400)

    reporters_list = storage.load(REPORTERS_FILE)
    if not any(r['id'] == reporter_id for r in reporters_list):
        return error('Reporter not found', 400)

    records = storage.load(ISSUES_FILE)
    issue_class = PRIORITY_CLASSES.get(data['priority'], Issue)
    issue = issue_class(
        id=storage.next_id(records),
        title=data['title'],
        description=data['description'],
        status=data['status'],
        priority=data['priority'],
        reporter_id=reporter_id,
    )

    try:
        issue.validate()
    except ValueError as e:
        return error(str(e), 400)

    records.append(issue.to_dict())
    storage.save(ISSUES_FILE, records)

    response = issue.to_dict()
    response['message'] = issue.describe()
    return JsonResponse(response, status=201)
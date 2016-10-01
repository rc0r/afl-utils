from django.db import models
from django.http import HttpResponse
from .models import FuzzerStats

def distinct_fuzzers(stats):
    fuzzers = stats.order_by().values('afl_banner').annotate(n=models.Count('pk'))
    fuzzers = [fuzzer['afl_banner'] for fuzzer in fuzzers]
    return fuzzers


def fuzzer_data(stats, fuzzer, field):
    data = stats.filter(afl_banner=fuzzer).values(field)
    data = [d[field] for d in data]
    return data

def fuzzer_json_data(stats, fuzzer):
    try:
        import simplejson as json
    except ImportError:
        import json

    json_data = {
        'fuzzer': fuzzer
    }

    for f in model_field_names(stats[0]):
        json_data[f] = fuzzer_data(stats, fuzzer, f)

    return json.dumps(json_data)


def model_field_names(model):
    return [field.name for field in model._meta.fields]


def index(request):
    stats = FuzzerStats.objects.all()
    fuzzers = distinct_fuzzers(stats)

    output = ''
    for fuzzer in fuzzers:
        output += '<br /><br>' + fuzzer_json_data(stats, fuzzer)

    return HttpResponse(output)

from django.db import models
from django.http import HttpResponse
from django.template import loader

from .models import Index, Fuzzers, Stats, Results


def distinct_fuzzers(stats):
    fuzzers = stats.order_by().values('fuzzer').annotate(n=models.Count('pk'))
    fuzzers = [fuzzer['fuzzer'] for fuzzer in fuzzers]
    return fuzzers


def fuzzer_data(stats, fuzzer_id, field):
    data = stats.filter(fuzzer_id=fuzzer_id).values(field)
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


def fuzzer_latest_data(stats, fuzzer_id):
    data = stats.filter(fuzzer_id=fuzzer_id).order_by('-id')[0]
    return data


def model_field_names(model):
    return [field.name for field in model._meta.fields]


def details(request, fuzzer_id):
    """
    Print detailed stats of the selected fuzzer.

    :param request: HttpRequest
    :param fuzzer:  Selected fuzzer
    :return:        HttpResponse
    """
    template = loader.get_template('aflutils/details.html')
    context = {
        'fuzzer': {
            'name': Fuzzers.objects.all().filter(id=fuzzer_id).values('fuzzer')[0]['fuzzer'],
            'd3': {
            }
        }
    }

    stats = Stats.objects.all()
    stats_fields = model_field_names(Stats)

    for field in stats_fields:
        context['fuzzer']['d3'][field] = ', '.join(map(str, fuzzer_data(stats, fuzzer_id, field)))

    return HttpResponse(template.render(context, request))


def index(request):
    """
    Print an overview of all fuzzers found in the database.

    :param request: HttpRequest
    :return:        HttpResponse
    """
    template = loader.get_template('aflutils/index.html')
    context = {
        'fuzzer_summary_list': []
    }

    stats = Stats.objects.all()
    fuzzers = Fuzzers.objects.all()

    for fuzzer in fuzzers:
        data = fuzzer_latest_data(stats, fuzzer.id)
        summary = {
            'fuzzer': fuzzer.fuzzer,
            'fuzzer_id': fuzzer.id,
            'paths_total': data.paths_total,
            'pending_total': data.pending_total,
            'pending_favs': data.pending_favs,
            'unique_crashes': data.unique_crashes,
            'unique_hangs': data.unique_hangs
        }
        context['fuzzer_summary_list'].append(summary)

    return HttpResponse(template.render(context, request))

    # print json dumps
    # output = ''
    # for fuzzer in fuzzers:
    #     output += '<br /><br>' + fuzzer_json_data(stats, fuzzer)
    #
    # return HttpResponse(output)

from django.http import HttpResponse
from .models import FuzzerStats

def index(request):
    stats = FuzzerStats.objects.order_by('afl_banner')
    output = '<br />'.join(str(s) for s in stats)
    return HttpResponse(output)

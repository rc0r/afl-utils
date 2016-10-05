from django.contrib import admin
from .models import Index, Fuzzers, Stats, Results


# Register your models here.
admin.site.register(Index)
admin.site.register(Fuzzers)
admin.site.register(Stats)
admin.site.register(Results)

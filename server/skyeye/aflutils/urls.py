from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^(?P<fuzzer_id>\d+)/$', views.details, name='details')
]

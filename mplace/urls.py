
#
from django.urls import path

import mplace.views


app_name = 'mplace'
urlpatterns = [
 
path('', mplace.views.home, name='home'),
path('market/', mplace.views.market_list, name='market'),
path('contact/', mplace.views.contact, name='contact'),
path('market/<slug:slug>/', mplace.views.detail_market, name='detail_market'),
]

from django.urls import path
from accounts.views import DepotView

urlpatterns = [
    path('accounts/', DepotView.as_view())
]

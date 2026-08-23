from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from currencies.services import fetch_exchange_rates

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/services/', include('services.urls')),
    path('api/pricing/', include('pricing.urls')),
    path('api/currencies/', include('currencies.urls')),
    path('api/quotations/', include('quotations.urls')),
    path('api/payments/', include('payments.urls')),
    path('api/customers/', include('customers.urls')),
    path('api/samples/', include('samples.urls')),
    path('api/contact/', include('contact.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

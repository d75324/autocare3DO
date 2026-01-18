from django.conf import settings
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),

    # 1️⃣ Tus overrides de auth (password reset)
    path('accounts/', include('accounts.urls')),

    # 2️⃣ El resto del auth de Django (login, logout, etc.)
    path('accounts/', include('django.contrib.auth.urls')),

    # 3️⃣ Tu app principal
    path('', include('autocare.urls')),
]

if settings.DEBUG:
    from django.conf.urls.static import static
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
from shop import views
from django.conf import settings 
from django.contrib import admin
from django.urls import path

urlpatterns = [
    path('admin/', admin.site.urls),
    path('catalog/', views.catalog, name = "catalog"), 
    path('catalog/<int:pk>', views.product_detail, name='product_detail'), 
    path('cart/add/<int:product_id>/',views.cart_add, name='cart_add'), 
    path('cart/update/<int:item_id>/', views.cart_update, name='cart_update'),
    path('cart/remove/<int:item_id>/', views.cart_remove, name='cart_remove'), 
    path('cart/', views.cart_view, name='cart_views'),
      ]


if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


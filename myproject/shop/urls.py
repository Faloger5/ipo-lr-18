from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'categories', views.CategoryViewSet)
router.register(r'manufacturers', views.ManufacturerViewSet)
router.register(r'products', views.ProductViewSet)
router.register(r'carts', views.CartViewSet, basename='cart')
router.register(r'cart-items', views.CartItemViewSet, basename='cartitem')

urlpatterns = [
    path('', views.home, name='home'),
    path('catalog/', views.product_list, name='catalog'),
    path('product/<int:pk>/', views.product_detail, name='product_detail'),
    path('cart/', views.cart_view, name='cart'),
    path('cart/add/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/update/<int:item_id>/', views.update_cart, name='update_cart'),
    path('cart/remove/<int:item_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('checkout/', views.checkout, name='checkout'),
    path('order-success/<int:order_id>/', views.order_success, name='order_success'),
    path('profile/', views.profile_view, name='profile'),
    
    path('api/', include(router.urls)),
    path('api/me/', views.MeAPIView.as_view(), name='api_me'),
    path('api/my-orders/', views.MyOrdersAPIView.as_view(), name='api_my_orders'),
    path('api-auth/', include('rest_framework.urls')),
]
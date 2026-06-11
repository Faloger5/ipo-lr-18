from rest_framework import serializers
from .models import Category, Manufacturer, Product, Cart, CartItem, UserProfile, Order, OrderItem


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = '__all__'


class ManufacturerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Manufacturer
        fields = '__all__'


class ProductSerializer(serializers.ModelSerializer):
    category_name = serializers.ReadOnlyField(source='category.name')
    manufacturer_name = serializers.ReadOnlyField(source='manufacturer.name')
    
    class Meta:
        model = Product
        fields = ['id', 'name', 'description', 'photo', 'price', 'stock', 
                  'category', 'manufacturer', 'category_name', 'manufacturer_name']


class CartItemSerializer(serializers.ModelSerializer):
    product_name = serializers.ReadOnlyField(source='product.name')
    product_price = serializers.ReadOnlyField(source='product.price')
    total_price = serializers.SerializerMethodField()
    
    class Meta:
        model = CartItem
        fields = ['id', 'cart', 'product', 'product_name', 'product_price', 
                  'quantity', 'total_price']
    
    def get_total_price(self, obj):
        return obj.product.price * obj.quantity


class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    total_price = serializers.SerializerMethodField()
    username = serializers.ReadOnlyField(source='user.username')
    
    class Meta:
        model = Cart
        fields = ['id', 'user', 'username', 'created_at', 'items', 'total_price']
    
    def get_total_price(self, obj):
        return obj.total_price()


class UserProfileSerializer(serializers.ModelSerializer):
    username = serializers.ReadOnlyField(source='user.username')
    email = serializers.ReadOnlyField(source='user.email')
    role_display = serializers.ReadOnlyField(source='get_role_display')
    
    class Meta:
        model = UserProfile
        fields = ['id', 'username', 'email', 'full_name', 'phone', 'address', 
                  'role', 'role_display', 'favorite_category', 'delivery_city', 
                  'postal_code', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at', 'username', 'email']


class OrderItemSerializer(serializers.ModelSerializer):
    product_name = serializers.ReadOnlyField(source='product.name')
    product_id = serializers.ReadOnlyField(source='product.id')
    
    class Meta:
        model = OrderItem
        fields = ['id', 'product', 'product_id', 'product_name', 'quantity', 'price']


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    status_display = serializers.ReadOnlyField(source='get_status_display')
    username = serializers.ReadOnlyField(source='user.username')
    
    class Meta:
        model = Order
        fields = ['id', 'user', 'username', 'customer_email', 'created_at', 
                  'address', 'phone', 'comment', 'total_amount', 'status', 
                  'status_display', 'items']
        read_only_fields = ['id', 'created_at', 'total_amount']
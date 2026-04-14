from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.contrib import messages
from .models import Product, Category, Manufacturer, Cart, CartItem

def product_list(request):
    """Список товаров с фильтрацией и поиском"""
    products = Product.objects.all()
    
    # Получаем параметры из GET-запроса
    search_query = request.GET.get('search', '')
    category_id = request.GET.get('category', '')
    manufacturer_id = request.GET.get('manufacturer', '')
    
    # Поиск по названию и описанию
    if search_query:
        products = products.filter(
            Q(name__icontains=search_query) | 
            Q(description__icontains=search_query)
        )
    
    # Фильтр по категории
    if category_id:
        products = products.filter(category_id=category_id)
    
    # Фильтр по производителю
    if manufacturer_id:
        products = products.filter(manufacturer_id=manufacturer_id)
    
    # Все категории и производители для фильтров
    categories = Category.objects.all()
    manufacturers = Manufacturer.objects.all()
    
    context = {
        'products': products,
        'categories': categories,
        'manufacturers': manufacturers,
        'search_query': search_query,
        'selected_category': category_id,
        'selected_manufacturer': manufacturer_id,
    }
    return render(request, 'shop/product_list.html', context)


def product_detail(request, pk):
    """Детальная информация о товаре"""
    product = get_object_or_404(Product, id=pk)
    return render(request, 'shop/product_detail.html', {'product': product})


@login_required
def add_to_cart(request, product_id):
    """Добавление товара в корзину (только для авторизованных)"""
    product = get_object_or_404(Product, id=product_id)
    
    # Получаем или создаём корзину для пользователя
    cart, created = Cart.objects.get_or_create(user=request.user)
    
    # Проверяем, есть ли уже этот товар в корзине
    cart_item, created = CartItem.objects.get_or_create(
        cart=cart,
        product=product,
        defaults={'quantity': 1}
    )
    
    # Если товар уже был, увеличиваем количество
    if not created:
        if cart_item.quantity + 1 <= product.stock:
            cart_item.quantity += 1
            cart_item.save()
            messages.success(request, f'Товар "{product.name}" добавлен в корзину')
        else:
            messages.error(request, f'Недостаточно товара на складе. Доступно: {product.stock} шт.')
    else:
        messages.success(request, f'Товар "{product.name}" добавлен в корзину')
    
    return redirect('cart')


@login_required
def update_cart(request, item_id):
    """Обновление количества товара в корзине"""
    cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    
    if request.method == 'POST':
        quantity = int(request.POST.get('quantity', 1))
        
        # Валидация: количество не должно превышать остаток на складе
        if quantity > cart_item.product.stock:
            messages.error(request, f'Недостаточно товара на складе. Доступно: {cart_item.product.stock} шт.')
        elif quantity > 0:
            cart_item.quantity = quantity
            cart_item.save()
            messages.success(request, 'Количество обновлено')
        else:
            cart_item.delete()
            messages.success(request, 'Товар удалён из корзины')
    
    return redirect('cart')


@login_required
def remove_from_cart(request, item_id):
    """Удаление товара из корзины"""
    cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    product_name = cart_item.product.name
    cart_item.delete()
    messages.success(request, f'Товар "{product_name}" удалён из корзины')
    return redirect('cart')


@login_required
def cart_view(request):
    """Просмотр корзины"""
    cart, created = Cart.objects.get_or_create(user=request.user)
    cart_items = cart.items.select_related('product').all()
    
    total_price = sum(item.item_price() for item in cart_items)
    
    context = {
        'cart': cart,
        'cart_items': cart_items,
        'total_price': total_price,
    }
    return render(request, 'shop/cart.html', context)
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from io import BytesIO
import openpyxl
from openpyxl.styles import Font, Alignment, Border, Side
from datetime import datetime
from .models import Product, Category, Manufacturer, Cart, CartItem, Order, OrderItem
from rest_framework import viewsets, permissions
from rest_framework.response import Response
from rest_framework.decorators import action
from .serializers import (
    CategorySerializer, ManufacturerSerializer, 
    ProductSerializer, CartSerializer, CartItemSerializer
)


def product_list(request):
    products = Product.objects.all()
    
    search_query = request.GET.get('search', '')
    category_id = request.GET.get('category', '')
    manufacturer_id = request.GET.get('manufacturer', '')
    
    if search_query:
        products = products.filter(
            Q(name__icontains=search_query) | 
            Q(description__icontains=search_query)
        )
    
    if category_id:
        products = products.filter(category_id=category_id)
    
    if manufacturer_id:
        products = products.filter(manufacturer_id=manufacturer_id)
         
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
    product = get_object_or_404(Product, id=pk)
    return render(request, 'shop/product_detail.html', {'product': product})


@login_required
def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    cart, created = Cart.objects.get_or_create(user=request.user)
    
    cart_item, created = CartItem.objects.get_or_create(
        cart=cart,
        product=product,
        defaults={'quantity': 1}
    )
    
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
    cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    
    if request.method == 'POST':
        quantity = int(request.POST.get('quantity', 1))
        
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
    cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    product_name = cart_item.product.name
    cart_item.delete()
    messages.success(request, f'Товар "{product_name}" удалён из корзины')
    return redirect('cart')


@login_required
def cart_view(request):
    cart, created = Cart.objects.get_or_create(user=request.user)
    cart_items = cart.items.select_related('product').all()
    total_price = sum(item.item_price() for item in cart_items)
    
    context = {
        'cart': cart,
        'cart_items': cart_items,
        'total_price': total_price,
    }
    return render(request, 'shop/cart.html', context)


@login_required
def checkout(request):
    try:
        cart = request.user.cart
        cart_items = cart.items.select_related('product').all()
    except Cart.DoesNotExist:
        messages.error(request, 'Ваша корзина пуста')
        return redirect('cart')

    if not cart_items:
        messages.error(request, 'Ваша корзина пуста')
        return redirect('cart')
    
    if request.method == 'POST':
        customer_email = request.POST.get('email', '').strip()
        address = request.POST.get('address', '').strip()
        phone = request.POST.get('phone', '').strip()
        comment = request.POST.get('comment', '').strip()

        errors = []
        if not customer_email:
            errors.append('Email обязателен')
        if not address:
            errors.append('Адрес обязателен')
        if not phone:
            errors.append('Телефон обязателен')
        
        if phone and not phone.startswith('+'):
            errors.append('Телефон должен начинаться с +')
        
        if errors:
            for error in errors:
                messages.error(request, error)
            return render(request, 'shop/checkout.html', {
                'cart_items': cart_items,
                'total_price': cart.total_price(),
                'email': customer_email,
                'address': address,
                'phone': phone,
                'comment': comment
            })
        
        order = Order.objects.create(
            user=request.user,
            customer_email=customer_email,
            address=address,
            phone=phone,
            comment=comment,
            total_amount=cart.total_price(),
            status='pending'
        )
        
        for cart_item in cart_items:
            OrderItem.objects.create(
                order=order,
                product=cart_item.product,
                quantity=cart_item.quantity,
                price=cart_item.product.price
            )
            product = cart_item.product
            product.stock -= cart_item.quantity
            product.save()

        excel_file = generate_receipt_excel(order)

        subject = f'Ваш заказ №{order.id} оформлен'
        message = f"""
Здравствуйте, {request.user.username}!

Ваш заказ №{order.id} успешно оформлен.

Адрес: {address}
Телефон: {phone}
Сумма: {order.total_amount} руб.

Чек во вложении.

Спасибо за покупку!
        """
        
        try:
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[customer_email],
                fail_silently=False,
                attachments=[('receipt.xlsx', excel_file.read(), 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')]
            )
            messages.success(request, f'Заказ №{order.id} оформлен! Чек отправлен на {customer_email}')
        except Exception as e:
            messages.warning(request, f'Заказ оформлен, но email не отправлен: {e}')

        cart_items.delete()
        return redirect('order_success', order_id=order.id)

    context = {
        'cart_items': cart_items,
        'total_price': cart.total_price(),
    }
    return render(request, 'shop/checkout.html', context)


def generate_receipt_excel(order):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Чек"

    title_font = Font(bold=True, size=14)
    header_font = Font(bold=True, size=12)
    border = Border(
        left=Side(style='thin'),
        right=Side(style='thin'),
        top=Side(style='thin'),
        bottom=Side(style='thin')
    )
    
    ws['A1'] = 'МАГАЗИН ПОДАРКОВ'
    ws['A1'].font = title_font
    ws.merge_cells('A1:E1')
    
    ws['A2'] = 'Кассовый чек'
    ws['A2'].font = header_font
    ws.merge_cells('A2:E2')
    
    ws['A3'] = f'Дата: {datetime.now().strftime("%d.%m.%Y %H:%M")}'
    ws.merge_cells('A3:E3')
    ws['A4'] = f'Заказ №: {order.id}'
    ws.merge_cells('A4:E4')
    
    ws['A6'] = 'Покупатель:'
    ws['A6'].font = header_font
    ws['B6'] = order.user.username
    ws['C6'] = 'Email:'
    ws['D6'] = order.customer_email
    
    ws['A7'] = 'Телефон:'
    ws['B7'] = order.phone
    ws['C7'] = 'Адрес:'
    ws['D7'] = order.address
    
    headers = ['№', 'Товар', 'Цена', 'Кол-во', 'Сумма']
    for col, header in enumerate(headers, 1):
        cell = ws.cell(row=9, column=col, value=header)
        cell.font = header_font
        cell.border = border

    row = 10
    for idx, item in enumerate(order.items.all(), 1):
        ws.cell(row=row, column=1, value=idx).border = border
        ws.cell(row=row, column=2, value=item.product.name).border = border
        ws.cell(row=row, column=3, value=float(item.price)).border = border
        ws.cell(row=row, column=4, value=item.quantity).border = border
        ws.cell(row=row, column=5, value=float(item.price * item.quantity)).border = border
        row += 1

    ws.cell(row=row, column=4, value='ИТОГО:').font = Font(bold=True)
    ws.cell(row=row, column=5, value=float(order.total_amount)).font = Font(bold=True)

    ws.column_dimensions['A'].width = 8
    ws.column_dimensions['B'].width = 30
    ws.column_dimensions['C'].width = 12
    ws.column_dimensions['D'].width = 10
    ws.column_dimensions['E'].width = 12
    
    output = BytesIO()
    wb.save(output)
    output.seek(0)
    return output


def order_success(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    return render(request, 'shop/order_success.html', {'order': order})


# ==================== API Views ====================

class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]


class ManufacturerViewSet(viewsets.ModelViewSet):
    queryset = Manufacturer.objects.all()
    serializer_class = ManufacturerSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]


class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    
    def get_queryset(self):
        queryset = Product.objects.all()
        category = self.request.query_params.get('category', None)
        manufacturer = self.request.query_params.get('manufacturer', None)
        search = self.request.query_params.get('search', None)
        
        if category:
            queryset = queryset.filter(category_id=category)
        if manufacturer:
            queryset = queryset.filter(manufacturer_id=manufacturer)
        if search:
            queryset = queryset.filter(name__icontains=search)
        
        return queryset


class CartViewSet(viewsets.ModelViewSet):
    serializer_class = CartSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return Cart.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
    
    @action(detail=True, methods=['post'])
    def add_item(self, request, pk=None):
        cart = self.get_object()
        product_id = request.data.get('product_id')
        quantity = request.data.get('quantity', 1)
        
        try:
            product = Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            return Response({'error': 'Товар не найден'}, status=404)
        
        cart_item, created = CartItem.objects.get_or_create(
            cart=cart,
            product=product,
            defaults={'quantity': quantity}
        )
        
        if not created:
            if cart_item.quantity + quantity <= product.stock:
                cart_item.quantity += quantity
                cart_item.save()
            else:
                return Response({'error': 'Недостаточно товара на складе'}, status=400)
        
        serializer = CartItemSerializer(cart_item)
        return Response(serializer.data)
    
    @action(detail=True, methods=['delete'])
    def remove_item(self, request, pk=None):
        cart = self.get_object()
        item_id = request.data.get('item_id')
        
        try:
            cart_item = CartItem.objects.get(id=item_id, cart=cart)
            cart_item.delete()
            return Response({'message': 'Товар удалён из корзины'})
        except CartItem.DoesNotExist:
            return Response({'error': 'Товар не найден в корзине'}, status=404)


class CartItemViewSet(viewsets.ModelViewSet):
    serializer_class = CartItemSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return CartItem.objects.filter(cart__user=self.request.user)
    
    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        quantity = request.data.get('quantity')
        
        if quantity and quantity > instance.product.stock:
            return Response({'error': 'Недостаточно товара на складе'}, status=400)
        
        return super().update(request, *args, **kwargs)
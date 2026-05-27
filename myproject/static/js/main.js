// Получение CSRF-токена из cookies
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

const csrftoken = getCookie('csrftoken');

// Показать уведомление
function showNotification(message, type = 'success') {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type === 'success' ? 'success' : 'danger'} alert-dismissible fade show position-fixed`;
    alertDiv.style.top = '20px';
    alertDiv.style.right = '20px';
    alertDiv.style.zIndex = '9999';
    alertDiv.style.minWidth = '300px';
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    document.body.appendChild(alertDiv);
    setTimeout(() => alertDiv.remove(), 3000);
}

// Загрузка товаров через API
async function loadProductsFromAPI() {
    const container = document.getElementById('api-products-container');
    if (!container) return;
    
    // Показать спиннер
    container.innerHTML = `
        <div class="text-center py-5">
            <div class="spinner-border text-primary" role="status">
                <span class="visually-hidden">Загрузка...</span>
            </div>
            <p class="mt-2">Загрузка товаров...</p>
        </div>
    `;
    
    try {
        const response = await fetch('/api/products/');
        if (!response.ok) throw new Error('Ошибка загрузки');
        const products = await response.json();
        
        if (products.length === 0) {
            container.innerHTML = '<p class="text-center">Товары не найдены</p>';
            return;
        }
        
        let html = '<div class="row">';
        products.slice(0, 6).forEach(product => {
            html += `
                <div class="col-md-4 mb-4">
                    <div class="card h-100">
                        <div class="card-body">
                            <h5 class="card-title">${escapeHtml(product.name)}</h5>
                            <p class="price">${product.price} руб.</p>
                            <button onclick="addToCartAPI(${product.id})" class="btn btn-primary w-100">
                                В корзину
                            </button>
                        </div>
                    </div>
                </div>
            `;
        });
        html += '</div>';
        container.innerHTML = html;
    } catch (error) {
        container.innerHTML = `
            <div class="alert alert-danger">
                Ошибка загрузки товаров. Попробуйте позже.
            </div>
        `;
        console.error(error);
    }
}

// Добавление в корзину через API
window.addToCartAPI = async function(productId) {
    try {
        const response = await fetch(`/api/carts/`, {
            method: 'GET',
            headers: { 'X-CSRFToken': csrftoken },
        });
        const carts = await response.json();
        
        let cartId;
        if (carts.length === 0) {
            const createResponse = await fetch('/api/carts/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrftoken,
                },
                body: JSON.stringify({}),
            });
            const newCart = await createResponse.json();
            cartId = newCart.id;
        } else {
            cartId = carts[0].id;
        }
        
        const addResponse = await fetch(`/api/carts/${cartId}/add_item/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrftoken,
            },
            body: JSON.stringify({ product_id: productId, quantity: 1 }),
        });
        
        if (addResponse.ok) {
            showNotification('Товар добавлен в корзину!', 'success');
        } else {
            const error = await addResponse.json();
            showNotification(error.error || 'Ошибка добавления', 'error');
        }
    } catch (error) {
        console.error('Ошибка:', error);
        showNotification('Ошибка соединения с сервером', 'error');
    }
};

function escapeHtml(str) {
    return str.replace(/[&<>]/g, function(m) {
        if (m === '&') return '&amp;';
        if (m === '<') return '&lt;';
        if (m === '>') return '&gt;';
        return m;
    });
}

// Загрузка при готовности DOM
document.addEventListener('DOMContentLoaded', function() {
    loadProductsFromAPI();
});
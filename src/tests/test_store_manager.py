"""
Tests for orders manager
SPDX - License - Identifier: LGPL - 3.0 - or -later
Auteurs : Gabriel C. Ullmann, Fabio Petrillo, 2025
"""

import json
import pytest
from store_manager import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_health(client):
    result = client.get('/health-check')
    assert result.status_code == 200
    assert result.get_json() == {'status':'ok'}

def test_stock_flow(client):
    # 1. Créez un article (`POST /products`)
    product_data = {'name': 'Pencil', 'sku': '123456789', 'price': 9.99}

    response = client.post('/products',
                          data=json.dumps(product_data),
                          content_type='application/json')
    print(response.get_json())
    assert response.status_code == 201
    data = response.get_json()
    assert data['product_id'] > 0

    # 2. Ajoutez 5 unités au stock de cet article (`POST /stocks`)
    add_stock_qty = 5
    add_stock_body = {'product_id': data.get('product_id'), 'quantity': add_stock_qty}

    add_stock_resp = client.post("/stocks", data=json.dumps(add_stock_body), content_type='application/json')

    assert add_stock_resp.status_code == 201
    assert "rows added" in add_stock_resp.get_json()['result']
    assert str(data['product_id']) in add_stock_resp.get_json()['result']

    # 3. Vérifiez le stock, votre article devra avoir 5 unités dans le stock (`GET /stocks/:id`)
    get_stock_resp = client.get(f"/stocks/{data['product_id']}")

    assert get_stock_resp.status_code == 201
    assert add_stock_qty == get_stock_resp.get_json()['quantity']

    # 4. Faites une commande de l'article que vous avez crée, 2 unités (`POST /orders`)
    order_qty = 2
    place_order_body = { "user_id": 1, "items": [{"product_id": data['product_id'], "quantity": order_qty}] }

    place_order_resp = client.post(f"/orders", data= json.dumps(place_order_body), content_type='application/json')
    print(place_order_resp.get_json())
    assert place_order_resp.status_code == 201
    assert place_order_resp.get_json()['order_id'] >= 1

    # 5. Vérifiez le stock encore une fois (`GET /stocks/:id`)
    expected_stock_qty = add_stock_qty - order_qty
    
    get_stock_resp = client.get(f"/stocks/{data['product_id']}")

    assert get_stock_resp.status_code == 201
    assert expected_stock_qty == get_stock_resp.get_json()['quantity']

    # 6. Étape extra: supprimez la commande    
    delete_order_resp = client.delete(f"/orders/{place_order_resp.get_json()['order_id']}")

    assert delete_order_resp.status_code == 200
    assert True == delete_order_resp.get_json()['deleted']

    # 6.1 et vérifiez le stock de nouveau. Le stock devrait augmenter après la suppression de la commande.
    expected_stock_qty = add_stock_qty

    get_stock_resp = client.get(f"/stocks/{data['product_id']}")

    assert get_stock_resp.status_code == 201
    assert expected_stock_qty == get_stock_resp.get_json()['quantity']
    
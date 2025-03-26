import json
import requests
import re

# Укажите API-ключ здесь
API_KEY = "dCaQleyZPgaSCsdgkHC95hYcjQoxG7wvLfBNC2OIVApulTH59JxcRlBpCZ281KNTGZdcMkQQo2pLvpuPQ9Av4O"  
BASE_URL = "https://api.ataix.kz"

def get_request(endpoint):
    url = f"{BASE_URL}{endpoint}"
    headers = {
        "accept": "application/json",
        "X-API-Key": API_KEY
    }
    print(f" GET {url}")  # Лог запроса
    
    try:
        response = requests.get(url, headers=headers, timeout=20)
        print(f" Response Code: {response.status_code}")
        print(f" Response Body: {response.text[:500]}")  # Вывод первых 500 символов ответа
        
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f" Ошибка запроса: {e}")
        return None

def post_request(endpoint, data):
    url = f"{BASE_URL}{endpoint}"
    headers = {
        "accept": "application/json",
        "X-API-Key": API_KEY,
        "Content-Type": "application/json"
    }
    print(f" POST {url} с данными: {json.dumps(data, indent=2)}")  

    try:
        response = requests.post(url, headers=headers, json=data, timeout=20)
        print(f" Response Code: {response.status_code}")
        print(f" Response Body: {response.text[:500]}")
        
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f" Ошибка запроса: {e}")
        return None

def get_balance(currency):
    data = get_request(f"/api/user/balances/{currency}")
    if not data:
        print(" Ошибка: баланс не получен")
        return 0
    currency="USDT"
    print(f" Баланс {currency}: {json.dumps(data, indent=2)}")
    
    match = re.search(r'"available"\s*:\s*"([\d.]+)"', json.dumps(data))
    return float(match.group(1)) if match else 0

def get_trading_pair():
    data = get_request("/api/symbols")
    
    if not data:
        print(" Ошибка: список торговых пар не получен")
        return None

    print(f" Доступные пары: {json.dumps(data, indent=2)}")

    for pair in data:
        if isinstance(pair, dict) and pair.get("quote") == "USDT" and float(pair.get("minPrice", 1)) <= 0.6:
            print(f" Найдена подходящая пара: {pair.get('symbol')}")
            return pair.get("symbol")

    print("Нет пары с ценой ≤ 0.6 USDT")
    return None

def get_highest_bid(symbol):
    data = get_request(f"/api/orderbook/{symbol}")
    if not data or "bids" not in data:
        print(f" Ошибка: не удалось получить стакан для {symbol}")
        return 0

    print(f" Стакан заявок: {json.dumps(data, indent=2)}")

    highest_bid = max(float(order["price"]) for order in data["bids"]) if data["bids"] else 0
    print(f" Максимальная цена покупки: {highest_bid}")
    return highest_bid

def place_order(symbol, price, amount=10):
    order_data = {
        "symbol": symbol,
        "side": "buy",
        "type": "limit",
        "price": str(price),
        "quantity": str(amount)
    }
    response = post_request("/api/orders", order_data)

    if response:
        print(f" Ордер размещён: {response}")
    else:
        print(f" Ошибка размещения ордера {order_data}")

    return response

def main():
    print("Запуск скрипта...")

    usdt_balance = get_balance("USDT")
    print(f" Баланс USDT: {usdt_balance}")
    
    if usdt_balance <= 0:
        print(" Баланс USDT пустой или недоступен.")
        return
    
    pair = get_trading_pair()
    if not pair:
        print(" Нет подходящей торговой пары.")
        return
    
    highest_bid = get_highest_bid(pair)
    if highest_bid == 0:
        print(" Ошибка при получении максимальной цены ордера.")
        return
    
    order_prices = [
        round(highest_bid * 0.98, 6),
        round(highest_bid * 0.95, 6),
        round(highest_bid * 0.92, 6)
    ]
    
    orders = []
    for price in order_prices:
        order = place_order(pair, price)
        if order:
            orders.append({"order_id": order.get("id", "unknown"), "status": "NEW"})
    
    with open("orders.json",
              "w") as f:
        json.dump(orders, f, indent=4)
    
    print(" Ордеры успешно размещены и сохранены в orders.json")

if __name__ == "__main__":
    main()

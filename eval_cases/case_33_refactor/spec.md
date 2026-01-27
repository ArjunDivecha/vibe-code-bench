# Refactor: Split Monolith into Modules

You're given a 400-line monolithic Python script. Your task is to refactor it into a clean, modular structure while maintaining all functionality.

## The Monolith

Create a file `monolith.py` with this structure, then refactor it:

```python
#!/usr/bin/env python3
"""
Inventory Management System - Monolithic Version
This needs to be refactored into separate modules.
"""

import json
import os
from datetime import datetime
from typing import Optional

# ============= DATA MODELS =============

class Product:
    def __init__(self, id: str, name: str, price: float, quantity: int, category: str):
        self.id = id
        self.name = name
        self.price = price
        self.quantity = quantity
        self.category = category
        self.created_at = datetime.now().isoformat()
        self.updated_at = datetime.now().isoformat()
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'price': self.price,
            'quantity': self.quantity,
            'category': self.category,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }
    
    @classmethod
    def from_dict(cls, data):
        product = cls(data['id'], data['name'], data['price'], 
                     data['quantity'], data['category'])
        product.created_at = data.get('created_at', product.created_at)
        product.updated_at = data.get('updated_at', product.updated_at)
        return product

# ============= STORAGE =============

class Storage:
    def __init__(self, filepath: str = 'inventory.json'):
        self.filepath = filepath
        self.data = {'products': [], 'transactions': []}
        self.load()
    
    def load(self):
        if os.path.exists(self.filepath):
            with open(self.filepath, 'r') as f:
                self.data = json.load(f)
    
    def save(self):
        with open(self.filepath, 'w') as f:
            json.dump(self.data, f, indent=2)

# ============= INVENTORY OPERATIONS =============

class InventoryManager:
    def __init__(self, storage: Storage):
        self.storage = storage
    
    def add_product(self, product: Product) -> bool:
        if self.get_product(product.id):
            return False
        self.storage.data['products'].append(product.to_dict())
        self.storage.save()
        return True
    
    def get_product(self, product_id: str) -> Optional[Product]:
        for p in self.storage.data['products']:
            if p['id'] == product_id:
                return Product.from_dict(p)
        return None
    
    def update_quantity(self, product_id: str, delta: int) -> bool:
        for p in self.storage.data['products']:
            if p['id'] == product_id:
                p['quantity'] += delta
                p['updated_at'] = datetime.now().isoformat()
                self.storage.save()
                return True
        return False
    
    def delete_product(self, product_id: str) -> bool:
        initial_len = len(self.storage.data['products'])
        self.storage.data['products'] = [
            p for p in self.storage.data['products'] if p['id'] != product_id
        ]
        if len(self.storage.data['products']) < initial_len:
            self.storage.save()
            return True
        return False
    
    def list_products(self, category: Optional[str] = None):
        products = self.storage.data['products']
        if category:
            products = [p for p in products if p['category'] == category]
        return [Product.from_dict(p) for p in products]
    
    def get_low_stock(self, threshold: int = 10):
        return [Product.from_dict(p) for p in self.storage.data['products'] 
                if p['quantity'] < threshold]

# ============= REPORTING =============

class ReportGenerator:
    def __init__(self, inventory: InventoryManager):
        self.inventory = inventory
    
    def inventory_summary(self):
        products = self.inventory.list_products()
        total_value = sum(p.price * p.quantity for p in products)
        categories = {}
        for p in products:
            if p.category not in categories:
                categories[p.category] = 0
            categories[p.category] += 1
        return {
            'total_products': len(products),
            'total_value': total_value,
            'by_category': categories
        }
    
    def low_stock_report(self, threshold: int = 10):
        low_stock = self.inventory.get_low_stock(threshold)
        return [{
            'id': p.id,
            'name': p.name,
            'quantity': p.quantity,
            'needs': threshold - p.quantity
        } for p in low_stock]

# ============= CLI =============

def main():
    storage = Storage()
    inventory = InventoryManager(storage)
    reports = ReportGenerator(inventory)
    
    import sys
    if len(sys.argv) < 2:
        print("Usage: python monolith.py <command> [args]")
        print("Commands: add, list, update, delete, report, low-stock")
        return
    
    cmd = sys.argv[1]
    
    if cmd == 'add':
        if len(sys.argv) < 6:
            print("Usage: add <id> <name> <price> <quantity> <category>")
            return
        product = Product(sys.argv[2], sys.argv[3], float(sys.argv[4]), 
                         int(sys.argv[5]), sys.argv[6])
        if inventory.add_product(product):
            print(f"Added: {product.name}")
        else:
            print("Product ID already exists")
    
    elif cmd == 'list':
        category = sys.argv[2] if len(sys.argv) > 2 else None
        for p in inventory.list_products(category):
            print(f"{p.id}: {p.name} - ${p.price} ({p.quantity} in stock)")
    
    elif cmd == 'update':
        if len(sys.argv) < 4:
            print("Usage: update <id> <quantity_change>")
            return
        if inventory.update_quantity(sys.argv[2], int(sys.argv[3])):
            print("Updated")
        else:
            print("Product not found")
    
    elif cmd == 'delete':
        if inventory.delete_product(sys.argv[2]):
            print("Deleted")
        else:
            print("Product not found")
    
    elif cmd == 'report':
        summary = reports.inventory_summary()
        print(f"Total products: {summary['total_products']}")
        print(f"Total value: ${summary['total_value']:.2f}")
        print("By category:", summary['by_category'])
    
    elif cmd == 'low-stock':
        threshold = int(sys.argv[2]) if len(sys.argv) > 2 else 10
        for item in reports.low_stock_report(threshold):
            print(f"{item['name']}: {item['quantity']} (need {item['needs']} more)")

if __name__ == '__main__':
    main()
```

## Your Task

Refactor this into a proper Python package structure:

```
inventory/
├── __init__.py       # Package init, exports main classes
├── models.py         # Product class and data models
├── storage.py        # Storage class for persistence
├── manager.py        # InventoryManager class
├── reports.py        # ReportGenerator class
└── cli.py            # CLI interface and main()

run.py                # Entry point: from inventory.cli import main; main()
```

## Requirements

1. **Same functionality** - All commands should work identically
2. **Proper imports** - Each module imports only what it needs
3. **Clean separation** - Each module has a single responsibility
4. **No circular imports** - Structure imports correctly
5. **Docstrings** - Add module and class docstrings
6. **Type hints** - Maintain existing type hints

## Deliverables

1. The `inventory/` package with all modules
2. `run.py` entry point
3. All existing functionality preserved

## Evaluation

- All CLI commands work
- Clean module separation
- No duplicate code
- Proper Python package structure
- No import errors

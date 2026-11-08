# LUSI

LUSI (Lifestyle and User Shopping Intelligence) is a starter project for a grocery
shopping assistant that helps users stay within weekly budget while balancing:

- Shopping across multiple stores
- Favorite meals and snacks
- Exploration of new meals with ingredient overlap

## What is implemented

`lusi.py` includes a budget-aware planner (`generate_shopping_plan`) that:

1. Prioritizes favorite meals
2. Selects a limited number of exploratory meals based on ingredient overlap and novelty
3. Chooses store-by-store item offers while considering preferred stores and price
4. Trims exploratory meals (then snacks if needed) to stay within weekly budget

## Quick example

```python
from lusi import Meal, generate_shopping_plan

store_prices = {
    "StoreA": {"chicken": 5.0, "rice": 2.0, "chips": 3.0},
    "StoreB": {"chicken": 4.8, "rice": 2.2, "chips": 2.6},
}

meals = [
    Meal("stir_fry", ("chicken", "rice"), is_favorite=True),
    Meal("burrito_bowl", ("chicken", "rice", "beans"), novelty_score=0.9),
]

plan = generate_shopping_plan(
    store_prices=store_prices,
    meals=meals,
    favorite_snacks=["chips"],
    preferred_stores=["StoreA"],
    weekly_budget=20.0,
)

print(plan.total_cost, plan.within_budget)
```

## Running tests

```bash
python -m unittest discover -s tests
```

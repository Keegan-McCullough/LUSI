from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List, Sequence, Tuple


@dataclass(frozen=True)
class Meal:
    name: str
    ingredients: Tuple[str, ...]
    is_favorite: bool = False
    novelty_score: float = 0.0


@dataclass(frozen=True)
class ShoppingItem:
    name: str
    store: str
    price: float
    category: str


@dataclass(frozen=True)
class ShoppingPlan:
    selected_meals: Tuple[str, ...]
    exploratory_meals: Tuple[str, ...]
    items: Tuple[ShoppingItem, ...]
    total_cost: float
    weekly_budget: float

    @property
    def within_budget(self) -> bool:
        return self.total_cost <= self.weekly_budget

    @property
    def budget_remaining(self) -> float:
        return round(self.weekly_budget - self.total_cost, 2)


PREFERRED_STORE_PENALTY_STEP = 0.05


def generate_shopping_plan(
    store_prices: Dict[str, Dict[str, float]],
    meals: Sequence[Meal],
    favorite_snacks: Sequence[str],
    preferred_stores: Sequence[str],
    weekly_budget: float,
    exploratory_meal_slots: int = 1,
) -> ShoppingPlan:
    """Build a budget-aware shopping plan across multiple stores.

    The planner prioritizes favorite meals and snacks, then optionally adds a small
    number of exploratory meals whose ingredients overlap with favorites.
    """

    if weekly_budget < 0:
        raise ValueError("weekly_budget must be non-negative")

    favorite_meals = [meal for meal in meals if meal.is_favorite]
    candidate_meals = [meal for meal in meals if not meal.is_favorite]

    selected_meals = list(favorite_meals)
    exploratory_meals = _choose_exploratory_meals(
        selected_meals,
        candidate_meals,
        store_prices,
        preferred_stores,
        exploratory_meal_slots,
    )
    selected_meals.extend(exploratory_meals)

    items = _build_items(selected_meals, favorite_snacks, store_prices, preferred_stores)
    total_cost = round(sum(item.price for item in items), 2)

    if total_cost > weekly_budget and exploratory_meals:
        selected_meals = list(favorite_meals)
        items = _build_items(selected_meals, favorite_snacks, store_prices, preferred_stores)
        total_cost = round(sum(item.price for item in items), 2)
        exploratory_meals = []

    if total_cost > weekly_budget and favorite_snacks:
        items = _drop_expensive_snacks(items, weekly_budget)
        total_cost = round(sum(item.price for item in items), 2)

    return ShoppingPlan(
        selected_meals=tuple(meal.name for meal in selected_meals),
        exploratory_meals=tuple(meal.name for meal in exploratory_meals),
        items=tuple(items),
        total_cost=total_cost,
        weekly_budget=weekly_budget,
    )


def _choose_exploratory_meals(
    selected_meals: Sequence[Meal],
    candidates: Sequence[Meal],
    store_prices: Dict[str, Dict[str, float]],
    preferred_stores: Sequence[str],
    slots: int,
) -> List[Meal]:
    if slots <= 0 or not candidates:
        return []

    selected_ingredients = {
        ingredient
        for meal in selected_meals
        for ingredient in meal.ingredients
    }

    scored: List[Tuple[float, Meal]] = []
    for meal in candidates:
        overlap = _overlap_ratio(meal.ingredients, selected_ingredients)
        estimated_cost = sum(
            _best_offer_price(ingredient, store_prices, preferred_stores)
            for ingredient in meal.ingredients
        )
        score = overlap * 2.0 + meal.novelty_score - (estimated_cost * 0.05)
        scored.append((score, meal))

    scored.sort(key=lambda pair: pair[0], reverse=True)
    return [meal for _, meal in scored[:slots]]


def _build_items(
    selected_meals: Sequence[Meal],
    favorite_snacks: Sequence[str],
    store_prices: Dict[str, Dict[str, float]],
    preferred_stores: Sequence[str],
) -> List[ShoppingItem]:
    meal_ingredients = sorted({ingredient for meal in selected_meals for ingredient in meal.ingredients})

    items = [
        _build_item(ingredient, "meal", store_prices, preferred_stores)
        for ingredient in meal_ingredients
    ]
    items.extend(
        _build_item(snack, "snack", store_prices, preferred_stores)
        for snack in favorite_snacks
    )

    return items


def _build_item(
    item_name: str,
    category: str,
    store_prices: Dict[str, Dict[str, float]],
    preferred_stores: Sequence[str],
) -> ShoppingItem:
    best_store, best_price = _best_offer(item_name, store_prices, preferred_stores)
    return ShoppingItem(name=item_name, store=best_store, price=round(best_price, 2), category=category)


def _best_offer(
    item_name: str,
    store_prices: Dict[str, Dict[str, float]],
    preferred_stores: Sequence[str],
) -> Tuple[str, float]:
    preferred_rank = {store: idx for idx, store in enumerate(preferred_stores)}

    best_store = None
    best_price = float("inf")
    best_adjusted_score = float("inf")

    for store, prices in store_prices.items():
        if item_name not in prices:
            continue

        price = prices[item_name]
        penalty = preferred_rank.get(store, len(preferred_rank)) * PREFERRED_STORE_PENALTY_STEP
        adjusted_score = price + penalty
        if adjusted_score < best_adjusted_score:
            best_adjusted_score = adjusted_score
            best_price = price
            best_store = store

    if best_store is None:
        raise ValueError(f"No store has price data for '{item_name}'")

    return best_store, best_price


def _best_offer_price(
    item_name: str,
    store_prices: Dict[str, Dict[str, float]],
    preferred_stores: Sequence[str],
) -> float:
    _, price = _best_offer(item_name, store_prices, preferred_stores)
    return price


def _overlap_ratio(items: Iterable[str], baseline: set[str]) -> float:
    items = tuple(items)
    if not items:
        return 0.0
    overlap_count = sum(1 for item in items if item in baseline)
    return overlap_count / len(items)


def _drop_expensive_snacks(items: List[ShoppingItem], weekly_budget: float) -> List[ShoppingItem]:
    result = list(items)
    if sum(item.price for item in result) <= weekly_budget:
        return result

    snack_indices_by_price = sorted(
        (idx for idx, item in enumerate(result) if item.category == "snack"),
        key=lambda idx: result[idx].price,
        reverse=True,
    )

    for idx in snack_indices_by_price:
        del result[idx]
        if sum(item.price for item in result) <= weekly_budget:
            return result

    return result

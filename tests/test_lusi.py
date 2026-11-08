import unittest

from lusi import Meal, generate_shopping_plan


class ShoppingPlanTests(unittest.TestCase):
    def setUp(self):
        self.store_prices = {
            "StoreA": {
                "chicken": 5.0,
                "rice": 2.0,
                "broccoli": 2.0,
                "beans": 2.0,
                "pasta": 4.0,
                "tomato": 2.0,
                "chips": 3.0,
            },
            "StoreB": {
                "chicken": 4.8,
                "rice": 2.2,
                "broccoli": 2.3,
                "beans": 2.5,
                "pasta": 2.0,
                "tomato": 1.0,
                "chips": 2.6,
            },
        }
        self.meals = [
            Meal("stir_fry", ("chicken", "rice", "broccoli"), is_favorite=True),
            Meal("burrito_bowl", ("chicken", "rice", "beans"), novelty_score=0.8),
            Meal("pasta_night", ("pasta", "tomato"), novelty_score=0.8),
        ]

    def test_prefers_exploratory_meal_with_overlap(self):
        plan = generate_shopping_plan(
            store_prices=self.store_prices,
            meals=self.meals,
            favorite_snacks=["chips"],
            preferred_stores=["StoreA"],
            weekly_budget=25.0,
            exploratory_meal_slots=1,
        )

        self.assertIn("burrito_bowl", plan.exploratory_meals)
        self.assertNotIn("pasta_night", plan.exploratory_meals)

    def test_drops_exploratory_before_snacks_when_budget_is_tight(self):
        plan = generate_shopping_plan(
            store_prices=self.store_prices,
            meals=self.meals,
            favorite_snacks=["chips"],
            preferred_stores=["StoreA"],
            weekly_budget=13.0,
            exploratory_meal_slots=1,
        )

        self.assertEqual(plan.exploratory_meals, ())
        self.assertIn("chips", [item.name for item in plan.items])
        self.assertTrue(plan.within_budget)

    def test_picks_best_store_per_item(self):
        plan = generate_shopping_plan(
            store_prices=self.store_prices,
            meals=self.meals,
            favorite_snacks=["chips"],
            preferred_stores=["StoreA"],
            weekly_budget=20.0,
            exploratory_meal_slots=0,
        )

        tomato_item = next(item for item in plan.items if item.name == "chips")
        self.assertEqual(tomato_item.store, "StoreB")


if __name__ == "__main__":
    unittest.main()

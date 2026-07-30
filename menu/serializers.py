# pyrefly: ignore [missing-import]
from rest_framework import serializers
from .models import Mood, IngredientCategory, Ingredient, MenuItem, CustomBowl

class MoodSerializer(serializers.ModelSerializer):
    class Meta:
        model = Mood
        fields = ['id', 'name', 'slug', 'icon']


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        # All nutritional metrics explicitly exposed for live UI updates
        fields = ['id', 'name', 'category', 'price', 'image_url', 'calories', 'protein', 'carbs', 'fats']


class IngredientCategorySerializer(serializers.ModelSerializer):
    # Nesting the pre-fetched ingredients list inside its target category layout structural step
    ingredients = IngredientSerializer(many=True, read_only=True)

    class Meta:
        model = IngredientCategory
        fields = ['id', 'name', 'max_selectable_items', 'display_order', 'ingredients']


class MenuItemSerializer(serializers.ModelSerializer):
    moods = MoodSerializer(many=True, read_only=True)
    base_ingredients = IngredientSerializer(many=True, read_only=True)

    class Meta:
        model = MenuItem
        fields = ['id', 'name', 'description', 'base_price', 'image', 'moods', 'base_ingredients', 'is_customizable']


class CustomBowlSerializer(serializers.ModelSerializer):
    # Exposing dynamic properties calculated real-time by the DB layer
    total_price = serializers.DecimalField(max_digits=6, decimal_places=2, read_only=True)
    total_calories = serializers.IntegerField(read_only=True)
    total_protein = serializers.FloatField(read_only=True)
    total_carbs = serializers.FloatField(read_only=True)
    total_fats = serializers.FloatField(read_only=True)
    selected_ingredients = IngredientSerializer(many=True, read_only=True)

    class Meta:
        model = CustomBowl
        fields = [
            'id', 'user', 'base_menu_item', 'selected_ingredients', 
            'total_price', 'total_calories', 'total_protein', 'total_carbs', 'total_fats'
        ]

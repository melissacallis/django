import os
import json

import requests

from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST

from .models import Favorite

SPOONACULAR_API_KEY = os.environ.get('SPOONACULAR_API_KEY', '')
SPOONACULAR_BASE = "https://api.spoonacular.com/recipes"
ORIGO_API_URL = os.environ.get('ORIGO_API_URL', 'https://assistant-app-production-92f5.up.railway.app')


def _clean_ingredient(text):
    return text.lstrip('•').strip()


def fetch_recipe(query):
    """Look up a recipe by name via the Spoonacular API and return a dict
    shaped like {external_id, title, image, source_url, ingredients,
    directions}, or None if no recipe matched the query."""
    search = requests.get(
        f"{SPOONACULAR_BASE}/complexSearch",
        params={"query": query, "number": 1, "apiKey": SPOONACULAR_API_KEY},
        timeout=15,
    )
    search.raise_for_status()
    results = search.json().get("results") or []
    if not results:
        return None

    recipe_id = results[0]["id"]
    info = requests.get(
        f"{SPOONACULAR_BASE}/{recipe_id}/information",
        params={"includeNutrition": "false", "apiKey": SPOONACULAR_API_KEY},
        timeout=15,
    )
    info.raise_for_status()
    data = info.json()

    ingredients = [_clean_ingredient(ing.get("original", "")) for ing in data.get("extendedIngredients", [])]

    directions = []
    analyzed = data.get("analyzedInstructions") or []
    if analyzed:
        for step in analyzed[0].get("steps", []):
            directions.append(step.get("step", "").strip())
    elif data.get("instructions"):
        directions = [data["instructions"]]

    return {
        'external_id': str(recipe_id),
        'title': data.get('title'),
        'image': data.get('image'),
        'source_url': data.get('sourceUrl'),
        'ingredients': ingredients,
        'directions': directions,
    }


def index(request):
    favorite_count = Favorite.objects.count()
    return render(request, 'recipelist/index.html', {'favorite_count': favorite_count})


def search(request):
    query = request.GET.get('q', '').strip()
    if not query:
        return render(request, 'recipelist/ingredients.html', {'search_query': query})

    recipe = fetch_recipe(query)
    if not recipe:
        return render(request, 'recipelist/ingredients.html', {'search_query': query})

    recipe['search_query'] = query
    recipe['is_favorite'] = Favorite.objects.filter(external_id=recipe['external_id']).exists()
    recipe['ingredients_json'] = json.dumps(recipe['ingredients'])
    recipe['directions_json'] = json.dumps(recipe['directions'])
    return render(request, 'recipelist/ingredients.html', recipe)


@require_POST
def add_favorite(request):
    external_id = request.POST.get('external_id', '')
    if not Favorite.objects.filter(external_id=external_id).exists():
        Favorite.objects.create(
            external_id=external_id,
            title=request.POST.get('title', ''),
            image=request.POST.get('image') or None,
            source_url=request.POST.get('source_url') or None,
            ingredients=json.loads(request.POST.get('ingredients', '[]')),
            directions=json.loads(request.POST.get('directions', '[]')),
        )
    return redirect(request.POST.get('next') or 'recipelist:favorites')


@require_POST
def remove_favorite(request, pk):
    get_object_or_404(Favorite, pk=pk).delete()
    return redirect('recipelist:favorites')


def favorites(request):
    return render(request, 'recipelist/favorites.html', {'favorites': Favorite.objects.all()})


def grocery_list(request):
    if request.method == 'POST':
        selected_ingredients = request.POST.getlist('ingredient')
        request.session['selected_ingredients'] = selected_ingredients
        context = {'selected_ingredients': selected_ingredients}
        return render(request, 'recipelist/grocery_list.html', context)
    return render(request, 'recipelist/grocery_list.html')


@require_POST
def send_to_origo(request):
    ingredients = request.POST.getlist('ingredient')
    if not ingredients:
        return redirect('recipelist:grocery_list')

    try:
        response = requests.post(
            f"{ORIGO_API_URL}/api/items",
            json={
                "title": "Grocery List",
                "type": "task",
                "notes": "\n".join(f"- {item}" for item in ingredients),
            },
            timeout=10,
        )
        sent_ok = response.status_code in (200, 201)
    except requests.RequestException:
        sent_ok = False

    context = {'selected_ingredients': ingredients, 'origo_sent_ok': sent_ok}
    return render(request, 'recipelist/grocery_list.html', context)

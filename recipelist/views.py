import requests

from django.shortcuts import render


MEALDB_SEARCH_URL = "https://www.themealdb.com/api/json/v1/1/search.php"


def fetch_recipe(query):
    """Look up a recipe by name via TheMealDB's free API and return a dict
    shaped like {source_url, stars, ingredients, directions}, or None if no
    recipe matched the query."""
    response = requests.get(MEALDB_SEARCH_URL, params={"s": query}, timeout=15)
    response.raise_for_status()
    meals = response.json().get("meals")
    if not meals:
        return None

    meal = meals[0]

    ingredients = []
    for i in range(1, 21):
        name = (meal.get(f"strIngredient{i}") or "").strip()
        measure = (meal.get(f"strMeasure{i}") or "").strip()
        if name:
            ingredients.append(f"{measure} {name}".strip())

    instructions = meal.get("strInstructions") or ""
    directions = [step.strip() for step in instructions.replace("\r\n", "\n").split("\n") if step.strip()]

    return {
        'title': meal.get('strMeal'),
        'image': meal.get('strMealThumb'),
        'source_url': meal.get('strSource'),
        'ingredients': ingredients,
        'directions': directions,
    }


def index(request):
    return render(request, 'recipelist/index.html')


def search(request):
    query = request.GET.get('q', '').strip()
    if not query:
        return render(request, 'recipelist/ingredients.html', {'search_query': query})

    recipe = fetch_recipe(query)
    if not recipe:
        return render(request, 'recipelist/ingredients.html', {'search_query': query})

    recipe['search_query'] = query
    return render(request, 'recipelist/ingredients.html', recipe)


def grocery_list(request):
    if request.method == 'POST':
        selected_ingredients = request.POST.getlist('ingredient')
        request.session['selected_ingredients'] = selected_ingredients
        context = {'selected_ingredients': selected_ingredients}
        return render(request, 'recipelist/grocery_list.html', context)
    return render(request, 'recipelist/grocery_list.html')

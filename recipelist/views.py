from django.shortcuts import render
from bs4 import BeautifulSoup
import requests
from django.http import HttpResponse
from fractions import Fraction
from django.shortcuts import render, redirect
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
import os
import time
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from urllib.parse import quote



ingredients=[]

def index(request):
    return render(request, 'recipelist/index.html')

def get_ingredients(request):
    if request.method == 'POST':
        url = request.POST['url']
        page = requests.get(url)
        soup = BeautifulSoup(page.content, 'html.parser')
        stars_html = soup.find(id='mntl-recipe-review-bar__rating_2-0')
        ingredients_html = soup.find(class_='mntl-structured-ingredients__list')
        directions_html= soup.find(class_='comp mntl-sc-block-group--OL mntl-sc-block mntl-sc-block-startgroup')
        ingredients = []
        directions = []
        stars = ''
        if stars_html:
            stars = stars_html.text
        if ingredients_html:
            for li in ingredients_html.find_all('li'):
                ingredients.append(li.text.strip())
        if directions_html:
            for li in directions_html.find_all('li'):
                directions.append(li.text.replace('.', '--').strip())

        context = {
            'url': url,
            'stars': stars,
            'ingredients': ingredients,
            'directions': directions,
        }

        return render(request, 'recipelist/ingredients.html', context)

    else:
        return render(request, 'recipelist/index.html')






def search(request):
    query = request.GET.get('q', '')
    url = f"https://www.google.com/search?q={query} site:allrecipes.com"
    page = requests.get(url)
    soup = BeautifulSoup(page.content, 'html.parser')
    search_results = soup.find_all('a')

    recipe_url = None
    for link in search_results:
        link_url = link.get('href')
        if link_url.startswith('/url?q=https://www.allrecipes.com/recipe/') and 'search' not in link_url:
            recipe_url = link_url.split('&')[0][7:]
            break

    if not recipe_url:
        return render(request, 'search.html', {'error_message': 'No recipe found.'})

    recipe_page = requests.get(recipe_url)
    recipe_soup = BeautifulSoup(recipe_page.content, 'html.parser')

    recipe_title = soup.find("title").text
    title, source = recipe_title.split(":")


    recipe_details = recipe_soup.find('div', {'class': 'comp recipe-details mntl-recipe-details'})
    details_items = recipe_details.find_all('div', {'class': 'mntl-recipe-details__item'})

    for item in details_items:
        label = item.find('div', {'class': 'mntl-recipe-details__label'}).text.strip()
        if label == 'Servings:':
            servings = item.find('div', {'class': 'mntl-recipe-details__value'}).text.strip()
            break
    else:
        servings = None


    stars = recipe_soup.find(id='mntl-recipe-review-bar__rating_2-0')
    if stars:
        stars_text = f'{stars.text} -- Ingredients:  '
    else:
        stars_text = 'Could not find stars information.'

    ingredients = []
    ingredients_html = recipe_soup.find(class_='mntl-structured-ingredients__list')
    for li in ingredients_html.find_all('li'):
        ingredients.append(li.text.strip())

    directions = []
    directions_html = recipe_soup.find(class_='comp mntl-sc-block-group--OL mntl-sc-block mntl-sc-block-startgroup')
    for li in directions_html.find_all('li'):
        directions.append(li.text.replace('.', '--').strip())

    context = {
        'recipe_url': recipe_url,
        'stars_text': stars_text,
        'servings': servings,
        'ingredients': ingredients,
        'directions': directions,
        'recipe_title': recipe_title,
        'title':title,
        'source':source,
    }
    return render(request, 'recipelist/search.html', context)



def adjusted_search(request):
    servings = request.GET.get('servings', '')
    recipe_url = request.GET.get('recipe_url', '')
    if not servings or not recipe_url:
        return redirect('search')

    try:
        servings = int(servings)
        if servings < 1 or servings > 10:
            raise ValueError
    except ValueError:
        return redirect('search')

    recipe_page = requests.get(recipe_url)
    recipe_soup = BeautifulSoup(recipe_page.content, 'html.parser')

    recipe_title = recipe_soup.find("title").text
    if ':' in recipe_title:
        title, source = recipe_title.split(":")
    else:
        title = recipe_title
        source = "Unknown"

    recipe_details = recipe_soup.find('div', {'class': 'comp recipe-details mntl-recipe-details'})
    details_items = recipe_details.find_all('div', {'class': 'mntl-recipe-details__item'})

    for item in details_items:
        label = item.find('div', {'class': 'mntl-recipe-details__label'}).text.strip()
        if label == 'Servings:':
            old_servings = int(item.find('div', {'class': 'mntl-recipe-details__value'}).text.strip())
            break
    else:
        old_servings = None

    stars = recipe_soup.find(id='mntl-recipe-review-bar__rating_2-0')
    if stars:
        stars_text = f'{stars.text} -- Ingredients:  '
    else:
        stars_text = 'Could not find stars information.'

    ingredients = []
    ingredients_html = recipe_soup.find(class_='mntl-structured-ingredients__list')
    for li in ingredients_html.find_all('li'):
        ingredient_text = li.text.strip()
        if '(' in ingredient_text and ')' in ingredient_text:
            # Remove parentheses and their contents, e.g. "(10 oz.)"
            start_index = ingredient_text.find('(')
            end_index = ingredient_text.find(')') + 1
            ingredient_text = ingredient_text[:start_index] + ingredient_text[end_index:]
        ingredient_parts = ingredient_text.split()
        try:
            amount = float(ingredient_parts[0])
            unit = ingredient_parts[1]
            name = ' '.join(ingredient_parts[2:])
            adjusted_amount = round(amount * servings / old_servings, 2)
            ingredient_text = f'{adjusted_amount} {unit} {name}'
        except (ValueError, IndexError):
            pass  # Leave ingredient text unchanged if parsing fails
        ingredients.append(ingredient_text)

    directions = []
    directions_html = recipe_soup.find(class_='comp mntl-sc-block-group--OL mntl-sc-block mntl-sc-block-startgroup')
    for li in directions_html.find_all('li'):
        directions.append(li.text.replace('.', '--').strip())

    context = {
        'recipe_url': recipe_url,
        'stars_text': stars_text,
        'servings': servings,
        'ingredients': ingredients,
        'directions': directions,
        'recipe_title': recipe_title,
        'title': title,
        'source': source,
    }
    return render(request, 'recipelist/adjusted_search.html', context)


from django.contrib.sessions.backends.db import SessionStore




def search_store(request):
    query = request.GET.get('q', '')
    url = f"https://www.google.com/search?q={query} site:allrecipes.com"
    page = requests.get(url)
    soup = BeautifulSoup(page.content, 'html.parser')
    search_results = soup.find_all('a')

    recipe_url = None
    for link in search_results:
        link_url = link.get('href')
        if link_url.startswith('/url?q=https://www.allrecipes.com/recipe/') and 'search' not in link_url:
            recipe_url = link_url.split('&')[0][7:]
            break

    if not recipe_url:
        return render(request, 'search.html', {'error_message': 'No recipe found.'})

    recipe_page = requests.get(recipe_url)
    recipe_soup = BeautifulSoup(recipe_page.content, 'html.parser')

    recipe_title = soup.find("title").text
    title, source = recipe_title.split(":")


    recipe_details = recipe_soup.find('div', {'class': 'comp recipe-details mntl-recipe-details'})
    details_items = recipe_details.find_all('div', {'class': 'mntl-recipe-details__item'})

    for item in details_items:
        label = item.find('div', {'class': 'mntl-recipe-details__label'}).text.strip()
        if label == 'Servings:':
            servings = item.find('div', {'class': 'mntl-recipe-details__value'}).text.strip()
            break
    else:
        servings = None


    stars = recipe_soup.find(id='mntl-recipe-review-bar__rating_2-0')
    if stars:
        stars_text = f'{stars.text} -- Ingredients:  '
    else:
        stars_text = 'Could not find stars information.'

    ingredients = []
    ingredients_html = recipe_soup.find(class_='mntl-structured-ingredients__list')
    for li in ingredients_html.find_all('li'):
        ingredients.append(li.text.strip())

    directions = []
    directions_html = recipe_soup.find(class_='comp mntl-sc-block-group--OL mntl-sc-block mntl-sc-block-startgroup')
    for li in directions_html.find_all('li'):
        directions.append(li.text.replace('.', '--').strip())

    context = {
        'recipe_url': recipe_url,
        'stars_text': stars_text,
        'servings': servings,
        'ingredients': ingredients,
        'directions': directions,
        'recipe_title': recipe_title,
        'title':title,
        'source':source,
    }
    return render(request, 'recipelist/search.html', context)



import os

def grocery_list(request):
    if request.method == 'POST':
        selected_ingredients = request.POST.getlist('ingredient')
        request.session['selected_ingredients'] = selected_ingredients
        context = {'selected_ingredients': selected_ingredients}
        return render(request, 'recipelist/grocery_list.html', context)
    else:
        return render(request, 'recipelist/grocery_list.html')

import os



from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options


from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

import traceback
import time


def login_heb(request):
    if request.method == 'POST':
        url = "https://accounts.heb.com/interaction/gAB3qIjVSAmZeiNryFlSRw/login"

        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")

        # Set the PATH environment variable to include the directory of chromedriver
        chromedriver_path = 'projectrecipe/chromedriver'
        os.environ['PATH'] += os.pathsep + chromedriver_path

        driver = webdriver.Chrome(options=chrome_options)

        try:
            driver.get(url)
            time.sleep(2)

            # Wait for the login form to load
            wait = WebDriverWait(driver, 20)
            email_input = wait.until(EC.viisibility_of_element_located((By.XPATH, "//div[@class='form-group']//input[@id='email']")))



            email_input = wait.until(EC.presence_of_element_located((By.ID, "email")))
            password_input = wait.until(EC.presence_of_element_located((By.ID, "password")))
            submit_button = wait.until(EC.element_to_be_clickable((By.ID, "submit-button")))

            # Get the email and password from the form submission
            email = request.POST['email']
            password = request.POST['password']

            # Fill in the login form
            email_input.send_keys(email)
            password_input.send_keys(password)

            # Submit the form
            submit_button.click()

            # Wait for the login process to complete (you can customize the conditions)
            wait.until(EC.title_contains("Logged in"))

            # Your additional actions after successful login
            # ...

            return HttpResponse("Login completed successfully.")

        except Exception as e:
            # Handle any exceptions that occurred during the login process
            traceback.print_exc()
            return HttpResponse(f"Error occurred during login: {str(e)}")

        finally:
            # Quit the driver to release resources
            driver.quit()

    return HttpResponse("Invalid request method.")



    # ...























































































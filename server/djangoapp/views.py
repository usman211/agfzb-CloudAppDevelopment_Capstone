from django.shortcuts import render
from django.http import HttpResponseRedirect, HttpResponse
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404, render, redirect
from .models import CarModel, CarDealer
from .restapis import get_dealers_from_cf,get_dealer_by_id,get_dealer_by_id_from_cf,get_dealer_reviews_from_cf,post_request
from django.contrib.auth import login, logout, authenticate
from django.contrib import messages
from datetime import datetime
import logging
import json

# Get an instance of a logger
logger = logging.getLogger(__name__)


# Create your views here.


# Create an `about` view to render a static about page
def about(request):
    context = {}
    if request.method == 'GET':
        return render(request, 'djangoapp/about.html', context)


# Create a `contact` view to return a static contact page
def contact(request):
    context = {}
    if(request.method) == 'GET':
        return render(request,'djangoapp/contact.html',context)
# Create a `login_request` view to handle sign in request
def login_request(request):
    context = {}
    # Handles POST request
    if request.method == "POST":
        # Get username and password from request.POST dictionary
        username = request.POST['username']
        password = request.POST['psw']
        # Try to check if provide credential can be authenticated
        user = authenticate(username=username, password=password)
        if user is not None:
            # If user is valid, call login method to login current user
            login(request, user)
            return redirect('/djangoapp/')
        else:
            # If not, return to login page again
            return render(request, 'djangoapp/user_login.html', context)
    else:
        return render(request, 'djangoapp/user_login.html', context)

# Create a `logout_request` view to handle sign out request
def logout_request(request):
    # Get the user object based on session id in request
    print("Log out the user `{}`".format(request.user.username))
    # Logout user in the request
    logout(request)
    # Redirect user back to course list view
    return redirect('/djangoapp')

# Create a `registration_request` view to handle sign up request
def registration_request(request):
    context = {}
    # If it is a GET request, just render the registration page
    if request.method == 'GET':
        return render(request, 'djangoapp/registration.html', context)
    # If it is a POST request
    elif request.method == 'POST':
        # Get user information from request.POST
        username = request.POST['username']
        password = request.POST['psw']
        first_name = request.POST['firstname']
        last_name = request.POST['lastname']
        user_exist = False
        try:
            # Check if user already exists
            User.objects.get(username=username)
            user_exist = True
        except:
            # If not, simply log this is a new user
            logger.debug("{} is new user".format(username))
        # If it is a new user
        if not user_exist:
            # Create user in auth_user table
            user = User.objects.create_user(username=username, first_name=first_name, last_name=last_name,
                                            password=password)
            # Login the user and redirect to course list page
            login(request, user)
            return redirect("/djangoapp/")
        else:
            return render(request, 'djangoapp/registration.html', context)

# Update the `get_dealerships` view to render the index page with a list of dealerships
def get_dealerships(request):
    if request.method == "GET":
        url = "https://usman211-3000.theiadockernext-0-labs-prod-theiak8s-4-tor01.proxy.cognitiveclass.ai/dealerships/get"
        
        # Get dealers from the URL
        context = {
            "dealerships": get_dealers_from_cf(url),
        }
        return render(request, 'djangoapp/index.html', context)


# Create a `get_dealer_details` view to render the reviews of a dealer
def get_dealer_details(request,dealer_id):
     if request.method == "GET":
         context = {}
         dealer_url = "https://usman211-3000.theiadockernext-0-labs-prod-theiak8s-4-tor01.proxy.cognitiveclass.ai/dealerships/get"
         dealer = get_dealer_by_id_from_cf(dealer_url, id = dealer_id)
         context['dealer'] = dealer

         review_url = "https://usman211-5000.theiadockernext-0-labs-prod-theiak8s-4-tor01.proxy.cognitiveclass.ai/api/get_reviews"
         reviews = get_dealer_reviews_from_cf(review_url, id = dealer_id)
         context["reviews"] = reviews
         if not context["reviews"] :
            messages.warning(request, "There are no reviews at the moment !!!")   
         return render(request, 'djangoapp/dealer_details.html', context)


def get_dealer_details1(request, dealer_id):
     if request.method == "GET":
         context = {}
         dealer_url = "https://usman211-3000.theiadockernext-0-labs-prod-theiak8s-4-tor01.proxy.cognitiveclass.ai/dealerships/get"
         dealer = get_dealer_by_id(dealer_url, id=id)
         context['dealer'] = dealer
         if not context["dealer"] :
            messages.warning(request, "There are no dealer at the moment !!!")   
         return render(request, 'djangoapp/dealer_details.html', context)


        #  review_url = "https://usman211-5000.theiadockernext-1-labs-prod-theiak8s-4-tor01.proxy.cognitiveclass.ai/api/get_reviews"
        #  reviews = get_dealer_reviews_from_cf(review_url, id = id)
        #  context["reviews"] = reviews
        #  if not context["reviews"] :
        #     messages.warning(request, "There are no reviews at the moment !!!")   
        #  return render(request, 'djangoapp/dealer_details.html', context)

# Create a `add_review` view to submit a review
# def add_review(request, dealer_id):
def add_review(request, id):
    context = {}
    dealer_url = "https://usman211-3000.theiadockernext-0-labs-prod-theiak8s-4-tor01.proxy.cognitiveclass.ai/dealerships/get"
    
    # Get dealer information
    dealer = get_dealer_by_id_from_cf(dealer_url, id)
    context["dealer"] = dealer
    
    if request.method == 'GET':
        # Get cars for the dealer
        cars = CarModel.objects.all()
        context["cars"] = cars
        return render(request, 'djangoapp/add_review.html', context)
    
    elif request.method == 'POST':
        if request.user.is_authenticated:
            username = request.user.username
            car_id = request.POST.get("car")
            
            # Get car information
            car = CarModel.objects.get(pk=car_id)
        
            # Prepare payload for the review
            payload = {
                "dealership": id,
                "name": username,
                "purchase": request.POST.get("purchasecheck") == 'on',
                "review": request.POST.get("content"),
                "purchase_date": request.POST.get("purchasedate"),
                "car_make": car.car_make.name,
                "car_model": car.name,
                "car_year": int(car.year.strftime("%Y")),
                "id": id,
                "time": datetime.utcnow().isoformat()
            }
            
            # Prepare payload for the API request
            # new_payload = {"review": payload}
            review_post_url = "https://usman211-5000.theiadockernext-0-labs-prod-theiak8s-4-tor01.proxy.cognitiveclass.ai/api/post_review"
            
            # Make the POST request
            post_request(review_post_url, payload, id=id)
            
            return redirect("djangoapp:dealer_details", dealer_id=id)
        else:
            # Handle the case where the user is not authenticated
            messages.warning(request, "New review not added. Please log in to add a review !!")
            return redirect('djangoapp:index')


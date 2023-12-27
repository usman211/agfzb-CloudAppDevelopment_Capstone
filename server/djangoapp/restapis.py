import requests
import json
from .models import CarDealer, DealerReview
from requests.auth import HTTPBasicAuth
from ibm_watson import NaturalLanguageUnderstandingV1
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator
from ibm_watson.natural_language_understanding_v1 import Features, SentimentOptions
import os


# Create a `get_request` to make HTTP GET requests
def get_request(url, **kwargs):
    print(kwargs)
    print("GET from {} ".format(url))
    apikey = kwargs.get("apikey")
    try:
        if apikey:
            params = dict()
            params["text"] = kwargs.get("text")
            params["version"] = kwargs.get("version")
            params["features"] = kwargs.get("features")
            params["return_analyzed_text"] = kwargs.get("return_analyzed_text")
            
            response = requests.get(url, data=params, auth=HTTPBasicAuth('apikey', apikey), headers={'Content-Type': 'application/json'})
        else:
            # Call get method of requests library with URL and parameters
            response = requests.get(url, headers={'Content-Type': 'application/json'}, params=kwargs)
        
        # Check if the response contains valid JSON
        response.raise_for_status()  # This will raise an exception if the response status code is an HTTP error.
        json_data = response.json()
        return json_data
    except json.JSONDecodeError as e:
        print(f"Error in get_request: {e}")
        return None


# Create a `post_request` to make HTTP POST requests
# e.g., response = requests.post(url, params=kwargs, json=payload)
def post_request(url, json_payload, **kwargs):
    print(kwargs)
    print("Payload: ", json_payload, ". Params: ", kwargs)
    print("POST to {} ".format(url))
    apikey = kwargs.get("apikey")
    dealer_id = kwargs.get("id")
    
    try:
        if apikey:
            params = dict()
            params["text"] = kwargs.get("text")
            params["version"] = kwargs.get("version")
            params["features"] = kwargs.get("features")
            params["return_analyzed_text"] = kwargs.get("return_analyzed_text")
            
            response = requests.post(url + f"?id={dealer_id}", json=json_payload, data=params, auth=HTTPBasicAuth('apikey', apikey), headers={'Content-Type': 'application/json'})
        else:
            # Call post method of requests library with URL, JSON payload, and parameters
            params = kwargs.copy()
            params.pop("id", None)
            
            response = requests.post(url + f"?id={dealer_id}", json=json_payload, headers={'Content-Type': 'application/json'}, params=params)
        
        # Check if the response contains valid JSON
        response.raise_for_status()  # This will raise an exception if the response status code is an HTTP error.
        status_code = response.status_code
        print(f"With status {status_code}")
        json_data = response.json()
        return json_data
    except json.JSONDecodeError as e:
        print(f"Error in post_request: {e}")
        return None
        

# Create a get_dealers_from_cf method to get dealers from a cloud function
def get_dealers_from_cf(url, **kwargs):
    results = []
    state = kwargs.get("state")
    if state:
        json_result = get_request(url, state=state)
    else:
        json_result = get_request(url)

    print('json_result RESTAPIS', json_result)    

    if json_result:
        # Get the row list in JSON as dealers
        dealers = json_result

        # For each dealer object
        for dealer in dealers:
            # Get its content in `doc` object
            dealer_doc = dealer
            # print(dealer_doc)
            # Create a CarDealer object with values in `doc` object
            dealer_obj = CarDealer(address=dealer_doc["address"], city=dealer_doc["city"],
                                   id=dealer_doc["id"], lat=dealer_doc["lat"], long=dealer_doc["long"], full_name=dealer_doc["full_name"],
                                
                                   st=dealer_doc["st"], zip=dealer_doc["zip"],  short_name=dealer_doc["short_name"])
            results.append(dealer_obj)

    return results
# more functions


def get_dealer_by_state(url, dealer_state):
    # Call get_request with the dealer_id param
    json_result = get_request(url, dealer_state=dealer_state)

    # Create a CarDealer object from response
    dealer = json_result[0]
    dealer_obj = CarDealer(address=dealer["address"], city=dealer["city"], full_name=dealer["full_name"],
                           id=dealer["id"], lat=dealer["lat"], long=dealer["long"],
                           short_name=dealer["short_name"],
                           st=dealer["st"], zip=dealer["zip"])
    return dealer_obj

# Create a get_dealer_reviews_from_cf method to get reviews by dealer id from a cloud function
def get_dealer_by_id_from_cf(url, id):
    result = {}
    # Call get_request with a URL parameter
    json_result = get_request(url, id=id)
    if json_result:
        # Get the row list in JSON as dealers
        dealers = json_result
        #print("dealers :",dealers)  
        # For each dealer object
        dealer = dealers[0]
        print("dealer :",dealer)
        # Create a CarDealer object with values in `doc` object
        dealer_obj = CarDealer(address=dealer["address"], city=dealer["city"], full_name=dealer["full_name"],
                                id=dealer["id"], lat=dealer["lat"], long=dealer["long"],
                                short_name=dealer["short_name"],
                                st=dealer["st"], zip=dealer["zip"])
        result = dealer_obj
    return result



def get_dealer_by_id(url, id):
    # Call get_request with the dealer_id param
    json_result = get_request(url, dealer_id=id)

    # Create a CarDealer object from response
    dealer = json_result[0]
    dealer_obj = CarDealer(address=dealer["address"], city=dealer["city"], full_name=dealer["full_name"],
                           id=dealer["id"], lat=dealer["lat"], long=dealer["long"],
                           short_name=dealer["short_name"],
                           st=dealer["st"], zip=dealer["zip"])
    return dealer_obj


# Create an `analyze_review_sentiments` method to call Watson NLU and analyze text
# def analyze_review_sentiments(text):
# - Call get_request() with specified arguments
# - Get the returned sentiment label such as Positive or Negative
def get_dealer_reviews_from_cf(url, **kwargs):
    results = []
    id = kwargs.get("id")
    if id:
        json_result = get_request(url, id=id)
    else:
        json_result = get_request(url)
    print('json_result RESTAPIS', json_result)
    if json_result:
        reviews = json_result
        for dealer_review in reviews:
            review_obj = DealerReview(
                dealership=dealer_review.get("dealership"),
                name=dealer_review.get("name"),
                purchase=dealer_review.get("purchase"),
                review=dealer_review.get("review"),
                purchase_date=dealer_review.get("purchase_date"),
                car_make=dealer_review.get("car_make"),
                car_model=dealer_review.get("car_model"),
                car_year=dealer_review.get("car_year"),
                sentiment='',
                id=dealer_review.get("id")
            )
            sentiment = analyze_review_sentiments(review_obj.review)
            review_obj.sentiment = sentiment
            results.append(review_obj)
    return results


# def analyze_review_sentiments(dealer_review):
#     try:
#         # Attempt to retrieve API key and URL from environment variables
#         apikey = os.environ.get('LwG_yYL2rVwuc5eWGz6RAH9dx_KeZStH-mncDTWOB4FU')  # export APINLU="apikey_nlu" in terminal
#         url = os.environ.get('https://api.au-syd.natural-language-understanding.watson.cloud.ibm.com/instances/235f9b08-229d-41de-9014-445ee9ea2a35')  # export URLNLU="url_nlu" in terminal

#         # Check if API key and URL are available
#         if not apikey:
#             raise ValueError("LwG_yYL2rVwuc5eWGz6RAH9dx_KeZStH-mncDTWOB4FU")
#         if not url:
#             raise ValueError("https://api.au-syd.natural-language-understanding.watson.cloud.ibm.com/instances/235f9b08-229d-41de-9014-445ee9ea2a35")
        
#         authenticator = IAMAuthenticator(apikey)
#         natural_language_understanding = NaturalLanguageUnderstandingV1(
#             version='2022-04-07',
#             authenticator=authenticator
#         )

#         natural_language_understanding.set_service_url(url)

#         response = natural_language_understanding.analyze(
#             text=dealer_review,
#             language='en',
#             features=Features(sentiment=SentimentOptions(targets=[dealer_review]))
#         ).get_result()

#         print(json.dumps(response, indent=2))

#         return response["sentiment"]["document"]["label"]

#     except Exception as e:
#         # Handle any exceptions that may occur
#         print(f"Error in analyze_review_sentiments: {e}")
#         return None

def analyze_review_sentiments(text):
    url = ""
    api_key = ""
    authenticator = IAMAuthenticator(api_key)
    natural_language_understanding = NaturalLanguageUnderstandingV1(version='2021-08-01',authenticator=authenticator)
    natural_language_understanding.set_service_url(url)
    response = natural_language_understanding.analyze( text=text+"hello hello hello",features=Features(sentiment=SentimentOptions(targets=[text+"hello hello hello"]))).get_result()
    label=json.dumps(response, indent=2)
    label = response['sentiment']['document']['label']
    
    
    return(label)

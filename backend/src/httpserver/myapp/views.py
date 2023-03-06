import os
import math

import secrets
import hashlib

from django.http import JsonResponse
from django.http import HttpResponse
from httpserver.modules.database.BitdotioDB import BitdotioDB
from httpserver.modules.Constants import DB_USERS, DB_FRIENDS
from django.views.decorators.csrf import csrf_exempt

from httpserver.modules.api.ApiHandler import ApiHandler
from httpserver.modules.api.ApiExceptions import ExternalAPIError, NoRouteFound

token = 'BITIO_API_TOKEN'


@csrf_exempt
def post_create_user(request):
    """
    Handles the /create endpoint.
    """
    try:
        if request.method == 'POST':
            data = request.POST
            email = data['email']
            password = data['password']
            address = data['address']
            db = BitdotioDB(os.getenv(token))
            if len(db.db_query(f'SELECT email FROM {DB_USERS} WHERE email = \'{email}\'')) <= 0:
                salt = secrets.token_hex(4)
                hash_pw = hashlib.sha256((password + salt).encode('UTF-8')).hexdigest()
                db.db_query(f'INSERT INTO {DB_USERS} VALUES (\'{email}\', \'{hash_pw}\', \'{salt}\', \'{address}\')')
                return JsonResponse({'email': email, 'address': address})
            else:
                return JsonResponse({'error': 'Cannot make account with provided parameters'}, status=400)
        else:
            return HttpResponse(status=404)
    except:
        return HttpResponse(status=500)


def get_login_credentials(request):
    """
    Handles the /login endpoint.
    """
    try:
        if request.method == 'GET':
            data = request.GET
            email = data['email']
            password = data['password']
            db = BitdotioDB(os.getenv(token))
            if len(db.db_query(f'SELECT address FROM {DB_USERS} WHERE email = \'{email}\'')) <= 0:
                return JsonResponse({'error': 'Invalid login credentials'}, status=401)
            salt = db.db_query(f'SELECT salt FROM {DB_USERS} WHERE email = \'{email}\'')[0][0]
            hash_pw = hashlib.sha256((password + salt).encode('UTF-8')).hexdigest()
            address = db.db_query(f'SELECT address FROM {DB_USERS} '
                                  f'WHERE email = \'{email}\' '
                                  f'AND password = \'{hash_pw}\'')
            if len(address) <= 0:
                return JsonResponse({'error': 'Invalid login credentials'}, status=401)
            # otherwise login is successful, assemble information
            address = address[0][0]
            friend_list = db.db_query(f'SELECT {DB_USERS}.email, {DB_USERS}.address, '
                                      f'{DB_FRIENDS}.status FROM {DB_FRIENDS} '
                                      f'JOIN {DB_USERS} '
                                      f'ON {DB_USERS}.email = {DB_FRIENDS}.user2 '
                                      f'WHERE {DB_USERS}.email = \'{email}\' '
                                      f'AND ({DB_FRIENDS}.status = 0 OR {DB_FRIENDS}.status = 2) '
                                      f'UNION ALL '
                                      f'SELECT {DB_USERS}.email, {DB_USERS}.address, '
                                      f'{DB_FRIENDS}.status FROM {DB_FRIENDS} '
                                      f'JOIN {DB_USERS} '
                                      f'ON {DB_USERS}.email = {DB_FRIENDS}.user1 '
                                      f'WHERE {DB_USERS}.email = \'{email}\' '
                                      f'AND ({DB_FRIENDS}.status = 0 OR {DB_FRIENDS}.status = 1)')
            friends = []
            friend_reqs = []
            for friend_tuple in friend_list:
                if int(friend_tuple[2]) == 0:
                    friends.append({'email': friend_tuple[0], 'address': friend_tuple[1]})
                else:
                    friend_reqs.append({'email': friend_tuple[0], 'address': friend_tuple[1]})

            # TODO: implement bearer
            return JsonResponse({'bearer:': 'some_bearer',
                                 'user': {
                                     'email': email,
                                     'address': address
                                 },
                                 'friends': friends,
                                 'friend_reqs': friend_reqs
                                 })
    except:
        return HttpResponse(status=500)


STANDARD_N = 10
STANDARD_RADIUS = 200
def get_locations(request):
    """
    Handles the /locations endpoint.
    """
    try:
        if request.method == 'GET':
            data = request.GET
            users = data['users']
            db = BitdotioDB(os.getenv(token))

            # Step 1 - Get lat_long coords for each user by converting addresses
            handler = ApiHandler()
            lat_longs = []
            for email in users:
                address = db.db_query(f'SELECT address FROM {DB_USERS} WHERE email = \'{email}\'')
                if len(address) <= 0:
                    return JsonResponse({'error': 'One or more users does not exist'}, status=400)

                # We have the address, turn it into a lat long
                try:
                    lat_long = handler.convert(address)
                    if lat_long is not None:
                        lat_longs.append(lat_long)
                    else:
                        return JsonResponse({'error': 'One or more users have invalid addresses'}, status=400)
                except:
                    # TODO: Is this the correct thing to do in this situation?
                    return JsonResponse({'error': 'Issue with external API'}, status=502)
                    
            
            # Step 2 - Calculate the midpoint of the given coords
            midpoint = calculate_midpoint(lat_longs)

            # Step 3 - Find possible options surrounding the midpoint
            options = []
            try:
                options = handler.get_nearby_options(midpoint, STANDARD_RADIUS, STANDARD_N)
            except ValueError:
                return JsonResponse({'error': 'One or more users have invalid addresses'}, status=400)
            except ExternalAPIError:
                return JsonResponse({'error': 'Issue with external API'}, status=502)

            # Step 4 - Find user travel times to each location found
            times = []
            for i in range(len(options)):
                try:
                    # Store a backpointer to the specific location in case we have invalid routes
                    times.append((
                        i,
                        [handler.get_travel_time(options[i].get_lat_long(), lat_long) for lat_long in lat_longs]
                    ))
                except NoRouteFound:
                    # Pass for now - if at the end of this, we have any empty list we found no routes
                    pass
            if len(times) == 0:
                # We found no valid routes
                return JsonResponse({'error': 'No route found betwen given users'}, status=500)
            
            # Step 5 - Returns results
            return JsonResponse({
                'locations': [{
                    'place': options[time[0]].get_lat_long(),
                    'name': options[time[0]].get_name(),
                    'rating': -1,
                    'travel_times': time[1],
                } for time in times]
            })
        else:
            return HttpResponse(status=404)
    except:
        return HttpResponse(status=500)

def calculate_midpoint(lat_longs):
    """
    Given a list of lat long coords, finds the midpoint and returns it
    """
    x, y, z = 0.0, 0.0, 0.0
    for lat, long in lat_longs:
        x += math.cos(lat) * math.cos(long)
        y += math.cos(lat) * math.sin(long)
        z += math.sin(lat)
    
    x /= len(lat_longs)
    y /= len(lat_longs)
    z /= len(lat_longs)

    central_longitude = math.atan2(y, x)
    central_square_root = math.sqrt(x * x + y * y)
    central_latitude = math.atan2(z, central_square_root)

    return (math.degrees(central_latitude), math.degrees(central_longitude))

def get_friends(request):
    """
    Handles the /friends endpoint.
    """
    if request.method == 'GET':
        data = request.GET
    return HttpResponse('Thanks for submitting your data')


def get_user(request):
    """
    Handles the /user endpoint.
    """
    if request.method == 'GET':
        data = request.GET
    return HttpResponse('Thanks for submitting your data')


def post_friend_request(request):
    """
    Handles the /sendFriendReq endpoint.
    """
    if request.method == 'POST':
        data = request.POST
    return HttpResponse('Thanks for submitting your data')


def post_friend_request_response(request):
    """
    Handles the /respondFriendReq endpoint.
    """
    if request.method == 'POST':
        data = request.POST
    return HttpResponse('Thanks for submitting your data')

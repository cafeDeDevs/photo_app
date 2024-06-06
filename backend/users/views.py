import requests
import logging
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from django.conf import settings
from django.middleware.csrf import get_token
from django.contrib.auth.models import AnonymousUser
from django.contrib.auth import login
from django.views.decorators.csrf import csrf_protect

from social_django.utils import psa

from users.serializers import UserSerializer

# TODO: Add note of logger in a best_practices.md doc
logger = logging.getLogger(__name__)


# NOTE: Helper function for setting cookies (consider moving into separate file/Class)
def set_authentication_cookies(response, access_token, refresh_token, request):
    response.set_cookie(
        key='access_token',
        value=access_token,
        httponly=True,
        samesite='None',
        secure=True,
        path='/',
    )
    response.set_cookie(
        key='refresh_token',
        value=refresh_token,
        httponly=True,
        samesite='None',
        secure=True,
        path='/',
    )
    # NOTE: Sets the csrftoken as cookie by default
    get_token(request)
    return response


# NOTE: Currently somewhat of a hack using python's native requests lib,
# there is probably a better way using the social_auth.core
# TODO: This route's logic is getting too long,
# refactor into smaller helper functions
@api_view(['POST'])
@permission_classes([AllowAny])
@psa()
def register_by_access_token(request, backend):
    code = request.data.get('code')
    if not code:
        logger.warning("Request does not have OAuth code")
        return Response({'error': 'No OAuth code provided.'},
                        status=status.HTTP_400_BAD_REQUEST)
    try:
        # NOTE: Consider moving these settings into separate file/Class
        token_url = 'https://www.googleapis.com/oauth2/v4/token'
        data = {
            'code': code,
            'client_id': settings.SOCIAL_AUTH_GOOGLE_OAUTH2_KEY,
            'client_secret': settings.SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET,
            'redirect_uri': settings.SOCIAL_AUTH_GOOGLE_OAUTH2_REDIRECT_URI,
            'grant_type': 'authorization_code'
        }

        response = requests.post(token_url, data=data)

        if response.status_code != 200:
            return Response({'error': 'Failed to get tokens from Google.'},
                            status=response.status_code)

        tokens = response.json()
        access_token = tokens.get('access_token')
        # TODO: refresh_token should be set in key/value store (i.e. redis cache)
        # and used to grab new access_token when access_token is expired
        # TODO: refresh_token could not exist, handle exception, but don't return
        refresh_token = tokens.get('refresh_token')
        user = request.backend.do_auth(access_token)

        if user:
            # NOTE: Temporary demonstration of "sign up" logic,
            # Uses Django REST framework serializers to save user to DB
            # TODO: We Need an Onboarding Process that establishes
            # the user_name (user chooses username)
            user_data = {
                'user_name': user.email,
                'user_email': user.email,
            }

            serializer = UserSerializer(data=user_data)
            existing_user = serializer.get_user_by_email(  # type:ignore
                data=user_data)
            if existing_user is not None:
                res = Response(
                    {
                        'msg':
                        'Sign Up Failed. User Already Exists. Please Login.'
                    },
                    status=status.HTTP_409_CONFLICT)
                logger.warning(
                    "%s attempted to sign up, but already has account",
                    user.email)
                return res
            if serializer.is_valid():
                serializer.save()

            token, _ = Token.objects.get_or_create(user=user)  # type:ignore
            # NOTE: Sets sessionid cookie, is necessary??
            # TODO: Investigate Django login() method more
            login(request, user)
            res = Response(
                {'msg': 'User Authenticated, setting credentials'},
                status=status.HTTP_200_OK,
            )
            res = set_authentication_cookies(res, token.key, refresh_token,
                                             request)

            logger.info("%s successful signed up", user.email)
            return res
        else:
            logger.warning("python social auth unable to authenticate user")
            return Response(
                {'error': 'User Not Found By OAuth Code'},
                status=status.HTTP_400_BAD_REQUEST,
            )
    except Exception as e:
        logger.error("%s Uncaught Exception Error:", str(e))
        return Response({'error': str(e)},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR)





# ! PAUL

@api_view(['POST'])
@permission_classes([AllowAny])
@psa()
def login_by_access_token(request, backend):
    code = request.data.get('code')
    if not code:
        logger.warning("Request does not have OAuth code")
        return Response({'error': 'No OAuth code provided.'},
                        status=status.HTTP_400_BAD_REQUEST)
    try:
        # NOTE: Consider moving these settings into separate file/Class
        token_url = 'https://www.googleapis.com/oauth2/v4/token'
        data = {
            'code': code,
            'client_id': settings.SOCIAL_AUTH_GOOGLE_OAUTH2_KEY,
            'client_secret': settings.SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET,
            'redirect_uri': settings.SOCIAL_AUTH_GOOGLE_OAUTH2_REDIRECT_URI,
            'grant_type': 'authorization_code'
        }

        response = requests.post(token_url, data=data)

        if response.status_code != 200:
            return Response({'error': 'Failed to get tokens from Google.'},
                            status=response.status_code)

        tokens = response.json()
        access_token = tokens.get('access_token')
        # TODO: refresh_token should be set in key/value store (i.e. redis cache)
        # and used to grab new access_token when access_token is expired
        # TODO: refresh_token could not exist, handle exception, but don't return
        refresh_token = tokens.get('refresh_token')
        user = request.backend.do_auth(access_token)

        if user:
            # NOTE: Temporary demonstration of "sign up" logic,
            # Uses Django REST framework serializers to save user to DB
            # TODO: We Need an Onboarding Process that establishes
            # the user_name (user chooses username)
            user_data = {
                'user_name': user.email,
                'user_email': user.email,
            }

            serializer = UserSerializer(data=user_data)
            existing_user = serializer.get_user_by_email(  # type:ignore
                data=user_data)
            if existing_user is not None:
                res = Response(
                    {
                        'msg':
                        'Sign Up Failed. User Already Exists. Please Login.'
                    },
                    status=status.HTTP_409_CONFLICT)
                logger.warning(
                    "%s attempted to sign up, but already has account",
                    user.email)
                return res
            if serializer.is_valid():
                serializer.save()

            token, _ = Token.objects.get_or_create(user=user)  # type:ignore
            # NOTE: Sets sessionid cookie, is necessary??
            # TODO: Investigate Django login() method more
            login(request, user)

            # ! PAUL 
            res = Response(
                {'msg': 'User Logged In.'},
                status=status.HTTP_200_OK,
            )
            res = set_authentication_cookies(res, token.key, refresh_token,
                                             request)

            logger.info("%s successful signed up", user.email)
            return res
        else:
            logger.warning("python social auth unable to find user")
            return Response(
                {'error': 'User Not Found in Database'},
                status=status.HTTP_401_UNAUTHORIZED,
            )
    except Exception as e:
        logger.error("%s Uncaught Exception Error:", str(e))
        return Response({'error': str(e)},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# TODO: redirect to get new access_token if access_token is expired via refresh_token
@api_view(['POST'])
@csrf_protect
def authentication_test(request):
    if isinstance(request.user, AnonymousUser):
        logger.warning("User attempted to login as AnonymousUser")
        return Response(
            {"error": "Access forbidden. You are not authenticated."},
            status=status.HTTP_401_UNAUTHORIZED)

    logger.info("%s successful authenticated", request.user)
    return Response(
        {'message': "User successfully authenticated"},
        status=status.HTTP_200_OK,
    )

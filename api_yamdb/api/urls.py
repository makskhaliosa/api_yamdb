from django.urls import path, include
from rest_framework.routers import SimpleRouter

from .views import (
    ReviewViewSet, UserViewSet, UserMeViewSet, GenreViewSets,
    CategoryViewSets, CommentViewSet, TitleViewSets,
    sign_up, token_obtain)

name = 'api'

router = SimpleRouter()

router.register(r'users', UserViewSet)
router.register(r'titles/(?P<title_id>\d+)/reviews',
                ReviewViewSet, basename='review')
router.register(r'titles/(?P<title_id>\d+)/reviews/'
                r'(?P<review_id>\d+)/comments',
                CommentViewSet, basename='comment')
router.register(r'categories', CategoryViewSets)
router.register(r'genres', GenreViewSets)
router.register(r'titles', TitleViewSets)


urlpatterns = [
    path('auth/signup/', sign_up, name='sign_up'),
    path('auth/token/', token_obtain, name='token_obtain'),
    path(
        'users/me/',
        UserMeViewSet.as_view(
            {'get': 'retrieve', 'patch': 'partial_update'}),
        name='user_me'),
    path('', include(router.urls)),
]

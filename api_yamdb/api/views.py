from rest_framework import viewsets, status, mixins
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework.decorators import api_view, permission_classes
from rest_framework_simplejwt.tokens import RefreshToken
from django.shortcuts import get_object_or_404
from rest_framework import viewsets
from rest_framework.filters import SearchFilter
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.pagination import LimitOffsetPagination
from django.core.mail import send_mail
from django.contrib.auth import get_user_model
from django_filters.rest_framework import DjangoFilterBackend

from reviews.models import (Title,
                            Review,
                            Category,
                            Genre,
                            Comment)
from users.models import JWTToken
from .serializers import (CategorySerializer,
                          TitleSerializer,
                          SignupSerializer,
                          AdminUserSerializer,
                          UserMeSerializer,
                          UserTokenSerializer,
                          ReviewSerializer,
                          CommentSerializer,
                          GenreSerializer)
from .permissions import (AuthorModeratorAdminOrReadOnly,
                          IsAdmin,
                          AdminOrRead,
                          AdminOrGetList)
from .core.utils import generate_code
from .filters import TitleFilter
from .filters import TitleFilter


User = get_user_model()


class CategoryViewSets(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = (AdminOrGetList,)
    pagination_class = LimitOffsetPagination
    filter_backends = (SearchFilter,)
    search_fields = ('name',)
    lookup_field = 'slug'

    def retrieve(self, request, *args, **kwargs):
        if request.method == 'GET':
            msg = {"error": f'Метод {request.method} не доступен.'}
            return Response(
                data=msg, status=status.HTTP_405_METHOD_NOT_ALLOWED)
        return super().update(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        if request.method == 'PATCH':
            msg = {"error": f'Метод {request.method} не доступен.'}
            return Response(
                data=msg, status=status.HTTP_405_METHOD_NOT_ALLOWED)
        return super().update(request, *args, **kwargs)


class TitleViewSets(viewsets.ModelViewSet):
    queryset = Title.objects.all()
    serializer_class = TitleSerializer
    permission_classes = (AdminOrRead,)
    pagination_class = LimitOffsetPagination
    filter_backends = (DjangoFilterBackend,)
    filterset_class = TitleFilter


class ReviewViewSet(viewsets.ModelViewSet):
    queryset = Review.objects.all()
    serializer_class = ReviewSerializer
    permission_classes = (AuthorModeratorAdminOrReadOnly,)
    pagination_class = LimitOffsetPagination

    def get_queryset(self):
        title_id = self.kwargs.get('title_id')
        return Review.objects.filter(title=title_id)

    def perform_create(self, serializer):
        title = get_object_or_404(Title, id=self.kwargs.get('title_id'))
        serializer.save(author=self.request.user, title=title)


class CommentViewSet(viewsets.ModelViewSet):
    serializer_class = CommentSerializer
    permission_classes = (AuthorModeratorAdminOrReadOnly,)
    pagination_class = LimitOffsetPagination

    def get_queryset(self):
        review = self.kwargs.get('review_id')
        return Comment.objects.filter(review=review)

    def perform_create(self, serializer):
        review = get_object_or_404(Review, id=self.kwargs.get('review_id'))
        title = get_object_or_404(Title, id=self.kwargs.get('title_id'))
        serializer.save(author=self.request.user, review=review, title=title)


class GenreViewSets(viewsets.ModelViewSet):
    queryset = Genre.objects.all()
    serializer_class = GenreSerializer
    queryset = Genre.objects.all()
    permission_classes = (AdminOrGetList,)
    pagination_class = LimitOffsetPagination
    filter_backends = (SearchFilter,)
    search_fields = ('name',)
    lookup_field = 'slug'

    def retrieve(self, request, *args, **kwargs):
        if request.method == 'GET':
            msg = {"error": f'Метод {request.method} не доступен.'}
            return Response(
                data=msg, status=status.HTTP_405_METHOD_NOT_ALLOWED)
        return super().update(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        if request.method == 'PATCH':
            msg = {"error": f'Метод {request.method} не доступен.'}
            return Response(
                data=msg, status=status.HTTP_405_METHOD_NOT_ALLOWED)
        return super().update(request, *args, **kwargs)


class UserViewSet(viewsets.ModelViewSet):
    """Создание, редактирование и удаление пользователя администратором."""
    serializer_class = AdminUserSerializer
    queryset = User.objects.all()
    permission_classes = (IsAdmin,)
    filter_backends = (SearchFilter,)
    search_fields = ('username',)
    lookup_field = 'username'
    lookup_value_regex = r'[\w.@+-]+'

    def update(self, request, *args, **kwargs):
        if request.method == 'PUT':
            msg = {"error": f'Метод {request.method} не доступен.'}
            return Response(
                data=msg, status=status.HTTP_405_METHOD_NOT_ALLOWED)
        return super().update(request, *args, **kwargs)


class UserMeViewSet(viewsets.GenericViewSet, mixins.RetrieveModelMixin,
                    mixins.UpdateModelMixin):
    """Самостоятельное получение и обновление данных о пользователе."""
    def retrieve(self, request, pk=None):
        user = get_object_or_404(User, username=request.user.username)
        serializer = UserMeSerializer(user)
        return Response(data=serializer.data, status=status.HTTP_200_OK)

    def partial_update(self, request, pk=None):
        user = get_object_or_404(User, username=request.user.username)
        serializer = UserMeSerializer(
            instance=user, data=request.data, partial=True)
        if serializer.is_valid():
            instance = serializer.instance
            data = serializer.validated_data
            instance.first_name = data.get('first_name', instance.first_name)
            instance.last_name = data.get('last_name', instance.last_name)
            instance.bio = data.get('bio', instance.bio)
            serializer.save()
            return Response(data=serializer.data, status=status.HTTP_200_OK)
        return Response(
            data=serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes(permission_classes=[AllowAny])
def sign_up(request):
    """
    Самостоятельная регистрация новых пользователей и получение кода на почту.
    """
    if request.method == 'POST':
        username = request.data.get('username')
        to_email = request.data.get('email')
        if not username or not to_email:
            msg = {
                'username': ['Поле "username" обязательно для заполнения.'],
                'email': ['Поле "email" обязательно для заполнения.']
            }
            return Response(data=msg, status=status.HTTP_400_BAD_REQUEST)
        if not User.objects.filter(username=username).exists():
            serializer = SignupSerializer(data=request.data)
        else:
            user = get_object_or_404(User, username=username)
            serializer = SignupSerializer(instance=user, data=request.data)
            if user.email != to_email:
                msg = {
                    'email':
                    [
                        'Введен неверный адрес электронной почты. '
                        'Проверь данные или зарегистрируйся.'
                    ]
                }
                return Response(data=msg, status=status.HTTP_400_BAD_REQUEST)
        if serializer.is_valid():
            to_email = serializer.validated_data['email']
            code = generate_code()
            msg = ('Привет! Воспользуйся, пожалуйста, '
                   f'этим кодом для получения токена {code}')
            send_mail(
                subject='Код-подтверждение',
                message=msg,
                from_email='example@mail.ru',
                recipient_list=[to_email],
                fail_silently=False
            )
            serializer.save(confirmation_code=code)
            return Response(data=serializer.data, status=status.HTTP_200_OK)
        return Response(
            data=serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes(permission_classes=[AllowAny])
def token_obtain(request):
    """Получение токена пользователем."""
    if request.method == 'POST':
        username = request.data.get('username')
        confirmation_code = request.data.get('confirmation_code')
        if not username or not confirmation_code:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        user = get_object_or_404(User, username=username)
        serializer = UserTokenSerializer(
            instance=user, data=request.data)
        code = user.confirmation_code
        if code != confirmation_code:
            msg = {'confirmation_code': 'Введен неверный код =('}
            return Response(data=msg, status=status.HTTP_400_BAD_REQUEST)
        if serializer.is_valid():
            token_pair = RefreshToken.for_user(user)
            if JWTToken.objects.filter(user=user).exists():
                JWTToken.objects.filter(user=user).delete()
            JWTToken.objects.create(
                key=str(token_pair.access_token), user=user)
            user.confirmation_code = ''
            serializer.save()
            return Response(
                data=serializer.data, status=status.HTTP_200_OK)
        return Response(
            data=serializer.errors, status=status.HTTP_400_BAD_REQUEST)

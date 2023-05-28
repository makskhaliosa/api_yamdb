import re
from datetime import datetime

from rest_framework import serializers
from django.core.exceptions import ValidationError
from django.db.models import Avg
from rest_framework.relations import SlugRelatedField, PrimaryKeyRelatedField
from rest_framework.serializers import HiddenField

from users.models import User
from reviews.models import Review, Comment, Title, Category, Genre, TitleGenre


class CategorySerializer(serializers.ModelSerializer):

    class Meta:
        model = Category
        fields = ('name', 'slug')
        fields = ('name', 'slug')


class GenreSerializer(serializers.ModelSerializer):

    class Meta:
        model = Genre
        fields = ('name', 'slug')


class GenreField(serializers.SlugRelatedField):
    def to_representation(self, obj):
        serializer = GenreSerializer(obj)
        return serializer.data


class CategoryField(serializers.SlugRelatedField):
    def to_representation(self, obj):
        serializer = CategorySerializer(obj)
        return serializer.data


class TitleSerializer(serializers.ModelSerializer):
    rating = serializers.SerializerMethodField()
    genre = GenreField(
        slug_field='slug',
        queryset=Genre.objects.all(),
        many=True,
        required=True)
    category = CategoryField(
        slug_field='slug',
        queryset=Category.objects.all(),
        required=True
    )
    year = serializers.IntegerField(required=True)

    class Meta:
        model = Title
        fields = (
            'id', 'name', 'year', 'rating', 'description', 'genre', 'category'
        )

    def get_rating(self, obj):
        if Review.objects.filter(title_id=obj.id).exists():
            score = Review.objects.filter(
                title_id=obj.id).aggregate(Avg('score'))
            return score['score__avg']
        return None

    def validate(self, data):
        if not data.get('year'):
            return data
        if data.get('year') > datetime.now().year:
            raise ValidationError(
                'Год выпуска произведения не может быть в будущем.')
        return data

    def create(self, validated_data):
        genres = validated_data.pop('genre')
        title = Title.objects.create(**validated_data)
        for genre in genres:
            TitleGenre.objects.create(title=title, genre=genre)
        return title


class SignupSerializer(serializers.ModelSerializer):
    def validate(self, data):
        username = data['username']
        prog = re.compile(r'^[\w.@+-]+\Z', re.ASCII)
        result = prog.match(username)
        if not result:
            raise ValidationError(
                'Введи корректное имя пользователя. Можно использовать '
                'только латинские буквы, цифры и символы "@/./+/-/_" .')
        if username == 'me':
            raise ValidationError(
                'Придумай другое имя пользователя, это уже занято.')
        return data

    class Meta:
        model = User
        fields = ('username', 'email')


class UserTokenSerializer(serializers.ModelSerializer):
    token = serializers.SlugRelatedField(
        slug_field='key',
        read_only=True
    )

    class Meta:
        model = User
        fields = ('token',)


class AdminUserSerializer(serializers.ModelSerializer):
    def validate(self, data):
        username = data.get('username')
        if not username:
            return data
        prog = re.compile(r'^[\w.@+-]+\Z', re.ASCII)
        result = prog.match(username)
        if not result:
            raise ValidationError(
                'Введи корректное имя пользователя. Можно использовать '
                'только латинские буквы, цифры и символы "@/./+/-/_" .')
        if username == 'me':
            raise ValidationError(
                'Придумай другое имя пользователя, это уже занято.')
        return data

    class Meta:
        model = User
        fields = (
            'username', 'email', 'first_name', 'last_name', 'bio', 'role')


class UserMeSerializer(serializers.ModelSerializer):
    def validate(self, data):
        username = data.get('username')
        if not username:
            return data
        prog = re.compile(r'^[\w.@+-]+\Z', re.ASCII)
        result = prog.match(username)
        if not result:
            raise ValidationError(
                'Введи корректное имя пользователя. Можно использовать '
                'только латинские буквы, цифры и символы "@/./+/-/_" .')
        if username == 'me':
            raise ValidationError(
                'Придумай другое имя пользователя, это уже занято.')
        return data

    class Meta:
        model = User
        fields = (
            'username', 'email', 'first_name', 'last_name', 'bio', 'role')
        read_only_fields = ('role',)


class ReviewSerializer(serializers.ModelSerializer):
    author = SlugRelatedField(read_only=True,
                              slug_field='username',
                              default=serializers.CurrentUserDefault())
    title = HiddenField(default=None)

    def get_title(self, obj):
        return self.context['title']

    class Meta:
        fields = '__all__'
        model = Review

    def validate(self, data):
        super().validate(data)
        if self.context['request'].method == 'POST':
            user = self.context['request'].user
            title_id = (
                self.context['request'].parser_context['kwargs']['title_id'])
            if Review.objects.filter(author=user, title__id=title_id).exists():
                raise serializers.ValidationError(
                    'Duplicated review')
            return data
        return data


class CommentSerializer(serializers.ModelSerializer):
    author = SlugRelatedField(read_only=True, slug_field='username',
                              default=serializers.CurrentUserDefault())
    review = PrimaryKeyRelatedField(read_only=True)
    title = PrimaryKeyRelatedField(read_only=True)

    class Meta:
        fields = '__all__'
        model = Comment

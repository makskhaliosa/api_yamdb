"""
Этот скрипт написан для преобразования
данных из *.csv файлов в записи db.sqlite3
"""
import csv
import os
import logging

from django.conf import settings
from django.core.management.base import BaseCommand

from reviews.models import (
    Category, Comment, Genre, Review, Title, TitleGenre, User
)

DATA_PATH = os.path.join(settings.BASE_DIR, 'static/data')

FILES_MODELS = {
    'users.csv': User,
    'category.csv': Category,
    'genre.csv': Genre,
    'titles.csv': Title,
    'genre_title.csv': TitleGenre,
    'review.csv': Review,
    'comments.csv': Comment,
}


class Command(BaseCommand):

    def handle(self, *args, **kwargs):
        for file_name in FILES_MODELS:
            file_path = os.path.join(DATA_PATH, file_name)
            model = FILES_MODELS.get(file_name)

            with open(file_path, mode='r') as f:
                reader = csv.DictReader(f)

                for row in reader:
                    category = row.get('category')
                    author = row.get('author')
                    pub_date = row.get('pub_date')

                    if category:
                        row['category'] = (Category.objects.get(pk=category))
                    if author:
                        row['author'] = User.objects.get(id=author)
                    if pub_date:
                        row.pop('pub_date')

                    try:
                        logging.info(model.objects.get_or_create(**row))
                    except Exception:
                        logging.error(file_path, model, row, exc_info=True)

import csv
from django.conf import settings
from django.core.management.base import BaseCommand
from recipes.models import Ingredient


def import_data():
    with open(
        f'{settings.BASE_DIR}/data/ingredients.csv', encoding='utf-8'
    ) as csvfile:
        reader = csv.DictReader(csvfile)
        ingredients = [Ingredient(**row) for row in reader]

        Ingredient.objects.bulk_create(ingredients)


class Command(BaseCommand):
    help = 'Import Ingredients data from a CSV file into the Ingredients model'

    def handle(self, *args, **options):
        import_data()
        self.stdout.write(self.style.SUCCESS('Data imported successfully'))

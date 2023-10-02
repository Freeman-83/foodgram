import csv
from django.conf import settings
from django.core.management.base import BaseCommand
from recipes.models import Ingredient


def import_data():
    with open(
        f'{settings.BASE_DIR}/data/ingredients.csv', encoding='utf-8'
    ) as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            Ingredient.objects.create(
                name=row['name'],
                measurement_unit=row['measurement_unit']
            )


class Command(BaseCommand):
    help = 'Import Ingredients data from a CSV file into the Ingredients model'

    def handle(self, *args, **options):
        import_data()
        self.stdout.write(self.style.SUCCESS('Data imported successfully'))

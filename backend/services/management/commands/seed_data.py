from django.core.management.base import BaseCommand
from decimal import Decimal
from datetime import date, timedelta


class Command(BaseCommand):
    help = 'Seed initial data for the pricing system'

    def handle(self, *args, **options):
        self._seed_currencies()
        self._seed_academic_levels()
        self._seed_service_types()
        self._seed_deadlines()
        self._seed_price_config()
        self._seed_pricing_seasons()
        self._seed_exchange_rates()
        self.stdout.write(self.style.SUCCESS('All seed data created successfully!'))

    def _seed_currencies(self):
        from currencies.models import Currency
        currencies = [
            ('GBP', 'British Pound', '£', True),
            ('USD', 'US Dollar', '$', False),
            ('CAD', 'Canadian Dollar', 'CA$', False),
            ('AUD', 'Australian Dollar', 'A$', False),
        ]
        for code, name, symbol, is_base in currencies:
            Currency.objects.get_or_create(
                code=code,
                defaults={'name': name, 'symbol': symbol, 'is_base': is_base}
            )
        self.stdout.write(f'  Seeded {len(currencies)} currencies')

    def _seed_academic_levels(self):
        from services.models import AcademicLevel
        levels = [
            ('High School', 'high-school', 0.80, 1),
            ('Undergraduate', 'undergraduate', 1.00, 2),
            ("Master's", 'masters', 1.40, 3),
            ('PhD', 'phd', 1.80, 4),
        ]
        for name, slug, mult, order in levels:
            AcademicLevel.objects.get_or_create(
                slug=slug,
                defaults={'name': name, 'multiplier': Decimal(str(mult)), 'order': order}
            )
        self.stdout.write(f'  Seeded {len(levels)} academic levels')

    def _seed_service_types(self):
        from services.models import ServiceType
        services = [
            ('Essay Writing', 'essay-writing', 15.00, 1),
            ('Research Paper', 'research-paper', 18.00, 2),
            ('Report Writing', 'report-writing', 16.00, 3),
            ('Case Study', 'case-study', 19.00, 4),
            ('Research Proposal', 'research-proposal', 22.00, 5),
            ('Literature Review', 'literature-review', 20.00, 6),
            ('Dissertation Support', 'dissertation-support', 28.00, 7),
            ('Thesis Writing', 'thesis-writing', 30.00, 8),
            ('Editing & Proofreading', 'editing-proofreading', 10.00, 9),
            ('Admission Essay', 'admission-essay', 20.00, 10),
            ('Annotated Bibliography', 'annotated-bibliography', 14.00, 11),
            ('Coursework', 'coursework', 15.00, 12),
            ('Lab Report', 'lab-report', 17.00, 13),
            ('Reflective Journal', 'reflective-journal', 14.00, 14),
            ('Programming Assignment', 'programming-assignment', 25.00, 15),
            ('Data Analysis', 'data-analysis', 24.00, 16),
        ]
        for name, slug, price, order in services:
            ServiceType.objects.get_or_create(
                slug=slug,
                defaults={'name': name, 'base_price_per_page': Decimal(str(price)), 'order': order}
            )
        self.stdout.write(f'  Seeded {len(services)} service types')

    def _seed_deadlines(self):
        from pricing.models import DeadlineMultiplier
        deadlines = [
            ('14 days', 14, 1.00, 1),
            ('7 days', 7, 1.20, 2),
            ('5 days', 5, 1.35, 3),
            ('3 days', 3, 1.60, 4),
            ('48 hours', 2, 1.85, 5),
            ('24 hours', 1, 2.20, 6),
            ('12 hours', 0.5, 2.80, 7),
            ('6 hours', 0.25, 3.50, 8),
        ]
        for name, days, mult, order in deadlines:
            DeadlineMultiplier.objects.get_or_create(
                days=days,
                defaults={'name': name, 'multiplier': Decimal(str(mult)), 'order': order}
            )
        self.stdout.write(f'  Seeded {len(deadlines)} deadline multipliers')

    def _seed_price_config(self):
        from pricing.models import PriceConfig
        PriceConfig.objects.get_or_create(
            name='Default',
            defaults={'words_per_page': 275, 'base_currency': 'GBP', 'is_active': True}
        )
        self.stdout.write('  Seeded price config')

    def _seed_pricing_seasons(self):
        from pricing.models import PricingSeason
        today = date.today()
        year = today.year
        seasons = [
            ('Normal', 'normal', date(year, 1, 1), date(year, 10, 31), 1.00),
            ('November Peak', 'november_peak', date(year, 11, 1), date(year, 11, 30), 1.15),
            ('December Peak', 'december_peak', date(year, 12, 1), date(year, 12, 31), 1.25),
            ('January Peak', 'january_peak', date(year + 1, 1, 1), date(year + 1, 1, 31), 1.20),
        ]
        for name, stype, start, end, mult in seasons:
            PricingSeason.objects.get_or_create(
                name=name,
                defaults={
                    'season_type': stype,
                    'start_date': start,
                    'end_date': end,
                    'global_multiplier': Decimal(str(mult)),
                }
            )
        self.stdout.write(f'  Seeded {len(seasons)} pricing seasons')

    def _seed_exchange_rates(self):
        from currencies.services import fetch_exchange_rates
        rates = fetch_exchange_rates('GBP')
        self.stdout.write(f'  Seeded exchange rates: {rates}')

from decimal import Decimal
from django.utils import timezone


class PricingEngine:
    """Calculates estimated price for a quotation based on service, level, pages, deadline, and season."""

    @staticmethod
    def calculate(service_type, academic_level, pages, deadline, target_currency_code='GBP'):
        from services.models import ServiceType, AcademicLevel
        from pricing.models import DeadlineMultiplier, PricingSeason, PriceConfig
        from currencies.models import Currency, ExchangeRate

        # Get the active price config
        config = PriceConfig.get_active()
        words_per_page = config.words_per_page
        base_currency = config.base_currency

        # Get service base price
        base_price = Decimal(str(service_type.base_price_per_page))

        # Apply academic level multiplier
        level_multiplier = Decimal(str(academic_level.multiplier))

        # Apply deadline multiplier
        deadline_multiplier = Decimal(str(deadline.multiplier))

        # Get current pricing season
        current_season = PricingSeason.get_current()
        season_multiplier = Decimal('1.00')
        season_name = 'Normal'
        if current_season:
            season_multiplier = Decimal(str(current_season.global_multiplier))
            season_name = current_season.name

        # Calculate base price (in base currency)
        pages_decimal = Decimal(str(pages))
        calculated_base = base_price * pages_decimal * level_multiplier * deadline_multiplier * season_multiplier

        # Round to 2 decimal places
        calculated_base = calculated_base.quantize(Decimal('0.01'))

        # Convert to target currency
        target_currency = Currency.objects.filter(code=target_currency_code, is_active=True).first()
        if not target_currency:
            target_currency = Currency.objects.filter(code=base_currency).first() or Currency.objects.first()

        exchange_rate = Decimal('1.00')
        if target_currency_code != base_currency:
            rate = ExchangeRate.get_latest_rate(base_currency, target_currency_code)
            if rate:
                exchange_rate = Decimal(str(rate))
            else:
                # Fallback: try reverse
                reverse_rate = ExchangeRate.get_latest_rate(target_currency_code, base_currency)
                if reverse_rate:
                    exchange_rate = (Decimal('1.0') / Decimal(str(reverse_rate))).quantize(Decimal('0.000001'))

        final_price = (calculated_base * exchange_rate).quantize(Decimal('0.01'))

        return {
            'base_price': calculated_base,
            'final_price': final_price,
            'base_currency': base_currency,
            'target_currency': target_currency.code if target_currency else target_currency_code,
            'currency_symbol': target_currency.symbol if target_currency else '£',
            'exchange_rate': exchange_rate,
            'pricing_season': season_name,
            'season_multiplier': float(season_multiplier),
            'level_multiplier': float(level_multiplier),
            'deadline_multiplier': float(deadline_multiplier),
            'words_per_page': words_per_page,
            'total_words': pages * words_per_page,
            'estimated': True,
            'note': 'This is an estimated quotation. Final pricing may vary based on scope and requirements.',
        }

import requests
from decimal import Decimal
from django.utils import timezone
from datetime import timedelta
from decouple import config


EXCHANGE_RATE_API_KEY = config('EXCHANGE_RATE_API_KEY', default='')
EXCHANGE_RATE_API_URL = config('EXCHANGE_RATE_API_URL', default='https://v6.exchangerate-api.com/v6')
CACHE_DURATION_HOURS = 12


def fetch_exchange_rates(base_currency='GBP'):
    """Fetch exchange rates from API and cache in database."""
    from .models import ExchangeRate

    if not EXCHANGE_RATE_API_KEY:
        return _get_fallback_rates(base_currency)

    url = f"{EXCHANGE_RATE_API_URL}/{EXCHANGE_RATE_API_KEY}/latest/{base_currency}"
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        data = resp.json()

        if data.get('result') != 'success':
            return _get_fallback_rates(base_currency)

        rates = data.get('conversion_rates', {})
        expires_at = timezone.now() + timedelta(hours=CACHE_DURATION_HOURS)

        target_currencies = ['USD', 'GBP', 'CAD', 'AUD']
        saved_rates = {}

        for code in target_currencies:
            if code in rates:
                rate_obj, _ = ExchangeRate.objects.update_or_create(
                    base_currency=base_currency,
                    target_currency=code,
                    defaults={
                        'rate': Decimal(str(rates[code])),
                        'expires_at': expires_at,
                        'api_source': 'exchangerate-api',
                    }
                )
                saved_rates[code] = float(rate_obj.rate)

        return saved_rates

    except Exception:
        return _get_fallback_rates(base_currency)


def _get_fallback_rates(base_currency='GBP'):
    """Fallback rates if API is unavailable."""
    from .models import ExchangeRate
    fallback = {
        'GBP': {'USD': 1.27, 'GBP': 1.0, 'CAD': 1.72, 'AUD': 1.93},
        'USD': {'USD': 1.0, 'GBP': 0.79, 'CAD': 1.36, 'AUD': 1.52},
    }
    rates = fallback.get(base_currency, fallback['GBP'])
    expires_at = timezone.now() + timedelta(hours=CACHE_DURATION_HOURS)

    for code, rate in rates.items():
        ExchangeRate.objects.update_or_create(
            base_currency=base_currency,
            target_currency=code,
            defaults={
                'rate': Decimal(str(rate)),
                'expires_at': expires_at,
                'api_source': 'fallback',
            }
        )
    return rates


def get_or_fetch_rate(base_currency, target_currency):
    """Get cached rate or fetch fresh ones."""
    from .models import ExchangeRate

    rate = ExchangeRate.get_latest_rate(base_currency, target_currency)
    if rate:
        return rate

    fetch_exchange_rates(base_currency)
    return ExchangeRate.get_latest_rate(base_currency, target_currency)

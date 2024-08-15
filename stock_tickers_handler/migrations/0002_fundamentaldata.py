# Generated by Django 5.1 on 2024-08-15 20:33

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('stock_tickers_handler', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='FundamentalData',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('currency', models.CharField(blank=True, max_length=10, null=True)),
                ('long_name', models.CharField(blank=True, max_length=255, null=True)),
                ('exchange', models.CharField(blank=True, max_length=50, null=True)),
                ('quote_type', models.CharField(blank=True, max_length=50, null=True)),
                ('industry', models.CharField(blank=True, max_length=100, null=True)),
                ('sector', models.CharField(blank=True, max_length=100, null=True)),
                ('long_business_summary', models.TextField(blank=True, null=True)),
                ('previous_close', models.DecimalField(blank=True, decimal_places=8, max_digits=20, null=True)),
                ('dividend_rate', models.DecimalField(blank=True, decimal_places=8, max_digits=15, null=True)),
                ('dividend_yield', models.DecimalField(blank=True, decimal_places=8, max_digits=15, null=True)),
                ('ex_dividend_date', models.DateTimeField(blank=True, null=True)),
                ('payout_ratio', models.DecimalField(blank=True, decimal_places=8, max_digits=15, null=True)),
                ('beta', models.DecimalField(blank=True, decimal_places=8, max_digits=15, null=True)),
                ('trailing_pe', models.DecimalField(blank=True, decimal_places=8, max_digits=15, null=True)),
                ('forward_pe', models.DecimalField(blank=True, decimal_places=8, max_digits=15, null=True)),
                ('volume', models.BigIntegerField(blank=True, null=True)),
                ('regular_market_volume', models.BigIntegerField(blank=True, null=True)),
                ('average_volume', models.BigIntegerField(blank=True, null=True)),
                ('average_volume_10_days', models.BigIntegerField(blank=True, null=True)),
                ('market_cap', models.BigIntegerField(blank=True, null=True)),
                ('fifty_two_week_low', models.DecimalField(blank=True, decimal_places=8, max_digits=20, null=True)),
                ('fifty_two_week_high', models.DecimalField(blank=True, decimal_places=8, max_digits=20, null=True)),
                ('price_to_sales_trailing_12_months', models.DecimalField(blank=True, decimal_places=8, max_digits=15, null=True)),
                ('fifty_day_moving_average', models.DecimalField(blank=True, decimal_places=8, max_digits=20, null=True)),
                ('two_hundred_day_moving_average', models.DecimalField(blank=True, decimal_places=8, max_digits=20, null=True)),
                ('price_to_book', models.DecimalField(blank=True, decimal_places=8, max_digits=15, null=True)),
                ('trailing_annual_dividend_rate', models.DecimalField(blank=True, decimal_places=8, max_digits=15, null=True)),
                ('trailing_annual_dividend_yield', models.DecimalField(blank=True, decimal_places=8, max_digits=15, null=True)),
                ('enterprise_value', models.BigIntegerField(blank=True, null=True)),
                ('profit_margins', models.DecimalField(blank=True, decimal_places=8, max_digits=15, null=True)),
                ('float_shares', models.BigIntegerField(blank=True, null=True)),
                ('shares_outstanding', models.BigIntegerField(blank=True, null=True)),
                ('shares_short', models.BigIntegerField(blank=True, null=True)),
                ('shares_short_prior_month', models.BigIntegerField(blank=True, null=True)),
                ('shares_short_previous_month_date', models.DateTimeField(blank=True, null=True)),
                ('date_short_interest', models.DateTimeField(blank=True, null=True)),
                ('shares_percent_shares_out', models.DecimalField(blank=True, decimal_places=8, max_digits=15, null=True)),
                ('held_percent_insiders', models.DecimalField(blank=True, decimal_places=8, max_digits=15, null=True)),
                ('held_percent_institutions', models.DecimalField(blank=True, decimal_places=8, max_digits=15, null=True)),
                ('short_ratio', models.DecimalField(blank=True, decimal_places=8, max_digits=15, null=True)),
                ('short_percent_of_float', models.DecimalField(blank=True, decimal_places=8, max_digits=15, null=True)),
                ('implied_shares_outstanding', models.BigIntegerField(blank=True, null=True)),
                ('book_value', models.DecimalField(blank=True, decimal_places=8, max_digits=20, null=True)),
                ('last_fiscal_year_end', models.DateTimeField(blank=True, null=True)),
                ('next_fiscal_year_end', models.DateTimeField(blank=True, null=True)),
                ('most_recent_quarter', models.DateTimeField(blank=True, null=True)),
                ('earnings_quarterly_growth', models.DecimalField(blank=True, decimal_places=8, max_digits=15, null=True)),
                ('net_income_to_common', models.BigIntegerField(blank=True, null=True)),
                ('trailing_eps', models.DecimalField(blank=True, decimal_places=8, max_digits=15, null=True)),
                ('forward_eps', models.DecimalField(blank=True, decimal_places=8, max_digits=15, null=True)),
                ('peg_ratio', models.DecimalField(blank=True, decimal_places=8, max_digits=15, null=True)),
                ('last_split_factor', models.CharField(blank=True, max_length=20, null=True)),
                ('last_split_date', models.DateTimeField(blank=True, null=True)),
                ('enterprise_to_revenue', models.DecimalField(blank=True, decimal_places=8, max_digits=15, null=True)),
                ('enterprise_to_ebitda', models.DecimalField(blank=True, decimal_places=8, max_digits=15, null=True)),
                ('fifty_two_week_change', models.DecimalField(blank=True, decimal_places=8, max_digits=15, null=True)),
                ('last_dividend_value', models.DecimalField(blank=True, decimal_places=8, max_digits=15, null=True)),
                ('last_dividend_date', models.DateTimeField(blank=True, null=True)),
                ('current_price', models.DecimalField(blank=True, decimal_places=8, max_digits=20, null=True)),
                ('target_high_price', models.DecimalField(blank=True, decimal_places=8, max_digits=20, null=True)),
                ('target_low_price', models.DecimalField(blank=True, decimal_places=8, max_digits=20, null=True)),
                ('target_mean_price', models.DecimalField(blank=True, decimal_places=8, max_digits=20, null=True)),
                ('target_median_price', models.DecimalField(blank=True, decimal_places=8, max_digits=20, null=True)),
                ('number_of_analyst_opinions', models.IntegerField(blank=True, null=True)),
                ('total_cash', models.BigIntegerField(blank=True, null=True)),
                ('total_cash_per_share', models.DecimalField(blank=True, decimal_places=8, max_digits=20, null=True)),
                ('ebitda', models.BigIntegerField(blank=True, null=True)),
                ('total_debt', models.BigIntegerField(blank=True, null=True)),
                ('quick_ratio', models.DecimalField(blank=True, decimal_places=8, max_digits=15, null=True)),
                ('current_ratio', models.DecimalField(blank=True, decimal_places=8, max_digits=15, null=True)),
                ('total_revenue', models.BigIntegerField(blank=True, null=True)),
                ('debt_to_equity', models.DecimalField(blank=True, decimal_places=8, max_digits=15, null=True)),
                ('revenue_per_share', models.DecimalField(blank=True, decimal_places=8, max_digits=20, null=True)),
                ('return_on_assets', models.DecimalField(blank=True, decimal_places=8, max_digits=15, null=True)),
                ('return_on_equity', models.DecimalField(blank=True, decimal_places=8, max_digits=15, null=True)),
                ('free_cashflow', models.BigIntegerField(blank=True, null=True)),
                ('operating_cashflow', models.BigIntegerField(blank=True, null=True)),
                ('earnings_growth', models.DecimalField(blank=True, decimal_places=8, max_digits=15, null=True)),
                ('revenue_growth', models.DecimalField(blank=True, decimal_places=8, max_digits=15, null=True)),
                ('gross_margins', models.DecimalField(blank=True, decimal_places=8, max_digits=15, null=True)),
                ('ebitda_margins', models.DecimalField(blank=True, decimal_places=8, max_digits=15, null=True)),
                ('operating_margins', models.DecimalField(blank=True, decimal_places=8, max_digits=15, null=True)),
                ('trailing_peg_ratio', models.DecimalField(blank=True, decimal_places=8, max_digits=15, null=True)),
                ('ticker', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='fundamental_data', to='stock_tickers_handler.activestocksalphavantage')),
            ],
            options={
                'verbose_name': 'Fundamental Data',
                'verbose_name_plural': 'Fundamental Data',
            },
        ),
    ]

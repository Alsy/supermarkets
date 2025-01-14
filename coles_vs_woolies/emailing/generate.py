import datetime
import pathlib

from rich.console import Console
from rich.table import Table

from coles_vs_woolies.search import available_merchants_names
from coles_vs_woolies.search.types import Merchant, ProductOffers

_SCRIPT_DIR = pathlib.Path(__file__).parent.absolute()
_TEMPLATE_DIR = _SCRIPT_DIR / 'templates'


def generate_weekly_email(product_offers: ProductOffers, out_path: str = None) -> str:
    """
    Returns a Mailersend email template populated from product_offers & save to out_path.
    :param product_offers: ProductOffers used for populating email template.
    :param out_path: optional, save destination for output email template.
    :return:
    """
    # Import HTML templates & snippets
    with open(_TEMPLATE_DIR / 'weekly.html', 'r', encoding="utf-8") as f:
        html_template = f.read()
    with open(_TEMPLATE_DIR / 'snippets/table.html', 'r', encoding="utf-8") as f:
        html_template_table = f.read()
    with open(_TEMPLATE_DIR / 'snippets/table_row.html', 'r', encoding="utf-8") as f:
        html_template_table_row: str = f.read()

    # Build merchant offer HTML rows from template
    rows = []
    green, light_grey = '#008000', '#afafaf'
    html_padding = '<span style="opacity:0;">0</span>'
    for product_name, offers in product_offers.items():
        row_template = html_template_table_row
        row_template = row_template.replace('{{ product }}', product_name)

        # Replace merchant offers
        lowest_price = min(offers).price
        is_sales = any((offer.is_on_special for offer in offers))
        merchants_with_offers: set[Merchant] = set()
        for offer in offers:
            merchant = offer.merchant
            merchants_with_offers.add(merchant)

            # Determine text replacement details
            price = f'${offer.price}' if offer.price is not None else '-'
            colour = green if is_sales and offer.price == lowest_price else light_grey
            zero_padding = html_padding if len(price.split('.')[-1]) == 1 else ''

            # Insert merchant offer into HTML template
            html_replacement = f'<a href="{offer.link}" style="color:{colour};text-decoration:inherit;">{price}{zero_padding}</a>'
            row_template = row_template.replace('{{ %(merchant)s_price }}' % {"merchant": merchant}, html_replacement)

        # Format email for merchants without offers
        for missing_merchant in available_merchants_names.difference(merchants_with_offers):
            html_replacement = f'<span style="color:{light_grey};">-<span style="opacity:0;">00</span></span>'
            row_template = row_template.replace('{{ %(merchant)s_price }}' % {"merchant": missing_merchant},
                                                html_replacement)

        rows.append(row_template)

    # Build HTML table of merchant offers
    html_template_table = html_template_table.replace('{{ rows }}', ''.join(rows))
    html_template = html_template.replace('{{ table }}', html_template_table)

    # Add timespan to template
    year, week, weekday = datetime.datetime.now().isocalendar()
    week_start, week_fin = (week - 1, week) if weekday < 3 else (week, week + 1)
    start = datetime.datetime.fromisocalendar(year, week_start, 3)
    fin = datetime.datetime.fromisocalendar(year, week_fin, 2)
    html_template = html_template.replace('{{ timespan }}',
                                          f"Deals from {start.strftime('%a %d/%m')} till {fin.strftime('%a %d/%m')}")

    # Output formatted template
    if out_path:
        pathlib.Path(out_path).parent.mkdir(parents=True, exist_ok=True)
        with open(out_path, 'w', encoding="utf-8") as f:
            f.write(html_template)

    return html_template


def _generate_weekly_template_old(offer_table: Table, out_path: str):
    # TODO this is legacy & requires printing garbage to console
    _console = Console(record=True)
    _console.print(offer_table)
    html_table = _console.export_html(inline_styles=True, code_format="<pre>{code}</pre>")

    with open(_TEMPLATE_DIR / 'old/rich_template.html', 'r') as f:
        html = f.read()

    pathlib.Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, 'w', encoding="utf-8") as f:
        f.write(html.replace('{{ table }}', html_table))

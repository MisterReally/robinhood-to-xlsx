from sql.operations.instruments import\
  get_instruments,\
    get_option_instruments
from utils.instruments import\
  handle_fetched_instrument_data,\
    handle_fetched_option_instrument_data

def aggregate_symbols(data, symbol, amount):
  if symbol in data:
    data[symbol] += float(amount)
  else:
    data[symbol] = float(amount)
  return data

def aggregate_orders(data, symbol, price, quantity, fees, side):
  gross_price = float(price) * float(quantity)
  if side == 'buy':
    net_price = gross_price * -1
  else:
    net_price = gross_price - float(fees)
  return aggregate_symbols(data, symbol, net_price)

def dividends(file_results):
  dividends = []
  company_totals = {}
  for item in file_results:
    try:
      instrument = item['instrument']
      fetched_row = get_instruments(instrument)
      simple_name, symbol = handle_fetched_instrument_data(fetched_row, instrument)
      item['simple_name'], item['symbol'] = simple_name, symbol
      net_price = gross_price - float(fees)
      company_totals = aggregate_symbols(company_totals, symbol, item['amount'])
      dividends.append(item)
    except Exception as e:
      print("There was an error fetching the instrument in dividend", str(e))
  return dividends, company_totals

def events(file_results):
  events = []
  for item in file_results:
    if item['state'] == 'confirmed' and item['type'] != 'expiration':
      option_instrument = item['option']
      fetched_row = get_option_instruments(option_instrument)
      instrument_values = handle_fetched_option_instrument_data(fetched_row, option_instrument)
      (item['strike_price'],
      item['chain_symbol'],
      item['option_type'],
      item['expiration_date'],
      item['created_at']) = instrument_values
      events.append(item)
  return events, {}

def events_orders(file_results, aggregates):
  events_orders = []
  company_totals = aggregates
  for item in file_results:
    if item['state'] == 'confirmed' and item['type'] != 'expiration':
      option_instrument = item['option']
      fetched_row = get_option_instruments(option_instrument)
      instrument_values = handle_fetched_option_instrument_data(fetched_row, option_instrument)

      (strike_price,
      chain_symbol,
      option_type,
      expiration_date,
      created_at) = instrument_values

      shares = float(item['quantity']) * 100
      fees = (float(strike_price) * shares) - float(item['total_cash_amount'])
      side = "buy" if item['direction'] == "debit" else "sell"

      event_order = {
        "fees": fees,
        "side": side,
        "quantity": shares,
        "settlement_date": expiration_date,
        "price": strike_price,
        "simple_name": "Events",
        "symbol": chain_symbol,
      }

      company_totals = aggregate_orders(
        company_totals,
        chain_symbol,
        strike_price,
        shares,
        fees,
        side,
      )
      events_orders.append(event_order)
  return events_orders, company_totals

def options(file_results):
  options = []
  for item in file_results:
    if item['state'] == 'filled':
    # for leg in item['legs']:
    #   option_instrument_url = leg["option"]
    #   side, effect = leg["side"], leg["position_effect"]

    #   try:
    #     option_instrument_data = get_option_instruments(option_instrument_url)
    #     option_instrument_values = handle_fetched_option_instrument_data(
    #       option_instrument_data,
    #       option_instrument_url,
    #     )
    #     (item['strike_price'],
    #     item['chain_symbol'],
    #     item['option_type'],
    #     item['expiration_date'],
    #     item['created_at']) = option_instrument_values
    #   except Exception as e:
    #     print("There was an error fetching the instrument", str(e))
      options.append(item)

  return options, {}

def orders(file_results):
  orders = []
  company_totals = {}
  for item in file_results:
    if item['state'] == 'filled':
      executions = item['executions'][0]
      item['settlement_date'] = executions['settlement_date']
      item['price'] = executions['price']
      try:
        instrument = item['instrument']
        fetched_row = get_instruments(instrument)
        simple_name, symbol = handle_fetched_instrument_data(fetched_row, instrument)
        item['simple_name'], item['symbol'] = simple_name, symbol
        company_totals = aggregate_orders(
          company_totals,
          item['symbol'],
          item['price'],
          item['quantity'],
          item['fees'],
          item['side'],
        )
      except Exception as e:
        print("There was an error fetching the instrument", str(e))
      orders.append(item)
  return orders, company_totals

entity_helpers = {
  "dividends": dividends,
  "events": events,
  "events_orders": events_orders,
  "orders": orders,
  "options": options
}

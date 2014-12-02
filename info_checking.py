#Checks the consistency of database software

import database_interface
import alert
import datetime
import custom_functions

def check_data():

  consistency_check()

  alerts = database_interface.get_data(database_interface.ALERT)
  messages = []
  for a in alerts:
    if a['type'] == 'time':
      x = _check_time_alert(a)
      if len(x) != 0:
        messages.append(x)
    elif a['type'] == 'quantity':
      x = _check_quantity_alert(a)
      if len(x) != 0:
        messages.append(x)
  
  #distille the messages
  ## !! Implement later !!
  # For now just send all emails
  
  if len(messages) != 0: 
    database_interface.update(database_interface.DETECTED_CONCERNS,{},{'info' : messages, 'date' : datetime.datetime.now()}, create=True)

  # Alert_set is a set of flags raised by one configured alert
  for alert_set in messages:
    # We process every alert in the set seperately
    for a in alert_set:
      #For now !! Remove later
      print("\n\nAddress: " +  ", ".join(a['address']))
      print("Subject: " + a['subject'])
      print("Message: " +a['message']['plain'])
      
      alert.send_email(a['address'],a['subject'],a['message'])
      alert.send_text(a['phone_num'],a['message'])
  
def _check_time_alert(alert):
  # !! Remove Later !!
  raise NotImplementedError
  # !!              !!


  time_delta = datetime.datetime.now() - datetime.timedelta(weeks = alert['flag']['week'], days = alert['flag']['day'], hours=alert['flag']['hour'] )

  query = {}
  query['number'] = {}
  query['number']['$in'] = alert['target_bins']
  query['date'] = {}
  query['date'] = {'$gte': time_delta} 

  data = database_interface.get_data(database_interface.FOOD, query)

  temp_ar = {}  

  for el in data:
    if el['bin'] not in temp_ar:
      temp_ar[el['bin']] = []
    temp_ar[el['bin']].append(el)
  
  data = temp_ar


  for key,bin in data.iter():
    data[key] = custom_functions.sort_by_date(bin) 

   
  # Check bins
   
 

def _check_quantity_alert(alert):

  time = datetime.datetime.now() - datetime.timedelta(hours=2)
  
  query = {}
  if alert['target_bins'] != -1:
    query['bin'] = {}
    query['bin']['$in'] = alert['target_bins']
  query['date'] = {'$gte':time}
  
  data = database_interface.get_data(database_interface.FOOD,query)
  stats_data = {}

  #gather preliminary information

  for d in data:
    if d['bin'] not in stats_data:
      stats_data[d['bin']] = {}
      stats_data[d['bin']]['avg'] = 0
      stats_data[d['bin']]['last_reading_date'] = d['date']
      stats_data[d['bin']]['last_reading'] = d['quantity']
      stats_data[d['bin']]['num'] = 0

    stats_data[d['bin']]['avg'] += d['quantity']
    stats_data[d['bin']]['num'] += 1
 
    if d['date'] > stats_data[d['bin']]['last_reading_date']:
      stats_data[d['bin']]['last_reading'] = d['quantity']
      stats_data[d['bin']]['last_reading_date'] = d['date']

  # Finalize the average computation

  for key in stats_data:
    stats_data[key]['avg'] /= stats_data[key]['num']

  del data
  problems = []

  for key in stats_data:
    type = None
    if stats_data[key]['avg'] < alert['flag']['min'] and stats_data[key]['last_reading'] < alert['flag']['min']:
      type = "min"
    elif stats_data[key]['avg'] > alert['flag']['max'] and stats_data[key]['last_reading'] > alert['flag']['max']:
      type = "max"
    if type is not None:
      problems.append(__create_quantity_message({"bin" : key, "quantity" : stats_data[key]['avg'], "date" : stats_data[key]['last_reading_date'], "type" : type}, alert))


  return problems


def consistency_check():
  time = datetime.datetime.now() - datetime.timedelta(hours=2)

  query = {}
  query['date'] = {'$gte':time}

  data = database_interface.get_data(database_interface.FOOD, query)

  stats_data = {}

  # setup data, setup avg

  for item in data:
  
    if item['bin'] not in stats_data:
      stats_data[item['bin']] = {}
      stats_data[item['bin']]['avg'] = 0.0
      stats_data[item['bin']]['cnt'] = 0
      stats_data[item['bin']]['std_dev'] = 0
      stats_data[item['bin']]['concern_cnt'] = 0
    stats_data[item['bin']]['avg'] += item['quantity']
    stats_data[item['bin']]['cnt'] += 1  

  # calc average

  for key,stats in stats_data.iteritems():
    stats_data[key]['avg'] /= stats_data[item['bin']]['cnt']
    

  # calc raw standard variance, not divded

  for item in data:
    stats_data[item['bin']]['std_dev'] += (item['quantity'] - stats_data[item['bin']]['avg'])**2 
    
  # calc std dev

  for key, stats in stats_data.iteritems():

    stats_data[key]['std_dev'] = (stats_data[key]['std_dev'] / (stats_data[key]['cnt']-stats_data[key]['cnt']!=1) )**(1/2)

  ## Check the amount of outliers

  for item in data:
    if item['quantity'] > 2*stats_data[item['bin']]['std_dev']:
      stats_data[item['bin']]['concern_cnt'] += 1

  # print results

  for key,stat in stats_data.iteritems():
    if stat['concern_cnt'] > 4:
      print ("Bin " + str(item['bin']) + " has highly inconsistent data")


def __create_quantity_message(info,alert):
  names = []
  for cont in alert['contact']:
    names.append(cont['name'])
  query = {}
  query['name'] = {}
  query['name']['$in'] = names

  contacts = database_interface.get_data(database_interface.CONTACT, query)
  
  msg = {}
  msg['address'] = []
  msg['phone_num'] = []
  for cont in contacts:
    msg['address'].append(cont['email'])
    msg['phone_num'].append(cont['phone'])
  
 
  msg['subject'] = "Low Stock - Bin " + str(info['bin']);

  msg['message'] = {}

  msg['message']['plain'] = info['date'].strftime("%Y-%m-%d") + "\n"
  msg['message']['html'] = "<p>" + msg['message']['plain'] + "</p><br>"

  msg['message']['plain'] = "Stock in Bin " + str(info['bin']) + " is "
  msg['message']['html'] = "<p>" + "Stock in Bin " + str(info['bin']) + " is "

  if info['type'] == "min":
    msg['message']['plain'] += "below configured minimum threshold. Stock must be replenished soon.\n"
    msg['message']['html'] += "below configured minimum threshold. Stock must be replenished soon.</p><br>"
  else:
    msg['message']['plain'] += "above configured maximum threshold.\n"
    msg['message']['html'] += "above configured maximum threshold.</p>"

  return msg


def __create_time_message(info,alert):
  raise NotImplementedError


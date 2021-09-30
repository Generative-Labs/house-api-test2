#  ga_analytics.py
#  Copyright 2021 Qunhe Tech, all rights reserved.
#  Qunhe PROPRIETARY/CONFIDENTIAL, any form of usage is subject to approval.
"""Hello Analytics Reporting API V4."""

import re
from googleapiclient.discovery import build
from oauth2client.service_account import ServiceAccountCredentials
import json

SCOPES = ['https://www.googleapis.com/auth/analytics.readonly']
KEY_FILE_LOCATION = r'./siyu/config/ga_config.json'
VIEW_ID = '250433594'


def initialize_analyticsreporting():
    """Initializes an Analytics Reporting API V4 service object.

  Returns:
    An authorized Analytics Reporting API V4 service object.
  """
    credentials = ServiceAccountCredentials.from_json_keyfile_name(
        KEY_FILE_LOCATION, SCOPES)

    # Build the service object.
    analytics = build('analyticsreporting', 'v4', credentials=credentials)

    return analytics


def get_report(analytics, post_id_path_list = {}, start_time = '2021-09-01', end_time = 'today', sources=['sms']):
    """Queries the Analytics Reporting API V4.

    Args:
      analytics: An authorized Analytics Reporting API V4 service object.
    Returns:
      The Analytics Reporting API V4 response.
    """
    body_dict = {}
    body_dict['reportRequests'] = []
    request ={}
    request['viewId'] = VIEW_ID
    request['dateRanges'] = []

    time_range = {}
    time_range['startDate'] = start_time
    time_range['endDate'] = end_time

    request['dateRanges'].append(time_range)

    request['dimensionFilterClauses'] = []
    

    
      #path = '/post/{}'.format(post_id) if post_id else ''
    #for post_id_path in post_id_path_list:
    filters = {}
    filters['filters'] = []
    
    ga_path = {}
    ga_path['dimensionName'] = 'ga:pagePath'
    ga_path['operator'] = 'IN_LIST'
    ga_path['expressions'] = post_id_path_list
    filters['filters'].append(ga_path)
    ga_source = {}
    ga_source['dimensionName'] = 'ga:source'
    ga_source['operator'] = 'IN_LIST'
    ga_source['expressions'] = sources
    filters['filters'].append(ga_source)
    filters['operator'] = 'AND'
    request['dimensionFilterClauses'].append(filters)

    request['metrics'] = []
    metrics = {}
    metrics['expression'] = 'ga:pageviews'
    request['metrics'].append(metrics)

    request['dimensions'] = []
    ga_path = {}
    ga_path['name'] = 'ga:pagePath'
    request['dimensions'].append(ga_path)

    ga_source = {}
    ga_source['name'] = 'ga:source'
    request['dimensions'].append(ga_source)

    body_dict['reportRequests'].append(request)

    #body_str = json.dumps(body_dict)
    #print("body_str:", body_str)
    analytics.reports()
    return analytics.reports().batchGet(body=body_dict).execute()

def get_pageview_dict(response):
  """Parses and prints the Analytics Reporting API V4 response.
  Args:
    response: An Analytics Reporting API V4 response.
  """
  page_path_dict = {}
  for report in response.get('reports',[]):
      for row in report.get('data', {}).get('rows',{}):
        print("row:", row)
        print("row_list:", row.get("dimensions", []))
        base_key_name = row.get("dimensions", [])
        if len(base_key_name) != 2:
          continue

        key_name = make_post_id_source_sum(base_key_name[0], base_key_name[1])
        for value in row.get('metrics',[]):
          #print("key_name:", key_name)
          #print("value:", value)
          #print("value:", value.get("values"))
          value_count = 0
          for value_em in value.get("values", []):
            value_count += int(value_em)
          page_path_dict[key_name]=value_count
  return page_path_dict

def make_post_id_path(post_id = ''):
  return '/post/{}'.format(post_id) if post_id else ''

def make_post_id_source_sum(post_path = '', source = 'sms'):
  return '{}|{}'.format(post_path,source) if source else 'sms'

def ga_api_rangtime(post_id_path_list = [], start_time = '2021-09-01', end_time = 'today', sources = ['sms']):
    analytics = initialize_analyticsreporting()
    response = get_report(analytics, post_id_path_list, start_time, end_time, sources)
    return get_pageview_dict(response)

if __name__ == '__main__':
    print("====test====")
    #ga_api_rangtime(1000)
    test_list=[]
    test_list.append(make_post_id_path(1000))
    test_list.append(make_post_id_path(3000))

    response = get_report(initialize_analyticsreporting(),test_list)
    print("respose:", response)
    print(get_pageview_dict(response))

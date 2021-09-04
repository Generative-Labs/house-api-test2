#  ga_analytics.py
#  Copyright 2021 Qunhe Tech, all rights reserved.
#  Qunhe PROPRIETARY/CONFIDENTIAL, any form of usage is subject to approval.
"""Hello Analytics Reporting API V4."""

from googleapiclient.discovery import build
from oauth2client.service_account import ServiceAccountCredentials

SCOPES = ['https://www.googleapis.com/auth/analytics.readonly']
KEY_FILE_LOCATION = r'C:\Users\`jun\Desktop\house-platform-324907-162a995beb43.json'
VIEW_ID = '250402833'


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


def get_report(analytics, post_id = '', source = ''):
    """Queries the Analytics Reporting API V4.

  Args:
    analytics: An authorized Analytics Reporting API V4 service object.
  Returns:
    The Analytics Reporting API V4 response.
  """
    path = '/post/{}'.format(post_id) if post_id else ''
    return analytics.reports().batchGet(
        body={
            'reportRequests': [
                {
                    'viewId': VIEW_ID,
                    'dateRanges': [{'startDate': '2021-09-01', 'endDate': 'today'}],
                    'dimensionFilterClauses': [{
                        'filters': [
                            {
                                "dimensionName": "ga:pagePath",
                                "expressions": [path],
                                "operator": "EXACT"
                            },
                            {
                                "dimensionName": "ga:source",
                                "expressions": [source],
                                "operator": "EXACT"
                            }
                        ],
                        'operator': 'AND'
                    }
                    ],
                    'metrics': [{'expression':'ga:pageviews'}],
                    'dimensions': [ {'name': 'ga:source'},  {'name': 'ga:pagePath'}]

                }]
        }
    ).execute()


def print_response(response):
    """Parses and prints the Analytics Reporting API V4 response.

  Args:
    response: An Analytics Reporting API V4 response.
  """
    for report in response.get('reports', []):
        columnHeader = report.get('columnHeader', {})
        dimensionHeaders = columnHeader.get('dimensions', [])
        metricHeaders = columnHeader.get('metricHeader', {}).get('metricHeaderEntries', [])

        for row in report.get('data', {}).get('rows', []):
            dimensions = row.get('dimensions', [])
            dateRangeValues = row.get('metrics', [])

            for header, dimension in zip(dimensionHeaders, dimensions):
                print(header + ': ' + dimension)

            for i, values in enumerate(dateRangeValues):
                print('Date range: ' + str(i))
                for metricHeader, value in zip(metricHeaders, values.get('values')):
                    print(metricHeader.get('name') + ': ' + value)
                    return value
        return 0


def ga_api(post_id = '', source = ''):
    analytics = initialize_analyticsreporting()
    response = get_report(analytics, post_id, source)
    return print_response(response)


if __name__ == '__main__':
    ga_api(22, 'test')

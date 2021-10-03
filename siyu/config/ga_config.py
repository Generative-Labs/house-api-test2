import json
import os

GA_KEY_DICT = json.loads(os.environ['GA_CONFIG'])
SCOPES = ['https://www.googleapis.com/auth/analytics.readonly']
VIEW_ID = '250433594'
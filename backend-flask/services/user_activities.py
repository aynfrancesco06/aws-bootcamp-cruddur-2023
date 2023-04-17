#from aws_xray_sdk.core import xray_recorder
from lib.db import db

class UserActivities:
  def run(user_handle):
    #try:
    # AWS Xray
      #segment = xray_recorder.begin_segment('user_activities')
      model = {
        'errors': None,
        'data': None
      }
      if user_handle == None or len(user_handle) < 1:
        model['errors'] = ['blank_user_handle']
      else:
        sql = db.template('users','show')
        results = db.query_object_json(sql,{'handle': user_handle})
        model['data'] = results
      return model
      #subsegment = xray_recorder.begin_subsegment('mock-data')
       # AWS Xray
      #dict = {
      #  "now": now.isoformat(),
      #  "results-size": len(model['data'])
      #  }
      #subsegment.put_metadata('key', dict, 'namespace')
      #xray_recorder.end_subsegment()
    #finally:
    #    #close the segment
    #    xray_recorder.end_subsegment()
    #  return model
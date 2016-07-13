# Copy this file to config.py and change the settings

# Project ID and dataset to use in Big query
PROJECT_ID = "my_project"
DATA_SET = "my_ga_data"
GA_BQ_UPLOAD_STATUS_LOG = (DATA_SET+".upload_progress_log")
# View ID of GA. Check your GA view to find it.
VIEW_ID = "12345678"
# First day we upload user_key_email and time so we can request every single log from ga
DATE_INIT = "2016-1-1"

# Tables we want to store from GA
ga_bq_config = {
    "user_page_view": {
        "request_body": {
            "reportRequests":
              [
                {
                  "viewId": VIEW_ID,
                  "dateRanges": [{"startDate": "", "endDate": ""}],
                  "dimensions": [{"name": "ga:dimension8"}, {"name": "ga:dimension9"}, {"name": "ga:pagePath"}, {"name": "ga:dateHour"}, {"name": "ga:minute"}],
                  "dimensionFilterClauses": {},
                  "metrics": [{"expression": "ga:timeOnPage"}, {"expression": "ga:exits"}],
                  "orderBys": [{"fieldName": "ga:dateHour"}, {"fieldName": "ga:minute"}, {"fieldName": "ga:dimension8"}],
                  "pageSize": "10000",
                  "pageToken": ""
                }
              ]
        },
        "destination_table": DATA_SET+".ga_page_view"
    },
    "user_event":{
        "request_body": {
            "reportRequests":
            [
                {
                  "viewId": VIEW_ID,
                  "dateRanges": [{"startDate": "", "endDate": ""}],
                  "dimensions": [{"name": "ga:dimension8"}, {"name": "ga:dimension9"}, {"name": "ga:dateHour"}, {"name": "ga:minute"}, {"name": "ga:eventCategory"}, {"name": "ga:eventAction"}, {"name": "ga:eventLabel"}],
                  "dimensionFilterClauses": {},
                  "metrics": [{"expression": "ga:hits"}],
                  "orderBys": [{"fieldName": "ga:dateHour"}, {"fieldName": "ga:minute"}, {"fieldName": "ga:dimension8"}],
                  "pageSize": "10000",
                  "pageToken": ""
                }
            ]
        },
        "destination_table": DATA_SET+".ga_user_event"
    },
    "user_device": {
        "request_body": {
            "reportRequests":
            [
                {
                  "viewId": VIEW_ID,
                  "dateRanges": [{"startDate": "", "endDate": ""}],
                  "dimensions": [{"name": "ga:dimension8"}, {"name": "ga:deviceCategory"}, {"name": "ga:operatingSystem"}, {"name": "ga:operatingSystemVersion"},
                    {"name": "ga:browser"}, {"name": "ga:browserVersion"}],
                  "dimensionFilterClauses": {},
                  "metrics": [{"expression": "ga:timeOnPage"}, {"expression": "ga:pageviews"}],
                  "orderBys": [{"fieldName": "ga:dimension8"}],
                  "pageSize": "10000",
                  "pageToken": ""
                }
            ]
        },
        "destination_table": DATA_SET+".ga_user_device"
    },
    "user_region": {
        "request_body": {
            "reportRequests":
              [
                {
                  "viewId": VIEW_ID,
                  "dateRanges": [{"startDate": "", "endDate": ""}],
                  "dimensions": [{"name": "ga:dimension8"}, {"name": "ga:region"}, {"name": "ga:city"}],
                  "dimensionFilterClauses": {},
                  "metrics": [{"expression": "ga:timeOnPage"}, {"expression": "ga:pageviews"}],
                  "orderBys": [{"fieldName": "ga:dimension8"}],
                  "pageSize": "10000",
                  "pageToken": ""
                }
              ]
        },
        "destination_table": DATA_SET+".ga_user_region"
    },
    "user_cookie_map": {
        "request_body": {
            "reportRequests":
              [
                {
                  "viewId": VIEW_ID,
                  "dateRanges": [{"startDate": "", "endDate": ""}],
                  "dimensions": [{"name": "ga:dimension8"}, {"name": "ga:dimension10"}],
                  "dimensionFilterClauses": {},
                  "metrics": [{"expression": "ga:timeOnPage"}, {"expression": "ga:pageviews"}],
                  "orderBys": [{"fieldName": "ga:dimension8"}],
                  "pageSize": "10000",
                  "pageToken": ""
                }
              ]
        },
        "destination_table": DATA_SET+".ga_user_cookie_map"
    },
    "user_mobile": {
        "request_body": {
            "reportRequests":
            [
                {
                  "viewId": VIEW_ID,
                  "dateRanges": [{"startDate": "", "endDate": ""}],
                  "dimensions": [{"name": "ga:dimension8"}, {"name": "ga:mobileDeviceInfo"},
                        {"name": "ga:operatingSystem"}, {"name": "ga:operatingSystemVersion"},
                        {"name": "ga:browser"}, {"name": "ga:browserVersion"}],
                  "dimensionFilterClauses": {},
                  "metrics": [{"expression": "ga:timeOnPage"}, {"expression": "ga:pageviews"}],
                  "orderBys": [{"fieldName": "ga:dimension8"}],
                  "pageSize": "10000",
                  "pageToken": ""
                }
            ]
        },
        "destination_table": DATA_SET+".ga_user_mobile"
    },
}

import argparse
import datetime
'''
pandas package now is installed from git+https://github.com/junyiacademy/pandas.git@tmp_solution_to_append_existed_bq_table
It is a fork from pandas for us to be able to append to existed bq table.
please use the following command to install pandas:
   pip install git+https://github.com/junyiacademy/pandas.git@tmp_solution_to_append_existed_bq_table
'''
import pandas as pd
# A self written library to handle google authorization
from google_auth import google_auth
# Import our config file
import config

def bq_query_to_table(query, table):  # query from bq then save into a bq table
    dataset = table.split('.')[0]
    table = table.split('.')[1]
    job = bigquery.jobs().insert(projectId=config.PROJECT_ID,
        body={"projectId": config.PROJECT_ID,
              "configuration":{
                "query": {
                    "query": query,
                        "destinationTable": {
                            "projectId": config.PROJECT_ID,
                            "datasetId": dataset,
                            "tableId": table
                        },
                    "writeDisposition":"WRITE_TRUNCATE",
                    "createDisposition":"CREATE_IF_NEEDED"
                }
              }
        }).execute()
    return job['id']


def check_table_exist(table):
    dataset = table.split('.')[0]
    table = table.split('.')[1]
    result = bigquery.tables().list(projectId=config.PROJECT_ID, datasetId=dataset).execute()
    if not 'tables' in result:
        return False
    table_list = [i['tableReference']['tableId'] for i in result['tables']]
    return table in table_list


def check_ga_session_date_exist(destination_table, date, credential_path):  # check if destination table has data of certain date
    if not check_table_exist(destination_table):  # has no certain date if the table not exist
        return False
    query = 'SELECT count(*) FROM [%s] WHERE DATE(ga_session_date) == "%s"' % (destination_table, date.strftime("%Y-%m-%d"))
    return (pd.read_gbq(query, project_id=config.PROJECT_ID, verbose=False, private_key=credential_path).iloc[0, 0] > 0)


def remove_certain_ga_session_date_data(destination_table, date):  # remove data of certain date
    query = 'SELECT * FROM [%s] WHERE DATE(ga_session_date) != "%s"' % (destination_table, date.strftime("%Y-%m-%d"))
    return bq_query_to_table(query, destination_table)


def parse_result_to_df(result):  # convert ga request response to df
    columns_list = []
    columns_list.extend(result['reports'][0]['columnHeader']['dimensions'])
    columns_list.extend([i['name'] for i in result['reports'][0]['columnHeader']['metricHeader']['metricHeaderEntries']])

    row_num = len(result['reports'][0]['data']['rows'])
    df = pd.DataFrame(columns = columns_list, index=range(row_num))
    for i, row in enumerate(result['reports'][0]['data']['rows']):
        list_to_append = []
        list_to_append.extend(row['dimensions'])
        list_to_append.extend(row['metrics'][0]['values'])
        for j in range(len(list_to_append)):
            df.iat[i, j] = list_to_append[j]  # df.append(my_dict, ignore_index=True)
    return df


def unix_time_millis(dt):
    epoch = datetime.datetime.utcfromtimestamp(0)
    return (dt - epoch).total_seconds() * 1000.0


def convert_js_date_format(date_str):  # change the js datetime format to python datetime format
    if date_str.isdigit():
        return date_str
    date_str = date_str.replace(' GMT', '').replace(' UTC', '')
    if date_str.count(":") == 3:
        try:
            return unix_time_millis(datetime.datetime.strptime(date_str, "%a, %d %b %Y %H:%M:%S:%f"))
        except:
            # print "date_str: %s cannot be converted" % date_str
            return date_str
    elif date_str.count(":") == 2:
        try:
            return unix_time_millis(datetime.datetime.strptime(date_str, "%a, %d %b %Y %H:%M:%S"))
        except:
            # print "date_str: %s cannot be converted" % date_str
            return date_str
    else:
        return date_str


def columns_conversion(df, date):  # change the df we request from ga to the one we upload to bq
    columns = [c.replace(':', '_') for c in df.columns]
    for i, c in enumerate(columns):
        if c == "ga_dimension8":
            columns[i] = "user_key_name"
        elif c == "ga_dimension9":
            columns[i] = "browser_utc_time"
            df.iloc[:, i] = df.iloc[:, i].apply(convert_js_date_format).astype(str)
        elif c == "ga_dimension10":
            columns[i] = "cookie_uuid"
        elif c == "ga_timeOnPage" or c == "ga_pageviews" or c == "ga_hits":
            df.iloc[:, i] = df.iloc[:, i].apply(lambda x: int(float(x)))
        elif c == "ga_exits":
            df.iloc[:, i] = df.iloc[:, i].astype(bool)
    df.columns = columns
    if 'ga_dateHour' in df.columns and 'ga_minute' in df.columns:
        df.loc[:, 'ga_session_time'] = pd.to_datetime((df.loc[:, 'ga_dateHour'] + df.loc[:, 'ga_minute']), format="%Y%m%d%H%M")
        df.drop(['ga_dateHour', 'ga_minute'], inplace=True, axis=1)
    df['ga_session_date'] = pd.to_datetime(date)  # we always add ga session date to data
    return df


def request_df_from_ga(request, page_token=""):
    request["reportRequests"][0]["pageToken"] = page_token
    result = analytics.reports().batchGet(body=request).execute()
    if 'rows' not in result['reports'][0]['data']:  # get no data from GA
        print 'reqeust from Ga get no data. Row number is 0'
        return (0, -1)
    df = parse_result_to_df(result)
    if 'nextPageToken' in result['reports'][0]:
        return (df, result['reports'][0]['nextPageToken'])
    else:
        return (df, -1)


def daterange(start_date, end_date):
    for n in range(int((end_date - start_date).days)):
        yield start_date + datetime.timedelta(n)


def ga_upload_to_bq_by_day(ga_to_bg_config_name, date, credential_path):
    if not isinstance(date, datetime.date):
        print 'force the date parameter as datetiem.date format'
        return None

    request_body = config.ga_bq_config[ga_to_bg_config_name]["request_body"]
    destination_table = config.ga_bq_config[ga_to_bg_config_name]["destination_table"]

    if len(request_body["reportRequests"]) > 1:
        print 'only allowed one reportRequests at this time'
        return None

    request_body["reportRequests"][0]['dateRanges'] = [{"startDate": date.strftime("%Y-%m-%d"), "endDate": date.strftime("%Y-%m-%d")}]

    cont_page_token = ''
    total_row = 0
    finish_flag = False
    retry_limit_flag = False
    cont_page_token = ''
    retry_count = 0
    print 'Start loading data from GA and upload to %s, from %s' % (destination_table, date)
    for i in range(1000):  # GA report API request limit: 1000 --> set limit to 50,000,000 row per day
        try:
            (df, cont_page_token) = request_df_from_ga(request_body, cont_page_token)
            df = columns_conversion(df, date)
            df.to_gbq(destination_table=destination_table, project_id=config.PROJECT_ID, if_exists='append', private_key=credential_path)
            # df.to_csv("%s-%s-data" % (ga_to_bg_config_name, date))
            row_num = len(df.index)
            total_row = total_row + row_num
            if cont_page_token == -1:
                finish_flag = True

        except Exception as e:
            print "Failing download response from Ga or upload to %s" % destination_table
            print str(e)
            retry_count += 1
            print "already tried %s times" % retry_count
            if retry_count == 10:
                retry_limit_flag = True

        if finish_flag:
            print 'Successfully download response from Ga and upload to %s' % destination_table
            return {"status": "success", "data_size": total_row}
        elif retry_limit_flag:
            print "Reach retry limit, Script Closed"
            return {"status": "failure", "data_size": total_row}
    print "Download GA data exceed row limit!!! Need to increase the GA report API request limit"
    return {"status": "failure", "data_size": total_row}


if __name__ == "__main__":
    # Parse the argument to get the credential_path
    parser = argparse.ArgumentParser(description='Input secre_json_path and corresponding dataset')
    parser.add_argument('--credential_path', type=str, dest='credential_path', required=True, help='input the path of service account credential from gcp, use $gcp_service_account in jenkings')
    args = vars(parser.parse_args())
    credential_path = args["credential_path"]
    # Use google_auth library to get access to google
    Auth = google_auth(credential_path)
    bigquery = Auth.get_auth('bigquery_v2')
    analytics = Auth.get_auth('analytics_v4')
    # Check if the GA_BQ_UPLOAD_STATUS_LOG table exist in gbq
    if check_table_exist(config.GA_BQ_UPLOAD_STATUS_LOG):
        ga_bq_upload_status_log = pd.read_gbq(query="SELECT * FROM [%s]" % config.GA_BQ_UPLOAD_STATUS_LOG, project_id=config.PROJECT_ID, private_key=credential_path)
    else:
        ga_bq_upload_status_log = pd.DataFrame(columns=['config_name', 'ga_session_date', 'status', 'backup_date', "uploaded_data_size"])
    # Set the time region
    d = config.DATE_INIT.split("-")
    date_init = datetime.date(int(d[0]),int(d[1]),int(d[2]))
    date_now = datetime.datetime.now().date()

    for config_name in config.ga_bq_config:
        for date in daterange(date_init, date_now):
            destination_table = config.ga_bq_config[config_name]["destination_table"]
            print "start checking (%s, %s) pair for GA to BQ" % (config_name, date)
            condition = (ga_bq_upload_status_log["config_name"]==config_name) & (ga_bq_upload_status_log["ga_session_date"]==date.strftime("%Y-%m-%d"))
            if ga_bq_upload_status_log[condition].empty:  # no such condition, totally new table-date pair
                print 'find no pair within the record, try to upload data with (%s, %s)' % (config_name, date)
                if check_ga_session_date_exist(destination_table, date, credential_path):
                    print 'find corresponding data in bq table, remove them.'
                    remove_certain_ga_session_date_data(destination_table, date)
                upload_result = ga_upload_to_bq_by_day(config_name, date, credential_path)
                current_result = pd.DataFrame(data={"config_name": config_name, "ga_session_date": date.strftime("%Y-%m-%d"), "status": upload_result['status'], "backup_date": date_now.strftime("%Y-%m-%d"), "uploaded_data_size": upload_result['data_size']}, index=[0])
                print "update corresponding result of (%s, %s) to %s" % (config_name, date, config.GA_BQ_UPLOAD_STATUS_LOG)
                current_result.to_gbq(destination_table=config.GA_BQ_UPLOAD_STATUS_LOG, project_id=config.PROJECT_ID, if_exists='append', private_key=credential_path)
            elif 'success' in ga_bq_upload_status_log[condition]['status'].values:
                print "already success in such pair"
            else:  # if failure, remove the data of that date/table and re-upload again
                print 'find pair with failure status, remove existed data and re-uploard'
                remove_certain_ga_session_date_data(destination_table, date)
                upload_result = ga_upload_to_bq_by_day(config_name, date, credential_path)
                current_result = pd.DataFrame(data={"config_name": config_name, "ga_session_date": date.strftime("%Y-%m-%d"), "status": upload_result['status'], "backup_date": date_now.strftime("%Y-%m-%d"), "uploaded_data_size": upload_result['data_size']}, index=[0])
                print "update corresponding result of (%s, %s) to %s" % (config_name, date, config.GA_BQ_UPLOAD_STATUS_LOG)
                current_result.to_gbq(destination_table=config.GA_BQ_UPLOAD_STATUS_LOG, project_id=config.PROJECT_ID, if_exists='append', private_key=credential_path)

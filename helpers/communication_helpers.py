
def create_message(method, record, tracking_code, broker_type, source, is_successful, size=1000, from_=0,
                   error_description=None, error_code=0, sort_by=None):
    if sort_by is None:
        sort_by = [{"DC_CREATE_TIME": "desc"}]

    message = {"method": method, "tracking_code": tracking_code, "broker_type": broker_type,
               "source": source, "size": size, "from": from_, "sort_by": sort_by,
               "is_successful": is_successful, "error_code": error_code,
               "error_description": error_description, "data": record}

    return message


def create_persian_error_message(method, record, tracking_code, broker_type, source, is_successful, member_id,
                                 size=1000, from_=0,
                                 error_description=None, error_code=0, sort_by=None, error_persian_description=None, ):
    if sort_by is None:
        sort_by = [{"DC_CREATE_TIME": "desc"}]

    message = {"method": method, "tracking_code": tracking_code, "broker_type": broker_type,
               "source": source, "size": size, "from": from_, "sort_by": sort_by,
               "is_successful": is_successful, "error_code": error_code,
               "error_description": error_description, "data": record, "member_id": member_id,
               "error_persian_description": error_persian_description}

    return message


def clear_response(response):
    if "broker_type" in response.keys():
        del response["broker_type"]
    if "source" in response.keys():
        del response["source"]
    if "tracking_code" in response.keys():
        del response["tracking_code"]
    if "method" in response.keys():
        del response["method"]
    if "sort_by" in response.keys():
        del response["sort_by"]

    if isinstance(response["data"], list):
        for data in response["data"]:
            if "body" in data.keys() and "broker_type" in data["body"].keys():
                del data["body"]["broker_type"]
            if "body" in data.keys() and "DC_CREATE_TIME" in data["body"].keys():
                del data["body"]["DC_CREATE_TIME"]
            if "body" in data.keys() and "pass_salt" in data["body"].keys():
                del data["body"]["pass_salt"]
            if "body" in data.keys() and "pass_hash" in data["body"].keys():
                del data["body"]["pass_hash"]
            if "body" in data.keys() and "score" in data["body"].keys():
                del data["body"]["score"]
            if "score" in data.keys():
                del data["score"]
        resp_data = response["data"].copy()
        del response["data"]
        response["data"] = {"results": resp_data}

    elif "results" in response["data"].keys() and isinstance(response["data"]["results"], list):
        for data in response["data"]["results"]:
            if "body" in data.keys() and "broker_type" in data["body"].keys():
                del data["body"]["broker_type"]
            if "body" in data.keys() and "DC_CREATE_TIME" in data["body"].keys():
                del data["body"]["DC_CREATE_TIME"]
            if "body" in data.keys() and "pass_salt" in data["body"].keys():
                del data["body"]["pass_salt"]
            if "body" in data.keys() and "pass_hash" in data["body"].keys():
                del data["body"]["pass_hash"]
            if "body" in data.keys() and "score" in data["body"].keys():
                del data["body"]["score"]
            if "score" in data.keys():
                del data["score"]
        resp_data = response["data"]["results"].copy()
        del response["data"]["results"]
        response["data"]["results"] = resp_data

    elif "member_data" in response["data"].keys():
        del response["data"]["member_data"]["broker_type"]
        del response["data"]["member_data"]["DC_CREATE_TIME"]
        del response["data"]["member_data"]["pass_salt"]
        del response["data"]["member_data"]["pass_hash"]

    else:
        if "body" in response["data"].keys() and "broker_type" in response["data"]["body"].keys():
            del response["data"]["body"]["broker_type"]
        if "broker_type" in response["data"].keys():
            del response["data"]["broker_type"]
        if "body" in response["data"].keys() and "DC_CREATE_TIME" in response["data"]["body"].keys():
            del response["data"]["body"]["DC_CREATE_TIME"]
        if "body" in response["data"].keys() and "pass_salt" in response["data"]["body"].keys():
            del response["data"]["body"]["pass_salt"]
        if "body" in response["data"].keys() and "pass_hash" in response["data"]["body"].keys():
            del response["data"]["body"]["pass_hash"]
        if "body" in response["data"].keys() and "score" in response["data"]["body"].keys():
            del response["data"]["body"]["score"]
        if "score" in response["data"].keys():
            del response["data"]["score"]

    return response



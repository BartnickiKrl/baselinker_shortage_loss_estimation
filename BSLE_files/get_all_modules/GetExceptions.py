import datetime

class Bl_token_ban(Exception):
    def __init__(self, error_dict):
        if error_dict['error_code'] == "ERROR_BLOCKED_TOKEN":
            self.why, _ = error_dict['error_message'].split(",",1)
            date_wait = list(error_dict['error_message'])[-19:]
            self.wait_till = datetime.strptime(date_wait, "%Y-%m-%d %H:%M:%S")
        else:
            self.why, _ = error_dict['error_message']
            self.wait_till = -1
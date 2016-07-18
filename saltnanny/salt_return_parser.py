#!/usr/bin/env python

import logging
import json
from ast import literal_eval


class SaltReturnParser:

    log = logging.getLogger('saltnanny')

    def __init__(self, cache_client):
        self.cache_client = cache_client

    def process_jids(self, completed_minions, all_minions_count):
        return_code_sum = 0
        for minion, jid in completed_minions.iteritems():
            return_info, return_code = self.get_return_info(minion, jid)
            return_code_sum += return_code
            self.log.info(json.dumps(return_info, indent=1))

        if not completed_minions:
            self.log.info('No highstates found in Job Cache, setting return_code_sum = 2')
            return_code_sum = 2

        if len(completed_minions) != all_minions_count and return_code_sum == 0:
            self.log.info('Highstates available in Job Cache were successful, timed out waiting for others.')
            return_code_sum = 1

        return return_code_sum

    def check_custom_event_failure(self, cache_key, failures):
        custom_results = literal_eval(self.cache_client.get_value_by_key(cache_key))
        failures_exist = [True for failure in failures if failure in custom_results]
        if True in failures_exist:
            return 1
        return 0

    def get_return_info(self, minion, jid):
        self.log.info('Getting return info for Minion:{0} JID:{1}'.format(minion, jid))
        return_info = self.cache_client.get_return_by_jid(minion, jid)
        return_dict = json.loads(return_info)
        return_code = return_dict.get('retcode')

        if self.highstate_failed(return_info) or not isinstance(return_code, int):
            return_code = 1
        return return_dict, return_code

    def highstate_failed(self, result):
        try:
            possible_failures = ['"result": false', 'Data failed to compile:', 'Pillar failed to render with the following messages:']
            failures = [failure in result for failure in possible_failures]
            self.log.info(failures)
            return True in failures
        except:
            self.log.info('Error finding if there was a failure in the result:\n {0}'.format(result))
            return True
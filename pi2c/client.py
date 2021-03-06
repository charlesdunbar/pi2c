#!/usr/bin/env python

import time
import icinga2api.client as icinga2api
from timeout import Timeout


class Client:
    """
    Interact with python-icinga2api library
    """
    def open_connection(self, server, user, password, port=5665):
        """
        Open connection to icinga2 server
        """
        server = server + ':' + str(port)
        client = icinga2api.Client(server, user, password)
        return client

    def host_filter(self, hostname):
        """
        Return a filter
        """
        filters = {
            'type': 'Host',
            'filter': 'match("{}", host.name)'.format(hostname),
        }
        return filters

    def service_filter(self, servicename, hostname=None):
        """
        Return filter for Service type
        """
        filters = {'type': 'Service'}
        service_part = 'match("{}", service.name)'.format(servicename)
        if hostname:
            host_part = 'match("{}", host.name)'.format(hostname)
            service_part = host_part + ' && ' + service_part
        filters['filter'] = service_part
        return filters

    def schedule_downtime(self, client, filters, comment, author, duration):
        """
        Schedule downtime for the provided filter
        """
        try_count = 0
        while try_count < 3:
            try:
                try_count = try_count + 1
                now = time.time()
                end_time = now + duration
                results = []
                with Timeout(20):
                    host_task = client.actions.schedule_downtime(
                        filters=filters,
                        start_time=now,
                        end_time=end_time,
                        duration=duration,
                        comment=comment,
                        author=author)
                    if len(host_task['results']) > 0:
                        for result in host_task['results']:
                            if result['code'] == 200.0:
                                results.append(result['status'])
                        return results
                    else:
                        return False
            except Timeout.Timeout:
                if try_count == 3:
                    return 'Operation timed out'

    def schedule_host_downtime(self, client, host, comment, author, duration=600):
        """
        Schedule host downtime for duration
        """
        host_filter = self.host_filter(host)
        downtime = self.schedule_downtime(client, host_filter, comment, author, duration)
        return downtime

    def schedule_service_downtime(self, client, comment, author,
                                  duration, service_name, host=None):
        """
        Schedule downtime for a service

        Filter on host if specified
        """
        service_filter = self.service_filter(service_name, host)
        downtime = self.schedule_downtime(client, service_filter, comment, author, duration)
        return downtime

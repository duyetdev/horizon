# Copyright 2012 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.
#
# Copyright 2012 Nebula, Inc.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import time
import re
import fileinput
import os
from collections import namedtuple

from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _
from django.views import generic
from django.conf import settings

from horizon import exceptions
from horizon import messages
from horizon import tables
from horizon import views
from horizon.utils import memoized
from horizon import workflows

from openstack_dashboard.dashboards.logmanagement import util

from openstack_dashboard.dashboards.logmanagement.view \
    import tables as log_tables

######################################
# import pandas as pd
# import numpy as np
# import re

# import matplotlib
# matplotlib.use('Agg')
# import matplotlib.pyplot as plt


# islab_log_path = getattr(settings, 'ROOT_PATH') + '/../../logs'
# with open(islab_log_path + '/horizon.log') as f:
#     islab_data = f.read()

# islab_data_line = islab_data.split('\n')
# islab_data_arr = []

# for i in range(len(islab_data_line)):
#     _group = re.match("([A-Z]+)\:", islab_data_line[i][27:])
#     if  _group and _group.group(1):
#         islab_data_arr.append({'date': islab_data_line[i][0:10], 'time': islab_data_line[i][11:19], 'type': _group.group(1), 'content': islab_data_line[i][27:], 'count': 1})
# islab_data_frame = pd.DataFrame(data=islab_data_arr)

# islab_data_frame_group = islab_data_frame.groupby(['date', 'type']).agg(np.sum)

# islab_data_frame_plot = islab_data_frame_group.unstack().plot(
#     kind='bar',
#     stacked=True,
#     layout=("Date", "Number"), 
#     figsize=(10, 5)
# )
# islab_data_frame_plot.legend(loc=1, borderaxespad=0.)

# fig = islab_data_frame_plot.get_figure()
# fig.savefig(getattr(settings, 'ROOT_PATH') + "/static/dashboard/img/horizon-admin-overview.png")

class IndexView(tables.DataTableView):
    template_name = 'logmanagement/view/index.html'
    page_title = _("Log Viewer")
    table_class = log_tables.LogTable

    def has_more_data(self, table):
        return self._more

    def get_project_name_from_log_file(self, filename):
        return filename

    def get_resource_name(self, filename):
        filename = filename.replace('.log', '')

        filename = filename.replace('key', 'keystone')

        resource_map = {
            'n-': 'nova.',
            'q-': 'neutron.',
            'g-': 'glance.',
            'c-': 'compu.'
        }

        for item in resource_map:
            filename = filename.replace(item, resource_map[item])

        return filename

    def replace_coloredlog_format(self, text):
        color = ['\033[95m', '\033[94m', '\033[92m', '\033[93m', '\033[91m', '\033[90m', '\033[0m', '\033[1m', '\033[4m']
        for c in color:
            text = text.replace(c, '')

        if not text:
            return ''
        return str(text)

    def parse_log_from_file(self, filename, log_path = '/var/log/apache2/'):
        LogRow = namedtuple('logrow', 'timestamp message project resource pid id level')
        data_arr = []
        file_path = log_path + '/' + filename
        if os.path.isfile(file_path):
            with open(file_path) as f:
                log_data = f.read()
                data_line = log_data.split('\n')

                OPENSTACK_TIMESTAMP = re.compile("\d{4}-\d{2}-\d{2}\s\d{2}:\d{2}:\d{2}\.[0-9]{6}")
                OPENSTACK_PID = re.compile("\s([0-9]+)?\s")
                OPENSTACK_RESOURCE = re.compile("\s([a-z\.]+)?\s")
                OPENSTACK_LOGLEVEL = re.compile("([D|d]ebug|DEBUG|[N|n]otice|NOTICE|[I|i]nfo|INFO|[W|w]arn?(?:ing)?|WARN?(?:ING)?|[E|e]rr?(?:or)?|ERR?(?:OR)?|[C|c]rit?(?:ical)?|CRIT?(?:ICAL)?|[F|f]atal|FATAL|[S|s]evere|SEVERE|[A|a]udit|AUDIT)")
 
                for i in range(min(10, len(data_line))):
                    current_line = self.replace_coloredlog_format(data_line[i])

                    _level = re.findall(OPENSTACK_LOGLEVEL, current_line)
                    _pid = re.findall(OPENSTACK_PID, current_line)
                    _timestamp = re.findall(OPENSTACK_TIMESTAMP, current_line)
                    _resource = re.findall(OPENSTACK_RESOURCE, current_line)
                    
                    _message = current_line

                    if not _timestamp:
                        continue
                    else:
                        _message = _message.replace(_timestamp[0], '')

                    if not _level:
                        _level.append(None)
                    else:
                        _message = _message.replace(_level[0], '')

                    if not _resource:
                        _resource.append(None)
                    else:
                        _message = _message.replace(_resource[0], '')
                    
                    if not _pid:
                        _pid.append(None)
                    else:
                        _message = _message.replace(_pid[0], '')
                    
                    _message = _message.strip()

                    current_dict = LogRow(
                        id = data_line[i][0:10], 
                        pid = _pid[0], 
                        timestamp = _timestamp[0], 
                        level = _level[0], 
                        message = _message, 
                        resource = _resource[0], # self.get_resource_name(filename),
                        project = filename)
                    data_arr.append(current_dict)
        
        return data_arr

    def get_data(self):
        data_arr = []
        self._more = False

        util.setConfig('x', 'y')

        log_path = '/opt/stack/logs'
        for filename in os.listdir(log_path):
            if filename.endswith(".log"):
                data_arr += self.parse_log_from_file(filename, log_path)

        return data_arr
###################################################################################
#	Marvell GPL License
#	
#	If you received this File from Marvell, you may opt to use, redistribute and/or
#	modify this File in accordance with the terms and conditions of the General
#	Public License Version 2, June 1991 (the "GPL License"), a copy of which is
#	available along with the File in the license.txt file or by writing to the Free
#	Software Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307 or
#	on the worldwide web at http://www.gnu.org/licenses/gpl.txt.
#	
#	THE FILE IS DISTRIBUTED AS-IS, WITHOUT WARRANTY OF ANY KIND, AND THE IMPLIED
#	WARRANTIES OF MERCHANTABILITY OR FITNESS FOR A PARTICULAR PURPOSE ARE EXPRESSLY
#	DISCLAIMED.  The GPL License provides additional details about this warranty
#	disclaimer.
###################################################################################

"""
HTML logger inspired by the Horde3D logger.

Usage:

 - call setup and specify the filename, title, version and level
 - call dbg, info, warn or err to log messages.
"""
from __future__ import absolute_import
from builtins import str
import logging
import time
from .BaseFileHandler import BaseFileHandler
#: HTML header (starts the document


_START_OF_DOC_FMT = """<html>
<head>
<meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
<title>%(title)s</title>
<!-- Latest compiled and minified CSS -->
<!--
<link rel="stylesheet" type="text/css" href="https://cdn.datatables.net/v/bs-3.3.7/jq-3.2.1/jq-3.2.1/dt-1.10.16/datatables.min.css"/>

<script type="text/javascript" src="https://cdn.datatables.net/v/bs-3.3.7/jq-3.2.1/jq-3.2.1/dt-1.10.16/datatables.min.js"></script>
-->
<script src="https://ajax.googleapis.com/ajax/libs/jquery/3.4.1/jquery.min.js"></script>
<!-- Latest compiled and minified CSS -->
<link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/3.3.7/css/bootstrap.min.css" integrity="sha384-BVYiiSIFeK1dGmJRAkycuHAHRg32OmUcww7on3RYdg4Va+PmSTsz/K68vbdEjh4u" crossorigin="anonymous">

<!-- Optional theme -->
<link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/3.3.7/css/bootstrap-theme.min.css" integrity="sha384-rHyoN1iRsVXV4nD0JutlnGaslCJuC7uwjduW9SVrLvRYooPp2bWYgmgJQIXwl/Sp" crossorigin="anonymous">

<!-- Latest compiled and minified JavaScript -->
<script src="https://maxcdn.bootstrapcdn.com/bootstrap/3.3.7/js/bootstrap.min.js" integrity="sha384-Tc5IQib027qvyjSMfHjOMaLkfuWVxZxUPnCJA7l2mCWNIpG9mGCD8wGNIcPD7Txa" crossorigin="anonymous"></script>
<link rel="stylesheet" type="text/css" href="https://cdn.datatables.net/1.10.20/css/jquery.dataTables.css">
  
<script type="text/javascript" charset="utf8" src="https://cdn.datatables.net/1.10.20/js/jquery.dataTables.js"></script>
<style>
pre {
margin : 0;
white-space: pre-wrap;
background-color: inherit;
border: none;
border-radius: inherit;
}
</style>
</head>

<body>
<div class="col-md-12 col-xs-12 col-lg-12">
<br>
<h1 style="text-align:center">%(title)s</h1>
<br>
<div class="input-group">
    <select class="form-control" id="min-severity" placeholder="Min Severity">
    </select>
    <span class="input-group-addon">-</span>
    <select class="form-control" id="max-severity" placeholder="Max Severity">
    </select>
</div>
&nbsp
<table id="data_table" class="table table-striped table-bordered" cellspacing="0">
<thead>
    <tr>
        <th style="width: 180px;">Time</th>
        <th style="width: 90px;">Log Level</th>
        <th>Message</th>
    </tr>
</thead>
<tbody>
"""

_END_OF_DOC_FMT = """</tbody></table></div>
</body>
<script>
    $.fn.dataTable.ext.search.push(
        function( settings, data, dataIndex ) {
            let minIndex = severities.indexOf($('#min-severity').find(':selected').text());
            let maxIndex = severities.indexOf($('#max-severity').find(':selected').text());
            var severity = data[1] || 'NOT SET';// use data for the Log Level column
            var severityIndex = severities.indexOf(severity);
            if ( ( maxIndex == -1 && minIndex == -1 ) ||
                 ( minIndex <= severityIndex && severityIndex <= maxIndex ) )
            {
                return true;
            }
            return false;
        }
    );
    
    function fill_select(id, items){
        for(t of items){
            $('#'+id).append(new Option(t, t));
        }
    }
    
    function selectionChanged(selectChanged, selectAffected, selectedOption, startFrom, end){
        let selected = $('#'+selectAffected).find(':selected').text(); //keep affected value
        $('#'+selectAffected).empty(); //empty the affected one

        fill_select(selectAffected, severities.slice(startFrom, end));
        selected = $('#'+selectAffected).find("option:contains('" + selected  + "')").length > 0 ? selected : $("#"+selectAffected+" option:first").val();
        $('#'+selectAffected).val(selected);
    }
    
    var severities = ['NOT SET','TRACE','DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
    $(document).ready(function() {
        for(severity of severities){
            $('#min-severity, #max-severity').append(new Option(severity, severity));
        }
        
        $('#max-severity option:last').attr('selected', 'selected');
        
        var table = $('#data_table').DataTable({
            "lengthMenu": [[-1, 10, 25, 50], ["All", 10, 25, 50]]
        });
        
        $('#min-severity, #max-severity').change( function(e) {
            if(e.target.id == 'min-severity'){
                selectionChanged(e.target.id, 'max-severity', e.target.selectedOptions[0].text, severities.indexOf(e.target.selectedOptions[0].text), severities.length+1);
            }
            else if(e.target.id == 'max-severity'){
                selectionChanged(e.target.id, 'min-severity',e.target.selectedOptions[0].text, 0 ,severities.indexOf(e.target.selectedOptions[0].text) + 1);
            }
            table.draw();
        } );
    } );
    
    
</script>
</html>
"""

_MSG_FMT = """
<tr class="%(class)s">
<td>%(time)s</td>
<td>%(level)s</td>
<td><pre>%(msg)s</pre></td>
</tr>
"""

_MSG_FMT_NO_FMT = """
<tr>
<td width="100"></td>
<td width="100"></td>
<td class="%(class)s"><pre>%(msg)s</pre></td>
</tr>
"""


class HTMLFileHandler(BaseFileHandler):
    """
    File handler specialised to write the start of doc as html and to close it
    properly.
    """

    def __init__(self, title, version, rename=False, *args):
        super(HTMLFileHandler, self).__init__(*args)
        assert self.stream is not None
        # Write header
        if not rename:
            self.stream.write(_START_OF_DOC_FMT % {"title": title, "version": version})

    def close(self):
        if self.renamed:
            self.renamed = False
            super(HTMLFileHandler, self).close()
            return

        # finish document
        if self.stream is not None:
            self.stream.write(_END_OF_DOC_FMT)
            super(HTMLFileHandler, self).close()


class HTMLFormatter(logging.Formatter):
    """
    Formats each record in html
    """
    CSS_CLASSES = {'WARNING': 'warning', 'INFO': 'info', 'TRACE': 'success', 'DEBUG': 'success', 'CRITICAL': 'danger', 'ERROR': 'danger'}

    def __init__(self):
        super(HTMLFormatter, self).__init__()
        self._start_time = time.time()

    def format(self, record):

        record.message = record.getMessage()
        record.asctime = self.formatTime(record, self.datefmt)

        class_name = self.get_class_name(record.levelname)
        t = time.time() - self._start_time

        # handle '<' and '>' (typically when logging %r)
        msg = str(record.msg)
        msg = msg.replace("<", "&#60")
        msg = msg.replace(">", "&#62")

        return _MSG_FMT % {"class": class_name, "level": record.levelname, "time": record.asctime, "msg": msg}

    def get_class_name(self, levelname):
        try:
            class_name = self.CSS_CLASSES[levelname]
        except KeyError:
            class_name = "info"
        return class_name


class HTMLFormatter_NoFormat(HTMLFormatter):
    """
    Formats each record in html
    """

    def __init__(self):
        super(HTMLFormatter_NoFormat, self).__init__()

    def format(self, record):
        class_name = self.get_class_name(record.levelname)
        t = time.time() - self._start_time

        # handle '<' and '>' (typically when logging %r)
        msg = str(record.msg)
        msg = msg.replace("<", "&#60")
        msg = msg.replace(">", "&#62")

        return _MSG_FMT_NO_FMT % {"class": class_name, "msg": msg}

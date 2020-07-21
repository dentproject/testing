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



#shark [ -2 ] [ -a <capture autostop condition> ] ... [ -b <capture ring buffer option>] ...
# [ -B <capture buffer size> ] [ -c <capture packet count> ] [ -C <configuration profile> ]
# [ -d <layer type>==<selector>,<decode-as protocol> ] [ -D ] [ -e <field> ] [ -E <field print option> ]
# [ -f <capture filter> ] [ -F <file format> ] [ -g ] [ -h ] [ -H <input hosts file> ]
# [ -i <capture interface>|- ] [ -j <protocol match filter> ] [ -I ] [ -K <keytab> ]
# [ -l ] [ -L ] [ -n ] [ -N <name resolving flags> ] [ -o <preference setting> ] ...
# [ -O <protocols> ] [ -p ] [ -P ] [ -q ] [ -Q ] [ -r <infile> ] [ -R <Read filter> ]
# [ -s <capture snaplen> ] [ -S <separator> ] [ -t a|ad|adoy|d|dd|e|r|u|ud|udoy ]
# [ -T ek|fields|json|pdml|ps|psml|tabs|text ] [ -u <seconds type>] [ -U <tap_name>]
# [ -v ] [ -V ] [ -w <outfile>|- ] [ -W <file format option>] [ -x ]
# [ -X <eXtension option>] [ -y <capture link type> ] [ -Y <displaY filter> ]
#  [ -M <auto session reset> ] [ -z <statistics> ] [ --capture-comment <comment> ]
#  [ --list-time-stamp-types ] [ --time-stamp-type <type> ] [ --color ]
# [ --no-duplicate-keys ] [ --export-objects <protocol>,<destdir> ]
# [ --enable-protocol <proto_name> ] [ --disable-protocol <proto_name> ]
# [ --enable-heuristic <short_name> ] [ --disable-heuristic <short_name> ]
#  [ <capture filter> ]

class TSHARK_ENUMS():
    from enum import Enum

    class OPTIONS(Enum):
        IN_FILE = '-r'
        OUT_FORMAT_OPTION = '-T'
        SEPARATOR = '-S'
        READ_FILTER = '-R'
        DISPLAY_FILTER = '-Y'
        FIELD_PRINT_OPTION = '-E'
        ADD_FIELD = '-e'
        OUT_RAW_FILE = '-w'
        RAW_PACKET_DATA = '-x'

    class OUT_FORMAT_OPTIONS(Enum):
        FIELDS = 'fields'
        JSON = 'json'

    class FIELD_PRINT_OPTIONS(Enum):
        SEPARATOR = 'separator='
        AGGREGATOR = 'aggregator='
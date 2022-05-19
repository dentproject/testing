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

import re
from copy import deepcopy


def clean_dut_cli_buffer(buffer,clear_patterns_list,strip_empty_lines=True):
    """
    cleans a string
    :param buffer:  the dut buffer containing the response from CLI
    :param clear_patterns_list: list of patterns you wish to clear from the buffer
    :param strip_empty_lines: indicates if to also clear empty lines from buffer
    :type clear_patterns_list: list[str]
    :type buffer: str
    :return: a copy of original buffer cleared from input patterns and optionally stripped from empty lines
    :rtype: str
    """
    buff = deepcopy(buffer)
    for ptrn in clear_patterns_list:
        # handle cases where the pattern contains re expression
        re_pattern = re.compile(ptrn)
        # strip the pattern from the buffer
        buff = re.sub(re_pattern, "", buff)
        if isinstance(ptrn,str ) and ptrn in buff:
            buff = buff.replace(ptrn,"")
    if strip_empty_lines:
        # strip empty lines
        buff = "".join([s+"\n" for s in buff.splitlines(False) if re.sub(r"\s","",s)])
    return buff

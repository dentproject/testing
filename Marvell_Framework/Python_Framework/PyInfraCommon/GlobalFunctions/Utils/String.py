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

from builtins import zip
from copy import copy
import re

class StrEx(str):
	"""
	this class extends builtin class str with more capabilities
	"""
	def replace_mutli_chars(self,old_chars,new_chars,count=None):
		"""
		Return a copy of string S with all occurrences of substring
        old replaced by new.  If the optional argument count is
        given, only the first count occurrences are replaced.

		:param old_chars: string of old chars
		:type old_chars:str
		:type new_chars:str
		:type count: int
		:param new_chars: string of new chars
		:param count: If the optional argument count is
        given, only the first count occurrences are replaced
		:return: a copy of string S with all occurrences of substring
        old_chars replaced by new_chars
        :rtype:StrEx
		"""
		ret = copy(self)
		escapes = ""
		if len(old_chars) != len(new_chars):
			if len(new_chars) > 0:
				raise ValueError("length of old_chars {} not equal to new_chars{}".format(len(old_chars),len(new_chars)))
			else:
				# user want to remove all old_chars
				for o in old_chars:
					if not escapes:
						if "\\" != o:
							ret = ret.replace(o,"")
						else:
							escapes += o+"\\"
					else:
						escapes +=o
						ret = re.sub(escapes,"",ret)
						escapes = ""

				return StrEx(ret)
		for o,n in zip(old_chars,new_chars):
			ret += self.replace(o,n)
		return StrEx(ret)

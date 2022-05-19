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

# from unittest import TestCase
#
#
# class TestInfrastructureExceptions(TestCase):
#
#     def test_file_not_found_exception(self):
#         from Marvell.pytoolsinfra.CommonDef.InfrastructureExceptions.Exceptions import FileNotFoundErrorInfra
#
#         class StamLogger(object):
#             def exception(self, message):
#                 print("i am stam's logger, Bringing you the exception: " + message)
#
#         class Stam(object):
#             def __init__(self):
#                 self.logger = StamLogger()
#
#             def raiseEx(self):
#                 raise FileNotFoundErrorInfra("Where is the file?", r"C:\Progs")
#
#         try:
#             a = Stam()
#             a.raiseEx()
#         except FileNotFoundErrorInfra:
#             print("Exception caught")
#

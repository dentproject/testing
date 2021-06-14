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



from builtins import object
class topic_1(object):
    """
    Explain when topic_1 should be used
    """

    def msgDataSpec(msg):
        """
        - msg: a text string message for recipient
        """

    class subtopic_11(object):
        """
        Explain when subtopic_11 should be used
        """

        def msgDataSpec(msg, extra=None):
            """
            - extra: something optional
            - msg2: a text string message #2 for recipient
            """


class topic_2(object):
    """
    Some something useful about topic2
    """

    # def msgDataSpec(msg=None):
    #     """
    #     - msg: a text string
    #     """

    class subtopic_21(object):
        """
        description for subtopic 21
        """

        def msgDataSpec(arg1):
            """
            - arg1: UNDOCUMENTED
            """
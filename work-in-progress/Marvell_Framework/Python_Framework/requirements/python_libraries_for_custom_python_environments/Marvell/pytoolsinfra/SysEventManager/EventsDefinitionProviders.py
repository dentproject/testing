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



# from builtins import object
class communication:
    """
    under this topic we will have all the list of communication events name
    """
    class connect:
        """
        Connection event - indicates the user that the communication has been connected
        """
        def msgDataSpec(data):
            """
            - data: a class that will hold all the information the event needs
            """

    class disconnect:
        """
        Disconnect event - indicates the user that the communication has been disconnected
        """
        def msgDataSpec(data):
            """
            - data: a class that will hold all the information the event needs
            """

    class connection_lost:
        """
        Connection Lost event - indicates the user that the connection was lost
        """
        def msgDataSpec(data):
            """
            - data: a class that will hold all the information the event needs
            """

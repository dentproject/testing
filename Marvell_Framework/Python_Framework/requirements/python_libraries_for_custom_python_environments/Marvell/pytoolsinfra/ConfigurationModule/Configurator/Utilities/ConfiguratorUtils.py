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

from builtins import str
from builtins import object
def fill_object(prototype, subject):
    if hasattr(prototype, '__dict__'):
        vs = vars(prototype)

        for prop, value in list(vs.items()):
            if not prop.startswith('__') and hasattr(subject, prop):
                setattr(subject, prop, getattr(prototype, prop))


def parse_integer(value):
    """
        Returns an integer representation of the value in value
        :param value: the value to check
        :return: The int if it is an integer, None otherwise
        """
    try:
        return int(value)
    except ValueError:
        try:
            # To avoid error in case of '0.0'
            return int(float(value))
        except ValueError:
            return None


def parse_float(value):
    """
    Returns a float representation of the value in value
    :param value: the value to check
    :return: The float if it is float, None otherwise
    """
    try:
        return float(value)
    except ValueError:
        return None


def get_similarity_rate(obj1, obj2, ignore_basic_attr=True):
    """
    Determines the similarity of obj2 to obj1, obj1 is the prototype
    :param ignore_basic_attr: weather to ignore attributes such as __dict__
    :param obj1: the prototype
    :param obj2: the subject
    :return: the similarity rate
    """
    if obj2 is None:
        return 1

    result = calculate_similarity(obj1, obj2, ignore_basic_attr)

    rate = result.get_rate()

    return rate


def calculate_similarity(obj1, obj2, ignore_basic_attr=True, sim_data=None):
    if sim_data is None:
        sim_data = SimilarData()

    if hasattr(obj1, '__dict__'):
        vs = vars(obj1)

        for prop, value in list(vs.items()):
            if ignore_basic_attr and not prop.startswith('__'):
                sim_data.add_to_prototype(str(prop))
                if hasattr(obj2, prop):
                    sim_data.add_to_subject(str(prop))
                    calculate_similarity(getattr(obj1, prop), getattr(obj2, prop), ignore_basic_attr,
                                         sim_data)

    return sim_data


class SimilarData(object):
    def __init__(self):
        self.prototype_props = []
        self.subject_props = []

    def add_to_prototype(self, prop):
        self.prototype_props.append(prop)

    def add_to_subject(self, prop):
        self.subject_props.append(prop)

    def get_rate(self):
        return len(self.subject_props) / float(len(self.prototype_props))

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

from __future__ import print_function
from builtins import str
from builtins import range
from past.builtins import basestring
from builtins import object
import json
import copy
import re
import collections
import jsonpickle



class JSONSerializable(object):
    """
    a class that allows serializing objects to json files
    """
    def toJSON(self,path=None):
        """
        serialize this object to json string if path is specified then also write the json string to file
        :param path: path to file to write serialized json string to
        :return: serialized json string or None if not succeeded
        :rtype: str
        """
        ret = None
        try:
            ret = jsonpickle.encode(self)
            if path:
                with open(path,"w") as data_file:
                    data_file.write(ret)
                    data_file.close()

        except Exception as e:
            err =  self.__class__.__name__+ "::fromJson: "
            err += str(e)
            print (err)
            ret = None
        finally:
            return ret

    def fromJson(self,filepath):
        """
        deserialize to this object from json file
        :param filepath: path to json file to restore object from
        :return: True or False if failed
        """
        res = True
        try:
            with open(filepath) as data_file:
                data = data_file.read()
                tmp = jsonpickle.decode(data)
                for k,v in list(tmp.__dict__.items()):
                    if hasattr(self,k):
                        # cast unicode to string type
                        self._cast_to_str(tmp,k)
                        setattr(self,k,getattr(tmp,k))
        except Exception as e:
            err =  self.__class__.__name__+ "::fromJson: "
            if isinstance(e,IOError):
                import os
                err += e.strerror + ": " + os.path.abspath(e.filename)
            else:
                err += str(e)
            print (err)
            res = False
        finally:
            return res

    def _cast_to_str(self,obj,key,index=None):
        val = getattr(obj, key)
        if isinstance(val,list) and index is not None:
            if type(val[index])  == str:
                newval = str(val[index])
                val[index] = newval
                setattr(obj, key, val)
            else:
                # check if list element value is class
                if len(re.findall(r' object at ', str(val[index]))) > 0:
                    if hasattr(val[index], "__dict__"):
                        for k, v in list(val[index].__dict__.items()):
                            # check if object is class
                            self._cast_to_str(val[index], k)
        else:
            # check if value is class
            if len(re.findall(r' object at ', str(val))) > 0:
                if hasattr(val,"__dict__"):
                    for k,v in list(val.__dict__.items()):
                        # check if object is class
                        self._cast_to_str(val,k)
                elif isinstance(val, collections.Iterable) and \
                isinstance(val, basestring) is False:
                    for i in range(len(val)):
                        self._cast_to_str(obj,key,i)
            elif type(val) == str:
                newval = str(val)
                setattr(obj,key,newval)


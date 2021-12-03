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
from builtins import object
import sys
import os
import re
import datetime
import getpass

from subprocess import Popen, PIPE, STDOUT

class MibLoader(object):
    """
    The class builds the PySnmp native MIB from standard MIB file, defined in Abstract Syntax Notation One (ASN.1),
    by calling the mibdump.py script installed as a part of pysmi package.
    """
    def __init__(self, mib_name=None, mib_source_url='http://mibs.snmplabs.com/asn1/@mib@', destDir=None):
        """
        :param mibName: MIB file name
        :type mibName: str
        :param mibSourceURL: MIB source URL
        URL - file, http, https, ftp, sftp schemes are supported.
        Use @mib@ placeholder token in URL location to refer to MIB module name requested.
        :type mibSourceURL: str
        :param destDir: destination directory
        :type destDir: str | None
        """
        self._mibBuilderScriptPath = os.path.join(self.__getInterpreterScriptsPath(), 'mibdump.py')
        #self._destinationDirectory = "C:\\temp1\\mibs"
        #self._destinationDirectory = os.path.join(self.__getSitePackagesPath(), 'pysnmp\smi\mibs')

        # setters call
        self.mibName = mib_name
        self.mibSourceUrl = mib_source_url
        self.destinationDirectory = destDir

    def setBuildParams(self, mib_name=None, mib_source_url='http://mibs.snmplabs.com/asn1/@mib@', destDir=None):
        """
        :param mibName: MIB file name
        :type mibName: str
        :param mibSourceURL: MIB source URL
        URL - file, http, https, ftp, sftp schemes are supported.
        Use @mib@ placeholder token in URL location to refer to MIB module name requested.
        :type mibSourceURL: str
        :param destDir: destination directory
        :type destDir: str | None
        """

        # setters call
        self.mibName = mib_name
        self.mibSourceUrl = mib_source_url
        self.destinationDirectory = destDir


    @property
    def mibName(self):
        return self._mibName

    @mibName.setter
    def mibName(self, value):
        if value is None or type(value) != str:
            raise ValueError("Wrong MIB name argument. Should be a string!")
        else:
            self._mibName = value

    @property
    def mibSourceUrl(self):
        return self._mibSourceUrl

    @mibSourceUrl.setter
    def mibSourceUrl(self, value):
        if value is None or type(value) != str:
            raise ValueError("Wrong MIB name argument. Should be a string!")
        else:
            self._mibSourceUrl = value

    @property
    def destinationDirectory(self):
        return self._destinationDirectory

    @destinationDirectory.setter
    def destinationDirectory(self, value):
        if value is None:
            self._destinationDirectory = os.path.join(self.__getSitePackagesPath(), 'pysnmp\smi\mibs')
        elif type(value) != str:
            raise ValueError("Wrong destination directory argument. Should be a string!")
        else:
            self._destinationDirectory = value

    def Build(self):
        #mibNames = ' '.join(self.mib_names)
        command = 'python {} --destination-directory {} --mib-source {} {}'.format(self._mibBuilderScriptPath,
                                                                                     self._destinationDirectory,
                                                                                     self._mibSourceUrl, self._mibName)

        pOut,pRetCode = self.RunCommand(command)
        reportStr  = '{}\nBuild finished {} errors, exit code: {}'.format(pOut, 'without' if pRetCode == 0 else
        'Fail', pRetCode)
        print(reportStr)
        self.__updateLog(reportStr)

    def __getInterpreterScriptsPath(self):
        return os.path.join(sys.exec_prefix, 'Scripts')

    def __getSitePackagesPath(self):
        from distutils.sysconfig import get_python_lib
        return get_python_lib()

    def RunCommand(self, command):
        print('Executing command: {}'.format(command))
        process = Popen(command, stdout=PIPE, stderr=STDOUT, shell=True)
        return process.communicate()[0],process.returncode

    def __updateLog(self, logStr):
        scriptDirName = os.path.dirname(os.path.realpath(__file__))
        logFileName = os.path.splitext(__file__)[0] + "_log.txt"
        time = datetime.datetime.now().strftime("%H:%M:%S on %B %d, %Y")
        header = "Built at {}, by {}".format(time, getpass.getuser())
        seperatorSymbol = "#"*80
        logStr = "{}\n{}\n{}\n{}\n{}{}".format(seperatorSymbol, header, seperatorSymbol, logStr, seperatorSymbol,"\n"*3)
        with open(logFileName, "a") as myfile:
            myfile.write(logStr)

def main():
    #ml = MibLoader('Sentry3-MIB','http://mibs.snmplabs.com/asn1/@mib@')
    #C:\Git\Python_Platform_Validation_Tests\PyInfraCommon\Managers\PowerDistributionUnit\mibs
    ml = MibLoader('Sentry3-MIB', 'http://mibs.snmplabs.com/asn1/@mib@',
                   'C:\Git\Python_Platform_Validation_Tests\PyInfraCommon\Managers\PowerDistributionUnit\mibs')

    ml.Build()
    ml.mibName = 'POWERNET-MIB'
    ml.Build()
    #ml.updateLog('Stas haha')
    #ml = MibLoader('powernet423.mib','ftp://ftp.apc.com/apc/public/software/pnetmib/mib/423/@mib@')
    #scriptDir = os.path.dirname(os.path.realpath(__file__)

if __name__ == "__main__":
    main()
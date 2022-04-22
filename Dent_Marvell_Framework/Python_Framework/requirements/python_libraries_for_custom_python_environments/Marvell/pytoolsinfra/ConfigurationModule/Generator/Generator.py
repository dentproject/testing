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
from __future__ import absolute_import
from builtins import object
import os

from enum import Enum

from .CodeGenerator import CodeGenerator
from .CodeGeneratorHw import CodeGeneratorHw
from .SheetBasedGenerator import SheetBasedGenerator


class Generator(object):
    val_generator = SheetBasedGenerator(CodeGenerator())
    hw_generator = SheetBasedGenerator(CodeGeneratorHw())

    class GeneratorType(Enum):
        VAL_GENERATOR_TYPE = 0
        HW_GENERATOR_TYPE = 1

    def __init__(self, reinit=False, gen_type=GeneratorType.VAL_GENERATOR_TYPE):
        if reinit:
            if gen_type == self.GeneratorType.VAL_GENERATOR_TYPE:
                self.generator = SheetBasedGenerator(CodeGenerator())
            elif gen_type == self.GeneratorType.HW_GENERATOR_TYPE:
                self.generator = SheetBasedGenerator(CodeGeneratorHw())
            else:
                self.generator = SheetBasedGenerator(CodeGenerator())
        else:
            if gen_type == self.GeneratorType.VAL_GENERATOR_TYPE:
                self.generator = self.val_generator
            elif gen_type == self.GeneratorType.HW_GENERATOR_TYPE:
                self.generator = self.hw_generator
            else:
                self.generator = self.val_generator

    def create(self, input_file_path, output_file, key=None):
        if not os.path.exists(input_file_path):
            print("----ERROR----> input_file_path points at a file that doesn't exist")
            return

        if not key:
            self.generator.create_workbook_code(input_file_path, output_file, True)  # return workbook presentation
        elif '.' not in key:
            self.generator.create_sheet_code(key, input_file_path, output_file, True)  # return sheet presentation
        else:
            # return section presentation
            key_sheet_name, key_section_name = key.split(".")
            self.generator.create_section_code(0, key_sheet_name, key_section_name, input_file_path, output_file, None,
                                               True)



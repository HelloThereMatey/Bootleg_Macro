import unittest
from custom_FI import CategoryData
from tkinter.filedialog import askopenfilename
import json
from pprint import pprint
import logging
import os

fdel = os.path.sep
wd = os.path.dirname(__file__) 
  

def TestCategoryData(inputDict: dict = None):
    if inputDict is None: 
        category_set = CategoryData(CategoryJSON_File_Path=askopenfilename())
    else:
        print("Input data: ", type(inputDict), ", keys: ", inputDict.keys())
        category_set = CategoryData(CategoryDict=inputDict)    
    testLog = "Input dict: \n"+json.dumps(inputDict)+"\n                                                          \n"    
    testLog += "Keys of the levels dict: \n"
    print("Keys of the levels dict: ",category_set.levels.keys())
    for level in category_set.levels.keys():
        testLog += level+", "
    testLog += "\n                                                          \n"   
    testLog += json.dumps(category_set.levels)
    testLog += "\n                                                          \n" 
    return testLog


if __name__ == '__main__':
    with open('/Users/jamesbishop/Documents/Python/Bootleg_Macro/MacroBackend/BEA_Data/Categories/PCE.json') as cunt:
        data = cunt.read()
        fur_catz = json.loads(data)
    
    log = ""
    testdicts = {"TopLevel": fur_catz, "Level_3": fur_catz['Personal consumption expenditures'], 
                 "Level_2": fur_catz['Personal consumption expenditures']['Services'],
                 "Level_1": fur_catz['Personal consumption expenditures']['Services']['Housing and utilities']}
    
    for test in testdicts:
        test_results = TestCategoryData(inputDict=testdicts[test])
        log += test_results+"\n############################################################################################################\n"

    with open(wd+fdel+"test_log.txt", 'w') as cunthead:
        cunthead.write(log)
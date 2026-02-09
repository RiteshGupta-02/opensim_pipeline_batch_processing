import opensim as osim
import os

os.chdir(r"D:\student\MTech\test") #already present
so_analysis = osim.AnalyzeTool("so_setup_s01_stw4.xml")
so_analysis.setResultsDir(r"D:\student\MTech\test\output")
so_analysis.run()
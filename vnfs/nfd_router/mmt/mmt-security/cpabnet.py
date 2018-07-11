import numpy as np
import pandas as pd
import sys
from pgmpy.models import BayesianModel
from pgmpy.inference import BeliefPropagation

from pgmpy.readwrite.BIF import BIFReader
reader = BIFReader('cpa.bif')
new_model = reader.get_model()

text_file = open("data4bnet.txt", "r")
lines = text_file.readlines()
min_value = np.array([0 for x in range(19)])
max_value = np.array([2 for x in range(19)])
for i in range(19):
        list_lines=map(int,lines[i].split("\t"))
        min_value[i]=list_lines[0]-1
        max_value[i]=list_lines[0]-1
        for j in range(len(list_lines)):           
                if (list_lines[j]-1<min_value[i]):
                        min_value[i]= list_lines[j]-1
                if (list_lines[j]-1>max_value[i]):
                        max_value[i]= list_lines[j]-1
text_file.close()
#input_value = 325235087
input_value=int(sys.argv[1])
test_value = np.array([0 for x in range(18)])
for i in reversed(range(18)):
        test_value[i]=int(input_value/(3**i))
        input_value=input_value%(3**i)
for i in reversed(range(18)):
        if (max_value[i]==1):
                test_value[i]=0
        elif (min_value[i]==1):
                if (test_value[i]<1):
                        test_value[i]=0
                else:
                        test_value[i]=test_value[i]-1
#print(model.check_model())
#bp.calibrate()
bp = BeliefPropagation(new_model)
result=bp.map_query(variables=['AN'],evidence={'CsM': test_value[0], 'CsH': test_value[1], 'CsI': test_value[2], 'InI': test_value[3], 'InD': test_value[4], 'InN': test_value[5],'OutI': test_value[6], 'OutD': test_value[7], 'OutN': test_value[8],'PitC': test_value[9], 'PitUp': test_value[10], 'PitD': test_value[11], 'PitT': test_value[12], 'PitUn': test_value[13], 'IDro': test_value[14], 'DDro': test_value[15], 'NDro': test_value[16], 'PitN': test_value[17]})
print (result['AN'])
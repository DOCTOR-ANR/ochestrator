import numpy as np
import pandas as pd
from pgmpy.models import BayesianModel
from pgmpy.factors.discrete import TabularCPD
from pgmpy.inference import BeliefPropagation
from pgmpy.estimators import BayesianEstimator
from pgmpy.readwrite.BIF import BIFWriter
model = BayesianModel([('CsM', 'OutI'), ('CsM', 'PitUp'), ('CsM', 'IDro'),
                        ('CsH', 'OutD'), ('CsH', 'PitD'), ('CsH', 'DDro'),
                        ('CsI', 'OutD'), ('CsI', 'PitUp'), ('CsI', 'PitD'), ('CsI', 'DDro'),
                        ('InI', 'CsM'), ('InI', 'CsH'), ('InI', 'OutN'), ('InI', 'IDro'), ('InI', 'PitC'), ('InI', 'PitUp'),
                        ('InD', 'CsI'), ('PitC', 'DDro'),
                        ('InN', 'OutN'), ('InN', 'PitUp'), ('InN', 'NDro'),
                        ('PitC', 'PitT'), ('PitC', 'PitN'),
                        ('PitD', 'PitT'), ('PitD', 'PitN'),
                        ('PitUn', 'PitD'),
                        ('AN', 'CsM'), ('AN', 'CsI'), ('AN', 'CsH'), ('AN', 'OutI'), ('AN', 'OutD'), ('AN', 'InD'), ('AN', 'InI'), ('AN', 'PitUn'), ('AN', 'PitC'), ('AN', 'PitUp'), ('AN', 'PitD'), ('AN', 'PitT'), ('AN', 'PitN'), ('AN', 'DDro')])           
#LOAD TRAIN DATA
data = np.array([[0 for x in range(19)] for y in range(2240)])
text_file = open("data4bnet.txt", "r")
lines = text_file.readlines()
min_value = np.array([0 for x in range(19)])
max_value = np.array([2 for x in range(19)])
for i in range(19):
        list_lines=map(int,lines[i].split("\t"))
        min_value[i]=list_lines[0]-1
        max_value[i]=list_lines[0]-1
        for j in range(len(list_lines)):           
                data[j][i]=list_lines[j]-1
                if (list_lines[j]-1<min_value[i]):
                        min_value[i]= list_lines[j]-1
                if (list_lines[j]-1>max_value[i]):
                        max_value[i]= list_lines[j]-1
text_file.close()
values = pd.DataFrame(data,columns=['CsM', 'CsH', 'CsI', 'InI', 'InD', 'InN', 'OutI', 'OutD', 'OutN', 'PitC', 'PitUp', 'PitD', 'PitT', 'PitUn', 'IDro', 'DDro', 'NDro', 'PitN', 'AN'])
model.fit(values, estimator=BayesianEstimator)
writer = BIFWriter(model)
writer.write_bif('cpa.bif')

#print (model.nodes())
"""
print (model.get_cpds('CsM'))
print (model.get_cpds('CsH'))
print (model.get_cpds('CsI'))
print (model.get_cpds('InI'))
print (model.get_cpds('InD'))
print (model.get_cpds('InN'))
print (model.get_cpds('OutI'))
print (model.get_cpds('OutD'))
print (model.get_cpds('OutN'))
print (model.get_cpds('PitC'))
print (model.get_cpds('PitUp'))
print (model.get_cpds('PitD'))
print (model.get_cpds('PitT'))
print (model.get_cpds('PitUn'))
print (model.get_cpds('IDro'))
print (model.get_cpds('DDro'))
print (model.get_cpds('NDro'))
print (model.get_cpds('PitN'))
print (model.get_cpds('AN'))
print (model.get_cpds())
"""

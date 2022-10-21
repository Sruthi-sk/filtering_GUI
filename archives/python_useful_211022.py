# -*- coding: utf-8 -*-
"""
Created on Fri Oct 21 15:41:27 2022
"""

#%% row and column major problems -------------------------------------------------------
import numpy as np
c = np.array([[1,2,3],
              [4,6,7]], order='C')
f = np.array([[1,2,3],
              [4,6,7]], order='F')
f.flags
  # C_CONTIGUOUS : False   # if True, row major
  # F_CONTIGUOUS : True   # column major
print(f.ravel(order='K'))   # [1 4 2 6 3 7]
print(c.ravel(order='K'))   # [1 2 3 4 6 7]

a = np.array([1,4,5,6])
res=a[::-1]
res.flags
  # C_CONTIGUOUS : False
  # F_CONTIGUOUS : False
#this caused an issue when I had to reverse data before filtering
res = np.asfortranarray(res) # or
res = np.ascontiguousarray(res)#- to make flags true

#%%
'''
#https://betterprogramming.pub/pythons-match-case-is-too-slow-if-you-don-t-understand-it-8e8d0cf927d
Summary:
    if-else and match-case work pretty much the same, use match-case if 
    you have a somewhat complex pattern you want to check for
    if you have a large number of possible cases that can be treated as simple conditions 
    or you need runtime performance, you would be better off using a hash table or a lookup table
    lookup tables and hash tables aren’t just limited to storing simple values, 
    but they can also contain whole functions or complex objects
    if you are coding in Python, chances are your primary goal is not runtime performance, 
    for which you should opt for a compiled language.
    The python match-case is not a performant lookup table-like tool 
    similar to how the C compiler optimizes switch-case statements
'''

#%% explore time taken for the filters
''' keep taking data from a synthetic stream - instead of a stream, from a prerecorded file?
, filter it and then only,take next data from buffer
----- or just run the filter on same piece of data 100 times - check time of filter
Current problem 
- Time -If we use higher order filters, more complex - so more time?
- We want filter to update based on our data
'''

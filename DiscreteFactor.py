# combinatorics
from itertools import product
# table formating for screen output
from tabulate import tabulate
# numpy is used for n-dimensional arrays
import numpy as np
import copy

class Factor:
    '''
    Factors are a generalisation of discrete probability distributions over one or more random variables.
    Each variable must have a name (which may be a string or integer).
    The domain of the factor specifies which variables the factor operates over.
    The outcomeSpace specifies the possible values of each random variable. 
    
    
    The probabilities are stored in a n-dimensional numpy array, using the domain and outcomeSpace
    as dimension and row labels respectively.
    '''
    def __init__(self, domain, outcomeSpace, table=None):
        '''
        Inititalise a factor with a given domain and outcomeSpace. 
        All probabilities are set to zero by default.
        '''
        self.domain = tuple(domain) # tuple of variable names, each of which may be a string or integer.
        
        # Initialise the outcomeSpace, which is provided as a dictionary.
        self.outcomeSpace = copy.copy(outcomeSpace)

        if table is None:
            # By default, intitialize with a uniform distribution
            self.table = np.ones(shape=tuple(len(outcomeSpace[var]) for var in self.domain))
            self.table = self.table/np.sum(self.table)
        else:
            self.table = table.copy()        
    
    def __getitem__(self, outcomes):
        '''
        This function allows direct access to individual probabilities.
        E.g. if the factor represents a joint distribution over variables 'A','B','C','D', each with outcomeSpace [0,1,2],
        then `Factor[0,1,0,2]` will return the probability that the four variables are set to 0,1,0,2 respectively.
        
        The outcomes used for indexing may also be strings. If in the example above the outcomeSpace of each variable is
        ['true','false'], then `factor['true','false','true','true']` will return the probability that 
        A='true', B='false', C='true' and D='true'. 
        
        The order of the indices is determined by the order of the variables in self.domain.
        '''
        
        # check if only a single index was used.
        if not isinstance(outcomes, tuple):
            outcomes = (outcomes,)
            
        assert(len(outcomes) == len(self.domain)) # confirm there is a correct number of indicies
        
        # convert outcomes into array indices
        indices = tuple(self.outcomeSpace[var].index(outcomes[i]) for i, var in enumerate(self.domain))
        return self.table[indices]
    
    def __setitem__(self, outcomes, new_value):
        '''
        This function is called when setting a probability. E.g. `factor[0,1,0,2] = 0.5`.        
        '''
        if not isinstance(outcomes, tuple):
            outcomes = (outcomes,)
        indices = tuple(self.outcomeSpace[var].index(outcomes[i]) for i, var in enumerate(self.domain))
        self.table[indices] = new_value
        
    def __str__(self):
        '''
        This function determines the string representation of an object.
        In this case, the function prints out a row for every possible instantiation 
        of the factor, along with the associated probability.
        This function will be called whenever you print out this object, i.e.
        a_prob = Factor(...)
        print(a_prob)
        '''
        table = []
        outcomeSpaces = [self.outcomeSpace[var] for var in self.domain]
        for key in product(*outcomeSpaces):
            row = list(key)
            row.append(self[key])
            table.append(row)
        header = list(self.domain) + ['Pr']
        return tabulate(table, headers=header, tablefmt='fancy_grid') + '\n'

    def __mul__(self, other):
        '''
        Override the * operator, so that it can be used to join factors
        '''
        return self.join(other)     
        
    def join(self, other):
        '''
        This function multiplies two factors: one in this object and the factor in `other`
        
        Usage: A.join(B)
        This returns a factor which has the join (multiplication) of A and B.
        '''
        # confirm that any shared variables have the same outcomeSpace
        for var in set(other.domain).intersection(set(self.domain)):
            if self.outcomeSpace[var] != other.outcomeSpace[var]:
                raise IndexError('Incompatible outcomeSpaces. Make sure you set the same evidence on all factors')

        # extend current domain with any new variables required
        new_dom = list(self.domain) + list(set(other.domain) - set(self.domain)) 

        self_t = self.table
        other_t = other.table
        
        # to prepare for multiplying arrays, we need to make sure both arrays have the correct number of axes
        # We will do this by adding axes to the end of the shape of each array.
        num_new_axes = len(set(other.domain) - set(self.domain))
        for i in range(num_new_axes):
            # add an axis to self_t. E.g. if shape is [3,5], new shape will be [3,5,1]
            self_t = np.expand_dims(self_t, -1) 
        num_new_axes = len(set(self.domain) - set(other.domain))
        for i in range(num_new_axes):
            # add an axis to other_t. E.g. if shape is [3,5], new shape will be [3,5,1]
            other_t = np.expand_dims(other_t, -1)       

        # And we need the new axes to be transposed to the correct location
        old_order = list(other.domain) + list(set(self.domain) - set(other.domain)) 
        new_order = []
        for v in new_dom:
            new_order.append(old_order.index(v))
        # reorder the axes of other_t to new_order (look up np.transpose)
        other_t = other_t.transpose(tuple(new_order))

        # Now that the arrays are all set up, we can rely on numpy broadcasting to work out which numbers need to be multiplied.
        # https://numpy.org/doc/stable/user/basics.broadcasting.html
        # multiply the two arrays
        new_table = self_t * other_t

        # The final step is to create the new outcomeSpace
        new_outcomeSpace = self.outcomeSpace.copy()
        new_outcomeSpace.update(other.outcomeSpace)

        # create a new factor out of the the new domain, outcomeSpace and table
        # in the following line, `self.__class__` is the same as `Factor` (except it doesn't break things when subclassing)
        return self.__class__(tuple(new_dom), new_outcomeSpace, table=new_table)

    def evidence(self, **kwargs):
        '''
        Sets evidence by modifying the outcomeSpace
        This function must be used to set evidence on all factors before joining,
        because it removes the irrelevant values from the factor. 

        Usage: fac.evidence(A='true',B='false')
        This returns a factor which has set the variable 'A' to 'true' and 'B' to 'false'.
        '''
        f = self.copy()
        evidence_dict = kwargs
        for var, value in evidence_dict.items():
            if var in f.domain:

                # find the row index that corresponds to var = value (use f.outcomeSpace)
                
                if value in f.outcomeSpace[var]:
                    valuepos = self.outcomeSpace[var].index(value)
                
                # create a tuple of "slice" objects, all of them `slice(None)` except
                # for the one corresponding to the `var` axis.
                # (for loop or list comprehension required)

    
                slices = tuple(slice(valuepos, valuepos+1) if v == var else slice(None) for v in f.domain)             
                

                # use the tuple to select the required section of f.table
                f.table = f.table[slices]

                # modify the outcomeSpace to correspond to the changes just made to self.table
                f.outcomeSpace[var] = (value,)
        return f

    def marginalize(self, var):
        '''
        This function removes a variable from the domain, and sums over that variable in the table
        
        Usage: fac.marginalize('A')
        This returns a factor in which variable A is marginalized (summed out).
        '''

        # create new domain
        new_dom = list(self.domain)
        new_dom.remove(var)

        # remove an axis of the table by summing it out
        # work out which axis to sum over
        axis = self.domain.index(var)
        # sum over that axis
        new_table =  np.sum(self.table, axis)

        # in the following line, `self.__class__` is the same as `Factor` (except it doesn't break things when subclassing)
        return self.__class__(tuple(new_dom),self.outcomeSpace, new_table)

    def normalize(self):
        '''
        Normalise the factor so that all probabilities add up to 1
        
        Usage: fac.normalize()
        This returns a normalized factor.
        '''
        # divide all elements of table by sum of every element
        self.table = self.table/np.sum(self.table) 
        return self
    
    def copy(self):
        return copy.deepcopy(self)
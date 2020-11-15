from prettytable import PrettyTable
import abc

class TableString(object):
    """Metaclass for formatted table strings."""
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod    
    def __unicode__(self): return

    @abc.abstractmethod    
    def __str__(self): return
    
    @abc.abstractmethod
    def get_string(self,outfile,**kwargs):
        '''return the string'''
        return


class latexTable(TableString):
    """Construct and export a LaTeX table from a PrettyTable.

    latexTableExporter(table,**kwargs)

    Required argument:
    -----------------
    table - an instance of prettytable.PrettyTable

    Optional keyword arguments:
    --------------------------
    caption - string - a caption for the table
    label - string - the latex reference ID
    """
    def __init__(self,table,caption='',label=''):
        self.table = table
        self.caption = caption
        self.label = label

    def __str__(self):
        return self.get_string()
        
    def __unicode__(self):
        return self.get_string()

    def get_string(self,**kwargs):
        ''' Construct LaTeX string from table'''
        options = self.table._get_options(kwargs) #does not work bc of prettytable bug
        s = r'\begin{table}' + '\n'
        s = s + r'\centering' + '\n'
        s = s + r'\caption{%s}\label{%s}' %(self.caption,self.label)
        s = s + '\n'
        s = s + r'\begin{tabular}{'
        s = s + ''.join(['c',]*len(self.table.field_names)) + '}'
        s = s + '\n'
        s = s + '&'.join(self.table.field_names)+r'\\ \hline'+'\n'
        rows = self.table._format_rows(self.table._rows,options)
        #print rows
        for i in range(len(rows)):
            row = [str(itm) for itm in rows[i]]
            s = s + '&'.join(row)
            if i != len(self.table._rows)-1:
                s = s + r'\\'
            s = s + '\n'
            
        s = s + r'\end{tabular}' + '\n'
        s = s + r'\end{table}'
        return s
        


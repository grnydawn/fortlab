"""
Fortran single line statements.

-----
Permission to use, modify, and distribute this software is given under the
terms of the NumPy License. See http://scipy.org.

NO WARRANTY IS EXPRESSED OR IMPLIED.  USE AT YOUR OWN RISK.
Author: Pearu Peterson <pearu@cens.ioc.ee>
Created: May 2006
-----
"""

__all__ = ['GeneralAssignment',
           'Assignment','PointerAssignment','Assign','Call','Goto','ComputedGoto','AssignedGoto',
           'Continue','Return','Stop','Print','Read','Read0','Read1','Write','Flush','Wait',
           'Contains','Allocate','Deallocate','ModuleProcedure','Access','Public','Private',
           'Close','Cycle','Backspace','Endfile','Rewind','Open','Format','Save',
           'Data','Nullify','Use','Exit','Parameter','Equivalence','Dimension','Target',
           'Pointer','Protected','Volatile','Value','ArithmeticIf','Intrinsic',
           'Inquire','Sequence','External','Namelist','Common','Optional','Intent',
           'Entry','Import','ForallStmt','SpecificBinding','GenericBinding',
           'FinalBinding','Allocatable','Asynchronous','Bind','Else','ElseIf',
           'Case','TypeGuard', 'WhereStmt','ElseWhere','Enumerator','FortranName','Threadsafe',
           'Depend','Check','CallStatement','CallProtoArgument','Pause',
           'Comment', 'StmtFuncStatement'] # KGEN addition
           #'Case','WhereStmt','ElseWhere','Enumerator','FortranName','Threadsafe', # KGEN deletion
           #'Comment'] # KGEN deletion

import re
import os
import sys

from fortlab.resolver.base_classes import Statement, Variable

# Auxiliary tools

from fortlab.resolver.utils import split_comma, specs_split_comma, AnalyzeError, ParseError,\
     get_module_file, parse_bind, parse_result, is_name, classes
#from utils import classes

# start of KGEN addition
#import fortlab.resolver.Fortran2003 as Fortran2003
from fortlab.resolver import Fortran2003
from fortlab.kgutils import traverse, pack_innamepath, ProgramException, UserException, logger

#import logging
#logger = logging.getLogger('kgen')

class DummyStatement(object):
    pass
# end of KGEN addition

class StatementWithNamelist(Statement):
    """
    <statement> [ :: ] <name-list>
    """
    def process_item(self):
        if self.item.has_map():
            self.isvalid = False
            return
        if hasattr(self,'stmtname'):
            clsname = self.stmtname
        else:
            clsname = self.__class__.__name__
        line = self.item.get_line()[len(clsname):].lstrip()
        if line.startswith('::'):
            line = line[2:].lstrip()
        self.items = items = []
        for item in split_comma(line):
            if not is_name(item):
                self.isvalid = False
                return
            items.append(item)
        return

    def tofortran(self,isfix=None):
        if hasattr(self,'stmtname'):
            clsname = self.stmtname.upper()
        else:
            clsname = self.__class__.__name__.upper()
        s = ', '.join(self.items)
        if s:
            s = ' ' + s
        return self.get_indent_tab(isfix=isfix) + clsname + s

    # start of KGEN addition
    def tokgen(self):
        if hasattr(self, 'new_items'):
            items = self.new_items
            del self.new_items
        else:
            items = self.items
    
        if hasattr(self,'stmtname'):
            clsname = self.stmtname.upper()
        else:
            clsname = self.__class__.__name__.upper()
        s = ', '.join(items)
        if s:
            s = ' ' + s
        return clsname + s

    def resolve_uname(self, uname, request, config):
        for item in self.items:
            if any(elem in item for elem in r'-=>'):
                print('DEBUG: %s has non-ascii character.'%self.__class__)
        if uname.firstpartname() in self.items:
            self.add_geninfo(uname, request)
    # end of KGEN addition

# Execution statements

class GeneralAssignment(Statement):
    """
    <variable> = <expr>
    <pointer variable> => <expr>
    """

    match = re.compile(r'\w[^=]*\s*=\>?').match
    item_re = re.compile(r'(?P<variable>\w[^=]*)\s*(?P<sign>=\>?)\s*(?P<expr>.*)\Z',re.I).match
    _repr_attr_names = ['variable','sign','expr'] + Statement._repr_attr_names

    def process_item(self):

        m = self.item_re(self.item.get_line())
        if not m:
            self.isvalid = False
            return
        self.sign = sign = m.group('sign')
        if isinstance(self, Assignment) and sign != '=':
            self.isvalid = False
            return
        elif isinstance(self, PointerAssignment) and sign != '=>':
            self.isvalid = False
            return
        else:
            if sign=='=>':
                self.__class__ = PointerAssignment
            else:
                self.__class__ = Assignment
        apply_map = self.item.apply_map
        v1 = v = m.group('variable').replace(' ','')
        while True:
            i = v.find(')')
            if i==-1:
                break
            v = v[i+1:]
            if v.startswith('(') or v.startswith(r'%'):
                continue
            if v:
                self.isvalid = False
                return
        self.variable = apply_map(v1)
        # start of KGEN addition
        # check variable
        if any( self.variable.endswith(ch) for ch in  [ '/' ] ):
            self.isvalid = False
            return
        # end of KGEN addition
        self.expr = apply_map(m.group('expr'))
        return

    # start of KGEN addition
    def tokgen(self):
        return '%s %s %s' % (self.variable, self.sign, self.expr)
    # end of KGEN addition

    def tofortran(self, isfix=None):
        return self.get_indent_tab(isfix=isfix) + '%s %s %s' \
               % (self.variable, self.sign, self.expr)

    def analyze(self): return

class Assignment(GeneralAssignment):
    f2003_class = Fortran2003.Assignment_Stmt # KGEN addition
    pass

class PointerAssignment(GeneralAssignment):
    f2003_class = Fortran2003.Pointer_Assignment_Stmt # KGEN addition
    pass

# start of KGEN addition
class StmtFuncStatement(Statement):
    """
        R1238
        function-name ( [ dummy-arg-name-list ] ) = scalar-expr
    """

    f2003_class = Fortran2003.Stmt_Function_Stmt

    match = re.compile(r'\w[^=]*\s*=\>?').match
    item_re = re.compile(r'(?P<variable>\w[^=]*)\s*(?P<sign>=\>?)\s*(?P<expr>.*)\Z',re.I).match
    _repr_attr_names = ['variable','sign','expr'] + Statement._repr_attr_names

    def process_item(self):
        from fortlab.resolver.block_statements import declaration_construct

        def get_names(node, bag, depth):
            from fortlab.resolver.Fortran2003 import Name
            if isinstance(node, Name) and node.string not in bag:
                bag.append(node.string)

        def get_partrefs(node, bag, depth):
            from fortlab.resolver.Fortran2003 import Part_Ref
            if isinstance(node, Part_Ref):
                bag.append(True)

        m = self.item_re(self.item.get_line())
        if not m:
            self.isvalid = False
            return
        self.sign = sign = m.group('sign')
        if sign != '=':
            self.isvalid = False
            return

        line = m.group('variable').replace(' ','')
        i = line.find('(')
        items = []
        if i==-1:
            self.isvalid = False
            return

        j = line.find(')')
        if j == -1 or len(line)-1 != j:
            self.isvalid = False
            return

        apply_map = self.item.apply_map
        self.func_name = apply_map(line[:i]).strip()
        self.func_stmt = apply_map(line).strip()
        self.scalar_expr = apply_map(m.group('expr'))

        child = None
        for child in reversed(self.parent.content):
            if not isinstance(child, Comment):
                break
        if child and child.__class__ in declaration_construct:
            try:
                self.parse_f2003()
                arg_names = []; traverse(self.f2003.items[1], get_names, arg_names)
                expr_names = []; traverse(self.f2003.items[2], get_names, expr_names)
                partrefs = []; traverse(self.f2003.items[2], get_partrefs, partrefs)
                if arg_names!=expr_names or any(partrefs):
                    self.isvalid = False
            except:
                self.isvalid = False
            finally:
                if hasattr(self, 'f2003'):
                    delattr(self, 'f2003')
        else: self.isvalid = False

        if self.isvalid:
            self.issfs = True # Is valid StatementFuncStatement

        return

    def tokgen(self):
        return '%s %s %s' % (self.func_stmt, self.sign, self.scalar_expr)

    def tofortran(self, isfix=None):
        return self.get_indent_tab(isfix=isfix) + '%s %s %s' \
               % (self.func_stmt, self.sign, self.scalar_expr)

    def analyze(self):
        for anc in self.ancestors():
            if hasattr(anc, 'a') and hasattr(anc.a, 'variables') and \
                self.func_name in anc.a.variables.keys():
                var = anc.a.variables[self.func_name]
                if var.is_array():
                    self.issfs = False
                    break
        return
# end of KGEN addition

class Assign(Statement):
    """
    ASSIGN <label> TO <int-variable-name>
    """
    f2003_class = Fortran2003.Assignment_Stmt # KGEN addition

    modes = ['fix77']
    match = re.compile(r'assign\s*\d+\s*to\s*\w+\s*\Z',re.I).match
    def process_item(self):
        line = self.item.get_line()[6:].lstrip()
        i = line.lower().find('to')
        assert not self.item.has_map()
        self.items = [line[:i].rstrip(),line[i+2:].lstrip()]
        return
    def tofortran(self, isfix=None):
        return self.get_indent_tab(isfix=isfix) + 'ASSIGN %s TO %s' \
               % (self.items[0], self.items[1])
    def analyze(self): return

    # start of KGEN addition
    def tokgen(self):
        return 'ASSIGN %s TO %s' % (self.items[0], self.items[1])
    # end of KGEN addition

class Call(Statement):
    """Call statement class
    CALL <procedure-designator> [ ( [ <actual-arg-spec-list> ] ) ]

    <procedure-designator> = <procedure-name>
                           | <proc-component-ref>
                           | <data-ref> % <binding-name>

    <actual-arg-spec> = [ <keyword> = ] <actual-arg>
    <actual-arg> = <expr>
                 | <variable>
                 | <procedure-name>
                 | <proc-component-ref>
                 | <alt-return-spec>
    <alt-return-spec> = * <label>

    <proc-component-ref> = <variable> % <procedure-component-name>

    <variable> = <designator>

    Call instance has attributes:
      designator
      arg_list
    """
    f2003_class = Fortran2003.Call_Stmt # KGEN addition

    match = re.compile(r'call\b', re.I).match

    def process_item(self):
        item = self.item
        apply_map = item.apply_map
        line = item.get_line()[4:].strip()
# start of KGEN addition
        i = line.rfind('(')
        items = []
        if i==-1:
            self.designator = apply_map(line).strip()
        else:
            j = line.rfind(')')
            if j == -1 or len(line)-1 != j:
                self.isvalid = False
                return
            self.designator = apply_map(line[:i]).strip()
            items = split_comma(line[i+1:-1], item)
        self.items = items
# end of KGEN addition

# start of KGEN deletion
#        i = line.find('(')
#        items = []
#        if i==-1:
#            self.designator = apply_map(line).strip()
#        else:
#            j = line.find(')')
#            if j == -1 or len(line)-1 != j:
#                self.isvalid = False
#                return
#            self.designator = apply_map(line[:i]).strip()
#            items = split_comma(line[i+1:-1], item)
#        self.items = items
#        i = line.find('(')
#        items = []
# end of KGEN deletion

        return

    def tofortran(self, isfix=None):
        s = self.get_indent_tab(isfix=isfix) + 'CALL '+str(self.designator)
        if self.items:
            s += '('+', '.join(map(str,self.items))+ ')'
        return s

    # start of KGEN addition
    def tokgen(self):
        s = 'CALL '+str(self.designator)
        if hasattr(self, 'items') and self.items:
            s += '('+', '.join(map(str,self.items))+ ')'
        return s
    # end of KGEN addition
    
    def analyze(self):
        a = self.programblock.a
        variables = a.variables
        if hasattr(a, 'external'):
            external = a.external
            if self.designator in external:
                print("Need to analyze: %s" % str(self))
        return

class Goto(Statement):
    """
    GO TO <label>
    """
    f2003_class = Fortran2003.Goto_Stmt # KGEN addition

    match = re.compile(r'go\s*to\s*\d+\s*\Z', re.I).match

    def process_item(self):
        assert not self.item.has_map()
        self.label = self.item.get_line()[2:].lstrip()[2:].lstrip()
        return

    def tofortran(self, isfix=None):
        return self.get_indent_tab(isfix=isfix) + 'GO TO %s' % (self.label)
    def analyze(self): return

    # start of KGEN addition
    def tokgen(self):
        return 'GO TO %s' % (self.label)
    # end of KGEN addition

class ComputedGoto(Statement):
    """
    GO TO ( <label-list> ) [ , ] <scalar-int-expr>
    """
    f2003_class = Fortran2003.Computed_Goto_Stmt # KGEN addition

    match = re.compile(r'go\s*to\s*\(',re.I).match
    def process_item(self):
        apply_map = self.item.apply_map
        line = self.item.get_line()[2:].lstrip()[2:].lstrip()
        i = line.index(')')
        self.items = split_comma(line[1:i], self.item)
        line = line[i+1:].lstrip()
        if line.startswith(','):
            line = line[1:].lstrip()
        self.expr = apply_map(line)
        return
    def tofortran(self, isfix=None):
        return  self.get_indent_tab(isfix=isfix) + 'GO TO (%s) %s' \
               % (', '.join(self.items), self.expr)
    def analyze(self): return

    # start of KGEN addition
    def tofortran(self):
        return  'GO TO (%s) %s' % (', '.join(self.items), self.expr)
    # end of KGEN addition

class AssignedGoto(Statement):
    """
    GO TO <int-variable-name> [ ( <label> [ , <label> ]... ) ]
    """
    modes = ['fix77']
    match = re.compile(r'go\s*to\s*\w+\s*\(?',re.I).match
    def process_item(self):
        line = self.item.get_line()[2:].lstrip()[2:].lstrip()
        i = line.find('(')
        if i==-1:
            self.varname = line
            self.items = []
            return
        self.varname = line[:i].rstrip()
        assert line[-1]==')', str(line)
        self
        self.items = split_comma(line[i+1:-1], self.item)
        return

    def tofortran(self, isfix=None):
        tab = self.get_indent_tab(isfix=isfix)
        if self.items:
            return tab + 'GO TO %s (%s)' \
                   % (self.varname, ', '.join(self.items))
        return tab + 'GO TO %s' % (self.varname)
    def analyze(self): return

    # start of KGEN addition
    def tofortran(self, isfix=None):
        if hasattr(self, 'items') and self.items:
            return 'GO TO %s (%s)' % (self.varname, ', '.join(self.items))
        return 'GO TO %s' % (self.varname)
    # end of KGEN addition

class Continue(Statement):
    """
    CONTINUE
    """
    f2003_class = Fortran2003.Continue_Stmt # KGEN addition

    match = re.compile(r'continue\Z',re.I).match

    def process_item(self):
        self.label = self.item.label
        return

    def tofortran(self, isfix=None):
        return self.get_indent_tab(deindent=True) + 'CONTINUE'

    def analyze(self): return

    # start of KGEN addition
    def tokgen(self):
        return 'CONTINUE'
    # end of KGEN addition

class Return(Statement):
    """
    RETURN [ <scalar-int-expr> ]
    """
    f2003_class = Fortran2003.Return_Stmt # KGEN addition

    match = re.compile(r'return\b',re.I).match

    def process_item(self):
        self.expr = self.item.apply_map(self.item.get_line()[6:].lstrip())
        return

    def tofortran(self, isfix=None):
        tab = self.get_indent_tab(isfix=isfix)
        if self.expr:
            return tab + 'RETURN %s' % (self.expr)
        return tab + 'RETURN'

    def analyze(self): return

    # start of KGEN addition
    def tokgen(self):
        if hasattr(self, 'expr') and self.expr:
            return 'RETURN %s' % (self.expr)
        return 'RETURN'
    # end of KGEN addition

class Stop(Statement):
    """
    STOP [ <stop-code> ]
    <stop-code> = <scalar-char-constant> | <1-5-digit>
    """
    f2003_class = Fortran2003.Stop_Stmt # KGEN addition

    match = re.compile(r'stop\s*((\'\w*\'|"\w*")+|\d+|)\Z',re.I).match

    def process_item(self):
        self.code = self.item.apply_map(self.item.get_line()[4:].lstrip())
        return

    def tofortran(self, isfix=None):
        tab = self.get_indent_tab(isfix=isfix)
        if self.code:
            return tab + 'STOP %s' % (self.code)
        return tab + 'STOP'

    def analyze(self): return

    # start of KGEN addition
    def tokgen(self):
        if hasattr(self, 'code') and self.code:
            return 'STOP %s' % (self.code)
        return 'STOP'

    # end of KGEN addition

class Print(Statement):
    """
    PRINT <format> [, <output-item-list>]
    <format> = <default-char-expr> | <label> | *

    <output-item> = <expr> | <io-implied-do>
    <io-implied-do> = ( <io-implied-do-object-list> , <implied-do-control> )
    <io-implied-do-object> = <input-item> | <output-item>
    <implied-do-control> = <do-variable> = <scalar-int-expr> , <scalar-int-expr> [ , <scalar-int-expr> ]
    <input-item> = <variable> | <io-implied-do>
    """
    f2003_class = Fortran2003.Print_Stmt # KGEN addition

    match = re.compile(r'print\s*(\'\w*\'|\"\w*\"|\d+|[*]|\b\w)', re.I).match

    def process_item(self):
        item = self.item
        apply_map = item.apply_map
        line = item.get_line()[5:].lstrip()
        items = split_comma(line, item)
        self.format = items[0]
        self.items = items[1:]
        return

    def tofortran(self, isfix=None):
        return self.get_indent_tab(isfix=isfix) + 'PRINT %s' \
               % (', '.join([self.format]+self.items))

    # start of KGEN addition
    def tokgen(self):
        if hasattr(self, 'format'):
            return 'PRINT %s' % (', '.join([self.format]+self.items))
        else:
            return 'PRINT *, %s' % (', '.join(self.items))
    # end of KGEN addition

    def analyze(self): return

class Read(Statement):
    """
Read0:    READ ( <io-control-spec-list> ) [ <input-item-list> ]

    <io-control-spec-list> = [ UNIT = ] <io-unit>
                             | [ FORMAT = ] <format>
                             | [ NML = ] <namelist-group-name>
                             | ADVANCE = <scalar-default-char-expr>
                             ...

Read1:    READ <format> [, <input-item-list>]
    <format> == <default-char-expr> | <label> | *
    """
    f2003_class = Fortran2003.Read_Stmt # KGEN addition

    match = re.compile(r'read\b\s*[\w(*\'"]', re.I).match

    def process_item(self):
        item = self.item
        line = item.get_line()[4:].lstrip()
        if line.startswith('('):
            self.__class__ = Read0
        else:
            self.__class__ = Read1
        self.process_item()
        return
    def analyze(self): return

    # start of KGEN addition
    def tokgen(self):
        if hasattr(self, 'format'):
            return 'READ ' + ', '.join([self.format]+self.items)
        elif not hasattr(self, 'specs'):
            self.specs = ['*', '*']
        s = 'READ (%s)' % ', '.join(self.specs)
        if hasattr(self, 'items') and self.items:
            s += ' ' + ', '.join(self.items)
        return s
    # end of KGEN addition

class Read0(Read):

    def process_item(self):
        item = self.item
        line = item.get_line()[4:].lstrip()
        i = line.find(')')
        self.specs = specs_split_comma(line[1:i], item)
        self.items = split_comma(line[i+1:], item)
        return

    def tofortran(self, isfix=None):
        s = self.get_indent_tab(isfix=isfix) + 'READ (%s)' % (', '.join(self.specs))
        if self.items:
            return s + ' ' + ', '.join(self.items)
        return s

    # start of KGEN addition
    def tokgen(self):
        s = 'READ (%s)' % (', '.join(self.specs))
        if hasattr(self, 'items') and self.items:
            return s + ' ' + ', '.join(self.items)
        return s
    # end of KGEN addition

class Read1(Read):

    def process_item(self):
        item = self.item
        line = item.get_line()[4:].lstrip()
        items = split_comma(line, item)
        self.format = items[0]
        self.items = items[1:]
        return

    def tofortran(self, isfix=None):
        return self.get_indent_tab(isfix=isfix) + 'READ ' \
               + ', '.join([self.format]+self.items)

    # start of KGEN addition
    def tokgen(self):
        return 'READ ' + ', '.join([self.format]+self.items)
    # end of KGEN addition

class Write(Statement):
    """
    WRITE ( io-control-spec-list ) [<output-item-list>]
    """
    f2003_class = Fortran2003.Write_Stmt # KGEN addition

    match = re.compile(r'write\s*\(', re.I).match
    def process_item(self):
        item = self.item
        line = item.get_line()[5:].lstrip()
        i = line.find(')')
        assert i != -1, str(line)
        self.specs = specs_split_comma(line[1:i], item)
        self.items = split_comma(line[i+1:], item)
        return

    def tofortran(self, isfix=None):
        s = self.get_indent_tab(isfix=isfix) + 'WRITE (%s)' % ', '.join(self.specs)
        if self.items:
            s += ' ' + ', '.join(self.items)
        return s
    def analyze(self): return

    # start of KGEN addition
    def tokgen(self):
        if not hasattr(self, 'specs'):
            self.specs = ['*', '*']

        s = 'WRITE (%s)' % ', '.join(self.specs)
        if hasattr(self, 'items') and self.items:
            s += ' ' + ', '.join(self.items)
        return s
    # end of KGEN addition
 
class Flush(Statement):
    """
    FLUSH <file-unit-number>
    FLUSH ( <flush-spec-list> )
    <flush-spec> = [ UNIT = ] <file-unit-number>
                 | IOSTAT = <scalar-int-variable>
                 | IOMSG = <iomsg-variable>
                 | ERR = <label>
    """
    f2003_class = Fortran2003.Flush_Stmt # KGEN addition

    match = re.compile(r'flush\b',re.I).match

    def process_item(self):
        line = self.item.get_line()[5:].lstrip()
        if not line:
            self.isvalid = False
            return
        if line.startswith('('):
            assert line[-1] == ')', str(line)
            self.specs = specs_split_comma(line[1:-1],self.item)
        else:
            self.specs = specs_split_comma(line,self.item)
        return

    def tofortran(self, isfix=None):
        tab = self.get_indent_tab(isfix=isfix)
        return tab + 'FLUSH (%s)' % (', '.join(self.specs))
    def analyze(self): return

    # start of KGEN addition
    def tokgen(self):
        return 'FLUSH (%s)' % (', '.join(self.specs))

    # end of KGEN addition
class Wait(Statement):
    """
    WAIT ( <wait-spec-list> )
    <wait-spec> = [ UNIT = ] <file-unit-number>
                | END = <label>
                | EOR = <label>
                | ERR = <label>
                | ID = <scalar-int-expr>
                | IOMSG = <iomsg-variable>
                | IOSTAT = <scalar-int-variable>

    """
    f2003_class = Fortran2003.Wait_Stmt # KGEN addition

    match = re.compile(r'wait\s*\(.*\)\Z',re.I).match
    def process_item(self):
        self.specs = specs_split_comma(\
            self.item.get_line()[4:].lstrip()[1:-1], self.item)
        return
    def tofortran(self, isfix=None):
        tab = self.get_indent_tab(isfix=isfix)
        return tab + 'WAIT (%s)' % (', '.join(self.specs))
    def analyze(self): return

    # start of KGEN addition
    def tofortran(self):
        return 'WAIT (%s)' % (', '.join(self.specs))
    # end of KGEN addition

class Contains(Statement):
    """
    CONTAINS
    """
    f2003_class = Fortran2003.Contains_Stmt # KGEN addition

    match = re.compile(r'contains\Z',re.I).match
    def process_item(self): return
    def tofortran(self, isfix=None): return self.get_indent_tab(isfix=isfix) + 'CONTAINS'

    # start of KGEN addition
    def analyze(self):
        if not hasattr(self.parent, 'spec_stmts'):
            self.parent.spec_stmts = []
        self.parent.spec_stmts.append(self)

    def tokgen(self):
        return 'CONTAINS'

    def resolve_uname(self, uname, request, config):
        from fortlab.resolver.block_statements import SubProgramStatement
        if isinstance(request.res_stmts[-1], SubProgramStatement):
            self.add_geninfo(uname, request)
    # end of KGEN addition

class Allocate(Statement):
    """
    ALLOCATE ( [ <type-spec> :: ] <allocation-list> [ , <alloc-opt-list> ] )
    <alloc-opt> = STAT = <stat-variable>
                | ERRMSG = <errmsg-variable>
                | SOURCE = <source-expr>
    <allocation> = <allocate-object> [ ( <allocate-shape-spec-list> ) ]
    """
    f2003_class = Fortran2003.Allocate_Stmt # KGEN addition

    match = re.compile(r'allocate\s*\(.*\)\Z',re.I).match
    def process_item(self):
        line = self.item.get_line()[8:].lstrip()[1:-1].strip()
        item2 = self.item.copy(line, True)
        line2 = item2.get_line()
        i = line2.find('::')
        if i != -1:
            spec = item2.apply_map(line2[:i].rstrip())
            # start of KGEN deletion
#            from block_statements import type_spec
#            stmt = None
#            for cls in type_spec:
#                if cls.match(spec):
#                    stmt = cls(self, item2.copy(spec))
#                    if stmt.isvalid:
#                        break
#            if stmt is not None and stmt.isvalid:
#                spec = stmt
#            else:
#                self.warning('TODO: unparsed type-spec' + `spec`)
            # end of KGEN deletion
            line2 = line2[i+2:].lstrip()
        else:
            spec = None
        self.spec = spec
        self.items = specs_split_comma(line2, item2)
        return

    def tofortran(self, isfix=None):
        t = ''
        if self.spec:
            #t = self.spec.tostr() + ' :: ' # KGEN deletion
            t = self.spec + ' :: ' # KGEN addition
        return self.get_indent_tab(isfix=isfix) \
               + 'ALLOCATE (%s%s)' % (t,', '.join(self.items))
    def analyze(self): return

    # start of KGEN addition
    def tokgen(self):
        t = ''
        if hasattr(self, 'spec') and self.spec:
            t = self.spec + ' :: '
        return 'ALLOCATE (%s%s)' % (t,', '.join(self.items))

    # end of KGEN addition

class Deallocate(Statement):
    """
    DEALLOCATE ( <allocate-object-list> [ , <dealloc-opt-list> ] )
    <allocate-object> = <variable-name>
                      | <structure-component>
    <structure-component> = <data-ref>
    <dealloc-opt> = STAT = <stat-variable>
                    | ERRMSG = <errmsg-variable>
    """
    f2003_class = Fortran2003.Deallocate_Stmt # KGEN addition

    match = re.compile(r'deallocate\s*\(.*\)\Z',re.I).match
    def process_item(self):
        line = self.item.get_line()[10:].lstrip()[1:-1].strip()
        self.items = specs_split_comma(line, self.item)
        return
    def tofortran(self, isfix=None): return self.get_indent_tab(isfix=isfix) \
        + 'DEALLOCATE (%s)' % (', '.join(self.items))
    def analyze(self): return

    # start of KGEN addition
    def tokgen(self):
        return 'DEALLOCATE (%s)' % (', '.join(self.items))
    # end of KGEN addition

class ModuleProcedure(Statement):
    """
    [ MODULE ] PROCEDURE <procedure-name-list>
    """
    f2003_class = Fortran2003.Procedure_Stmt # KGEN addition

    match = re.compile(r'(module\s*|)procedure\b',re.I).match
    def process_item(self):
        line = self.item.get_line()
        m = self.match(line)
        assert m,str(line)
        items = split_comma(line[m.end():].strip(), self.item)
        for n in items:
            if not is_name(n):
                self.isvalid = False
                return
        self.items = items
        return

    def tofortran(self, isfix=None):
        tab = self.get_indent_tab(isfix=isfix)
        return tab + 'MODULE PROCEDURE %s' % (', '.join(self.items))

    def analyze(self):
        module_procedures = self.parent.a.module_procedures
        module_procedures.extend(self.items)
        # XXX: add names to parent_provides
        return

    # start of KGEN
    def tokgen(self):
        return 'MODULE PROCEDURE %s' % (', '.join(self.items))
    # end of KGEN

class Access(Statement):
    """
    <access-spec> [ [::] <access-id-list>]
    <access-spec> = PUBLIC | PRIVATE
    <access-id> = <use-name> | <generic-spec>
    """
    f2003_class = Fortran2003.Access_Stmt # KGEN addition

    match = re.compile(r'(public|private)\b',re.I).match

    # start of KGEN
    def tokgen(self):
        if hasattr(self, 'new_items'):
            items = self.new_items
            del self.new_items
        elif hasattr(self, 'items'): items = self.items
        else: items = None

        if isinstance(self, Statement):
            clsname = self.__class__.__name__.upper()
        else: clsname = self.kgen_match_class.__name__.upper()

        if items:
            return clsname + ' ' + ', '.join(items)
        return clsname
    # end of KGEN

    def process_item(self):
        clsname = self.__class__.__name__.lower()
        line = self.item.get_line()
        if not line.lower().startswith(clsname):
            self.isvalid = False
            return
        line = line[len(clsname):].lstrip()
        if line.startswith('::'):
            line = line[2:].lstrip()
        self.items = split_comma(line, self.item)
        return

    def tofortran(self, isfix=None):
        clsname = self.__class__.__name__.upper()
        tab = self.get_indent_tab(isfix=isfix)
        if self.items:
            return tab + clsname + ' ' + ', '.join(self.items)
        return tab + clsname

    def analyze(self):
        # start of KGEN addition
        from fortlab.resolver.block_statements import TypeDecl, Module
        if not hasattr(self.parent, 'spec_stmts'):
            self.parent.spec_stmts = []
        self.parent.spec_stmts.append(self)
        # end of KGEN addition

        clsname = self.__class__.__name__
        l = getattr(self.parent.a, clsname.lower() + '_id_list')
        if self.items:
            for name in self.items:
                if name not in l: l.append(name)
        else:
            if '' not in l:
                l.append('')
            #if not isinstance(self.parent, classes.Module): # KGEN deletion
            if not isinstance(self.parent, Module): # KGEN addition
                if not isinstance(self.parent, TypeDecl) or self.is_public: # KGEN addition
                    parentclsname = self.parent.__class__.__name__
                    message = 'C548 violation: %s statement only allowed in the'\
                              ' specification-part of a module, not in a %s.'\
                              % (clsname.upper(), parentclsname.lower())
                    self.warning(message)
        access_id_list = self.parent.a.private_id_list + self.parent.a.public_id_list
        if access_id_list.count('')>1:
            message = 'C548 violation: only one access-stmt with omitted'\
                      ' access-id-list is permitted in'\
                      ' the module-specification-part.'
            self.warning(message)
        # todo: check for conflicting access statement usages (e.g. private foo; public foo)
        # todo: check for conflicting generic-spec id-s.
        return

    # start of KGEN addition
    def resolve_uname(self, uname, request, config):
        if not self.items or uname.firstpartname() in self.items:
            self.add_geninfo(uname, request)
    # end of KGEN addition

class Public(Access):
    is_public = True
class Private(Access):
    is_public = False

class Close(Statement):
    """
    CLOSE ( <close-spec-list> )
    <close-spec> = [ UNIT = ] <file-unit-number>
                   | IOSTAT = <scalar-int-variable>
                   | IOMSG = <iomsg-variable>
                   | ERR = <label>
                   | STATUS = <scalar-default-char-expr>
    """
    f2003_class = Fortran2003.Close_Stmt # KGEN addition

    match = re.compile(r'close\s*\(.*\)\Z',re.I).match
    def process_item(self):
        line = self.item.get_line()[5:].lstrip()[1:-1].strip()
        self.specs = specs_split_comma(line, self.item)
        return
    def tofortran(self, isfix=None):
        tab = self.get_indent_tab(isfix=isfix)
        return tab + 'CLOSE (%s)' % (', '.join(self.specs))
    def analyze(self): return

    # start of KGEN addition
    def tokgen(self):
        return 'CLOSE (%s)' % (', '.join(self.specs))
    # end of KGEN addition

class Cycle(Statement):
    """
    CYCLE [ <do-construct-name> ]
    """
    f2003_class = Fortran2003.Cycle_Stmt # KGEN addition

    match = re.compile(r'cycle\b\s*\w*\s*\Z',re.I).match
    def process_item(self):
        self.name = self.item.get_line()[5:].lstrip()
        return
    def tofortran(self, isfix=None):
        if self.name:
            return self.get_indent_tab(isfix=isfix) + 'CYCLE ' + self.name
        return self.get_indent_tab(isfix=isfix) + 'CYCLE'
    def analyze(self): return

    # start of KGEN addition
    def tokgen(self):
        if hasattr(self, 'name') and self.name:
            return 'CYCLE ' + self.name
        return 'CYCLE'
    # end of KGEN addition

class FilePositioningStatement(Statement):
    """
    REWIND <file-unit-number>
    REWIND ( <position-spec-list> )
    <position-spec-list> = [ UNIT = ] <file-unit-number>
                           | IOMSG = <iomsg-variable>
                           | IOSTAT = <scalar-int-variable>
                           | ERR = <label>
    The same for BACKSPACE, ENDFILE.
    """
    #f2003_class = Fortran2003.Rewind_Stmt # KGEN addition        

    match = re.compile(r'(rewind|backspace|endfile)\b',re.I).match

    def process_item(self):
        clsname = self.__class__.__name__.lower()
        line = self.item.get_line()
        if not line.lower().startswith(clsname):
            self.isvalid = False
            return
        line = line[len(clsname):].lstrip()
        if line.startswith('('):
            assert line[-1]==')',str(line)
            spec = line[1:-1].strip()
        else:
            spec = line
        self.specs = specs_split_comma(spec, self.item)
        return

    def tofortran(self, isfix=None):
        clsname = self.__class__.__name__.upper()
        return self.get_indent_tab(isfix=isfix) + clsname + ' (%s)' % (', '.join(self.specs))
    def analyze(self): return

    # start of KGEN addition
    def tokgen(self):
        if isinstance(self, Statement): 
            clsname = self.__class__.__name__.upper()
        elif hasattr(self, 'kgen_match_class'):
            clsname = self.kgen_match_class.__name__.upper()
        return clsname + ' (%s)' % (', '.join(self.specs))
    # end of KGEN addition


class Backspace(FilePositioningStatement):
    f2003_class = Fortran2003.Backspace_Stmt # KGEN addition
    pass

class Endfile(FilePositioningStatement):
    f2003_class = Fortran2003.Endfile_Stmt # KGEN addition
    pass

class Rewind(FilePositioningStatement):
    f2003_class = Fortran2003.Rewind_Stmt # KGEN addition
    pass

class Open(Statement):
    """
    OPEN ( <connect-spec-list> )
    <connect-spec> = [ UNIT = ] <file-unit-number>
                     | ACCESS = <scalar-default-char-expr>
                     | ..
    """
    f2003_class = Fortran2003.Open_Stmt # KEGN addition

    match = re.compile(r'open\s*\(.*\)\Z',re.I).match
    def process_item(self):
        line = self.item.get_line()[4:].lstrip()[1:-1].strip()
        self.specs = specs_split_comma(line, self.item)
        return
    def tofortran(self, isfix=None):
        return self.get_indent_tab(isfix=isfix) + 'OPEN (%s)' % (', '.join(self.specs))
    def analyze(self): return

    # start of KGEN addition
    def tokgen(self):
        return 'OPEN (%s)' % (', '.join(self.specs))
    # end of KGEN addition

class Format(Statement):
    """
    FORMAT <format-specification>
    <format-specification> = ( [ <format-item-list> ] )
    <format-item> = [ <r> ] <data-edit-descr>
                    | <control-edit-descr>
                    | <char-string-edit-descr>
                    | [ <r> ] ( <format-item-list> )
    <data-edit-descr> = I <w> [ . <m> ]
                        | B <w> [ . <m> ]
                        ...
    <r|w|m|d|e> = <int-literal-constant>
    <v> = <signed-int-literal-constant>
    <control-edit-descr> = <position-edit-descr>
                         | [ <r> ] /
                         | :
                         ...
    <position-edit-descr> = T <n>
                            | TL <n>
                            ...
    <sign-edit-descr> = SS | SP | S
    ...

    """
    f2003_class = Fortran2003.Format_Stmt # KGEN addition

    match = re.compile(r'format\s*\(.*\)\Z', re.I).match
    def process_item(self):
        item = self.item
        if item.label is None:
            # R1001:
            self.warning('FORMAT statement must be labeled (F2008:C1001).' \
                         % (item.label))
        line = item.get_line()[6:].lstrip()
        assert line[0]+line[-1]=='()',str(line)
        self.specs = split_comma(line[1:-1], item)
        return
    def tofortran(self, isfix=None):
        return self.get_indent_tab(isfix=isfix) + 'FORMAT (%s)' % (', '.join(self.specs))
    def analyze(self): return

    # start of KGEN addition
    def tokgen(self):
        return 'FORMAT (%s)' % (', '.join(self.specs))
    # end of KGEN addition

class Save(Statement):
    """
    SAVE [ [ :: ] <saved-entity-list> ]
    <saved-entity> = <object-name>
                     | <proc-pointer-name>
                     | / <common-block-name> /
    <proc-pointer-name> = <name>
    <object-name> = <name>
    """
    f2003_class = Fortran2003.Save_Stmt # KGEN addition

    match = re.compile(r'save\b',re.I).match
    def process_item(self):
        assert not self.item.has_map()
        line = self.item.get_line()[4:].lstrip()
        if line.startswith('::'):
            line = line[2:].lstrip()
        items = []
        for s in line.split(','):
            s = s.strip()
            if not s: continue
            if s.startswith('/'):
                assert s.endswith('/'),str(s)
                n = s[1:-1].strip()
                assert is_name(n),str(n)
                items.append('/%s/' % (n))
            elif is_name(s):
                items.append(s)
            else:
                self.isvalid = False
                return
        self.items = items
        return
    def tofortran(self, isfix=None):
        tab = self.get_indent_tab(isfix=isfix)
        if not self.items:
            return tab + 'SAVE'
        return tab + 'SAVE %s' % (', '.join(self.items))
    def analyze(self):
        # start of KGEN addition
        if not hasattr(self.parent, 'spec_stmts'):
            self.parent.spec_stmts = []
        self.parent.spec_stmts.append(self)
        # end of KGEN addition

    # start of KGEN addition
    def tokgen(self):
        if hasattr(self, 'new_items'):
            items = self.new_items
            del self.new_items
        else:
            items = self.items

        if not items:
            return 'SAVE'
        return 'SAVE %s' % (', '.join(items))

    def resolve_uname(self, uname, request, config):
        from fortlab.kgutils import KGName
        if hasattr(self, 'items'):
            if self.items:
                for item in self.items:
                    if item.startswith('/') and item.endswith('/'):
                        if uname.firstpartname()==item[1:-1].strip():
                            newname = KGName(pack_innamepath(self, uname.firstpartname()))
                            self.add_geninfo(newname, request)
                    else:
                        if uname.firstpartname()==item:
                            newname = KGName(pack_innamepath(self, uname.firstpartname()))
                            self.add_geninfo(newname, request)
            else:
                self.add_geninfo(uname, request)
    # end of KGEN addition

class Data(Statement):
    """
    DATA <data-stmt-set> [ [ , ] <data-stmt-set> ]...
    <data-stmt-set> = <data-stmt-object-list> / <data-stmt-value-list> /
    <data-stmt-object> = <variable> | <data-implied-do>
    <data-implied-do> = ( <data-i-do-object-list> , <data-i-do-variable> = <scalar-int-expr> , <scalar-int-expr> [ , <scalar-int-expr> ] )
    <data-i-do-object> = <array-element> | <scalar-structure-component> | <data-implied-do>
    <data-i-do-variable> = <scalar-int-variable>
    <variable> = <designator>
    <designator> = <object-name>
                   | <array-element>
                   | <array-section>
                   | <structure-component>
                   | <substring>
    <array-element> = <data-ref>
    <array-section> = <data-ref> [ ( <substring-range> ) ]

    """
    f2003_class = Fortran2003.Data_Stmt # KGEN addition

    match = re.compile(r'data\b',re.I).match

    def process_item(self):
        line = self.item.get_line()[4:].lstrip()
        stmts = []
        self.isvalid = False
        while line:
            i = line.find('/')
            if i==-1: return
            j = line.find('/',i+1)
            if j==-1: return
            l1, l2 = line[:i].rstrip(),line[i+1:j].strip()
            l1 = split_comma(l1, self.item)
            l2 = split_comma(l2, self.item)
            stmts.append((l1,l2))
            line = line[j+1:].lstrip()
            if line.startswith(','):
                line = line[1:].lstrip()
        self.stmts = stmts
        self.isvalid = True
        return

    def tofortran(self, isfix=None):
        tab = self.get_indent_tab(isfix=isfix)
        l = []
        for o,v in self.stmts:
            l.append('%s / %s /' %(', '.join(o),', '.join(v)))
        return tab + 'DATA ' + ' '.join(l)
    def analyze(self):
        pass

    # start of KGEN addition
    def tokgen(self):
        l = []
        for o,v in self.stmts:
            l.append('%s / %s /' %(', '.join(o),', '.join(v)))
        return 'DATA ' + ' '.join(l)
    # end of KGEN addition


class Nullify(Statement):
    """
    NULLIFY ( <pointer-object-list> )
    <pointer-object> = <variable-name>
    """
    f2003_class = Fortran2003.Nullify_Stmt # KGEN addition

    match = re.compile(r'nullify\s*\(.*\)\Z',re.I).match
    def process_item(self):
        line = self.item.get_line()[7:].lstrip()[1:-1].strip()
        self.items = split_comma(line, self.item)
        return
    def tofortran(self, isfix=None):
        return self.get_indent_tab(isfix=isfix) + 'NULLIFY (%s)' % (', '.join(self.items))
    def analyze(self): return

    # start of KGEN addition
    def tokgen(self):
        return 'NULLIFY (%s)' % (', '.join(self.items))
    # end of KGEN addition

class Use(Statement):
    """
    USE [ [ , <module-nature> ] :: ] <module-name> [ , <rename-list> ]
    USE [ [ , <module-nature> ] :: ] <module-name> , ONLY : [ <only-list> ]
    <module-nature> = INTRINSIC | NON_INTRINSIC
    <rename> = <local-name> => <use-name>
               | OPERATOR ( <local-defined-operator> ) => OPERATOR ( <use-defined-operator> )
    <only> = <generic-spec> | <only-use-name> | <rename>
    <only-use-name> = <use-name>
    """
    f2003_class = Fortran2003.Use_Stmt # KGEN addition

    match = re.compile(r'use\b',re.I).match
    def process_item(self):
        line = self.item.get_line()[3:].lstrip()
        nature = ''
        if line.startswith(','):
            i = line.find('::')
            nature = line[1:i].strip().upper()
            line = line[i+2:].lstrip()
        if line.startswith('::'):
            line = line[2:].lstrip()
        if nature and not is_name(nature):
            self.isvalid = False
            return
        self.nature = nature
        i = line.find(',')
        self.isonly = False
        if i==-1:
            self.name = line
            self.items = []
        else:
            self.name = line[:i].rstrip()
            line = line[i+1:].lstrip()
            if line.lower().startswith('only') and line[4:].lstrip().startswith(':'):
                self.isonly = True
                line = line[4:].lstrip()[1:].lstrip()
            self.items = split_comma(line, self.item)
        return

    def tofortran(self, isfix=None):
        tab = self.get_indent_tab(isfix=isfix)
        s = 'USE'
        if self.nature:
            #s += ' ' + self.nature + ' ::' # KGEN deletion
            s += ', ' + self.nature + ' ::' # KGEN addition
        s += ' ' + self.name
        if self.isonly:
            s += ', ONLY:'
        elif self.items:
            s += ','
        if self.items:
            s += ' ' + ', '.join(self.items)
        return tab + s
    # start of KGEN

    class KgenIntrinsicModule(object):
        def __init__(self, public_names):
            self.supporting_names = public_names

        def resolve(self, request, config):
            from fortlab.resolver.kgparse import ResState
            from fortlab.resolver.api import parse

            if request.state != ResState.RESOLVED and request.uname.firstpartname() in self.supporting_names:
                #tree = parse('!kgen dummy comment for intrinsic module', \
                #    ignore_comments=False, analyze=False, isfree=True, isstrict=False, include_dirs=None, source_only=None )
                #request.res_stmt = tree.content[0]
                request.res_stmt = None
                request.state = ResState.RESOLVED

    def analyze(self):
        if not hasattr(self.parent, 'use_stmts'):
            self.parent.use_stmts = {}

        if self.name in self.parent.use_stmts and self in self.parent.use_stmts[self.name]:
            return

        if self.name not in self.parent.use_stmts:
            self.parent.use_stmts[self.name] = []

        self.parent.use_stmts[self.name].append(self)

        if not hasattr(self, 'renames'):
            self.renames = [split_comma(item, comma='=>') for item in self.items if '=>' in item]
        if not hasattr(self, 'norenames'):
            self.norenames = [item for item in self.items if '=>' not in item]

        if not hasattr(self, 'module'):
            self.module = None

        if not hasattr(self, 'used'):
            self.used = []

    def intrinsic_module(self, modname):
        from fortlab.resolver.kgintrinsics import Intrinsic_Modules

        if modname.upper() in Intrinsic_Modules:
            return self.KgenIntrinsicModule(Intrinsic_Modules[modname.upper()])

    def get_exclude_actions(self, section_name, config, *args ):
        from fortlab.kgutils import match_namepath
        if section_name=='namepath':
            if len(args)<1: return []

            if section_name in config["exclude"]:
                options = config["exclude"][section_name]
                for pattern, actions in options.items():
                    if match_namepath(pattern, args[0]):
                        return actions
            return []
        else:
            UserException('Not supported section name in exclusion input file: %s'%section)

    def resolve(self, request, config):
        from fortlab.resolver.kgparse import ResState, SrcFile
        from fortlab.resolver.kgintrinsics import Intrinsic_Modules

        src = None
        if self.module is None:
            if self.name in config["modules"]:
                self.module = config["modules"][self.name]['stmt']
            else:
                if (self.nature and self.nature=='INTRINSIC') or \
                    self.name.upper() in Intrinsic_Modules:
                    self.module = self.intrinsic_module(self.name)
                else:
                    # skip if excluded
                    if 'skip_module' in self.get_exclude_actions('namepath', config, self.name):
                        return

                    fn = self.reader.find_module_source_file(self.name, config)
                    if fn:
                        src = SrcFile(fn, config)
                        logger.debug('\tin the search of "%s" directly from %s and originally from %s' % \
                            (request.uname.firstpartname(), os.path.basename(self.reader.id), \
                            os.path.basename(request.originator.reader.id)))

                        self.module = src.tree.a.module[self.name]
                    elif "module" in config["custom_resolvers"] and \
                        self.name in config["custom_resolvers"]["module"]:
                        self.module = config["custom_resolvers"]["module"][self.name]
                    else:
                        raise UserException("Module, %s, is not found at %s. "
                            "Please check include paths for searching module "
                            "files." % (self.name, self.reader.id))

        if self.module:
            self.module.resolve(request, config)

        if request.state == ResState.RESOLVED:
            # if intrinsic module

            if (self.nature and self.nature=='INTRINSIC') or \
                self.name.upper() in Intrinsic_Modules:
                pass
            # if newly found moudle is not in srcfiles
            elif not self.module in config["srcfiles"][self.top.reader.id][1]:
                config["srcfiles"][self.top.reader.id][1].append(self.module)

    def tokgen(self):
        def get_rename(node, bag, depth):
            from fortlab.resolver.Fortran2003 import Rename
            if isinstance(node, Rename) and node.items[1].string==bag['newname']:
                bag['onlyitem'] = '%s => %s'%(node.items[1].string, node.items[2].string)
                return True

        items = self.items
        if hasattr(self, 'new_items'):
            items = []
            for item in self.new_items:
                if item in self.norenames:
                    items.append(item)
                else:
                    rename = {'newname':item, 'onlyitem': item}
                    traverse(self.f2003, get_rename, rename)
                    items.append(rename['onlyitem'])
            del self.new_items

        s = 'USE'
        if hasattr(self, 'nature') and self.nature:
            s += ', ' + self.nature + ' ::'
        s += ' ' + self.name
        if hasattr(self, 'isonly') and self.isonly:
            s += ', ONLY:'
        elif items:
            s += ','
        if items:
            s += ' ' + ', '.join(items)
        return s
    # end of KGEN


    #def analyze(self): # KGEN deletion
    def analyze_org(self): # KGEN addition
        use = self.parent.a.use
        if self.name in use:
            return

        modules = self.top.a.module
        if self.name not in modules:
            fn = self.reader.find_module_source_file(self.name)
            if fn is not None:
                from fortlab.resolver.readfortran import FortranFileReader
                from fortlab.resolver.parsefortran import FortranParser
                self.info('looking module information from %r' % (fn))
                reader = FortranFileReader(fn, include_dirs=self.reader.include_dirs, source_only=self.reader.source_only)
                parser = FortranParser(reader)
                parser.parse()
                parser.block.a.module.update(modules)
                parser.analyze()
                modules.update(parser.block.a.module)

        if self.name not in modules:
            self.warning('no information about the module %r in use statement' % (self.name))
            return

        module = modules[self.name]
        use[self.name] = module
        use_provides = self.parent.a.use_provides
        renames = [split_comma(item, comma='=>') for item in self.items if '=>' in item]
        norenames = [item for item in self.items if '=>' not in item]
        all_mod_provides = dict(module.a.module_provides)
        all_mod_provides.update(module.a.use_provides)
        if self.isonly:
            # populate use_provides with items/renames only.
            for rename, orig in renames:
                self.populate_use_provides(all_mod_provides, use_provides, orig, rename)
            for name in norenames:
                self.populate_use_provides(all_mod_provides, use_provides, name)
        else:
            # norenames should be empty
            if norenames:
                self.warning("'use' without 'only' clause does not rename the variables '%s'" % ', '.join(norenames))
            # populate use_provides with renamed vars from module.
            for rename, orig in renames:
                self.populate_use_provides(all_mod_provides, use_provides, orig, rename)
            # get all the rest
            unrenamed = set(all_mod_provides) - set([b for (a,b) in renames])
            for name in unrenamed:
                self.populate_use_provides(all_mod_provides, use_provides, name)
        return

    def populate_use_provides(self, all_mod_provides, use_provides, name, rename=None):
        ovar = all_mod_provides.get(name, None)
        if ovar is None:
            raise AnalyzeError("entity name '%s' is not in module '%s'" % (name, self.name))
        if rename:
            name_idx = rename #XXX: rename != ovar.name -- should mark this somehow?
        else:
            name_idx = name
        if name_idx in use_provides:
            if ovar != use_provides[name_idx]:
                self.warning("entity name '%s' is already declared in module '%s' while adding it to '%s', overriding." % (name, self.name, self.parent.name))
        use_provides[name_idx] = ovar



class Exit(Statement):
    """
    EXIT [ <do-construct-name> ]
    """
    f2003_class = Fortran2003.Exit_Stmt # KGEN addition

    match = re.compile(r'exit\b\s*\w*\s*\Z',re.I).match
    def process_item(self):
        self.name = self.item.get_line()[4:].lstrip()
        return
    def tofortran(self, isfix=None):
        if self.name:
            return self.get_indent_tab(isfix=isfix) + 'EXIT ' + self.name
        return self.get_indent_tab(isfix=isfix) + 'EXIT'
    def analyze(self): return

    # start of KGEN addition
    def tokgen(self):
        if hasattr(self, 'name') and self.name:
            return 'EXIT ' + self.name
        return 'EXIT'
    # end of KGEN addition

class Parameter(Statement):
    """
    PARAMETER ( <named-constant-def-list> )
    <named-constant-def> = <named-constant> = <initialization-expr>
    """
    f2003_class = Fortran2003.Parameter_Stmt # KGEN addition

    match = re.compile(r'parameter\s*\(.*\)\Z', re.I).match
    def process_item(self):
        line = self.item.get_line()[9:].lstrip()[1:-1].strip()
        self.items = split_comma(line, self.item)
        # start of KGEN addition
        self.leftnames = [ item.split('=')[0].strip() for item in self.items ]
        # end of KGEN addition
        return
    def tofortran(self, isfix=None):
        return self.get_indent_tab(isfix=isfix) + 'PARAMETER (%s)' % (', '.join(self.items))
    def analyze(self):
        # start of KGEN addition
        if not hasattr(self.parent, 'spec_stmts'):
            self.parent.spec_stmts = []
        self.parent.spec_stmts.append(self)
        # end of KGEN addition

        for item in self.items:
            i = item.find('=')
            assert i!=-1,str(item)
            name = item[:i].rstrip()
            value = item[i+1:].lstrip()
            var = self.get_variable(name)
            var.update('parameter')
            var.set_init(value)
        return

    # start of KGEN addition
    def resolve_uname(self, uname, request, config):
        from fortlab.resolver.kgsearch import f2003_search_unknowns
        from fortlab.resolver.kgparse import ResState

        if uname.firstpartname() in self.leftnames:
            self.add_geninfo(uname, request)

            node = None
            if isinstance(self.f2003.items[1], Fortran2003.Named_Constant_Def):
                if self.f2003.items[1].items[0].string.lower()==uname.firstpartname():
                    node = self.f2003.items[1]
            elif isinstance(self.f2003.items[1], Fortran2003.Named_Constant_Def_List):
                for item in self.f2003.items[1].items:
                    if isinstance(item, Fortran2003.Named_Constant_Def) and \
                        item.items[0].string.lower()==uname.firstpartname():
                        node = item
                        break
            else:
                raise ProgramException('%s is not allowed'%self.f2003.items[1].__class__)

            if node:
                if not hasattr(self, 'unknowns') or len(self.unknowns)==0:
                    f2003_search_unknowns(self, node.items[1], config)
                    for unknown, request in self.unknowns.items():
                        if request.state != ResState.RESOLVED:
                            self.resolve(request, config)

    def tokgen(self):
        if hasattr(self, 'new_items'):
            return 'PARAMETER (%s)' % (', '.join(self.new_items))
            del self.new_items
        else:
            return 'PARAMETER (%s)' % (', '.join(self.items))
    # end of KGEN addition

class Equivalence(Statement):
    """
    EQUIVALENCE <equivalence-set-list>
    <equivalence-set> = ( <equivalence-object> , <equivalence-object-list> )
    <equivalence-object> = <variable-name> | <array-element> | <substring>
    """
    f2003_class = Fortran2003.Equivalence_Stmt # KGEN addition

    match = re.compile(r'equivalence\s*\(.*\)\Z', re.I).match
    def process_item(self):
        items = []
        for s in self.item.get_line()[11:].lstrip().split(','):
            s = s.strip()
            assert s[0]+s[-1]=='()',str(s,self.item.get_line())
            s = ', '.join(split_comma(s[1:-1], self.item))
            items.append('('+s+')')
        self.items = items
        return
    def tofortran(self, isfix=None):
        return self.get_indent_tab(isfix=isfix) + 'EQUIVALENCE %s' % (', '.join(self.items))
    def analyze(self):
        # start of KGEN addition
        if not hasattr(self.parent, 'spec_stmts'):
            self.parent.spec_stmts = []
        self.parent.spec_stmts.append(self)
        # end of KGEN addition


    # start of KGEN addition
    def resolve_uname(self, uname, request, config):
        def get_equivname(node, bag, depth):
            from fortlab.resolver.Fortran2003 import Equivalence_Object_List, Equivalence_Set, Name
            if isinstance(node, Name) and node.string==uname.firstpartname():
                if isinstance(node.parent, Equivalence_Set):
                    bag['equiv_names'].append(node.parent.items[1])
                elif hasattr(node.parent, 'parent') and isinstance(node.parent.parent, Equivalence_Set):
                    bag['equiv_names'].append(node.parent.parent.items[1])
                elif isinstance(node.parent, Equivalence_Object_List):
                    bag['equiv_names'].append(node.parent.parent.items[0])
                elif hasattr(node.parent, 'parent') and isinstance(node.parent.parent, Equivalence_Object_List):
                    bag['equiv_names'].append(node.parent.parent.parent.items[0])

                return True
                 
        names = {'search_name': uname.firstpartname(), 'equiv_names': []}
        traverse(self.f2003, get_equivname, names)
        if len(names['equiv_names'])>0:
            self.add_geninfo(uname, request)
            #raise ProgramException('Equivalent names are not correctly resolved.')

    def tokgen(self):
        if hasattr(self, 'new_items'):
            items = self.new_items
            del self.new_items
        else:
            items = self.items

        if items:
            return 'EQUIVALENCE %s' % (', '.join(self.items))
        else: return ''
    # end of KGEN addition

class Dimension(Statement):
    """
    DIMENSION [ :: ] <array-name> ( <array-spec> ) [ , <array-name> ( <array-spec> ) ]...

    """
    f2003_class = Fortran2003.Dimension_Stmt # KGEN addition

    match = re.compile(r'dimension\b', re.I).match
    def process_item(self):
        line = self.item.get_line()[9:].lstrip()
        if line.startswith('::'):
            line = line[2:].lstrip()
        self.items = split_comma(line, self.item)
        return
    def tofortran(self, isfix=None):
        return self.get_indent_tab(isfix=isfix) + 'DIMENSION %s' % (', '.join(self.items))
    def analyze(self):
        # start of KGEN addition
        if not hasattr(self.parent, 'spec_stmts'):
            self.parent.spec_stmts = []
        self.parent.spec_stmts.append(self)
        # end of KGEN addition

        for line in self.items:
            i = line.find('(')
            assert i!=-1 and line.endswith(')'),str(line)
            name = line[:i].rstrip()
            array_spec = split_comma(line[i+1:-1].strip(), self.item)
            var = self.get_variable(name)
            var.set_bounds(array_spec)
        return

    # start of KGEN addition
    def resolve_uname(self, uname, request, config):
        pass

    def tokgen(self):
        return 'DIMENSION %s' % (', '.join(self.items))
    # end of KGEN addition

class Target(Statement):
    """
    TARGET [ :: ] <object-name> ( <array-spec> ) [ , <object-name> ( <array-spec> ) ]...

    """
    f2003_class = Fortran2003.Target_Stmt # KGEN addition

    match = re.compile(r'target\b', re.I).match
    def process_item(self):
        line = self.item.get_line()[6:].lstrip()
        if line.startswith('::'):
            line = line[2:].lstrip()
        self.items = split_comma(line, self.item)
        return
    def tofortran(self, isfix=None):
        return self.get_indent_tab(isfix=isfix) + 'TARGET %s' % (', '.join(self.items))
    def analyze(self):
        # start of KGEN addition
        if not hasattr(self.parent, 'spec_stmts'):
            self.parent.spec_stmts = []
        self.parent.spec_stmts.append(self)
        # end of KGEN addition

        for line in self.items:
            i = line.find('(')
            # start of KGEN deletion
#            assert i!=-1 and line.endswith(')'),`line`
#            name = line[:i].rstrip()
#            array_spec = split_comma(line[i+1:-1].strip(), self.item)
#            var = self.get_variable(name)
#            var.set_bounds(array_spec)
            # end of KGEN deletion
            # start of KGEN addition
            if i!=-1:
                assert line.endswith(')'),str(line)
                name = line[:i].rstrip()
                array_spec = split_comma(line[i+1:-1].strip(), self.item)
                var = self.get_variable(name)
                var.set_bounds(array_spec)
            else:
                var = self.get_variable(line.strip())
            # end of KGEN addition
            var.update('target')
        return

    # start of KGEN addition
    def resolve_uname(self, uname, request, config):
        pass

    def tokgen(self):
        return 'TARGET %s' % (', '.join(self.items))
    # end of KGEN addition


class Pointer(Statement):
    """
    POINTER [ :: ] <pointer-decl-list>
    <pointer-decl> = <object-name> [ ( <deferred-shape-spec-list> ) ]
                   | <proc-entity-name>

    """
    f2003_class = Fortran2003.Pointer_Stmt # KGEN addition

    match = re.compile(r'pointer\b',re.I).match
    def process_item(self):
        line = self.item.get_line()[7:].lstrip()
        if line.startswith('::'):
            line = line[2:].lstrip()
        self.items = split_comma(line, self.item)
        return
    def tofortran(self, isfix=None):
        return self.get_indent_tab(isfix=isfix) + 'POINTER %s' % (', '.join(self.items))
    def analyze(self):
        # start of KGEN addition
        if not hasattr(self.parent, 'spec_stmts'):
            self.parent.spec_stmts = []
        self.parent.spec_stmts.append(self)
        # end of KGEN addition

        for line in self.items:
            i = line.find('(')
            if i==-1:
                name = line
                array_spec = None
            else:
                assert line.endswith(')'),str(line)
                name = line[:i].rstrip()
                array_spec = split_comma(line[i+1:-1].strip(), self.item)
            var = self.get_variable(name)
            var.set_bounds(array_spec)
            var.update('pointer')
        return

    # start of KGEN addition
    def resolve_uname(self, uname, request, config):
        pass

    def tokgen(self):
        return 'POINTER %s' % (', '.join(self.items))
    # end of KGEN addition

class Protected(StatementWithNamelist):
    """
    PROTECTED [ :: ] <entity-name-list>
    """
    f2003_class = Fortran2003.Protected_Stmt # KGEN addition

    match = re.compile(r'protected\b',re.I).match
    def analyze(self):
        # start of KGEN addition
        if not hasattr(self.parent, 'spec_stmts'):
            self.parent.spec_stmts = []
        self.parent.spec_stmts.append(self)
        # end of KGEN addition

        for name in self.items:
            var = self.get_variable(name)
            var.update('protected')
        return

class Volatile(StatementWithNamelist):
    """
    VOLATILE [ :: ] <object-name-list>
    """
    f2003_class = Fortran2003.Volatile_Stmt # KGEN addition

    match = re.compile(r'volatile\b',re.I).match
    def analyze(self):
        # start of KGEN addition
        if not hasattr(self.parent, 'spec_stmts'):
            self.parent.spec_stmts = []
        self.parent.spec_stmts.append(self)
        # end of KGEN addition

        for name in self.items:
            var = self.get_variable(name)
            var.update('volatile')
        return

class Value(StatementWithNamelist):
    """
    VALUE [ :: ] <dummy-arg-name-list>
    """
    f2003_class = Fortran2003.Value_Stmt # KGEN addition

    match = re.compile(r'value\b',re.I).match
    def analyze(self):
        # start of KGEN addition
        if not hasattr(self.parent, 'spec_stmts'):
            self.parent.spec_stmts = []
        self.parent.spec_stmts.append(self)
        # end of KGEN addition

        for name in self.items:
            var = self.get_variable(name)
            var.update('value')
        return

class ArithmeticIf(Statement):
    """
    IF ( <scalar-numeric-expr> ) <label> , <label> , <label>
    """
    f2003_class = Fortran2003.Arithmetic_If_Stmt # KGEN addition

    match = re.compile(r'if\s*\(.*\)\s*\d+\s*,\s*\d+\s*,\s*\d+\s*\Z', re.I).match
    def process_item(self):
        line = self.item.get_line()[2:].lstrip()
        line,l2,l3 = line.rsplit(',',2)
        i = line.rindex(')')
        l1 = line[i+1:]
        self.expr = self.item.apply_map(line[1:i]).strip()
        self.labels = [l1.strip(),l2.strip(),l3.strip()]
        return

    def tofortran(self, isfix=None):
        return self.get_indent_tab(isfix=isfix) + 'IF (%s) %s' \
               % (self.expr,', '.join(self.labels))
    def analyze(self): return

    # start of KGEN addition
    def tokgen(self):
        return 'IF (%s) %s' % (self.expr,', '.join(self.labels))
    # end of KGEN addition

class Intrinsic(StatementWithNamelist):
    """
    INTRINSIC [ :: ] <intrinsic-procedure-name-list>
    """
    f2003_class = Fortran2003.Intrinsic_Stmt # KGEN addition

    match = re.compile(r'intrinsic\b',re.I).match
    def analyze(self):
        for name in self.items:
            var = self.get_variable(name)
            var.update('intrinsic')
        return

class Inquire(Statement):
    """
    INQUIRE ( <inquire-spec-list> )
    INQUIRE ( IOLENGTH = <scalar-int-variable> ) <output-item-list>

    <inquire-spec> = [ UNIT = ] <file-unit-number>
                     | FILE = <file-name-expr>
                     ...
    <output-item> = <expr>
                  | <io-implied-do>
    """
    f2003_class = Fortran2003.Inquire_Stmt # KGEN addition

    match = re.compile(r'inquire\s*\(',re.I).match
    def process_item(self):
        line = self.item.get_line()[7:].lstrip()
        i = line.index(')')
        self.specs = specs_split_comma(line[1:i].strip(), self.item)
        self.items = split_comma(line[i+1:].lstrip(), self.item)
        return
    def tofortran(self, isfix=None):
        if self.items:
            return self.get_indent_tab(isfix=isfix) + 'INQUIRE (%s) %s' \
                   % (', '.join(self.specs), ', '.join(self.items))
        return self.get_indent_tab(isfix=isfix) + 'INQUIRE (%s)' \
                   % (', '.join(self.specs))
    def analyze(self): return

    # start of KGEN addition
    def tokgen(self):
        if hasattr(self, 'items') and self.items:
            return 'INQUIRE (%s) %s'%(', '.join(self.specs), ', '.join(self.items))
        return 'INQUIRE (%s)'%(', '.join(self.specs))
    # start of KGEN addition

class Sequence(Statement):
    """
    SEQUENCE
    """
    f2003_class = Fortran2003.Sequence_Stmt # KGEN addition

    match = re.compile(r'sequence\Z',re.I).match
    def process_item(self):
        return
    def tofortran(self, isfix=None): return self.get_indent_tab(isfix=isfix) + 'SEQUENCE'
    def analyze(self):
        self.parent.update_attributes('SEQUENCE')
        return

    def tokgen(self): return 'SEQUENCE'

class External(StatementWithNamelist):
    """
    EXTERNAL [ :: ] <external-name-list>
    """
    f2003_class = Fortran2003.External_Stmt # KGEN addition

    match = re.compile(r'external\b', re.I).match
    def analyze(self):
        # start of KGEN addition
        if not hasattr(self.parent, 'spec_stmts'):
            self.parent.spec_stmts = []
        self.parent.spec_stmts.append(self)
        # end of KGEN addition

        for name in self.items:
            var = self.get_variable(name)
            var.update('external')
        return

class Namelist(Statement):
    """
    NAMELIST / <namelist-group-name> / <namelist-group-object-list> [ [ , ] / <namelist-group-name> / <namelist-group-object-list> ]...
    <namelist-group-object> = <variable-name>
    """
    f2003_class = Fortran2003.Namelist_Stmt # KGEN addition

    match = re.compile(r'namelist\b',re.I).match
    def process_item(self):
        line = self.item.get_line()[8:].lstrip()
        items = []
        while line:
            assert line.startswith('/'),str(line)
            i = line.find('/',1)
            assert i!=-1,str(line)
            name = line[:i+1]
            line = line[i+1:].lstrip()
            i = line.find('/')
            if i==-1:
                items.append((name,line))
                line = ''
                continue
            s = line[:i].rstrip()
            if s.endswith(','):
                s = s[:-1].rstrip()
            items.append((name,s))
            line = line[i+1:].lstrip()
        self.items = items
        return

    def tofortran(self, isfix=None):
        l = []
        for name,s in self.items:
            l.append('%s %s' % (name,s))
        tab = self.get_indent_tab(isfix=isfix)
        return tab + 'NAMELIST ' + ', '.join(l)

    # start of KGEN
    def analyze(self):
        pass

    def tokgen(self):
        l = []
        for name,s in self.items:
            l.append('%s %s' % (name,s))
        return 'NAMELIST ' + ', '.join(l)

    # end of KGEN

class Common(Statement):
    """
    COMMON [ / [ <common-block-name> ] / ]  <common-block-object-list> \
      [ [ , ] / [ <common-block-name> ] /  <common-block-object-list> ]...
    <common-block-object> = <variable-name> [ ( <explicit-shape-spec-list> ) ]
                          | <proc-pointer-name>
    """
    f2003_class = Fortran2003.Common_Stmt # KGEN addition

    match = re.compile(r'common\b',re.I).match
    def process_item(self):
        item = self.item
        line = item.get_line()[6:].lstrip()
        items = []
        while line:
            if not line.startswith('/'):
                name = ''
                assert not items,str(line)
            else:
                i = line.find('/',1)
                assert i!=-1,str(line)
                name = line[1:i].strip()
                line = line[i+1:].lstrip()
            i = line.find('/')
            if i==-1:
                items.append((name,split_comma(line, item)))
                line = ''
                continue
            s = line[:i].rstrip()
            if s.endswith(','):
                s = s[:-1].rstrip()
            items.append((name,split_comma(s,item)))
            line = line[i:].lstrip()
        self.items = items
        return
    def tofortran(self, isfix=None):
        l = []
        for name,s in self.items:
            s = ', '.join(s)
            if name:
                l.append('/ %s / %s' % (name,s))
            else:
                l.append(s)
        tab = self.get_indent_tab(isfix=isfix)
        return tab + 'COMMON ' + ' '.join(l)
    def analyze(self):
        # start of KGEN addition
        if not hasattr(self.parent, 'spec_stmts'):
            self.parent.spec_stmts = []
        self.parent.spec_stmts.append(self)
        # end of KGEN addition

        for cname, items in self.items:
            self.parent.a.common_stmts[cname] = self # KGEN addition
            for item in items:
                i = item.find('(')
                if i!=-1:
                    assert item.endswith(')'),str(item)
                    name = item[:i].rstrip()
                    shape = split_comma(item[i+1:-1].strip(), self.item)
                else:
                    name = item
                    shape = None
                var = self.get_variable(name)
                if shape is not None:
                    var.set_bounds(shape)
            # XXX: add name,var to parent_provides
        return

    # start of KGEN addition
    def tokgen(self):
        l = []
        for name,s in self.items:
            s = ', '.join(s)
            if name:
                l.append('/ %s / %s' % (name,s))
            else:
                l.append(s)
        return 'COMMON ' + ' '.join(l)

    def resolve_uname(self, uname, request, config):
        if self.items:
            for bname, vname in self.items:
                if uname.firstpartname()==bname: 
                    self.add_geninfo(uname, request)
                    break
    # end of KGEN addition

class Optional(StatementWithNamelist):
    """
    OPTIONAL [ :: ] <dummy-arg-name-list>
    <dummy-arg-name> = <name>
    """
    f2003_class = Fortran2003.Optional_Stmt # KGEN addition

    match = re.compile(r'optional\b',re.I).match
    def analyze(self):
        # start of KGEN addition
        if not hasattr(self.parent, 'spec_stmts'):
            self.parent.spec_stmts = []
        self.parent.spec_stmts.append(self)
        # end of KGEN addition

        for name in self.items:
            var = self.get_variable(name)
            var.update('optional')
        return

class Intent(Statement):
    """
    INTENT ( <intent-spec> ) [ :: ] <dummy-arg-name-list>
    <intent-spec> = IN | OUT | INOUT

    generalization for pyf-files:
    INTENT ( <intent-spec-list> ) [ :: ] <dummy-arg-name-list>
    <intent-spec> = IN | OUT | INOUT | CACHE | HIDE | OUT = <name>
    """
    f2003_class = Fortran2003.Intent_Stmt # KGEN addition

    match = re.compile(r'intent\s*\(',re.I).match
    def process_item(self):
        line = self.item.get_line()[6:].lstrip()
        i = line.find(')')
        self.specs = specs_split_comma(line[1:i], self.item, upper=True)
        line = line[i+1:].lstrip()
        if line.startswith('::'):
            line = line[2:].lstrip()
        self.items = [s.strip() for s in line.split(',')]
        for n in self.items:
            if not is_name(n):
                self.isvalid = False
                return
        return
    def tofortran(self, isfix=None):
        return self.get_indent_tab(isfix=isfix) + 'INTENT (%s) %s' \
               % (', '.join(self.specs), ', '.join(self.items))
    def analyze(self):
        # start of KGEN addition
        if not hasattr(self.parent, 'spec_stmts'):
            self.parent.spec_stmts = []
        self.parent.spec_stmts.append(self)
        # end of KGEN addition

        for name in self.items:
            var = self.get_variable(name)
            var.set_intent(self.specs)
        return

    # start of KGEN addition
    def resolve_uname(self, uname, request, config):
        pass

    def tokgen(self):
        return 'INTENT (%s) %s' % (', '.join(self.specs), ', '.join(self.items))

    # end of KGEN addition


class Entry(Statement):
    """
    ENTRY <entry-name> [ ( [ <dummy-arg-list> ] ) [ <suffix> ] ]
    <suffix> = <proc-language-binding-spec> [ RESULT ( <result-name> ) ]
             | RESULT ( <result-name> ) [ <proc-language-binding-spec> ]
    <proc-language-binding-spec> = <language-binding-spec>
    <language-binding-spec> = BIND ( C [ , NAME = <scalar-char-initialization-expr> ] )
    <dummy-arg> = <dummy-arg-name> | *
    """
    f2003_class = Fortran2003.Entry_Stmt # KGEN addition

    match = re.compile(r'entry\s+[a-zA-Z]\w', re.I).match
    def process_item(self):
        line = self.item.get_line()[5:].lstrip()
        m = re.match(r'\w+', line)
        name = line[:m.end()]
        line = line[m.end():].lstrip()
        if line.startswith('('):
            i = line.find(')')
            assert i!=-1,str(line)
            items = split_comma(line[1:i], self.item)
            line = line[i+1:].lstrip()
        else:
            items = []
        self.bind, line = parse_bind(line, self.item)
        self.result, line = parse_result(line, self.item)
        if line:
            assert self.bind is None,str(self.bind)
            self.bind, line = parse_bind(line, self.item)
        assert not line,str(line)
        self.name = name
        self.items = items
        return
    def tofortran(self, isfix=None):
        tab = self.get_indent_tab(isfix=isfix)
        s = tab + 'ENTRY '+self.name
        if self.items:
            s += ' (%s)' % (', '.join(self.items))
        if self.result:
            s += ' RESULT (%s)' % (self.result)
        if self.bind:
            s += ' BIND (%s)' % (', '.join(self.bind))
        return s

    # start of KGEN addition
    def tofortran(self, isfix=None):
        s = 'ENTRY '+self.name
        if hasattr(self, 'items') and self.items:
            s += ' (%s)' % (', '.join(self.items))
        if hasattr(self, 'result') and self.result:
            s += ' RESULT (%s)' % (self.result)
        if hasattr(self, 'bind') and self.bind:
            s += ' BIND (%s)' % (', '.join(self.bind))
        return s
    # end of KGEN addition


class Import(StatementWithNamelist):
    """
    IMPORT [ [ :: ] <import-name-list> ]
    """
    f2003_class = Fortran2003.Import_Stmt # KGEN addition

    match = re.compile(r'import(\b|\Z)',re.I).match

    # start of KGEN addition
    def analyze(self):
        if not hasattr(self.parent, 'spec_stmts'):
            self.parent.spec_stmts = []
        self.parent.spec_stmts.append(self)
    # end of KGEN addition

class Forall(Statement):
    """
    FORALL <forall-header> <forall-assignment-stmt>
    <forall-header> = ( <forall-triplet-spec-list> [ , <scalar-mask-expr> ] )
    <forall-triplet-spec> = <index-name> = <subscript> : <subscript> [ : <stride> ]
    <subscript|stride> = <scalar-int-expr>
    <forall-assignment-stmt> = <assignment-stmt> | <pointer-assignment-stmt>
    """
    f2003_class = Fortran2003.Forall_Stmt # KGEN addition

    match = re.compile(r'forall\s*\(.*\).*=', re.I).match
    def process_item(self):
        line = self.item.get_line()[6:].lstrip()
        i = line.index(')')

        line0 = line[1:i]
        line = line[i+1:].lstrip()
        stmt = GeneralAssignment(self, self.item.copy(line, True))
        if stmt.isvalid:
            self.content = [stmt]
        else:
            self.isvalid = False
            return

        specs = []
        mask = ''
        for l in split_comma(line0,self.item):
            j = l.find('=')
            if j==-1:
                assert not mask, str(mask)+str(l)
                mask = l
                continue
            assert j!=-1,str(l)
            index = l[:j].rstrip()
            it = self.item.copy(l[j+1:].lstrip())
            l = it.get_line()
            k = l.split(':')
            if len(k)==3:
                s1, s2, s3 = map(it.apply_map,
                                 [k[0].strip(),k[1].strip(),k[2].strip()])
            else:
                assert len(k)==2,str(k)
                s1, s2 = map(it.apply_map,
                             [k[0].strip(),k[1].strip()])
                s3 = '1'
            specs.append((index,s1,s2,s3))

        self.specs = specs
        self.mask = mask
        return

    def tofortran(self, isfix=None):
        tab = self.get_indent_tab(isfix=isfix)
        l = []
        for index,s1,s2,s3 in self.specs:
            s = '%s = %s : %s' % (index,s1,s2)
            if s3!='1':
                s += ' : %s' % (s3)
            l.append(s)
        s = ', '.join(l)
        if self.mask:
            s += ', ' + self.mask
        return tab + 'FORALL (%s) %s' % \
               (s, str(self.content[0]).lstrip())
    def analyze(self): return

    # start of KGEN addition
    def tokgen(self):
        l = []
        for index,s1,s2,s3 in self.specs:
            s = '%s = %s : %s' % (index,s1,s2)
            if s3!='1':
                s += ' : %s' % (s3)
            l.append(s)
        s = ', '.join(l)
        if hasattr(self, 'mask') and self.mask:
            s += ', ' + self.mask
        return 'FORALL (%s) %s' %(s, str(self.content[0]).lstrip())
    # end of KGEN addition

ForallStmt = Forall

class SpecificBinding(Statement):
    """
    PROCEDURE [ ( <interface-name> ) ]  [ [ , <binding-attr-list> ] :: ] <binding-name> [ => <procedure-name> ]
    <binding-attr> = PASS [ ( <arg-name> ) ]
                   | NOPASS
                   | NON_OVERRIDABLE
                   | DEFERRED
                   | <access-spec>
    <access-spec> = PUBLIC | PRIVATE
    """
    f2003_class = Fortran2003.Specific_Binding # KGEN addition

    match = re.compile(r'procedure\b',re.I).match
    def process_item(self):
        line = self.item.get_line()[9:].lstrip()
        if line.startswith('('):
            i = line.index(')')
            name = line[1:i].strip()
            line = line[i+1:].lstrip()
        else:
            name = ''
        self.iname = name
        if line.startswith(','):
            line = line[1:].lstrip()
        i = line.find('::')
        if i != -1:
            attrs = split_comma(line[:i], self.item)
            line = line[i+2:].lstrip()
        else:
            attrs = []
        attrs1 = []
        for attr in attrs:
            if is_name(attr):
                attr = attr.upper()
            else:
                i = attr.find('(')
                assert i!=-1 and attr.endswith(')'), str(attr)
                attr = '%s (%s)' % (attr[:i].rstrip().upper(), attr[i+1:-1].strip())
            attrs1.append(attr)
        self.attrs = attrs1
        i = line.find('=')
        if i==-1:
            self.name = line
            self.bname = ''
        else:
            self.name = line[:i].rstrip()
            self.bname = line[i+1:].lstrip()[1:].lstrip()
        return
    def tofortran(self, isfix=None):
        tab = self.get_indent_tab(isfix=isfix)
        s = 'PROCEDURE '
        if self.iname:
            s += '(' + self.iname + ') '
        if self.attrs:
            s += ', ' + ', '.join(self.attrs) + ' :: '
        if self.bname:
            s += '%s => %s' % (self.name, self.bname)
        else:
            s += self.name
        return tab + s

    # start of KGEN addtion
    def analyze(self):
        return

    def tokgen(self):
        s = 'PROCEDURE '
        if self.iname:
            s += '(' + self.iname + ') '
        if self.attrs:
            s += ', ' + ', '.join(self.attrs) + ' :: '
        if self.bname:
            s += '%s => %s' % (self.name, self.bname)
        else:
            s += self.name
        return s
    # end of KGEN addtion

class GenericBinding(Statement):
    """
    GENERIC [ , <access-spec> ] :: <generic-spec> => <binding-name-list>
    """
    f2003_class = Fortran2003.Generic_Binding # KGEN addition

    match = re.compile(r'generic\b.*::.*=\>.*\Z', re.I).match
    def process_item(self):
        line = self.item.get_line()[7:].lstrip()
        if line.startswith(','):
            line = line[1:].lstrip()
        i = line.index('::')
        self.aspec = line[:i].rstrip().upper()
        line = line[i+2:].lstrip()
        i = line.index('=>')
        self.spec = self.item.apply_map(line[:i].rstrip())
        self.items = split_comma(line[i+2:].lstrip())
        return

    def tofortran(self, isfix=None):
        tab = self.get_indent_tab(isfix=isfix)
        s = 'GENERIC'
        if self.aspec:
            s += ', '+self.aspec
        s += ' :: ' + self.spec + ' => ' + ', '.join(self.items)
        return tab + s

    # start of KGEN addition
    def tokgen(self):
        s = 'GENERIC'
        if self.aspec:
            s += ', '+self.aspec
        s += ' :: ' + self.spec + ' => ' + ', '.join(self.items)
        return s

    def analyze(self):
        return

    # end of KGEN addition

class FinalBinding(StatementWithNamelist):
    """
    FINAL [ :: ] <final-subroutine-name-list>
    """
    f2003_class = Fortran2003.Final_Binding # KGEN addition

    stmtname = 'final'
    match = re.compile(r'final\b', re.I).match

    # start of KGEN addition
    def tokgen(self):
        return 'FINAL :: ' + ', '.join(self.items)

    def analyze(self):
        return

    # end of KGEN addition

class Allocatable(Statement):
    """
    ALLOCATABLE [ :: ] <object-name> [ ( <deferred-shape-spec-list> ) ] [ , <object-name> [ ( <deferred-shape-spec-list> ) ] ]...
    """
    f2003_class = Fortran2003.Allocatable_Stmt # KGEN addition

    match = re.compile(r'allocatable\b',re.I).match
    def process_item(self):
        line = self.item.get_line()[11:].lstrip()
        if line.startswith('::'):
            line = line[2:].lstrip()
        self.items = split_comma(line, self.item)
        return
    def tofortran(self, isfix=None):
        return self.get_indent_tab(isfix=isfix) + 'ALLOCATABLE ' + ', '.join(self.items)
    def analyze(self):
        # start of KGEN addition
        if not hasattr(self.parent, 'spec_stmts'):
            self.parent.spec_stmts = []
        self.parent.spec_stmts.append(self)
        # end of KGEN addition

        for line in self.items:
            i = line.find('(')
            if i==-1:
                name = line
                array_spec = None
            else:
                assert line.endswith(')')
                name = line[:i].rstrip()
                array_spec = split_comma(line[i+1:-1], self.item)
            var = self.get_variable(name)
            var.update('allocatable')
            if array_spec is not None:
                var.set_bounds(array_spec)
        return

    # start of KGEN addition
    def resolve_uname(self, uname, request, config):
        pass

    def tokgen(self):
        return 'ALLOCATABLE ' + ', '.join(self.items)
    # end of KGEN addition

class Asynchronous(StatementWithNamelist):
    """
    ASYNCHRONOUS [ :: ] <object-name-list>
    """
    f2003_class = Fortran2003.Asynchronous_Stmt # KGEN addition

    match = re.compile(r'asynchronous\b',re.I).match
    def analyze(self):
        # start of KGEN addition
        if not hasattr(self.parent, 'spec_stmts'):
            self.parent.spec_stmts = []
        self.parent.spec_stmts.append(self)
        # end of KGEN addition

        for name in self.items:
            var = self.get_variable(name)
            var.update('asynchronous')
        return

class Bind(Statement):
    """
    <language-binding-spec> [ :: ] <bind-entity-list>
    <language-binding-spec> = BIND ( C [ , NAME = <scalar-char-initialization-expr> ] )
    <bind-entity> = <entity-name> | / <common-block-name> /
    """
    f2003_class = Fortran2003.Bind_Stmt # KGEN addition

    match = re.compile(r'bind\s*\(.*\)',re.I).match
    def process_item(self):
        line = self.item.line
        self.specs, line = parse_bind(line, self.item)
        if line.startswith('::'):
            line = line[2:].lstrip()
        items = []
        for item in split_comma(line, self.item):
            if item.startswith('/'):
                assert item.endswith('/'),str(item)
                item = '/ ' + item[1:-1].strip() + ' /'
            items.append(item)
        self.items = items
        return
    def tofortran(self, isfix=None):
        return self.get_indent_tab(isfix=isfix) + 'BIND (%s) %s' %\
               (', '.join(self.specs), ', '.join(self.items))

    # start of KGEN addition
    def analyze(self):
        if not hasattr(self.parent, 'spec_stmts'):
            self.parent.spec_stmts = []
        self.parent.spec_stmts.append(self)

    def resolve_uname(self, uname, request, config):
        pass

    def tokgen(self):
        return 'BIND (%s) %s' % (', '.join(self.specs), ', '.join(self.items))
    # end of KGEN addition

# IF construct statements

class Else(Statement):
    """
    ELSE [<if-construct-name>]
    """
    f2003_class = Fortran2003.Else_Stmt # KGEN addition

    match = re.compile(r'else\b\s*\w*\s*\Z',re.I).match

    def process_item(self):
        item = self.item
        self.name = item.get_line()[4:].strip()
        #parent_name = getattr(self.parent,'name','') # KGEN deletion
        parent_name = getattr(self.parent,'construct_name','') # KGEN addition
        if self.name and self.name!=parent_name:
            self.warning('expected if-construct-name %r but got %r, skipping.'\
                         % (parent_name, self.name))
            self.isvalid = False
        return

    def tofortran(self, isfix=None):
        if self.name:
            return self.get_indent_tab(deindent=True) + 'ELSE ' + self.name
        return self.get_indent_tab(deindent=True) + 'ELSE'

    def analyze(self): return

    # start of KGEN addition
    def tokgen(self):
        if hasattr(self, 'name') and self.name:
            return 'ELSE ' + self.name
        return 'ELSE'

    # end of KGEN addition

class ElseIf(Statement):
    """
    ELSE IF ( <scalar-logical-expr> ) THEN [ <if-construct-name> ]
    """
    f2003_class = Fortran2003.Else_If_Stmt # KGEN addition

    match = re.compile(r'else\s*if\s*\(.*\)\s*then\s*\w*\s*\Z',re.I).match

    def process_item(self):
        item = self.item
        line = item.get_line()[4:].lstrip()[2:].lstrip()
        i = line.find(')')
        assert line[0]=='('
        self.expr = item.apply_map(line[1:i])
        self.name = line[i+1:].lstrip()[4:].strip()
        parent_name = getattr(self.parent,'name','')
        if self.name and self.name!=parent_name:
            self.warning('expected if-construct-name %r but got %r, skipping.'\
                         % (parent_name, self.name))
            self.isvalid = False
        return

    def tofortran(self, isfix=None):
        s = ''
        if self.name:
            s = ' ' + self.name
        return self.get_indent_tab(deindent=True) + 'ELSE IF (%s) THEN%s' \
               % (self.expr, s)

    def analyze(self): return

    # start of KGEN addition
    def tokgen(self):
        s = ''
        if hasattr(self, 'name') and self.name:
            s = ' ' + self.name
        return 'ELSE IF (%s) THEN%s'%(self.expr, s)

    # end of KGEN addition

# SelectCase construct statements

class Case(Statement):
    """
    CASE <case-selector> [ <case-constract-name> ]
    <case-selector> = ( <case-value-range-list> ) | DEFAULT
    <case-value-range> = <case-value>
                         | <case-value> :
                         | : <case-value>
                         | <case-value> : <case-value>
    <case-value> = <scalar-(int|char|logical)-initialization-expr>
    """
    f2003_class = Fortran2003.Case_Stmt # KGEN addition

    match = re.compile(r'case\b\s*(\(.*\)|DEFAULT)\s*\w*\Z',re.I).match
    def process_item(self):
        #assert self.parent.__class__.__name__=='Select',`self.parent.__class__`
        line = self.item.get_line()[4:].lstrip()
        if line.startswith('('):
            i = line.find(')')
            items = split_comma(line[1:i].strip(), self.item)
            line = line[i+1:].lstrip()
        else:
            assert line.lower().startswith('default'),str(line)
            items = []
            line = line[7:].lstrip()
        for i in range(len(items)):
            it = self.item.copy(items[i])
            rl = []
            for r in it.get_line().split(':'):
                rl.append(it.apply_map(r.strip()))
            items[i] = rl
        self.items = items
        self.name = line
        parent_name = getattr(self.parent, 'name', '')
        if self.name and self.name!=parent_name:
            self.warning('expected case-construct-name %r but got %r, skipping.'\
                         % (parent_name, self.name))
            self.isvalid = False
        return

    def tofortran(self, isfix=None):
        tab = self.get_indent_tab(isfix=isfix)
        s = 'CASE'
        if self.items:
            l = []
            for item in self.items:
                l.append((' : '.join(item)).strip())
            s += ' ( %s )' % (', '.join(l))
        else:
            s += ' DEFAULT'
        if self.name:
            s += ' ' + self.name
        return s
    def analyze(self): return

    # start of KGEN addition
    def tokgen(self):
        s = 'CASE'
        if self.items:
            l = []
            for item in self.items:
                l.append((' : '.join(item)).strip())
            s += ' ( %s )' % (', '.join(l))
        else:
            s += ' DEFAULT'
        if self.name:
            s += ' ' + self.name
        return s
    # end of KGEN addition

# start of KGEN addition

class TypeGuard(Statement):
    """
    TYPE IS ( <type-spec> ) [ <select-constract-name> ]
    CLASS IS ( <type-spec> ) [ <select-constract-name> ]
    CLASS DEFAULT [ <select-constract-name> ]

    <type-spec> = <intrinsic-type-spec>
                  | <derived-type-spec>
    """

    f2003_class = Fortran2003.Type_Guard_Stmt

    match = re.compile(r'(type|class)\b\s+(is\s*\(.*\)|DEFAULT)\s*\w*\Z',re.I).match
    def process_item(self):
        #assert self.parent.__class__.__name__=='Select',`self.parent.__class__`
        line = self.item.get_line().lstrip()
        if line.startswith('type'):
            line = line[4:].lstrip()
            assert line[:2] == 'is'
           
            line = line[2:].lstrip()
            assert line[0] == '('
            i = line.find(')')
            self.typespec = line[1:i]
            line = line[i+1:].lstrip() 
            self.guard = 'type is'
        elif line.startswith('class'):
            line = line[5:].lstrip()

            if line[:2] == 'is':
                line = line[2:].lstrip()
                assert line[0] == '('
                i = line.find(')')
                self.typespec = line[1:i]
                line = line[i+1:].lstrip() 
                self.guard = 'class is'

            elif line[:7] == 'default':
                self.typespec = None
                line = line[7:].lstrip()
                self.guard = 'class default'
            else:
                raise

        self.name = line

        parent_name = getattr(self.parent, 'name', '')
        if self.name and self.name!=parent_name:
            self.warning('expected select-construct-name %r but got %r, skipping.'\
                         % (parent_name, self.name))
            self.isvalid = False
        return

    def tofortran(self, isfix=None):
        tab = self.get_indent_tab(isfix=isfix)
        s = self.guard
        if self.typespec:
            s += '( %s )'%self.typespec
        if self.name:
            s += ' ' + self.name
        return s

    def analyze(self): return

    def tokgen(self):
        s = self.guard
        if self.typespec:
            s += '( %s )'%self.typespec
        if self.name:
            s += ' ' + self.name
        return s

# end of KGEN addition

# Where construct statements

class Where(Statement):
    """
    WHERE ( <mask-expr> ) <where-assignment-stmt>
    """
    f2003_class = Fortran2003.Where_Stmt # KGEN addition

    match = re.compile(r'where\s*\(.*\)\s*\w.*\Z',re.I).match
    def process_item(self):
        line = self.item.get_line()[5:].lstrip()
        i = line.index(')')
        self.expr = self.item.apply_map(line[1:i].strip())
        line = line[i+1:].lstrip()

        #newitem = self.item.copy(line)
        if not line:
            newitem = self.get_item()
        else:
            newitem = self.item.copy(line, apply_map=True)
        newline = newitem.get_line()

        cls = Assignment
        #if cls.match(line):
        if cls.match(newline):
            stmt = cls(self, newitem)
            if stmt.isvalid:
                self.content = [stmt]
                return
        self.isvalid = False
        return

    def tofortran(self, isfix=None):
        tab = self.get_indent_tab(isfix=isfix)
        return tab + 'WHERE ( %s ) %s' % (self.expr, str(self.content[0]).lstrip())
    def analyze(self): return

    # start of KGEN addition
    def tokgen(self):
        return 'WHERE ( %s ) %s' % (self.expr, str(self.content[0]).lstrip())
    # end of KGEN addition

WhereStmt = Where

class ElseWhere(Statement):
    """
    ELSE WHERE ( <mask-expr> ) [ <where-construct-name> ]
    ELSE WHERE [ <where-construct-name> ]
    """
    f2003_class = Fortran2003.Elsewhere_Stmt # KGEN addition

    match = re.compile(r'else\s*where\b',re.I).match
    def process_item(self):
        line = self.item.get_line()[4:].lstrip()[5:].lstrip()
        self.expr = None
        if line.startswith('('):
            i = line.index(')')
            assert i != -1, str(line)
            self.f2003_class = Fortran2003.Masked_Elsewhere_Stmt # KGEN addition
            self.expr = self.item.apply_map(line[1:i].strip())
            line = line[i+1:].lstrip()
        self.name = line
        parent_name = getattr(self.parent,'name','')
        if self.name and not self.name==parent_name:
            self.warning('expected where-construct-name %r but got %r, skipping.'\
                         % (parent_name, self.name))
            self.isvalid = False
        return

    def tofortran(self, isfix=None):
        tab = self.get_indent_tab(isfix=isfix)
        #s = 'ELSE WHERE' # KEGN deletion
        s = 'ELSEWHERE' # KGEN addition
        if self.expr is not None:
            s += ' ( %s )' % (self.expr)
        if self.name:
            s += ' ' + self.name
        return tab + s
    def analyze(self): return

    # start of KGEN addition
    def tokgen(self):
        s = 'ELSEWHERE' # KGEN addition
        if hasattr(self, 'expr') and self.expr is not None:
            s += ' ( %s )' % (self.expr)
        if hasattr(self, 'name') and self.name:
            s += ' ' + self.name
        return s
    # end of KGEN addition

# Enum construct statements

class Enumerator(Statement):
    """
    ENUMERATOR [ :: ] <enumerator-list>
    <enumerator> = <named-constant> [ = <scalar-int-initialization-expr> ]
    """
    f2003_class = Fortran2003.Enumerator_Def_Stmt # KGEN addition

    match = re.compile(r'enumerator\b',re.I).match

    def process_item(self):
        line = self.item.get_line()[10:].lstrip()
        if line.startswith('::'):
            line = line[2:].lstrip()
        self.items = split_comma(line, self.item)

        # start of KGEN addition
        self.named_consts = {}
        for item in self.items:
            pos = item.find("=")

            if pos > 0:
                self.named_consts[item[:pos].strip()] = item[pos+1:].strip()

            else:
                self.named_consts[item.strip()] = None
        # end of KGEN addition
        return

    def tofortran(self, isfix=None):
        return self.get_indent_tab(isfix=isfix) + 'ENUMERATOR ' + ', '.join(self.items)

    # start of KGEN addition
    def analyze(self):

        for consts in self.named_consts:
            self.parent.parent.a.enum_decls[consts] = (self.parent, self)
        return

    def tokgen(self):
        return 'ENUMERATOR ' + ', '.join(self.items)
    # end of KGEN addition

# F2PY specific statements

class FortranName(Statement):
    """
    FORTRANNAME <name>
    """
    match = re.compile(r'fortranname\s*\w+\Z',re.I).match
    def process_item(self):
        self.value = self.item.get_line()[11:].lstrip()
        return
    def tofortran(self, isfix=None):
        return self.get_indent_tab(isfix=isfix) + 'FORTRANNAME ' + self.value

    # start of KGEN addition
    def tokgen(self):
        return 'FORTRANNAME ' + self.value
    # end of KGEN addition

class Threadsafe(Statement):
    """
    THREADSAFE
    """
    match = re.compile(r'threadsafe\Z',re.I).match
    def process_item(self):
        return
    def tofortran(self, isfix=None):
        return self.get_indent_tab(isfix=isfix) + 'THREADSAFE'

    # start of KGEN addition
    def tofortran(self, isfix=None):
        return 'THREADSAFE'
    # end of KGEN addition

class Depend(Statement):
    """
    DEPEND ( <name-list> ) [ :: ] <dummy-arg-name-list>

    """
    match = re.compile(r'depend\s*\(',re.I).match
    def process_item(self):
        line = self.item.get_line()[6:].lstrip()
        i = line.find(')')
        self.depends = split_comma(line[1:i].strip(), self.item)
        line = line[i+1:].lstrip()
        if line.startswith('::'):
            line = line[2:].lstrip()
        self.items = split_comma(line)
        return

    def tofortran(self, isfix=None):
        return self.get_indent_tab(isfix=isfix) + 'DEPEND ( %s ) %s' \
               % (', '.join(self.depends), ', '.join(self.items))

    # start of KGEN addition
    def tokgen(self):
        return 'DEPEND ( %s ) %s' % (', '.join(self.depends), ', '.join(self.items))
    # end of KGEN addition

class Check(Statement):
    """
    CHECK ( <c-int-scalar-expr> ) [ :: ] <name>

    """
    match = re.compile(r'check\s*\(',re.I).match
    def process_item(self):
        line = self.item.get_line()[5:].lstrip()
        i = line.find(')')
        assert i!=-1, str(line)
        self.expr = self.item.apply_map(line[1:i].strip())
        line = line[i+1:].lstrip()
        if line.startswith('::'):
            line = line[2:].lstrip()
        self.value = line
        return
    def tofortran(self, isfix=None):
        return self.get_indent_tab(isfix=isfix) + 'CHECK ( %s ) %s' \
               % (self.expr, self.value)

    # start of KGEN addition
    def tokgen(self):
        return 'CHECK ( %s ) %s' % (self.expr, self.value)
    # end of KGEN addition

class CallStatement(Statement):
    """
    CALLSTATEMENT <c-expr>
    """
    match = re.compile(r'callstatement\b', re.I).match
    def process_item(self):
        self.expr = self.item.apply_map(self.item.get_line()[13:].lstrip())
        return
    def tofortran(self, isfix=None):
        return self.get_indent_tab(isfix=isfix) + 'CALLSTATEMENT ' + self.expr

    # start of KGEN addition
    def tofortran(self, isfix=None):
        return 'CALLSTATEMENT ' + self.expr
    # end of KGEN addition

class CallProtoArgument(Statement):
    """
    CALLPROTOARGUMENT <c-type-spec-list>
    """
    match = re.compile(r'callprotoargument\b', re.I).match
    def process_item(self):
        self.specs = self.item.apply_map(self.item.get_line()[17:].lstrip())
        return
    def tofortran(self, isfix=None):
        return self.get_indent_tab(isfix=isfix) + 'CALLPROTOARGUMENT ' + self.specs

    # start of KGEN addition
    def tofortran(self, isfix=None):
        return 'CALLPROTOARGUMENT ' + self.specs
    # end of KGEN addition
# Non-standard statements

class Pause(Statement):
    """
    PAUSE [ <char-literal-constant|int-literal-constant> ]
    """
    match = re.compile(r'pause\s*(\d+|\'\w*\'|"\w*"|)\Z', re.I).match
    def process_item(self):
        self.value = self.item.apply_map(self.item.get_line()[5:].lstrip())
        return
    def tofortran(self, isfix=None):
        if self.value:
            return self.get_indent_tab(isfix=isfix) + 'PAUSE ' + self.value
        return self.get_indent_tab(isfix=isfix) + 'PAUSE'
    def analyze(self): return

    # start of KGEN addition
    def tofortran(self):
        if hasattr(self, 'value') and self.value:
            return 'PAUSE ' + self.value
        return 'PAUSE'
    # end of KGEN addition

class Comment(Statement):
    """

    Attributes
    ----------
    content : str
      Content of the comment.
    is_blank : bool
      When True then Comment represents blank line.
    """
    f2003_class = Fortran2003.Comment # KGEN addition

    match = lambda s: True
    def process_item(self):
        assert self.item.comment.count('\n')<=1, str(self.item)
        stripped = self.item.comment.lstrip()
        self.is_blank = not stripped
        self.content = stripped[1:] if stripped else ''
    def tofortran(self, isfix=None):
        if self.is_blank:
            return ''
        if isfix:
            tab = 'C' + self.get_indent_tab(isfix=isfix)[1:]
        else:
            tab = self.get_indent_tab(isfix=isfix) + '!'
        return tab + self.content
    def analyze(self): return

    # start of KGEN addition
    def tokgen(self):
        if hasattr(self, 'comment') and self.comment:
            if hasattr(self, 'style') and self.style:
                if self.style=='openmp':
                    return '!$OMP %s'%self.comment
                elif self.style=='rawtext':
                    return self.comment
                elif self.style=='cpp':
                    return self.comment
                else:
                    return '!%s'%self.comment
            else:
                return '!%s'%self.comment
        else: return ''

    # start of KGEN deletion

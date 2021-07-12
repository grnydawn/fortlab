# simple_timing.py

#import os 
from fortlab.resolver import statements, block_statements, typedecl_statements
from fortlab.resolver.block_statements import SubProgramStatement, Function, Subroutine, Module
from fortlab.resolver.kgparse import KGGenType
from fortlab.kgplugin import Kgen_Plugin

class GenVar(Kgen_Plugin):
    def __init__(self):
        self.frame_msg = None

    # registration
    def register(self, msg):
        self.frame_msg = msg

        self.callsite_stmts = getinfo('callsite_stmts')

        # register initial events
        self.frame_msg.add_event(KERNEL_SELECTION.ALL, FILE_TYPE.KERNEL, GENERATION_STAGE.FINISH_PROCESS, \
            self.callsite_stmts[0], None, self.create_callsite_varlist)

        self.frame_msg.add_event(KERNEL_SELECTION.ALL, FILE_TYPE.KERNEL, GENERATION_STAGE.FINISH_PROCESS, \
            SubProgramStatement, None, self.create_subp_varlist)

        self.frame_msg.add_event(KERNEL_SELECTION.ALL, FILE_TYPE.KERNEL, GENERATION_STAGE.FINISH_PROCESS, \
            Module, None, self.create_module_varlist)

    def create_module_varlist(self, node):

        for typedecl in node.kgen_stmt.typedecl_resolvers:
            for uname, req in KGGenType.get_state_in(typedecl.geninfo):
                # add comment at referrer
                obj = req.originator.genkpair
                idx, name, part = get_part_index(obj)
                line = str(typedecl.item.span)
                cmt = "\"%s\" is defined at module \"%s\" near original line %s" % (uname.last(), node.name, line)
                part_insert_comment(obj.kgen_parent, name, idx, cmt)

                # add comment at referee
                obj = typedecl.genkpair
                idx, name, part = get_part_index(obj)
                ref = ":".join(uname.namelist[:-1])
                line = str(uname.stmt.item.span)
                cmt = "\"%s\" is referenced from namepath of \"%s\" near original line %s" % (uname.last(), ref, line)
                part_insert_comment(obj.kgen_parent, name, idx, cmt)

    def create_subp_varlist(self, node):

        idx, name, part = get_part_index(node)

        part_insert_comment(node.kgen_parent, name, idx, "")

        if hasattr(node.kgen_stmt, "geninfo"):
            for gendata in node.kgen_stmt.geninfo.values():
                for uname, res in gendata:
                    call = ":".join(uname.namelist[:-1])
                    line = str(uname.stmt.item.span)
                    cmt = "referenced from \"%s\" near original line %s" % (call, line)
                    part_insert_comment(node.kgen_parent, name, idx, cmt)

                    call = ":".join(uname.namelist[:-1])
                    line = str(uname.stmt.item.span)
                    cmt = "referenced from \"%s\" near original line %s" % (call, line)
                    part_insert_comment(node.kgen_parent, name, idx, cmt)

        part_insert_comment(node.kgen_parent, name, idx, "")
        part_insert_comment(node.kgen_parent, name, idx, "#########################################################")
        part_insert_comment(node.kgen_parent, name, idx, "This subprogram is called from following callsites:")
        part_insert_comment(node.kgen_parent, name, idx, "#########################################################")
        part_insert_comment(node.kgen_parent, name, idx, "")


        # TODO: mark at originator and destination too
        #for typedecl in node.kgen_stmt.typedecl_resolvers:
        #    for uname, req in KGGenType.get_state_in(typedecl.geninfo):
        #        import pdb;pdb.set_trace()


    def create_callsite_varlist(self, node):
  
        idx, name, part = get_part_index(node)

        # VAR

        for insubr in getinfo("modreadsubrs").values():
            for stmt in get_part(insubr, EXEC_PART):
                #part_append_node(node.kgen_parent, name, stmt)
                part_insert_node(node.kgen_parent, name, idx, stmt)

        part_insert_comment(node.kgen_parent, name, idx, "#########################################################")
        part_insert_comment(node.kgen_parent, name, idx, "External variables possibly used for calculating value(s) for other variable(s)")
        part_insert_comment(node.kgen_parent, name, idx, "#########################################################")
        part_insert_comment(node.kgen_parent, name, idx, "")

        for outsubr in getinfo("modwritesubrs").values():
            for stmt in get_part(outsubr, EXEC_PART):
                #part_append_node(node.kgen_parent, name, stmt)
                part_insert_node(node.kgen_parent, name, idx, stmt)

        part_insert_comment(node.kgen_parent, name, idx, "#########################################################")
        part_insert_comment(node.kgen_parent, name, idx, "External variables possibly being modified in the following part")
        part_insert_comment(node.kgen_parent, name, idx, "#########################################################")
        part_insert_comment(node.kgen_parent, name, idx, "")

        for stmt in getinfo("localread"):
            part_insert_node(node.kgen_parent, name, idx, stmt)

        part_insert_comment(node.kgen_parent, name, idx, "#########################################################")
        part_insert_comment(node.kgen_parent, name, idx, "Local variables possibly used for calculating value(s) for other variable(s)")
        part_insert_comment(node.kgen_parent, name, idx, "#########################################################")
        part_insert_comment(node.kgen_parent, name, idx, "")

        for stmt in getinfo("localwrite"):
            part_insert_node(node.kgen_parent, name, idx, stmt)

        part_insert_comment(node.kgen_parent, name, idx, "#########################################################")
        part_insert_comment(node.kgen_parent, name, idx, "Local variables possibly being modified in the following part")
        part_insert_comment(node.kgen_parent, name, idx, "#########################################################")
        part_insert_comment(node.kgen_parent, name, idx, "")


#        # register event per function 
#        self.frame_msg.add_event(KERNEL_SELECTION.ALL, FILE_TYPE.KERNEL, GENERATION_STAGE.NODE_CREATED, \
#            getinfo('parentblock_stmt'), None, self.register_event) 
#
#    def register_event(self, node):
#
#        attrs = {'type_spec': 'INTEGER', 'selector': ('8', None), \
#            'entity_decls': ['kgen_start_clock', 'kgen_stop_clock', 'kgen_rate_clock']}
#        part_append_genknode(node, DECL_PART, typedecl_statements.Integer, attrs=attrs) 
#
#        attrs = {'type_spec': 'REAL', 'selector': (None, 'kgen_dp'), 'entity_decls': ['gkgen_measure']}
#        part_append_genknode(node, DECL_PART, typedecl_statements.Real, attrs=attrs) 
#
#        prenode = getinfo('blocknode_aftercallsite_main')
#        self.frame_msg.add_event(KERNEL_SELECTION.ALL, FILE_TYPE.KERNEL, GENERATION_STAGE.BEGIN_PROCESS, \
#            prenode, None, self.add_execblock)
#
#    def add_execblock(self, node):
#
#        attrs = {'designator': 'SYSTEM_CLOCK', 'items': ['kgen_start_clock', 'kgen_rate_clock']}
#        part_append_genknode(node, EXEC_PART, statements.Call, attrs=attrs)
#       
#        attrs = {'loopcontrol': 'kgen_intvar = 1, KGEN_MAXITER'}
#        doiter = part_append_genknode(node, EXEC_PART, block_statements.Do, attrs=attrs)
#
#        kernel_stmts = getinfo('callsite_stmts')
#        start = kernel_stmts[0].item.span[0]-1
#        end = kernel_stmts[-1].item.span[1]
#        lines = kernel_stmts[0].top.prep[start:end]
#        lines_str = '\n'.join(lines)
#        dummy_node = part_append_genknode(doiter, EXEC_PART, statements.Call)
#        dummy_node.kgen_stmt = getinfo('dummy_stmt')
#        dummy_node.kgen_forced_line = lines_str
#
#        attrs = {'designator': 'SYSTEM_CLOCK', 'items': ['kgen_stop_clock', 'kgen_rate_clock']}
#        part_append_genknode(node, EXEC_PART, statements.Call, attrs=attrs)
#
#        if getinfo('cache_pollution'):
#            attrs = {'expr': 'kgen_cache_control(1) == 0'}
#            ifcache = part_append_genknode(node, EXEC_PART, block_statements.IfThen, attrs=attrs)
#
#            attrs = {'variable': 'kgen_stop_clock', 'sign': '=', 'expr': 'kgen_stop_clock  + kgen_cache_control(1)'}
#            part_append_genknode(ifcache, EXEC_PART, statements.Assignment, attrs=attrs)
#
#        attrs = {'variable': 'kgen_measure', 'sign': '=', 'expr': '1.0D6*(kgen_stop_clock - kgen_start_clock)/DBLE(kgen_rate_clock*KGEN_MAXITER)'}
#        part_append_genknode(node, EXEC_PART, statements.Assignment, attrs=attrs)
#
#        if getinfo('add_mpi_frame'):
#            part_append_comment(node, EXEC_PART, '#ifdef _MPI', style='rawtext')
#            part_append_comment(node, EXEC_PART, 'CALL mpi_allreduce(kgen_measure, gkgen_measure, 1, mpi_real8, mpi_max, mpi_comm_world, kgen_ierr)', style='rawtext')
#            attrs = {'variable': 'kgen_measure', 'sign': '=', 'expr': 'gkgen_measure'}
#            part_append_genknode(node, EXEC_PART, statements.Assignment, attrs=attrs)
#            part_append_comment(node, EXEC_PART, '#endif', style='rawtext')
#
#        attrs = {'expr': 'check_status%rank==0'}
#        ifrank = part_append_genknode(node, EXEC_PART, block_statements.IfThen, attrs=attrs)
#
#        attrs = {'items': ['"%s : Time per call (usec): "'%getinfo('kernel_name'), 'kgen_measure']}
#        part_append_gensnode(ifrank, EXEC_PART, statements.Write, attrs=attrs)

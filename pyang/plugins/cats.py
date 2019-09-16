'''
Created on Sep 4, 2019

@author: djyang
'''

import optparse
import sys
import re
import xml.dom.minidom as mndom

from pyang import plugin
from pyang import statements

def pyang_plugin_init():
    plugin.register_plugin(CatsPlugin())

class CatsPlugin(plugin.PyangPlugin):
    def __init__(self):
        plugin.PyangPlugin.__init__(self, 'cats')
        self.doc = mndom.Document()
        self.maps = {}
        self.diffns = []
        self.buildinType = ["int8","int16","int32","int64","uint8","uint16","uint32","uint64",
                           "decimal64","string","boolean","enumeration","bit", "binary","leafref",
                           "identityref","empty","union","instance-identifier"]
        self.integerTye = ["int8","int16","int32","int64","uint8","uint16","uint32","uint64",
                           "decimal64"]

    def add_output_format(self, fmts):
        self.multiple_modules = True
        fmts['cats'] = self

    def add_opts(self, optparser):
        optlist = [
            optparse.make_option("--cats-help",
                                 dest="cats_help",
                                 action="store_true",
                                 help="Print help on cats structure and exit"),
            optparse.make_option("--cats-prefix",
                                 type="string",
                                 dest="cats_prefix",
                                 help="the prefix of cats object"),
            optparse.make_option("--cats-platform-name",
                                 type="string",
                                 dest="cats_platform_name",
                                 help="the platform name"),
            optparse.make_option("--cats-platform-release",
                                 type="string",
                                 dest="cats_platform_release",
                                 help="the platform release number"),
            optparse.make_option("--cats-product-name",
                                 type="string",
                                 dest="cats_product_name",
                                 help="the product name"),
            optparse.make_option("--cats-product-release",
                                 type="string",
                                 dest="cats_product_release",
                                 help="the product release"),
            ]
        g = optparser.add_option_group("Cats output specific options")
        g.add_options(optlist)

    def setup_ctx(self, ctx):
        if ctx.opts.cats_help:
            print_help()
            sys.exit(0)

    def setup_fmt(self, ctx):
        ctx.implicit_errors = False

    def emit(self, ctx, modules, fd):
        if ctx.opts.cats_prefix is not None:
            self.name_prefix = ctx.opts.cats_prefix
        else:
            self.name_prefix = ""
        platform = self.doc.createElement("platform")
        platform.setAttribute("name" , "DCI")
        platform.setAttribute("release" , "1.0")
        self.doc.appendChild(platform)
        self.emit_tree(platform, ctx, modules)
        self.doc.writexml(fd, indent='  ', addindent='  ', newl='\n', encoding='utf-8')
        for key, value in self.maps.items():
            print(key+"\n")
        for value in self.diffns:
            print(value + "\n")
    def emit_tree(self, platformnode, ctx, modules):
        for module in modules:    
            chs = [ch for ch in module.i_children
                   if ch.keyword in statements.data_definition_keywords]
    
            if len(chs) > 0:
                self.print_children(chs, module, platformnode, 'data', None)
    
#             mods = [module]
#             for i in module.search('include'):
#                 subm = ctx.get_module(i.arg)
#                 if subm is not None:
#                     mods.append(subm)
#             section_delimiter_printed=False
#             for m in mods:
#                 for augment in m.search('augment'):
#                     if (hasattr(augment.i_target_node, 'i_module') and
#                         augment.i_target_node.i_module not in modules + mods):
#                         if not section_delimiter_printed:
#                             fd.write('\n')
#                             section_delimiter_printed = True
#                         # this augment has not been printed; print it
#                         if not printed_header:
#                             print_header()
#                             printed_header = True
#                         print_path("  augment", ":", augment.arg, fd, llen)
#                         mode = 'augment'
#                         if augment.i_target_node.keyword == 'input':
#                             mode = 'input'
#                         elif augment.i_target_node.keyword == 'output':
#                             mode = 'output'
#                         elif augment.i_target_node.keyword == 'notification':
#                             mode = 'notification'
#                         self.print_children(augment.i_children, m, fd,
#                                        '  ', path, mode, depth, llen,
#                                        ctx.opts.tree_no_expand_uses,
#                                        prefix_with_modname=ctx.opts.modname_prefix)
#     
            rpcs = [ch for ch in module.i_children
                    if ch.keyword == 'rpc']
            if len(rpcs) > 0:
                self.print_children(rpcs, module, platformnode, 'rpc', None)
      
            notifs = [ch for ch in module.i_children
                      if ch.keyword == 'notification']
            if len(notifs) > 0:
                self.print_children(notifs, module, platformnode,
                               'notification', None)
#     
#             if ctx.opts.tree_print_groupings:
#                 section_delimiter_printed = False
#                 for m in mods:
#                     for g in m.search('grouping'):
#                         if not printed_header:
#                             print_header()
#                             printed_header = True
#                         if not section_delimiter_printed:
#                             fd.write('\n')
#                             section_delimiter_printed = True
#                         fd.write("  grouping %s\n" % g.arg)
#                         self.print_children(g.i_children, m, fd,
#                                        '  ', path, 'grouping', depth, llen,
#                                        ctx.opts.tree_no_expand_uses,
#                                        prefix_with_modname=ctx.opts.modname_prefix)
#     
#             if ctx.opts.tree_print_yang_data:
#                 yds = module.search(('ietf-restconf', 'yang-data'))
#                 if len(yds) > 0:
#                     if not printed_header:
#                         print_header()
#                         printed_header = True
#                     section_delimiter_printed = False
#                     for yd in yds:
#                         if not section_delimiter_printed:
#                             fd.write('\n')
#                             section_delimiter_printed = True
#                         fd.write("  yang-data %s:\n" % yd.arg)
#                         self.print_children(yd.i_children, module, fd, '  ', path,
#                                        'yang-data', depth, llen,
#                                        ctx.opts.tree_no_expand_uses,
#                                        prefix_with_modname=ctx.opts.modname_prefix)

    def print_children(self, i_children, module, platformnode , mode, parentnode):
    
        for ch in i_children:
            if ((ch.keyword == 'input' or ch.keyword == 'output') and
                len(ch.i_children) == 0):
                pass
            else:
                if ch.keyword == 'input':
                    mode = 'input'
                elif ch.keyword == 'output':
                    mode = 'output'
                    continue #we don't care output
                self.print_node(ch, module, platformnode, mode, parentnode)
    
    def print_node(self, s, module, platformnode, mode, parentnode):

        def createElement(parent, stmt, name, nodetype):
            assert nodetype == "list" or nodetype == "container" or nodetype == "rpc" or nodetype == "notification"
            if nodetype == "list" or nodetype == "container":
                middlename = ''
            else:
                middlename = nodetype
            prefix = ''
            if self.name_prefix != '':
                prefix = self.name_prefix + '_'
            if middlename != '':
                prefix = prefix + middlename + '_'
            if parent is not None:
                if stmt.i_orig_module.arg != stmt.i_module.arg and stmt.i_uses_top:
                    if stmt.i_orig_module.arg == stmt.arg:
                        prefix += "___"
                    else:
                        prefix += (stmt.i_orig_module.arg+"__")
                elif stmt.i_module.arg != stmt.parent.i_module.arg:
                    if stmt.i_module.arg == stmt.arg:
                        prefix += "__"
                    else:
                        prefix += (stmt.i_module.arg+"__")
                else:  
                    parentname=parent.getAttribute("name")
                    prefix = parentname + "_"
            else: 
                nodename = name
            if prefix != '':
                nodename = prefix + name
            nodename = re.sub("org-openroadm-",'',nodename)
            try:
                childxmlnode = self.maps[nodename]
                return (childxmlnode, False)
            except KeyError:
                pass
            childxmlnode = self.doc.createElement("object")
            childxmlnode.setAttribute("name", nodename)
            childxmlnode.setAttribute("orig_module",stmt.i_orig_module.arg)
            childxmlnode.setAttribute("nodeType", nodetype)
            childxmlnode.setAttribute("__name",name)
            childxmlnode.setAttribute("objectType","xmlBean")
            childxmlnode.setAttribute("anto-create","yes")
            childxmlnode.setAttribute("extends","CommonXMLBean")
            self.maps[nodename] = childxmlnode
            return (childxmlnode, True)
        
        def createElementWithNameValue(elemname, name, value):
            anode = self.doc.createElement(elemname)
            anode.setAttribute("name", name)
            anode.setAttribute("value", value)
            return anode
        
        def addMetaInfo(xmlnode, module, adddeclareNS=True):
            metainfos = xmlnode.getElementsByTagName("metaInfo");
            if metainfos is None or len(metainfos) == 0:
                metainfonode = self.doc.createElement("metaInfo")
            else:
                metainfonode = metainfos[0]
            ns = module.search_one('namespace')
            if ns is not None:
                nsstr = ns.arg
            pr = module.search_one('prefix')
            if pr is not None:
                prstr = pr.arg
            metainfonode.appendChild(createElementWithNameValue("metaInfo", "__prefix", prstr))
            metainfonode.appendChild(createElementWithNameValue("metaInfo", "__uri", nsstr))
            if adddeclareNS:
                metainfonode.appendChild(createElementWithNameValue("metaInfo", "__declaredNS_prefix", "netconf"))
                metainfonode.appendChild(createElementWithNameValue("metaInfo", "__declaredNS_URI", "urn:ietf:params:xml:ns:netconf:base:1.0"))
            xmlnode.appendChild(metainfonode)

        def createAttribute(name, typestr):
            childxmlnode = self.doc.createElement("attribute")
            childxmlnode.setAttribute("name", name)
            tmpnode = self.doc.createElement("value")
            if typestr == '':
                tmpnode.setAttribute('type', "string")
            else:
                types = typestr.split("\n")
                type = types[0]
                types = types[1:]
                if type not in self.buildinType:
                    type = types[0]
                    types = types[1:]
                if type not in self.buildinType:
                    print("type string:%s is not buildin type" % typestr)
                    sys.exit(1)
                if types is not None and len(types) > 0:
                    hinttype = type + " " + types[0]
                else:
                    hinttype = type
                if type in self.integerTye:
                    tmpnode.setAttribute("type", "integer")
                    tmpnode.setAttribute("range", hinttype)
                elif type == "enumeration":
                    if types is not None and len(types) > 0:
                        enums = types[0].split(",")
                        if enums is not None and len(enums) > 0:
                            tmpnode.setAttribute("type","enum")
                            for enum in enums:
                                if enum.strip() == '':
                                    continue
                                option = self.doc.createElement("option")
                                option.setAttribute("name", enum.strip())
                                tmpnode.appendChild(option)
                        else:
                            tmpnode.setAttribute("type","format")
                            tmpnode.setAttribute("format", hinttype)     
                elif type == "identityref":
                    if types is not None and len(types) > 0:
                        enums = types[0].split(",")
                        if enums is not None and len(enums) > 0:
                            tmpnode.setAttribute("type","enum")
                            for enum in enums:
                                if enum.strip() == '':
                                    continue
                                option = self.doc.createElement("option")
                                option.setAttribute("name", enum.strip())
                                tmpnode.appendChild(option)
                        else:
                            tmpnode.setAttribute("type","format")
                            tmpnode.setAttribute("format", hinttype)                                  
                else: 
                    tmpnode.setAttribute("type","format")
                    tmpnode.setAttribute("format", hinttype)
            childxmlnode.appendChild(tmpnode)
            return childxmlnode

        def createElementAttribute(node):
            attrnode = self.doc.createElement("attribute")
            name = node.getAttribute("__name")
            attrnode.setAttribute("name", name)
            valuenode = self.doc.createElement("value")
            valuenode.setAttribute("type","object-name")
            optionnode = self.doc.createElement("option")
            optionnode.setAttribute("name", node.getAttribute("name"))
            valuenode.appendChild(optionnode)
            attrnode.appendChild(valuenode)           
            return attrnode
            
        def addAction(parent, name):
            addnode = self.doc.createElement("action")
            addnode.setAttribute("name", name)
            addnode.setAttribute("type", "cli")
            parent.appendChild(addnode)
            return addnode
            
        def addAttribute(parent, child):
            addnodes = parent.getElementsByTagName("action");
            if addnodes is None:
                addnode = addAction(parent, "add")
            else:
                found = False
                for node in addnodes:
                    name = node.getAttribute("name")
                    if name == "add":
                        found = True
                        addnode = node
                        break
                if not found:
                    addnode = addAction(parent,"add")  
            addnode.appendChild(child)

        def addElementAttribute(parent, child):
            childNode = createElementAttribute(child)
            addnodes = parent.getElementsByTagName("action");
            if addnodes is None:
                addnode = addAction(parent, "add")
            else:
                found = False
                for node in addnodes:
                    name = node.getAttribute("name")
                    if name == "add":
                        found = True
                        addnode = node
                        break
                if not found:
                    addnode = addAction(parent,"add")  
            addnode.appendChild(childNode)

        def setAttribute(parent, child):
            addnodes = parent.getElementsByTagName("action");
            if addnodes is None:
                addnode = addAction(parent, "set")
            else:
                found = False
                for node in addnodes:
                    name = node.getAttribute("name")
                    if name == "set":
                        found = True
                        addnode = node
                        break
                if not found:
                    addnode = addAction(parent,"set")  
            addnode.appendChild(child)

        def setElementAttribute(parent, child):
            childNode = createElementAttribute(child)
            addnodes = parent.getElementsByTagName("action");
            if addnodes is None:
                addnode = addAction(parent, "set")
            else:
                found = False
                for node in addnodes:
                    name = node.getAttribute("name")
                    if name == "set":
                        found = True
                        addnode = node
                        break
                if not found:
                    addnode = addAction(parent,"set")  
            addnode.appendChild(childNode)
        
        def updateRelationship(parent,child):
            metaInfos = child.getElementsByTagName("metaInfo");
            if metaInfos is None or len(metaInfos) == 0:
                metaInfo = self.doc.createElement("metaInfo")
            else:
                metaInfo = metaInfos[0]
            metaInfo.appendChild(createElementWithNameValue("metaInfo", "super", parent.getAttribute("name")))
            child.appendChild(metaInfo)  

        def createAction(parent,child,type):
            if type == 'list':
                addElementAttribute(parent, child)
            elif type == 'container':
                setElementAttribute(parent, child)
            else:
                print("don't support create action for type %s." % type)
        
        name = s.arg
        if s.i_module.i_modulename == module.i_modulename:
            tmpmodule = module
        else:
            tmpmodule = s.i_module
        flags = get_flags_str(s, mode)
#         print("%s %s -> module(%s)%s -> parent(%s).module:%s" % 
#               (s.keyword, s.arg, s.i_module.i_prefix, s.i_module.arg,
#                s.parent.keyword,
#                 s.parent.i_module))
        if s.keyword in ["list", "container"] and ((s.i_orig_module.arg != s.i_module.arg and s.i_uses_top) or 
                                                   (parentnode is not None and s.i_module.arg != s.parent.i_module.arg)):
            self.diffns.append("%s -> orig_module:%s   current_module:%s  parent_module:%s"  % 
                  (s.arg, s.i_orig_module.arg, s.i_module.arg, s.parent.i_module.arg))
            
        newObject = True
        if s.keyword == 'list' or s.keyword == 'container' or s.keyword == "rpc" or s.keyword == "notification":
            childxmlnode, newObject = createElement(parentnode, s, name, s.keyword)
            if newObject: platformnode.appendChild(childxmlnode)
            if parentnode is not None:
                createAction(parentnode, childxmlnode, s.keyword)
                updateRelationship(parentnode,childxmlnode)
            else:
                addMetaInfo(childxmlnode, module)
        elif s.keyword  == 'choice':
            childxmlnode = parentnode
        elif s.keyword == 'case':
            childxmlnode = parentnode
        elif s.keyword == 'input':
            childxmlnode = parentnode
        else:
#             t = get_typename(s, False)
            t = typestring(s)
            childxmlnode = createAttribute(name, t)
            if s.keyword == 'leaf-list':
                addAttribute(parentnode,childxmlnode)
            else:
                setAttribute(parentnode, childxmlnode)
        
        if not newObject: return
                    
        if s.keyword == 'list':
            if s.search_one('key') is not None:
                keystr = re.sub('\s+', '::', s.search_one('key').arg)
                childxmlnode.setAttribute("keys",keystr)
        elif s.keyword == 'container':
            p = s.search_one('presence')
            if p is not None:
                childxmlnode.setAttribute("presence","yes")
            
        if parentnode is not None and parentnode != childxmlnode and s.i_module.arg != s.parent.i_module.arg:
            addMetaInfo(childxmlnode, s.i_module, False)
             
        features = s.search('if-feature')
        featurenames = [f.arg for f in features]
        if hasattr(s, 'i_augment'):
            afeatures = s.i_augment.search('if-feature')
            featurenames.extend([f.arg for f in afeatures
                                 if f.arg not in featurenames])
    
        if hasattr(s, 'i_children') and s.keyword != 'uses':
            chs = s.i_children
            if s.keyword in ['choice', 'case']:
                self.print_children(chs, module, platformnode, mode, childxmlnode)
            else:
                self.print_children(chs, module, platformnode, mode, childxmlnode)
                      

def print_help():
    print("""
Each node is printed as:

<status>--<flags> <name><opts> <type> <if-features>

  <status> is one of:
    +  for current
    x  for deprecated
    o  for obsolete

  <flags> is one of:
    rw  for configuration data
    ro  for non-configuration data, output parameters to rpcs
        and actions, and notification parameters
    -w  for input parameters to rpcs and actions
    -u  for uses of a grouping
    -x  for rpcs and actions
    -n  for notifications

  <name> is the name of the node
    (<name>) means that the node is a choice node
   :(<name>) means that the node is a case node

   If the node is augmented into the tree from another module, its
   name is printed as <prefix>:<name>.

  <opts> is one of:
    ?  for an optional leaf, choice, anydata or anyxml
    !  for a presence container
    *  for a leaf-list or list
    [<keys>] for a list's keys

    <type> is the name of the type for leafs and leaf-lists, or
           "<anydata>" or "<anyxml>" for anydata and anyxml, respectively

    If the type is a leafref, the type is printed as "-> TARGET", where
    TARGET is the leafref path, with prefixes removed if possible.

  <if-features> is the list of features this node depends on, printed
    within curly brackets and a question mark "{...}?"
""")


def unexpand_uses(i_children):
    res = []
    uses = []
    for ch in i_children:
        if hasattr(ch, 'i_uses'):
            # take first from i_uses, which means "closest" grouping
            g = ch.i_uses[0].arg
            if g not in uses:
                # first node from this uses
                uses.append(g)
                res.append(ch.i_uses[0])
        else:
            res.append(ch)
    return res

def print_path(pre, post, path, fd, llen):
    def print_comps(pre, p, is_first):
        line = pre + '/' + p[0]
        p = p[1:]
        if len(line) > llen:
            # too long, print it anyway; it won't fit next line either
            pass
        else:
            while len(p) > 0 and len(line) + 1 + len(p[0]) <= llen:
                if len(p) == 1 and len(line) + 1 + len(p[0]) + len(post) > llen:
                    # if this is the last component, ensure 'post' fits
                    break
                line += '/' + p[0]
                p = p[1:]
        if len(p) == 0:
            line += post
        line += '\n'
        fd.write(line)
        if len(p) > 0:
            if is_first:
                pre = ' ' * (len(pre) + 2) # indent next line
            print_comps(pre, p, False)

    line = pre + ' ' + path + post
    if llen is None or len(line) <= llen:
        fd.write(line + '\n')
    else:
        p = path.split('/')
        if p[0] == '':
            p = p[1:]
        pre += " "
        print_comps(pre, p, True)


def get_status_str(s):
    status = s.search_one('status')
    if status is None or status.arg == 'current':
        return '+'
    elif status.arg == 'deprecated':
        return 'x'
    elif status.arg == 'obsolete':
        return 'o'

def get_flags_str(s, mode):
    if mode == 'input':
        return "-w"
    elif s.keyword in ('rpc', 'action', ('tailf-common', 'action')):
        return '-x'
    elif s.keyword == 'notification':
        return '-n'
    elif s.keyword == 'uses':
        return '-u'
    elif s.i_config == True:
        return 'rw'
    elif s.i_config == False or mode == 'output' or mode == 'notification':
        return 'ro'
    else:
        return ''

def get_leafref_path(s):
    t = s.search_one('type')
    if t is not None:
        if t.arg == 'leafref':
            return t.search_one('path')
    else:
        return None

def get_typename(s, prefix_with_modname=False):
    t = s.search_one('type')
    if t is not None:
        if t.arg == 'leafref':
            p = t.search_one('path')
            if p is not None:
                # Try to make the path as compact as possible.
                # Remove local prefixes, and only use prefix when
                # there is a module change in the path.
                target = []
                curprefix = s.i_module.i_prefix
                for name in p.arg.split('/'):
                    if name.find(":") == -1:
                        prefix = curprefix
                    else:
                        [prefix, name] = name.split(':', 1)
                    if prefix == curprefix:
                        target.append(name)
                    else:
                        if prefix_with_modname:
                            if prefix in s.i_module.i_prefixes:
                                # Try to map the prefix to the module name
                                (module_name, _) = s.i_module.i_prefixes[prefix]
                            else:
                                # If we can't then fall back to the prefix
                                module_name = prefix
                            target.append(module_name + ':' + name)
                        else:
                            target.append(prefix + ':' + name)
                        curprefix = prefix
                return "-> %s" % "/".join(target)
            else:
                # This should never be reached. Path MUST be present for
                # leafref type. See RFC6020 section 9.9.2
                # (https://tools.ietf.org/html/rfc6020#section-9.9.2)
                if prefix_with_modname:
                    if t.arg.find(":") == -1:
                        # No prefix specified. Leave as is
                        return t.arg
                    else:
                        # Prefix found. Replace it with the module name
                        [prefix, name] = t.arg.split(':', 1)
                        #return s.i_module.i_modulename + ':' + name
                        if prefix in s.i_module.i_prefixes:
                            # Try to map the prefix to the module name
                            (module_name, _) = s.i_module.i_prefixes[prefix]
                        else:
                            # If we can't then fall back to the prefix
                            module_name = prefix
                        return module_name + ':' + name
                else:
                    return t.arg
        else:
            if prefix_with_modname:
                if t.arg.find(":") == -1:
                    # No prefix specified. Leave as is
                    return t.arg
                else:
                    # Prefix found. Replace it with the module name
                    [prefix, name] = t.arg.split(':', 1)
                    #return s.i_module.i_modulename + ':' + name
                    if prefix in s.i_module.i_prefixes:
                        # Try to map the prefix to the module name
                        (module_name, _) = s.i_module.i_prefixes[prefix]
                    else:
                        # If we can't then fall back to the prefix
                        module_name = prefix
                    return module_name + ':' + name
            else:
                return t.arg
    elif s.keyword == 'anydata':
        return '<anydata>'
    elif s.keyword == 'anyxml':
        return '<anyxml>'
    else:
        return ''

def identitystring(node, baseid):
    t = node.search_one('type')
    if baseid.find(":") == -1:
        prefix = None
        name = baseid
    else:
        [prefix, name] = baseid.split(':', 1)
    if prefix is None or t.i_module.i_prefix == prefix:
        # check local typedefs
        pmodule = node.i_module
    else:
        # this is a prefixed name, check the imported modules
        err = []
        pmodule = statements.prefix_to_module(t.i_module,prefix,t.pos,err)
        if pmodule is None:
            return baseid
    identities = pmodule.search('identity')
    identitylist = []
    tmpidentitylist = [name]
    nextidentitylist = [name]
    while len(nextidentitylist) != 0:
        tmpidentitylist = nextidentitylist
        nextidentitylist = []
        for tmpidentity in tmpidentitylist:
            newidentitylist = [identity.arg for identity in identities 
                       if identity.search_one('base') is not None and identity.search_one('base').arg == tmpidentity]
            if newidentitylist is None or len(newidentitylist) == 0:
                identitylist.append(tmpidentity)
            else:
                nextidentitylist += newidentitylist
    return ','.join(identitylist)
    
def typestring(node):

    def get_nontypedefstring(node):
        s = ""
        found  = False
        t = node.search_one('type')
        if t is not None:
            s = t.arg + '\n'
            if t.arg == 'enumeration':
                found = True
                s = s + ' '
                for enums in t.substmts:
                    s = s + enums.arg + ','
                s = s + ' '
            elif t.arg == 'leafref':
                found = True
                if node.i_leafref_expanded:
                    targetnode = node.i_leafref.i_target_node
                    return get_nontypedefstring(targetnode)
                else:
                    print("node does not expand leafref")
                    sys.exit(1)
            elif t.arg == 'identityref':
                found = True
                b = t.search_one('base')
                if b is not None:
                    s = s + identitystring(node, b.arg)

            elif t.arg == 'union':
                found = True
                uniontypes = t.search('type')
                s = s + '' + uniontypes[0].arg
                for uniontype in uniontypes[1:]:
                    s = s + ', ' + uniontype.arg
                s = s + ''

            typerange = t.search_one('range')
            if typerange is not None:
                found = True
                s = s + ' [' + typerange.arg + ']'
            length = t.search_one('length')
            if length is not None:
                found = True
                s = s + ' {length = ' + length.arg + '}'

            pattern = t.search_one('pattern')
            if pattern is not None: # truncate long patterns
                found = True
                s = s + ' {pattern = ' + pattern.arg + '}'
        return s

    s = get_nontypedefstring(node)

    if s != "":
        t = node.search_one('type')
        # chase typedef
        type_namespace = None
        i_type_name = None
        name = t.arg
        if name.find(":") == -1:
            prefix = None
        else:
            [prefix, name] = name.split(':', 1)
        if prefix is None or t.i_module.i_prefix == prefix:
            # check local typedefs
            pmodule = node.i_module
            typedef = statements.search_typedef(t, name)
        else:
            # this is a prefixed name, check the imported modules
            err = []
            pmodule = statements.prefix_to_module(t.i_module,prefix,t.pos,err)
            if pmodule is None:
                return
            typedef = statements.search_typedef(pmodule, name)
        if typedef != None:
            s = s + get_nontypedefstring(typedef)
    return s

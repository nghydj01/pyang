'''
Created on Sep 4, 2019

@author: djyang
'''

import optparse
import sys
import io
import os
import re
import codecs
import configparser
import xml.dom.minidom as mndom

from pyang import plugin
from pyang import statements
from pip._internal.cli.cmdoptions import platform

def pyang_plugin_init():
    plugin.register_plugin(CatsPlugin())

class CatsPlugin(plugin.PyangPlugin):
    def __init__(self):
        plugin.PyangPlugin.__init__(self, 'cats')
        self.doc = mndom.Document()
        self.maps = {}
        self.diffns = []
        self.objnames = []
        self.topObj = []
        self.rpcObj = []
        self.naming_replace = True
        self.naming_without_parent = False
        self.naming_without_module = False
        self.notificationObj = []
        self.buildinType = ["int8","int16","int32","int64","uint8","uint16","uint32","uint64",
                           "decimal64","string","boolean","enumeration","bits", "binary","leafref",
                           "identityref","empty","union","instance-identifier", "inet:uri"]
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
            optparse.make_option("--cats-names-file",
                                 type="string",
                                 dest="cats_names_file",
                                 help="the file to store object names "),
            optparse.make_option("--cats-name-without-replace",
                                 dest="cats_without_replace",
                                 type="string",
                                 help="Print don't do replace and deletion"),
            optparse.make_option("--cats-name-without-parent",
                                 dest="cats_without_parent",
                                 type="string",
                                 help="Print don't prefix parent's name"),
            optparse.make_option("--cats-name-without-module",
                                 dest="cats_without_module",
                                 type="string",
                                 help="Print don't prefix module name"),
            optparse.make_option("--cats-config",
                                 type="string",
                                 dest="cats_config",
                                 help="options and/or naming substitution"),
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
        self.config = None
        if ctx.opts.cats_config is not None:
            if not os.path.isfile(ctx.opts.cats_config):
                print("Error: %s file not found" % ctx.opts.cats_config)
                sys.exit(1)
            self.config = configparser.ConfigParser()
            self.config.optionxform = lambda option:option
            self.config.read(ctx.opts.cats_config)

    def setup_fmt(self, ctx):
        ctx.implicit_errors = False
    
    def init_cats_options(self, ctx):
        if ctx.opts.cats_prefix is not None:
            self.name_prefix = ctx.opts.cats_prefix
        else:
            if self.config is not None and self.config.has_option('options', 'prefix'):
                self.name_prefix=self.config['options']['prefix']
            else:
                self.name_prefix = ""        
        if ctx.opts.cats_without_replace is not None:
            self.naming_replace=ctx.opts.cats_without_replace=="false"
        if ctx.opts.cats_without_parent is not None:
            self.naming_without_parent=ctx.opts.cats_without_parent=="true"
        if ctx.opts.cats_without_module is not None:
            self.naming_without_module=ctx.opts.cats_without_module=="true"
            
    def createElementWithNameValue(self, elemname, name, value):
        anode = self.doc.createElement(elemname)
        anode.setAttribute("name", name)
        anode.setAttribute("value", value)
        return anode
    
    def createAttribute(self, name, typestr, option_list=None):
        childxmlnode = self.doc.createElement("attribute")
        childxmlnode.setAttribute("name", name)
        tmpnode = self.doc.createElement("value")
        if typestr == '':
            tmpnode.setAttribute('type', "string")
        else:
            types = typestr.split("\n")
            type = types[0]
            types = types[1:]
            hinttype = ''
            while type not in self.buildinType:
                if "{rang " in type or \
                   "{pattern " in type or\
                   "{length " in type or\
                   "{fraction-digits " in type:
                    hinttype += type
                if len(types) > 0:
                    type = types[0]
                    types = types[1:]
                else:
                    break
            if type not in self.buildinType and type != "cats_object_name":
                print("type :%s is not buildin type" % typestr)
                sys.exit(1)
            if len(hinttype) > 1:
                pass
            elif types is not None and len(types) > 0:
                hinttype = type + " " + ' '.join(types)
            else:
                hinttype = type
            if type in self.integerTye:
                tmpnode.setAttribute("type", "integer")
                tmpnode.setAttribute("range", hinttype)
            elif type == "enumeration" or type == "bits":
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
            elif type == "cats_object_name"  :
                tmpnode.setAttribute("type","object-name")  
                for opt in option_list:
                    option = self.doc.createElement("option")
                    option.setAttribute("name", opt.strip())
                    tmpnode.appendChild(option)                                               
            else: 
                tmpnode.setAttribute("type","format")
                tmpnode.setAttribute("format", hinttype)
        childxmlnode.appendChild(tmpnode)
        return childxmlnode

    def addAction(self, parent, name):
        addnode = self.doc.createElement("action")
        addnode.setAttribute("name", name)
        addnode.setAttribute("type", "cli")
        parent.appendChild(addnode)
        return addnode
        
    def addAttribute(self, parent, child):
        addnodes = parent.getElementsByTagName("action");
        if addnodes is None:
            addnode = self.addAction(parent, "add")
        else:
            found = False
            for node in addnodes:
                name = node.getAttribute("name")
                if name == "add":
                    found = True
                    addnode = node
                    break
            if not found:
                addnode = self.addAction(parent,"add")  
        addnode.appendChild(child)

    def createElementAttribute(self, node):
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
            
    def addElementAttribute(self, parent, child):
        childNode = self.createElementAttribute(child)
        addnodes = parent.getElementsByTagName("action");
        if addnodes is None:
            addnode = self.addAction(parent, "add")
        else:
            found = False
            for node in addnodes:
                name = node.getAttribute("name")
                if name == "add":
                    found = True
                    addnode = node
                    break
            if not found:
                addnode = self.addAction(parent,"add")  
        addnode.appendChild(childNode)

    def setAttribute(self, parent, child):
        addnodes = parent.getElementsByTagName("action");
        if addnodes is None:
            addnode = self.addAction(parent, "set")
        else:
            found = False
            for node in addnodes:
                name = node.getAttribute("name")
                if name == "set":
                    found = True
                    addnode = node
                    break
            if not found:
                addnode = self.addAction(parent,"set")  
        addnode.appendChild(child)

    def setElementAttribute(self, parent, child):
        childNode = self.createElementAttribute(child)
        addnodes = parent.getElementsByTagName("action");
        if addnodes is None:
            addnode = self.addAction(parent, "set")
        else:
            found = False
            for node in addnodes:
                name = node.getAttribute("name")
                if name == "set":
                    found = True
                    addnode = node
                    break
            if not found:
                addnode = self.addAction(parent,"set")  
        addnode.appendChild(childNode)

    def add_meta_info(self, parent, metaItems):
        info = self.doc.createElement("metaInfo");
        for key, value in metaItems.items():
            info.appendChild(self.createElementWithNameValue("metaItem", key, value))
        parent.appendChild(info)
        return info
        
    def add_platform_element(self, platform, attributes):
        elem = self.doc.createElement("object")
        for key, value in attributes.items():
            elem.setAttribute(key,value)
        platform.appendChild(elem)
        return elem
    
    def add_rpc_bean(self, platform):
        container = self.add_platform_element(platform, {
            "name": self.name_prefix+"_Container_RPC",
            "extends":"CommonXMLBean",
            "objectType":"xmlBean",
            "auto-create":"yes"
            })
        attr = self.createAttribute("__rpc_name", "cats_object_name\ncats_object_name", self.rpcObj)
        self.setAttribute(container, attr)
    
    def add_filter_get(self, platform):
        filter = self.add_platform_element(platform, {
            "name": self.name_prefix+"_filter_get",
            "extends":"CommonXMLBean",
            "objectType":"xmlBean",
            "auto-create":"yes",
            "__name":"filter"
            })
        self.add_meta_info(filter, {
            "__uri":"urn:ietf:params:xml:ns:netconf:base:1.0"
            })
        attr = self.createAttribute("type", "enumeration\n subtree,xpath")
        action = self.addAction(filter, "setXMLAttribute")
        action.appendChild(attr)
        attr = self.createAttribute("select", "string\n")
        self.setAttribute(filter, attr)
        attr = self.createAttribute("__subtree", "cats_object_name\ncats_object_name", self.topObj)
        self.addAttribute(filter, attr)

    def add_filter_notification(self, platform):
        filter = self.add_platform_element(platform, {
            "name": self.name_prefix+"_filter_notification",
            "extends":"CommonXMLBean",
            "objectType":"xmlBean",
            "auto-create":"yes",
            "__name":"filter"
            })
        self.add_meta_info(filter, {
            "__uri":"urn:ietf:params:xml:ns:netconf:base:1.0",
            "__declaredNS_prefix":"xc",
            "__declaredNS_URI":"urn:ietf:params:xml:ns:netconf:base:1.0"
            })
        attr = self.createAttribute("xc:type", "enumeration\n subtree,xpath")
        action = self.addAction(filter, "setXMLAttribute")
        action.appendChild(attr)
        attr = self.createAttribute("select", "string\n")
        self.setAttribute(filter, attr)
        attr = self.createAttribute("__subtree", "cats_object_name\ncats_object_name", self.notificationObj)
        self.addAttribute(filter, attr)
        
    def add_platform_attribute(self,platform):
        if self.config is not None and self.config.has_section("platform"):
            items = self.config.items('platform')
            for key, value in items: 
                platform.setAttribute(key,value)
            
    def add_platform_property(self,platform):
        if self.config is not None and self.config.has_section("properties"):
            items = self.config.items('properties')
            for key, value in items: 
                property = self.doc.createElement("property")
                property.setAttribute("name",key)
                property.setAttribute("value",value)
                platform.appendChild(property)
        
    def init_cats_model(self):
        platform = self.doc.createElement("platform")
        self.add_platform_attribute(platform)
        self.add_platform_property(platform)
        return platform
            
    def emit(self, ctx, modules, fd):
        self.init_cats_options(ctx)
        platform = self.init_cats_model()
        self.doc.appendChild(platform)
        self.emit_tree(platform, ctx, modules)
        self.add_filter_get(platform)
        self.add_filter_notification(platform)
        self.add_rpc_bean(platform)
        self.doc.writexml(fd, indent='  ', addindent='  ', newl='\n', encoding='utf-8')

        tmpfile = None
        if ctx.opts.cats_names_file == None:
            if sys.version < '3':
                self.namefd = codecs.getwriter('utf8')(sys.stdout)
            else:
                self.namefd = sys.stdout
        else:
            tmpfile = ctx.opts.cats_names_file + ".tmp"
            if sys.version < '3':
                self.namefd = codecs.open(tmpfile, "w+", encoding="utf-8")
            else:
                self.namefd = io.open(tmpfile, "w+", encoding="utf-8")
        try:
            for key, value in self.maps.items():
                self.namefd.write(key+"\n")            
        except:
            if tmpfile != None:
                self.namefd.close()
                os.remove(tmpfile)
            raise
        if tmpfile != None:
            self.namefd.close()
            if os.path.isfile(ctx.opts.cats_names_file):
                os.remove(ctx.opts.cats_names_file)
            os.rename(tmpfile, ctx.opts.cats_names_file)
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

        def revisename(nodename):
            if self.config.has_option("naming", "delimiter"):
                snames = nodename.split(self.config['naming']['delimiter'])
                if len(snames) > 1:
                    nodename=snames[0]+''.join([nn.capitalize() for nn in snames[1:]])

            if not self.naming_replace:
                return nodename
            
            if self.config.has_section('naming substitution'):
                items = self.config.items('naming substitution')
                for key, value in items: 
                    nodename = re.sub(key, value, nodename)

            if self.config.has_section("naming deletion"):
                deletions = self.config.options("naming deletion")
                for k in deletions:  
                    nodename = re.sub(k,'',nodename)
            
            if len(nodename) > 4:
                nodename = nodename[0:3] + nodename[3:4].lower() + nodename[4:]
            return nodename
                
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
                    found=False
                    if self.config.has_section('naming add module'):
                        items = self.config.items('naming add module')
                        for key, value in items: 
                            if value.find(":"+name+":")>=0:
                                prefix += stmt.i_orig_module.arg + "_"
                                found=True
                                break;
                    if not found:
                        if not self.naming_without_module:
                            if stmt.i_orig_module.arg == stmt.arg:
                                prefix += "___"
                            else:
                                prefix += (stmt.i_orig_module.arg+"__")
                elif stmt.i_module.arg != stmt.parent.i_module.arg:
                    found=False
                    if self.config.has_section('naming add module'):
                        items = self.config.items('naming add module')
                        for key, value in items: 
                            if value.find(":"+name+":")>=0:
                                prefix += stmt.i_module.arg + "_"
                                found=True
                                break;
                    if not found:
                        if not self.naming_without_module:
                            if stmt.i_module.arg.endswith(stmt.arg):
                                prefix += "__"
                            else:
                                prefix += (stmt.i_module.arg+"__")
                else:  
                    found=False
                    if self.config.has_section('naming add parent'):
                        items = self.config.items('naming add parent')
                        for key, value in items: 
                            if value.find(":"+name+":")>=0:
                                parentname=parent.getAttribute("name")
                                prefix = parentname + "_"
                                found=True
                                break;
                    if not found and not self.naming_without_parent:
                        parentname=parent.getAttribute("name")
                        prefix = parentname + "_"
            else: 
                nodename = name
                
            if prefix != '':
                nodename = prefix + name
            nodename = revisename(nodename)
            commonnodename=stmt.i_orig_module.arg + stmt.arg
            if self.maps.__contains__(nodename):
                childxmlnode = self.maps[nodename]
                omod = childxmlnode.getAttribute("orig_module")
                oname = childxmlnode.getAttribute("__name")
                print("omod:%s, cmod:%s, oname:%s, cname:%s" % \
                      (omod, stmt.i_orig_module.arg,oname,stmt.arg))
                assert omod == stmt.i_orig_module.arg and oname == stmt.arg
                return (childxmlnode, False)
#             try:
#                 childxmlnode = self.maps[nodename]
#                 return (childxmlnode, False)
#             except KeyError:
#                 pass
            childxmlnode = self.doc.createElement("object")
            childxmlnode.setAttribute("name", nodename)
            childxmlnode.setAttribute("nodeType", nodetype)
            childxmlnode.setAttribute("objectType","xmlBean")
            childxmlnode.setAttribute("auto-create","yes")
            childxmlnode.setAttribute("extends","CommonXMLBean")
            metainfonode=self.doc.createElement("metaInfo")
#            metainfonode.appendChild(createElementWithNameValue("metaItem","orig_module",stmt.i_orig_module.arg))
#            metainfonode.appendChild(createElementWithNameValue("metaItem","__name",name))
            childxmlnode.setAttribute("__name", name)
            childxmlnode.setAttribute("orig_module", stmt.i_orig_module.arg)
            childxmlnode.appendChild(metainfonode)
            self.maps[nodename] = childxmlnode
            if parent is None:
                if nodetype == "notification":
                    self.notificationObj.append(nodename)
                elif nodetype == "rpc":
                    self.rpcObj.append(nodename)
                else:
                    self.topObj.append(nodename)
            return (childxmlnode, True)
        
        def getAttributeValue(metaitems, namevalue):
            Items = [metaitem for metaitem in metaitems if metaitem.getAttribute("name") == namevalue]
            assert len(Items) == 0 or len(Items) == 1
            if len(Items) == 0:
                value = None
            else:
                value = Items[0].getAttribute("value")
            return value
           
        def getNamespace(metaitems):
            if metaitems is None:
                return (None, None)
            prefix = getAttributeValue(metaitems, "__prefix")
            uri = getAttributeValue(metaitems, "__uri")
            return prefix, uri
        
        def addMetaInfo(xmlnode, module, adddeclareNS=True, parentxmlnode=None):
            metainfos = xmlnode.getElementsByTagName("metaInfo")
            if metainfos is None or len(metainfos) == 0:
                metainfonode = self.doc.createElement("metaInfo")
                xmlnode.appendChild(metainfonode)
            else:
                metainfonode = metainfos[0]
            ns = module.search_one('namespace')
            if ns is not None:
                nsstr = ns.arg
            pr = module.search_one('prefix')
            if pr is not None:
                prstr = pr.arg
            metaitems = metainfonode.getElementsByTagName("metaItem")
            prefix, uri = getNamespace(metaitems)
            assert prefix == None and uri == None or prefix is not None and uri is not None
            if prefix is not None:
                assert prefix == prstr and uri == nsstr
            if prefix is None:
                metainfonode.appendChild(self.createElementWithNameValue("metaItem", "__prefix", prstr))
                metainfonode.appendChild(self.createElementWithNameValue("metaItem", "__uri", nsstr))
            if parentxmlnode is not None:
                whenItem = [metaitem for metaitem in metaitems if metaitem.getAttribute("name") == "__ns_when"]
                if whenItem is None or len(whenItem) == 0:
                    metainfonode.appendChild(self.createElementWithNameValue("metaItem", "__ns_when", 
                                                                        "parent in "+parentxmlnode.getAttribute("name")))
                else:
                    ov = whenItem.getAttribute("value")
                    whenItem.setAttribute("value",ov + ","+parentxmlnode.getAttribute("name"))
            if adddeclareNS:
                metainfonode.appendChild(self.createElementWithNameValue("metaItem", "__declaredNS_prefix", "xc"))
                metainfonode.appendChild(self.createElementWithNameValue("metaItem", "__declaredNS_URI", "urn:ietf:params:xml:ns:netconf:base:1.0"))


        
        def updateRelationship(parent,child):
            metaInfos = child.getElementsByTagName("metaInfo");
            if metaInfos is None or len(metaInfos) == 0:
                metaInfo = self.doc.createElement("metaInfo")
            else:
                metaInfo = metaInfos[0]
            metaInfo.appendChild(self.createElementWithNameValue("metaItem", "super", parent.getAttribute("name")))
            child.appendChild(metaInfo)  

        def createAction(parent,child,type):
            if type == 'list':
                self.addElementAttribute(parent, child)
            elif type == 'container':
                self.setElementAttribute(parent, child)
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
            childxmlnode = self.createAttribute(name, t)
            if s.keyword == 'leaf-list':
                self.addAttribute(parentnode,childxmlnode)
            else:
                self.setAttribute(parentnode, childxmlnode)
        
        if parentnode is not None and parentnode != childxmlnode and s.i_module.arg != s.parent.i_module.arg:
            addMetaInfo(childxmlnode, s.i_module, False, parentnode)
        if not newObject: return
                    
        if s.keyword == 'list':
            if s.search_one('key') is not None:
                keystr = re.sub('\s+', '::', s.search_one('key').arg)
                childxmlnode.setAttribute("keys",keystr)
        elif s.keyword == 'container':
            p = s.search_one('presence')
            if p is not None:
                childxmlnode.setAttribute("presence","yes")
             
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
            if t.arg == 'bits':
                found = True
                s = s + ' '
                for bit in t.substmts:
                    s += bit.arg + ','
                s = s + ' '
            elif t.arg == 'leafref':
                found = True
                if node.i_leafref_expanded:
                    targetnode = node.i_leafref.i_target_node
                    return typestring(targetnode)
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
                s = s + ' {range =' + typerange.arg + '}\n'
            length = t.search_one('length')
            if length is not None:
                found = True
                s = s + ' {length =' + length.arg + '}\n'

            pattern = t.search_one('pattern')
            if pattern is not None: # truncate long patterns
                found = True
                s = s + ' {pattern = ' + pattern.arg + '}\n'
                
            fractiondigits = t.search_one('fraction-digits')
            if fractiondigits is not None:
                found = True
                s = s + ' {fraction-digits = ' + fractiondigits.arg + '}\n'
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
            typedef = statements.search_typedef(pmodule, name)
            if typedef is None:
                typedef = statements.search_typedef(t, name)
        else:
            # this is a prefixed name, check the imported modules
            err = []
            pmodule = statements.prefix_to_module(t.i_module,prefix,t.pos,err)
            if pmodule is None:
                return
            typedef = statements.search_typedef(pmodule, name)
        if typedef != None:
#            s = s + get_nontypedefstring(typedef)
            s = s + typestring(typedef)
    return s

#!/usr/bin/env python
# vim: set encoding=utf-8 tabstop=4 softtabstop=4 shiftwidth=4 expandtab
#########################################################################
# Copyright 2012 KNX-User-Forum e.V.            http://knx-user-forum.de/
#########################################################################
#  This file is part of SmartHome.py.   http://smarthome.sourceforge.net/
#
#  SmartHome.py is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  SmartHome.py is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with SmartHome.py. If not, see <http://www.gnu.org/licenses/>.
#########################################################################

import logging

logger = logging.getLogger('')


def return_html(node):
    html = ''
    if 'visu' in node.conf:
        visu = node.conf['visu']
        dom = node.id().replace('.', '_')
        if visu in ['text', 'textarea', 'toggle', 'checkbox', 'radio', 'select', 'slider']:  # regular form elements
            html += '<div data-role="fieldcontain">\n'.format(dom)
            if visu == 'text':
                html += '    <label for="{0}">{1}</label>\n'.format(dom, node)
                html += '    <input id="{0}" data-sh="{1}" type="text" />\n'.format(dom, node.id())
            elif visu == 'textarea':
                html += '    <label for="{0}">{1}</label>\n'.format(dom, node)
                html += '    <textarea id="{0}" data-sh="{1}" type="checkbox"></textarea>\n'.format(dom, node.id())
            elif visu == 'toggle':
                html += '    <label for="{0}">{1}</label>\n'.format(dom, node)
                if 'visu_opt' in node.conf:
                    opt = node.conf['visu_opt']
                else:
                    opt = ['Off', 'On']
                html += '    <select id="{0}" data-sh="{1}" data-role="slider"><option value="off">{2}</option><option value="on">{3}</option></select>\n'.format(dom, node.id(), opt[0], opt[1])
            elif visu == 'checkbox':
                html += '    <label for="{0}">{1}</label>\n'.format(dom, node)
                html += '    <input id="{0}" data-sh="{1}" type="checkbox" />\n'.format(dom, node.id())
            elif visu == 'slider':
                html += '    <label for="{0}">{1}</label>\n'.format(dom, node)
                if 'visu_opt' in node.conf:
                    opt = node.conf['visu_opt']
                else:
                    opt = [0, 100, 5]
                html += '    <input id="{0}" data-sh="{1}" type="range" min="{2}" max="{3}" step="{4}" />\n'.format(dom, node.id(), opt[0], opt[1], opt[2])
            elif visu == 'select':
                html += '<fieldset data-role="controlgroup">\n'
                if 'visu_opt' in node.conf:
                    opt = node.conf['visu_opt']
                else:
                    opt = ['Please specify the "visu_opt" attribute']
                html += '    <legend>{0}</legend>\n'.format(node)
                html += '    <select id="{0}" data-sh="{1}">\n'.format(dom, node.id())
                for value in opt:
                    html += '        <option value="{0}">{0}</option>\n'.format(value)
                html += '    </select>\n'
                html += '</fieldset>\n'
            elif visu == 'radio':
                html += '<fieldset data-role="controlgroup">\n'
                i = 0
                if 'visu_opt' in node.conf:
                    opt = node.conf['visu_opt']
                else:
                    opt = ['Please specify the "visu_opt" attribute']
                html += '    <legend>{0}</legend>\n'.format(node)
                for value in opt:
                    i += 1
                    html += '    <label for="{0}{1}">{2}</label>\n'.format(dom, i, value)
                    html += '    <input id="{0}{1}" name="{0}" data-sh="{2}" value="{3}" type="radio" />\n'.format(dom, i, node.id(), value)
                html += '</fieldset>\n'
            html += '</div>\n'
        elif visu in ['div', 'span', 'img']:  # passive elements
            if visu == 'div':
                html += '<div>{0}: <span data-sh="{1}"></span></div>\n'.format(node, node.id())
            elif visu == 'span':
                html += '<span>{0}: <span data-sh="{1}"></span></span>\n'.format(node, node.id())
            elif visu == 'img':
                html += '<img data-sh="{0}" src="{1}" />\n'.format(node.id(), node())
        elif visu in ['switch', 'push']:  # active elements
            if visu == 'switch':
                html += '<img data-sh="{0}" src="/img/t.png" class="switch" />\n'.format(node.id())
            elif visu == 'push':
                html += '<img data-sh="{0}" src="/img/t.png" class="push" />\n'.format(node.id())
    return html


def return_tree(node):
    html = ''
    html += return_html(node)
    for child in node:
        html += return_tree(child)
    return html

#!/usr/bin/env python
# vim: set encoding=utf-8 tabstop=4 softtabstop=4 shiftwidth=4 expandtab
#########################################################################
# Copyright 2013 KNX-User-Forum e.V.            http://knx-user-forum.de/
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


def parse_tpl(template, replace):
    try:
        with open(template, 'r') as f:
            tpl = f.read()
    except IOError, e:
        logger.error("Could not read template file: {0}".format(template))
        return
    for s,r in replace:
        tpl = tpl.replace(s, r)
    return tpl


def room(smarthome, room, directory):
    widgets = ''
    for item in smarthome.find_children(room, 'visu_widget'):
        if 'visu_img' in item.conf:
            img = item.conf['visu_img']
        else:
            img = ''
        if isinstance(item.conf['visu_widget'], list):
            widget = ', '.join(item.conf['visu_widget'])
        else:
            widget = item.conf['visu_widget']
        widgets += parse_tpl(directory + '/base/tpl/widget.html', [('{{ visu_name }}', str(item)), ('{{ visu_img }}', img), ('{{ visu_widget }}', widget), ('__ID__', item.id()), ('__NAME__',str(item))])
    return parse_tpl(directory + '/base/tpl/room.html', [('{{ visu_name }}', str(room)), ('{{ visu_widgets }}', widgets)])


def pages(smarthome, directory):
    nav_lis = ''
    for item in smarthome.find_items('visu_page'):
        r = room(smarthome, item, directory)
        if 'visu_img' in item.conf:
            img = item.conf['visu_img']
        else:
            img = ''
        nav_lis += parse_tpl(directory + '/base/tpl/nav.html', [('{{ visu_page }}', item.id()), ('{{ visu_name }}', str(item)), ('{{ visu_img }}', img)])
        with open("{0}/smarthome/{1}.html".format(directory, item.id()), 'w') as f:
            f.write(r)
    nav = parse_tpl(directory + '/base/tpl/navigation.html', [('{{ visu_navis }}', nav_lis)])
    with open(directory + '/smarthome/navigation.html', 'w') as f:
        f.write(nav)

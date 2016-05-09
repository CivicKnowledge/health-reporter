# -*- coding: utf-8 -*-
#
# Copyright 2016 Civic Knowledge. All Rights Reserved
# This software may be modified and distributed under the terms of the BSD license.  
# See the LICENSE file for details.

from . import jsonify

def get_root():
    return jsonify('do some magic!')
    
def get_measure_root(id):
    return jsonify("got id {} ({}) ".format(id, type(id)))


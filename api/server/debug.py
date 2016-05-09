# -*- coding: utf-8 -*-
#
# Copyright 2016 Civic Knowledge. All Rights Reserved
# This software may be modified and distributed under the terms of the BSD license.  
# See the LICENSE file for details.

import connexion

if __name__ == '__main__':
    app = connexion.App(__name__, specification_dir='./')
    app.add_api('swagger.yaml', arguments={'title': 'Returns indicators from properly classified Ambry bundles. \n'})
    app.run(port=8082, debug = True)

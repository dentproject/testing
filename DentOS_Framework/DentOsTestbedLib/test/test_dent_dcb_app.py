# Copyright 2020 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
# generated using file ./gen/model/dent/network/dcb/dcb.yaml
#
# DONOT EDIT - generated by diligent bots

import asyncio
from .utils import TestDevice
from dent_os_testbed.lib.dcb.dcb_app import DcbApp


def test_that_dcb_app_show(capfd):

    dv1 = TestDevice(platform='dentos')
    dv2 = TestDevice(platform='dentos')
    loop = asyncio.get_event_loop()
    out = loop.run_until_complete(DcbApp.show(input_data = [{
        # device 1
        'test_dev' : [{}],
    }], device_obj={'test_dev':dv1}))
    print(out)
    assert 'command' in out[0]['test_dev'].keys()
    assert 'result' in out[0]['test_dev'].keys()
    # check the rc
    assert out[0]['test_dev']['rc'] == 0

    loop = asyncio.get_event_loop()
    out = loop.run_until_complete(DcbApp.show(input_data = [{
        # device 1
        'test_dev1' : [{
        # command 1
            'dev':'grjvikgf',
            'default-prio':'',
            'dscp-prio':'',
            'ethtype-prio':'',
            'port-prio':'',
            'stream-port-prio':'',
            'dgram-port-prio':'',

        },{
        # command 2
            'dev':'vaoohlzo',
            'default-prio':'',
            'dscp-prio':'',
            'ethtype-prio':'',
            'port-prio':'',
            'stream-port-prio':'',
            'dgram-port-prio':'',

        }],
    }], device_obj={'test_dev1':dv1, 'test_dev2':dv2}))
    print(out)
    # check if the command was formed
    assert 'command' in out[0]['test_dev1'].keys()
    # check if the result was formed
    assert 'result' in out[0]['test_dev1'].keys()
    # check the rc
    assert out[0]['test_dev1']['rc'] == 0

    loop = asyncio.get_event_loop()
    out = loop.run_until_complete(DcbApp.show(input_data = [{
        # device 1
        'test_dev1' : [{
            'dev':'grjvikgf',
            'default-prio':'',
            'dscp-prio':'',
            'ethtype-prio':'',
            'port-prio':'',
            'stream-port-prio':'',
            'dgram-port-prio':'',

         }],
        # device 2
        'test_dev2' : [{
            'dev':'vaoohlzo',
            'default-prio':'',
            'dscp-prio':'',
            'ethtype-prio':'',
            'port-prio':'',
            'stream-port-prio':'',
            'dgram-port-prio':'',

        }],
    }], device_obj={'test_dev1':dv1, 'test_dev2':dv2}))
    print(out)
    # check if the command was formed
    assert 'command' in out[0]['test_dev1'].keys()
    assert 'command' in out[1]['test_dev2'].keys()
    # check if the result was formed
    assert 'result' in out[0]['test_dev1'].keys()
    assert 'result' in out[1]['test_dev2'].keys()
    # check the rc
    assert out[0]['test_dev1']['rc'] == 0
    assert out[1]['test_dev2']['rc'] == 0


def test_that_dcb_app_flush(capfd):

    dv1 = TestDevice(platform='dentos')
    dv2 = TestDevice(platform='dentos')
    loop = asyncio.get_event_loop()
    out = loop.run_until_complete(DcbApp.flush(input_data = [{
        # device 1
        'test_dev' : [{}],
    }], device_obj={'test_dev':dv1}))
    print(out)
    assert 'command' in out[0]['test_dev'].keys()
    assert 'result' in out[0]['test_dev'].keys()
    # check the rc
    assert out[0]['test_dev']['rc'] == 0

    loop = asyncio.get_event_loop()
    out = loop.run_until_complete(DcbApp.flush(input_data = [{
        # device 1
        'test_dev1' : [{
        # command 1
            'dev':'slvrkgyg',
            'default-prio':'',
            'dscp-prio':'',
            'ethtype-prio':'',
            'port-prio':'',
            'stream-port-prio':'',
            'dgram-port-prio':'',

        },{
        # command 2
            'dev':'sxlqptce',
            'default-prio':'',
            'dscp-prio':'',
            'ethtype-prio':'',
            'port-prio':'',
            'stream-port-prio':'',
            'dgram-port-prio':'',

        }],
    }], device_obj={'test_dev1':dv1, 'test_dev2':dv2}))
    print(out)
    # check if the command was formed
    assert 'command' in out[0]['test_dev1'].keys()
    # check if the result was formed
    assert 'result' in out[0]['test_dev1'].keys()
    # check the rc
    assert out[0]['test_dev1']['rc'] == 0

    loop = asyncio.get_event_loop()
    out = loop.run_until_complete(DcbApp.flush(input_data = [{
        # device 1
        'test_dev1' : [{
            'dev':'slvrkgyg',
            'default-prio':'',
            'dscp-prio':'',
            'ethtype-prio':'',
            'port-prio':'',
            'stream-port-prio':'',
            'dgram-port-prio':'',

         }],
        # device 2
        'test_dev2' : [{
            'dev':'sxlqptce',
            'default-prio':'',
            'dscp-prio':'',
            'ethtype-prio':'',
            'port-prio':'',
            'stream-port-prio':'',
            'dgram-port-prio':'',

        }],
    }], device_obj={'test_dev1':dv1, 'test_dev2':dv2}))
    print(out)
    # check if the command was formed
    assert 'command' in out[0]['test_dev1'].keys()
    assert 'command' in out[1]['test_dev2'].keys()
    # check if the result was formed
    assert 'result' in out[0]['test_dev1'].keys()
    assert 'result' in out[1]['test_dev2'].keys()
    # check the rc
    assert out[0]['test_dev1']['rc'] == 0
    assert out[1]['test_dev2']['rc'] == 0


def test_that_dcb_app_add(capfd):

    dv1 = TestDevice(platform='dentos')
    dv2 = TestDevice(platform='dentos')
    loop = asyncio.get_event_loop()
    out = loop.run_until_complete(DcbApp.add(input_data = [{
        # device 1
        'test_dev' : [{}],
    }], device_obj={'test_dev':dv1}))
    print(out)
    assert 'command' in out[0]['test_dev'].keys()
    assert 'result' in out[0]['test_dev'].keys()
    # check the rc
    assert out[0]['test_dev']['rc'] == 0

    loop = asyncio.get_event_loop()
    out = loop.run_until_complete(DcbApp.add(input_data = [{
        # device 1
        'test_dev1' : [{
        # command 1
            'dev':'zsewizgk',
            'default-prio':'',
            'dscp-prio':'',
            'ethtype-prio':'',
            'port-prio':'',
            'stream-port-prio':'',
            'dgram-port-prio':'',

        },{
        # command 2
            'dev':'apzgccxw',
            'default-prio':'',
            'dscp-prio':'',
            'ethtype-prio':'',
            'port-prio':'',
            'stream-port-prio':'',
            'dgram-port-prio':'',

        }],
    }], device_obj={'test_dev1':dv1, 'test_dev2':dv2}))
    print(out)
    # check if the command was formed
    assert 'command' in out[0]['test_dev1'].keys()
    # check if the result was formed
    assert 'result' in out[0]['test_dev1'].keys()
    # check the rc
    assert out[0]['test_dev1']['rc'] == 0

    loop = asyncio.get_event_loop()
    out = loop.run_until_complete(DcbApp.add(input_data = [{
        # device 1
        'test_dev1' : [{
            'dev':'zsewizgk',
            'default-prio':'',
            'dscp-prio':'',
            'ethtype-prio':'',
            'port-prio':'',
            'stream-port-prio':'',
            'dgram-port-prio':'',

         }],
        # device 2
        'test_dev2' : [{
            'dev':'apzgccxw',
            'default-prio':'',
            'dscp-prio':'',
            'ethtype-prio':'',
            'port-prio':'',
            'stream-port-prio':'',
            'dgram-port-prio':'',

        }],
    }], device_obj={'test_dev1':dv1, 'test_dev2':dv2}))
    print(out)
    # check if the command was formed
    assert 'command' in out[0]['test_dev1'].keys()
    assert 'command' in out[1]['test_dev2'].keys()
    # check if the result was formed
    assert 'result' in out[0]['test_dev1'].keys()
    assert 'result' in out[1]['test_dev2'].keys()
    # check the rc
    assert out[0]['test_dev1']['rc'] == 0
    assert out[1]['test_dev2']['rc'] == 0


def test_that_dcb_app_delete(capfd):

    dv1 = TestDevice(platform='dentos')
    dv2 = TestDevice(platform='dentos')
    loop = asyncio.get_event_loop()
    out = loop.run_until_complete(DcbApp.delete(input_data = [{
        # device 1
        'test_dev' : [{}],
    }], device_obj={'test_dev':dv1}))
    print(out)
    assert 'command' in out[0]['test_dev'].keys()
    assert 'result' in out[0]['test_dev'].keys()
    # check the rc
    assert out[0]['test_dev']['rc'] == 0

    loop = asyncio.get_event_loop()
    out = loop.run_until_complete(DcbApp.delete(input_data = [{
        # device 1
        'test_dev1' : [{
        # command 1
            'dev':'qmhrjard',
            'default-prio':'',
            'dscp-prio':'',
            'ethtype-prio':'',
            'port-prio':'',
            'stream-port-prio':'',
            'dgram-port-prio':'',

        },{
        # command 2
            'dev':'pzcioafr',
            'default-prio':'',
            'dscp-prio':'',
            'ethtype-prio':'',
            'port-prio':'',
            'stream-port-prio':'',
            'dgram-port-prio':'',

        }],
    }], device_obj={'test_dev1':dv1, 'test_dev2':dv2}))
    print(out)
    # check if the command was formed
    assert 'command' in out[0]['test_dev1'].keys()
    # check if the result was formed
    assert 'result' in out[0]['test_dev1'].keys()
    # check the rc
    assert out[0]['test_dev1']['rc'] == 0

    loop = asyncio.get_event_loop()
    out = loop.run_until_complete(DcbApp.delete(input_data = [{
        # device 1
        'test_dev1' : [{
            'dev':'qmhrjard',
            'default-prio':'',
            'dscp-prio':'',
            'ethtype-prio':'',
            'port-prio':'',
            'stream-port-prio':'',
            'dgram-port-prio':'',

         }],
        # device 2
        'test_dev2' : [{
            'dev':'pzcioafr',
            'default-prio':'',
            'dscp-prio':'',
            'ethtype-prio':'',
            'port-prio':'',
            'stream-port-prio':'',
            'dgram-port-prio':'',

        }],
    }], device_obj={'test_dev1':dv1, 'test_dev2':dv2}))
    print(out)
    # check if the command was formed
    assert 'command' in out[0]['test_dev1'].keys()
    assert 'command' in out[1]['test_dev2'].keys()
    # check if the result was formed
    assert 'result' in out[0]['test_dev1'].keys()
    assert 'result' in out[1]['test_dev2'].keys()
    # check the rc
    assert out[0]['test_dev1']['rc'] == 0
    assert out[1]['test_dev2']['rc'] == 0


def test_that_dcb_app_replace(capfd):

    dv1 = TestDevice(platform='dentos')
    dv2 = TestDevice(platform='dentos')
    loop = asyncio.get_event_loop()
    out = loop.run_until_complete(DcbApp.replace(input_data = [{
        # device 1
        'test_dev' : [{}],
    }], device_obj={'test_dev':dv1}))
    print(out)
    assert 'command' in out[0]['test_dev'].keys()
    assert 'result' in out[0]['test_dev'].keys()
    # check the rc
    assert out[0]['test_dev']['rc'] == 0

    loop = asyncio.get_event_loop()
    out = loop.run_until_complete(DcbApp.replace(input_data = [{
        # device 1
        'test_dev1' : [{
        # command 1
            'dev':'jkdlzioq',
            'default-prio':'',
            'dscp-prio':'',
            'ethtype-prio':'',
            'port-prio':'',
            'stream-port-prio':'',
            'dgram-port-prio':'',

        },{
        # command 2
            'dev':'ckdmewks',
            'default-prio':'',
            'dscp-prio':'',
            'ethtype-prio':'',
            'port-prio':'',
            'stream-port-prio':'',
            'dgram-port-prio':'',

        }],
    }], device_obj={'test_dev1':dv1, 'test_dev2':dv2}))
    print(out)
    # check if the command was formed
    assert 'command' in out[0]['test_dev1'].keys()
    # check if the result was formed
    assert 'result' in out[0]['test_dev1'].keys()
    # check the rc
    assert out[0]['test_dev1']['rc'] == 0

    loop = asyncio.get_event_loop()
    out = loop.run_until_complete(DcbApp.replace(input_data = [{
        # device 1
        'test_dev1' : [{
            'dev':'jkdlzioq',
            'default-prio':'',
            'dscp-prio':'',
            'ethtype-prio':'',
            'port-prio':'',
            'stream-port-prio':'',
            'dgram-port-prio':'',

         }],
        # device 2
        'test_dev2' : [{
            'dev':'ckdmewks',
            'default-prio':'',
            'dscp-prio':'',
            'ethtype-prio':'',
            'port-prio':'',
            'stream-port-prio':'',
            'dgram-port-prio':'',

        }],
    }], device_obj={'test_dev1':dv1, 'test_dev2':dv2}))
    print(out)
    # check if the command was formed
    assert 'command' in out[0]['test_dev1'].keys()
    assert 'command' in out[1]['test_dev2'].keys()
    # check if the result was formed
    assert 'result' in out[0]['test_dev1'].keys()
    assert 'result' in out[1]['test_dev2'].keys()
    # check the rc
    assert out[0]['test_dev1']['rc'] == 0
    assert out[1]['test_dev2']['rc'] == 0

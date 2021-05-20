md_header = """
# %(cls_name)s Class
Description
```
%(cls_desc)s
```
"""

md_sample_call = """
out = await %(cname_cc)s.%(api)s(input_data = [
    {
        # device 1
        'test_dev1' : [
            {
%(params)s            },
       ],
     }
])
# check if the command was formed
assert 'command' in out[0]['test_dev1'].keys()
# check if the result was formed
assert 'result' in out[0]['test_dev1'].keys()
# check the rc
assert out[0]['test_dev1']["rc"] == 0
# print the output of the command
print (out[0]['test_dev1']["output"])
"""


md_apis="""
## %(api_name)s API
Description
```
%(api_desc)s
```

Sample Usage
```
%(api_usage)s
```

"""


md_mbr_hdr="""
## Properties
Name | Type | Description
------------ | ------------- |  -------------"""
md_mbr_entry="""%(cmbr_name)s|%(cmbr_type)s|%(cmbr_desc)s"""


md_mod_hdr="""
## Modules
Name | Classes | Description
---------------------- | -------------------------- |  ------------------------"""
md_mod_entry="""%(mod_name)s|%(classes)s|%(mod_desc)s"""

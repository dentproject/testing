# DentOsTestbedLib

## 1. Abstract

The purpose of this package is to describe the object model used to represent the networking and other essential features of NetProd Testbed. The purpose of representing the specification using object model is to represent the features abstractly so that the model can be used to automate and generate code that will implement, test, and provide different interfaces to the features

## 2. Data Model
The data model used to represent the features follow UML style schema where we have packages, classes, members, data types etc.

### 2.1 Package
A  package is the collection of features/modules of the full system. For example package of linux contains the description of features within linux NOS like networking, routing,  platform and OS components. The model is fully sufficient to represent and implement the features with support for implementing custom logic.

### 2.2 Module
A module is the collection of classes and datatypes that fully represents the subsystem/feature. The information represented in each module is sufficient to represent the part/full feature/features that are inter-related to each other. For example ip is a module and it contains various classes like route, address, link etc.
```code
- module: ip
  desc: IP module
  classes:
   - name: route
     ...
  types:
   - name: protocol_type
   ...
```
### 2.3 Class
A Class represents the independent entity of the subsystem comprising of properties and methods, Each property has name, datatype, description and semantics to impose restrictions. Methods provide the behavioral aspect of class where the business logic of the class would be represented.

```code
- module: ip
  desc: IP module
  classes:
   - name: ip_route
     apis: ['add', 'del', 'change', 'append', 'replace', 'get', 'show', 'flush', 'save', 'restore']
     members:
      - name: type
        type: ip:route_type
      - name: prefix
        type: ip_addr_t
        mandatory: [ "Yes" ]
```

### 2.4 Types

Types represent the custom and complex data types that are used within the module. Each type can be of type enumeration, structure, union or an reference to another data type. we can define more complex data types using these primitive data types (int, string, char, ip_addr_t, mac_t etc)

```code
- module: ip
  desc: IP module
  types:
  - name: route_type
     type: enum
     members:
      - name: unspec
        desc: 'Unspecified'
      - name: unicast
        desc: 'Gateway or direct route'
```

## 3. CodeGen Infrastructure
 - The codegen infrastructure works on the model defined in above section.
 - The model is represented using YAML notation and validated using pykwalify python utility.
 - The schema.yaml at the top level model directory (gen/model/schema.yaml) contains valid syntax that can be used in the YAML files.
 - The sub directories under gen/model/ represent package, all the files under that subdirectories represent the module as specified in the previous section.
 - The model is later converted to python objects using the classes under gen/lib/database.py(Package, Module, Class...).

### 3.1 Plugin based code generation
The Codegen infra works on dynamically loading the plugins that will work on the processed model. Each plugin is responsible for generating very specific implementation of the model. For example the test plugin is responsible to generate the test library python code using the model. Similarly various plugins can be written to generate very specific implementation of the model for example we can generate CLI code using the model or we can generate REST APIs using the model or we can generate discovery modules to get the switch state.

```code
class TestCodePlugin(SamplePlugin):
    def __init__(self, name):
        self.name = name
    def generate_code(self, dbs, odir):
        print("Generating Test Code")
        #code generation logic here
```
The codegen infra scans for all the plugin.py files under gen/plugins/ directory and loads the classes that have inherited from SamplePlugin base class and calls the generate_code function to generate the code with the digested DB.

### 3.2 Test Plugin
The Test plugin generates python API library to interact with the device/devices. The library provides abstraction to the user by providing a uniform interface to the Test Lib features (*platform independent*) (model under gen/model/netprod) and internally dealing with the platform specific (*platform dependent*) (model under gen/model/linux) details of interacting with the device to perform command operations/ parse the output from the commands.
#### 3.2.1 PI Test Class generation
#### 3.2.2 PD Test Class generation
#### 3.2.3 PD Impl Test Class generation
#### 3.2.4 PI Unit Test generation

### 3.3 Discovery Plugin
#### 3.3.1 Discovery Schema Class generation
#### 3.3.2 Discovery Class generation

### 3.4 TestSuite Plugin
#### 3.4.1 Test case generation

## Documentation

refer doc/

## regenerating the library and test code

$ python setup.py release

## Installation

```
pip3 install -r Requirements.txt
pip3 install .
```

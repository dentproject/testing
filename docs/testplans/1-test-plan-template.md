# Test Plan - *[Feature Name]*

|Authors| *[write authors here]* |
|--|--|
|Last update  | *[date]* |
|version  | *[version 1.0]* |


**Reviewers**:
 - *[reviewer 1]*
 - *[reviewer 2]*

## TABLE OF CONTENTS

 1. **[Feature Overview](#feature-overview)**   
 2. **[Reference Documents](#reference-documents)**
 3. **[Risks and Assumptions](#risks-and-assumptions)**
 4. **[Test Strategy](#test-strategy)**
 	 a. Test Approach
	 b. Covered Items
	 c. Items Not Covered
 5. **[Test Areas](#test-areas)**
	 a. Functional Testing
	 b. Negative Testing
	 c. Compatibility & Interoperability Testing
	 d. Documentation
	 e. Performance Testing
	 f. Scalability
	 g. Stress
	 h. Integration Testing
	 i. Automation & Regression Strategy

 6. **[Test Resources](#test-resources)**
	 a. Platforms/Dependencies
	 b. Hardware
	 c. Software
	 d. Tools 
 7. **[Schedules](#schedules)**
 8. **[Test Cases](#test-cases)**




## Feature Overview
<a name="feature-overview"/>

*[write here few words about the feature]*

## Reference Documents
<a name="feature-overview"/>

*[Provide links/URLs for the documents which QA will be referring here for more information and background]
[Functional Specification for the feature]*

## Risks and Assumptions
<a name="feature-overview"/>

*[This section lists risks and assumptions for the testing plan.]*

### Risks

*Risk analysis. Making clear other risk factors you will evaluate as you create and prioritize test cases. Include mitigation strategies and contingencies for each applicable risk.  Address each section below:
 - Technical risk: Is the feature being implemented complex? Timing dependent? [ elaborate more detailed examples] 
 - Platform independence: To what degree is a feature’s behavior decoupled from the platform it resides on? How do you know? 
 - Testing Risk:  Lack of critical equipment, reference standard, etc.? 
 - History: Based on root cause analysis or defect density history is the module being enhanced error prone?*

### Assumptions

*[any assumptions that may have been made]*

## Test Strategy
<a name="feature-overview"/>

### Test Approach
*Describe the approach to be used for each level of testing that will be performed on the feature.  Enough information should be included to support required project planning prior to Execute Commit.  If a section is not applicable, say "N/A" or "Not applicable" and state briefly why the testing is not being planned.  
List feature specific entry criteria. 
a.	Testing Prioritization: How should testing order be prioritized to mitigate risks for the feature/project detail even with breakdown to TC per type of tests.
b.	Coverage rules: Explain the selection  criteria for covered items.*


### Covered Items
*Test Coverage. How will you know that your test plan provides the right amount of coverage to ensure a successful deployment to end customers? Here is a list of suggested methods,. 
Test Case coverage: Estimate the number of test cases to be created to cover each part of the feature, establish criteria at each test phase for number of test cases that must be run including the percentage of passed cases needed to proceed to next phase.
	Test coverage metric may be used to evaluate the progress of testing, or establish confidence in the quality of the product. Quality criteria may be established for the project, based upon the metric.*

### Items Not Covered

*[Identify all critical items that will NOT be tested and say why the testing will not be done.]*

## Test Areas
<a name="feature-overview"/>

**a. Functional Testing**
	 *Feature/Function is about validation of individual feature behavior as defined in one or more requirements documents. Feature level testing is deterministic and analogous to state-machine validation. Describe the approach feature/function testing. What documents will you use to determine feature requirements ? If you find ambiguity in specifications, how will you resolve and document their resolution? < It is good to adopt of practice of test planning once the FS is out.> How will you quantify coverage of feature specifications? If you are implementing an industry standard protocol, will you run conformance tests using an industry standard reference engine (conformance test harness – HW and SW DUTs)?
Make sure to include every functional area discussed in the Functional Spec. In addition, all user scenarios discussed in the functional spec Release Requirement Document should be covered here as well.
GUI/CLI test cases will be covered here.*
	 
**b. Negative Testing**
*Negative tests evaluate the error handling capabilities and fault tolerance of features. Fault behavior should be specified in feature definition documents. What documents will you use to establish your negative tests? How will you measure your negative test coverage?*

**c. Compatibility & Interoperability Testing**
*To ensure that the functionality works with the previous released HW or across different vendors or platforms. provide a compatibility matrix where applicable*

**d. Documentation**
*List what kind of documentation will be verified, created, tested as part of this feature validation.* 

**e. Performance Testing**
*Performance testing at the feature level derives from feature specifications. Feature level performance testing considers the feature’s real-time behavior as decoupled from overall system dynamics as possible. Examples might be packets-per-second, call-setup time, response time. Are there feature level performance requirements for your project? In what documents are they specified? Are the requirements clear with respect to pass/fail thresholds? How will you conduct these measurements? How will you report results?
To ensure that the functionality meets the performance and scalability requirement as stated by Functional spec or the RRD (Release Requirement Document). In addition, These test cases should be performed early enough to identify if there has been performance requirements are satisfactory.
State the performance requirement (or desired) as identified for the specific platforms. Otherwise, state the platforms on which the maximum performance needs to be obtained.

**f. Scalability**
*Describe your approach to scalability testing? What scalability requirements exist for your product (e.g.  numbers of ports, users, managed entities, etc)? What customer realistic loads will you impose as you evaluate scalability? Will this testing yield design guidelines? Who is responsible for Scalability testing?*

**g. Stress**
*Describe the approach for stress testing.  What test setups will be used for stress testing?  What customer scenarios will be used to guide selection of configurations for stress testing?  How will the system be stressed?  How will typical or peak levels of network traffic be simulated?  What features or components will be pushed to the breaking point?  How will the level of stress on the system be measured?  How does this testing relate to customer requirements?  What will be the duration of stress testing? What is the expected operational envelope for your product? What are the expected failure behaviors (graceful fail or crash?).  What entry criteria apply?  Who is responsible for stress testing?*

**h. Integration Testing**
*To ensure that the functionality works with other features in the product. These test cases should be performed early enough to identify if there has been a collateral damage to legacy functionality.*

**i. Automation & Regression Strategy**
*List here your automation strategy*

## Test Resources
<a name="feature-overview"/>

 **a. Platforms/Dependencies**
*Software or hardware dependencies.*

 **b. Hardware**
*List all of your hardware requirements including any expenditures that are needed.  Include resources that you may utilize in addition to the “normal” testbed. THIS MUST BE IDENTIFIED AS EARLY AS POSSIBLE.*

 **c. Software**
*List all of your software requirements and dependencies. This would include base operating systems, levels, and service through additional software, which may include things that need to be added to existing testbed.*

 **d. Tools** 
*List all tools/automation that you will be using/needing, which may include new tools/automation that need to be purchased, written, or upgraded (this many overlap back too the hardware and software requirements).  Suggest breaking this section down to these subsections:*
*1.	Reuse/upgrading of existing automation*
*2.	New automation*
*3.	Retooling*
*4.	Requests to development for integrated APIs to improve testability*


## Schedules
<a name="schedules"/>

*List the test schedules.  List the effort involved in each Milestone listed here.* 




## Test Cases
<a name="test-cases"/>

*List each test case* 

### Test Case #3 - PFC PAUSE with lossy priorities

#### Test Objective

Verify Device Under Test (DUT) processes the PFC PAUSE frame with lossy priorities properly.

#### Test Configuration

- On SONiC Device Under Test (DUT) configure a single lossless priority value Pi (0 \<= i \<=
7).
- Configure following traffic items on the Keysight device:
  1. Test data traffic: A traffic item from the Keysight Tx port to
        the Keysight Rx port with the lossy priorities (DSCP value !=
        Pi). Traffic should be configured with 50% line rate.
  2. Background data traffic: A traffic item from the Keysight Tx
        port to the Keysight Rx port with the lossless priority (DSCP
        value == Pi). Traffic should be configured with 50% line rate.
  3. PFC PAUSE storm: Persistent PFC pause frames from the Keysight
        Rx port to the connected DUT port. The priorities of PFC pause
        frames should be same as that of 'Test data traffic'. And the
        inter-frame transmission interval should be smaller than
        per-frame pause duration.

#### Test Steps

1. Start PFC PAUSE storm.
2. After a fixed duration (eg. 1 sec), start the Test data traffic and Background data traffic simultaneously.
3. Keep the Test and Background traffic running for a fixed duration and then stop both the traffic items.
4. Verify the following:
   * Keysight Rx port should receive all the 'Background data traffic' as well as 'Test data traffic'. There should not be any loss observed.
5. Stop the PFC PAUSE storm.
6. Repeat the test with a different lossless priority value (!=Pi).





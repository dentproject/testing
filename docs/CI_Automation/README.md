# Dent CI Automation

- Purpose: Automate Dent CI/CT process in stages
- First released in: 10/2023
- Framework designed and developed by: Hubert.Gee@Keysight

## Table Of Contents

- What this framework does
- Key features
- Installation & requirements
- Test Suite file
- CLI parameters
- How to run test
- ciUtils:  A utility to view test status, results and more
- Results location
- Disable the CI framework for maintenance
- CI framework and test procedures and workflow
- CI stage logs
- Known issues

## What this framework does

- Stage 1: Clone test repo
- Stage 1: Download new builds
- Stage 2: Install Dent OS
- Stage 2: Deploy IxNetwork
- Stage 2: Deploy Dent test containers
- Stage 3: Run Test

- This framework will perform all of the above in stages
- Stage 1 and 2 are done in parallel.  Stage 2 will perform after Stage 1
- The CI test will abort if stage 1 or stage 2 fails
- Test will not run obviously

```text
Note

Deploy IxNetwork is disabled by default because IxNetwork must always be enabled
IxNetwork shuts down and reinstalled when Keysight release a new version and user
must include the CLI paramter -deployIxNetwork
```

## Key features

- Download builds
  - Automatically download the latest builds (ARM and AMD)
  - You could also specify which builds to download
  - Each test will download to its own testId folder
  - This allows users to download/install any build for testing
  - The testId build folder will be removed at the end of the test

- Pull testing repo from Github:
  - Automatically pull Github test repo from main branch
  - You could also specify which branch to pull from
  - Will pull the testing repo and put them in its own testId folder for testing
  - This allows each test to test different testing repositories and different
    branches within a repo
  - Automatically remove testing folder when the test is done

- Docker test containers
  - The framework creates a unique docker image for each test
  - The docker images is created off the "dent/test-framework-base   latest" image
  - The unique docker images begins with CI-: CI-\<repo\>-\<branch\>-\<unique Identifier\>

  ```text
  Example

  REPOSITORY                 TAG
  dent/test-framework        CI-dentproject-testing-main-525761
  dent/test-framework-base   latest
  ```

  - The testing docker image will be removed after the test

    - Locking/Unlocking testbeds
      - Automatically lock testbeds so other incoming tests using the same
        testbeds will not collide
      - New test that wants to use the same testbeds will go to the Waiting folder
      - Testbed usage is first-come first-server
      - Self recovery
        - Locked testbeds are verified if they're actively in used.  The PID is checked.
        - If not in used, the CI framework will unlock the testbeds so other
          test could use it

    - Deploying new IxNetwork version
      - Move the current IxNetworkVMs folder to IxNetworkVMs_backup
      - New download and installation will recreate IxNetworkVMs folder
      - If the download/installation failed, restore the IxNetworkVMs folder with
        the IxNetworkVMs_backup
      - If the download/installation passed, remove the IxNetworkVMs_backup folder

    - Test results:
      - Automatically remove old test results after the 10 days to save storage space
      - The days to remain test results is set in the file
        /home/dent/DentCiMgmt/settings.sh

    - Test suite files:
      - Group suite_group testcases into runInSeries and runInParallel for speed

    - Jenkins CI
      - The test result path is appended to
        /home/dent/DentCiMgmt/CiResultPaths/ciResultPaths.json
      - The CI framework will automatically remove older than 10+ days results

## Installation & requirements

- The installation has a dedicate page
- Please view the installation file
- Please finish reading the rest of this file first!

## Test Suite file

- Test suite yaml files are custom selections of Dent suite_group testcases to run.

- You group suite_group testcases in "runInSeries" and in "runInParallel"
  NOTE: If grouping testcases in runInParallel, each testcase must use a
        different testbed.

- Look at examples in /home/dent/testing/CI_Automation/TestSuites

- Create your own test suite files in this directory

- Current test suites
  - fullRegression: All of SIT testings and functional testings
                    (Takes 2 days to complete)
  - sitTest:        Only testing SIT test cases
  - functional:     Only testing functional test cases
  - l3tests:        A quick test with traffic (10 minutes)
  - cleanConfig:    A quick test for CI framework development
                    (few minutes)

- Below shows a preview of a test suite example

```text
  NOTE
     Every "name" MUST BE UNIQUE! Otherwise, only the last test with
     the same name will be executed

  suiteGroups:
     runInParallel:
          - name: clean_config_infra1
            config: ./DentOsTestbed/configuration/testbed_config/hw/sit/basic_infra1/testbed.json
            suiteGroups:
                - suite_group_clean_config

          - name: clean_config_infra2
            config: ./DentOsTestbed/configuration/testbed_config/hw/sit/basic_infra2/testbed.json
            suiteGroups:
                - suite_group_clean_config

     runInSeries:
          - name: clean_config_agg1
            config: ./DentOsTestbed/configuration/testbed_config/hw/sit/basic_agg1/testbed.json
            suiteGroups:
                - suite_group_clean_config

          - name: clean_config_agg2
            config: ./DentOsTestbed/configuration/testbed_config/hw/sit/basic_agg2/testbed.json
            suiteGroups:
                - suite_group_clean_config
```

## CLI Parameters

Supporting parameters

```text
  -testName:         Optional: A test name to identify your test
                     Especially for Jenkins CI testing!
                     Begin the testName with jenkinsCI_<unique label>

  -testSuites:       Mandatory: The test suite(s) containing which test
                     cases to run

  -builds:           Optional: State both ARM and AMD full path URLs
                     for the builds to download
                     Default: Downloads the latest builds

  -repo:             Optional: The repo to clone for testing
                     Default: Cloning from dent's main branch

  -branchName:       Optional: The repo branch to use for testing

  -localBranch:      Optional: Test with a local branch that is already
                     cloned. Provide the full path.

  -localBuilds:      Optional: The full paths to the AMD and ARM builds in the local dent server

  -keepTestBranch:   Optional: Do not delete the test branch after the
                     test for debugging purpose.

  -deployIxNetwork:  Optional: Install Keysight new IxNetwork VM release.
                     NOTE: The CI framework will be disabled for other
                           test to run. It will wait for all current tests
                           to finish before doing so.
```

## How To Run Test

CLI command on how to run test

```text
NOTE

You could enter runDentCi anywhere in the filesystem or enter
"python3 /home/dent/testing/CI_Automation/runDentCi.py"
```

```text
Most simplest:  This will automatically download the latest builds and
pull Dent testing repo from the main branch
runDentCi   -testSuite   <test_suite_name>    -testName    myTestName

Download the latest build and pull from a specific repo
runDentCi   -testSuite   <test_suite_name>
   -repo     [https://github.com/dentproject/testing.git]  -testName   myTestName

Pull a specific branch from the repo and download specific build release (URLs)
runeDentCi   -testSuite    fullRegression.yml
  -repo   [https://github.com/dentproject/testing.git]
  -branchName   repoBranchName   -keepTestBranch    -builds    <url_amd>     <url_arm>

Test a local branch on the Linux server that is already pulled from github
runDentCi   -testSuite    <test_suite_name>   -testName   myTestName
   -localBranch     /home/dent/testing

To install IxNetwork Server (This is rarely done.  Once or twice a year
when Keysight releases a new version)
runDentCi   -testSuite   <test_suite_name>   -deployIxNetwork
```

## ciUtils

Use this utility to do the followings

```text
NOTE

You could enter ciUtils anywhere in the filesystem or enter
"python3 /home/dent/testing/CI_Automation/ciUtils.py"

    -showtests                       Show all past and current tests to get the testId
                                     for viewing
    -showstatus <testId>             Show a testId status
    -showtestresults <testId>        Show a testId results
    -showtestbeds                    Show all testbed names. Retrieved from:
                                      /testing/DentOS_Framework/DentOsTestbed/configuration/testbed_config
    -showlockedtestbeds              Show all locked testbeds and test IDs waiting
                                     for testbeds
    -unlocktestbeds <testbed name>   Forcefully unlock one or more testbeds for usage
    -unlockalltestbeds               Forcefully unlock all testbeds for usage
    -remove <testId or use regex>    Remove testId names or use regex such as:
                                     -remove  .*myDev
                                     remove everything with myDev
                                     Regex removes all testIds that matches the pattern
    -kill <testId>                   Terminate a running test by killing
                                     the process ID
    -disableci                       This will stop executing incoming test
                                     Incoming test will wait until the CI framework
                                     is enabled
    -enableci                        This will enable the CI framework for testing
    -iscienabled                     Check if the CI framework is enabled
```

## Results location

- Results are stored in /home/dent/testing/CI_Automation/TestResults
- Automatically remove results after 10 days to clean up storage
- View on web browser: [http://10.36.118.11/TestResults]
- ciUtils  -showtestresults \<testId\>
- For public access viewing, results are store in Jenkins cloud
  service under each Jenkins test ID

  For Jenkins CI testing, read this json file to get the test result path

  - /home/dent/DentCiMgmt/CiResultPaths/ciResultPaths.json
  - Automatically removes 10 days and older results

```text
{
"results": [
    {
        "testName": "jenkinsCI_myDevTest1",
        "timestamp": "10-06-2023-16-53-17-633554",
        "resultPath": "/home/dent/DentCiMgmt/TestResults/10-06-2023-16-53-17-633554_jenkinsCI_myDevTest1"
    },
    {
        "testName": "jenkinsCI_myDevTest2",
        "timestamp": "10-06-2023-16-55-43-573603",
        "resultPath": "/home/dent/DentCiMgmt/TestResults/10-06-2023-16-55-43-573603_jenkinsCI_myDevTest2"
    },
    {
        "testName": "jenkinsCI_myDevTest3",
        "timestamp": "10-06-2023-17-02-52-525761",
        "resultPath": "/home/dent/DentCiMgmt/TestResults/10-06-2023-17-02-52-525761_jenkinsCI_myDevTest3"
    }
  ]
}
```

## Disable the CI framework for maintenance

- To disable or enable this CI framework, use ciUtils:
      ciUtils  -disableci | -enableci

- To verify if the CI framework is enabled, enter: ciUtils -iscienabled

```text
Note

If disabled, all incoming tests will wait until the CI framework is enabled
```

## CI framework process flow

- Incoming test -\>
  - Perform some system clean ups:
    - Remove all 10+ days  old test results
    - Remove stale test branches
    - Remove past build downloads after 1 day old

  - Verify new test repo and branch name for existing docker image with
    the same tag name.
    If docker image tag exists, wait until the current test finishes and\
    remove the docker image

  - Get all required testbeds for the test by reading the test suite file -\>
    Check if testbeds are locked in folder: /home/dent/DentCiMgmt/TestbedMgmt
    If any testbed is locked, go to the Waiting folder and wait until they're
    all available.
  - If testbeds are available, check who is next in the Waiting Folder
  - Lock the testbeds and run test

  ```text
  NOTE

  Testbed usage is based on first come first served
  ```

  - The CI framework has self-recovery to verify
    - If locked testbeds are in use by checking its testId process ID.
      If the test's process ID isn't running, then it get unlocked/removed

    - If the testbed is freed and you are not next in line to use it, the CI
      framework will check who is next to use it.

    - If who-is-next test's process ID isn't running, the it gets removed.

  - Each test has its own timestamp as testId in format: m/d/yr hr:min:sec:ms

    - All build downloads are stored in its own testId folder: /DentBuildReleases/\<testId\>
      This allows users to install any build version on Dent switches

  - Each test does a git pull for testing branch into its own \<testId\> folder
    /home/dent/DentCiMgmt/TestBranches
    They get removed after the test is done or aborted.
    This allows user to test any testing branch from github Dent repository.

  - If the test is aborted or ran to completion
    - Testbeds are unlocked
    - Remove the test branch
    - Remove the downloaded builds
    - Remove the testId docker image
    - Exit code 0 for failed and no error
    - Exit code 1 for failed and error

## CI Stage Logs

```text
Note

This Logs folder contains both Dent project test logs and CI framework logs
The below only shows the CI framework logs
```

- CI framework stage logs are in /home/dent/DentCiMgmt/TestResults/\<testId\>
- ciOverallSummary.json: This shows the test ID's metadatas
- ciTestReport:          This shows the overall test results
- CI_Logs folder
  - ciSessionLogs
  - deployTestContainersLogs

    Each Dent switch OS upgrade has its own log file
    - Dent_infra1_updateLogs
    - Dent_infra2_updateLogs
    - Dent_agg1_updateLogs
    - Dent_agg2_updateLogs
    - Dent_dist1_updateLogs

## Known issues

Git clone fatal error

```text
  [Problem]: Running "git clone" command by multiple tests at the same time
             encounter fatal error.

          The test will abort and unlock the testbed while the multithread's build
          download thread is still running.

          Error example<br>
              fatal: could not open '/09-26-2023-17-52-29-832785_myDev/.git/objects/pack/tmp_pack_cnaNCX'
              for reading: No such file or directory
              fatal: fetch-pack: invalid index-pack output
              [Info]: UnlockTestbed: sit-testbed_09-26-2023-17-52-29-832785_myDev

  [Reason]: Git is not thread safe.  You cannot run git in parallel.

  [Solution]: The CI framework keep checking the "git clone" process name
              until it doesn't exists.
              Then the next test could do a git clone safely.  Hopefully!

  [Note]: This is still not guaranteed to work
```

Installing DentOS

```text
  [Problem]: Sometimes one or more Dent switches times out waiting to get the
             Linux OS prompt

  [Solution]: Might have to detach DeployDent from multithreading.
              Or set a longer timeout value.

  [Note]: Must rerun the test
```

Setup issues

```text
  [Problem]: Sometimes the traffic generator crashed or a Dent switch is
             unreachable during the test.
             At the end of the test, the results will indicate as failed.
             This a false.

  [Solution]: You have to look at the failed logs to get an understanding
              of the failure.
              Future enhancements will include checkpoints before starting the test.

  [Note]: The Keysight Novus traffic generator is currently a Windows chassis.
          There is no API support to verify card UP, reboot the card and reboot services.
          Switching to a Linux based chassis that supports verifying the above
          has been requested.
```

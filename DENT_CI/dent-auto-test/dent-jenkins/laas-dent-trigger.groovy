properties([
  parameters([
    extendedChoice(
      name: 'device',
      description: '',
      type: 'PT_SINGLE_SELECT',
      visibleItemCount: 5,
      multiSelectDelimiter: ',',
      value: 'as4224,as5114',
      defaultValue: 'as4224'
    ),
    [$class: 'CascadeChoiceParameter',
      name: 'image_version',
      description: '',
      choiceType: 'PT_SINGLE_SELECT',
      filterLength: 0,
      filterable: false,
      referencedParameters: '',
      script: [
        $class: 'GroovyScript',
        fallbackScript: [
          classpath: [],
          sandbox: false,
          script:
            'return[\'Could not get image_version Param\']'
        ],
        script: [
          classpath: [],
          sandbox: false,
          script:
          '''def imageList = []
              def substring = ""
              def command = """curl -s https://nexus.dent.dev/content/repositories/snapshots/org/dent/dentos/ --list-only | grep href | cut -d \\\\\" -f 2"""
              def proc = ['bash', '-c', command].execute()
              proc.waitFor()

              proc.in.eachLine {
                if (it =~ /.+(DENTOS-HEAD_ONL-.+)_INSTALLED_INSTALLER$/) {
                  substring = (it =~ /.+(DENTOS-HEAD_ONL-.+)_INSTALLED_INSTALLER$/)[0][1]
                  imageList << substring
                }
              }

              return imageList.reverse()
          '''
        ]
      ]
    ],
    extendedChoice(
        name: 'select_all_suite_group',
        description: 'Select all the DENT test suite group.',
        type: 'PT_SINGLE_SELECT',
        visibleItemCount: 2,
        multiSelectDelimiter: ',',
        value: 'yes,no',
        defaultValue: 'yes'
    ),
    [$class: 'CascadeChoiceParameter',
      name: 'test_suite_group',
      description: 'The DENT test suite group.',
      choiceType: 'PT_CHECKBOX',
      filterLength: 1,
      filterable: true,
      referencedParameters: 'select_all_suite_group',
      script: [
        $class: 'GroovyScript',
        fallbackScript: [
          classpath: [],
          sandbox: false,
          script:
            'return[\'Could not get test_suite_group.\']'
        ],
        script: [
          classpath: [],
          sandbox: false,
          script:
            '''def list = []
                String fileContents = new File('/home/dent_volume/testing/Amazon_Framework/DentOsTestbed/src/dent_os_testbed/constants.py').text

                fileContents.eachLine { line ->
                  if (line =~ /^.+(suite_group_.+)":.*$/) {
                    suite_group = (line =~ /^.+(suite_group_.+)":.*$/)[0][1]
                    if (select_all_suite_group == 'yes') {
                      list << suite_group.concat(":selected")
                    } else {
                      list << suite_group
                    }
                  }
                }

                return list
            '''
        ]
      ]
    ],
  ])
])

pipeline {
  agent {
    label 'master'
  }
  environment {
    downstream_job = "job/laas-dent-main"   // !!!  the path shall includes "job/" !!!"
    lass_reservation_time = 0     // The time that is used to make a reservation for LaSS
    account = credentials('laas-dent-test')
    dent = credentials('jenkins-dent-trigger')
    device_prefix = ""
  }
  options { timestamps () }
  stages {
    stage("Calculate the laas reservation time") {
      steps {
        script {
          download_image_time = 5*60
          upgrade_dut_time = 5*60
          testsuite_running_time = params.test_suite_group.tokenize(',').size()*60
          
          lass_reservation_time = download_image_time + upgrade_dut_time + testsuite_running_time

          println "lass_reservation_time = ${lass_reservation_time}"

          // Since the laas requires to input the full device name and the device name looks like this:
          // /tainan/as4xxx/as4224-1,
          // get the middle value from params.device
          if (params.device =~ /^(as\d).+$/) {
            device_prefix = (device =~ /^(as\d).+$/)[0][1]
            device_prefix += 'xxx'
            println "device_prefix = ${device_prefix}"
          } else {
            throw new Exception("Cannot find the correct prefix from the input device ${params.device}")
          }

        }
      }
    } // end of stage("Calculate the laas reservation time")
    stage ("Send resource request to LaaS server") {
      steps {
        script {
          domain_name = "52.25.246.140:8080"
          if (HUDSON_URL =~ /^http[s]*:\/\/(.+)\/$/) {
            domain_name = (HUDSON_URL =~ /^http[s]*:\/\/(.+)\/$/)[0][1]
            println "domain_name = ${domain_name}"
          }
          dir("script") {
            checkout([$class: 'GitSCM', branches: [[name: '*/dent-aws']], doGenerateSubmoduleConfigurations: false, extensions: [[$class: 'SparseCheckoutPaths', sparseCheckoutPaths: [[path: 'dent-script/']]]], submoduleCfg: [], userRemoteConfigs: [[credentialsId: 'jenkins_gitlab', url: 'git@gitlab.edge-core.com:root/dent-auto-test.git']]])
            DUT = "/tainan/${device_prefix}/"
            url = 'http://$dent_USR:$dent_PSW@' + "${domain_name}/" + "${downstream_job}/buildWithParameters?image_version=${params.image_version}&select_all_suite_group=${params.select_all_suite_group}&test_suite_group=${params.test_suite_group}&reservation_id={ID}&reservation_duration={DURATION}&test=\\\\{{ID}}\\\\\\{{DURATION}}{\\\\\\{ID}}"
            ID = sh (script: """python3 ./dent-script/laas_interface_for_jenkins.py request type -u ${account_USR} Dent ${DUT}:1 ${lass_reservation_time} -T "${url}" << EOF
${account_PSW}
EOF""", returnStdout: true).trim()
              println "*****************************************************************************************************"
              println "* LaaS server return value (a series number. non-zero means the reservation is success): " + ID + "       *"
            if (ID != "0") {
              println "* Reservation is success.                                                                           *"
              println "* Main Job will be triggered by LaaS server later.                                                  *"
            } else {
              println "* Reservation is fail.                                                                              *"
            }
            println "*****************************************************************************************************"
          }
        } //end of script
      } // end of steps
    } // end of stage
  }
}
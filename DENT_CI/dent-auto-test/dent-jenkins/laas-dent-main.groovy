properties([
  parameters([
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
    string(name: 'reservation_id', defaultValue: "", description: 'The reservation id on LaaS.' ),
    string(name: 'reservation_duration', defaultValue: "600", description: 'The unit is seconds. Default is 10 minutes.')
  ])
])

def TESTBED = ""
def DUT = ""

// To get the TESTBED and DUT information by the reservation id
node("master") {
  withCredentials([usernamePassword(credentialsId: 'laas-dent-test', passwordVariable: 'account_PSW', usernameVariable: 'account_USR')]) {
    dir("script") {
      // Pull code from repository
      checkout([$class: 'GitSCM', branches: [[name: '*/dent-aws']], doGenerateSubmoduleConfigurations: false, extensions: [[$class: 'SparseCheckoutPaths', sparseCheckoutPaths: [[path: 'dent-script/']]]], submoduleCfg: [], userRemoteConfigs: [[credentialsId: 'jenkins_gitlab', url: 'git@gitlab.edge-core.com:root/dent-auto-test.git']]])
      // Get the testbed information by reservation id
      device_info = sh(script:"""python3 ./dent-script/laas_interface_for_jenkins.py get reservation device-info -u ${account_USR} ${params.reservation_id}<< EOF
${account_PSW}
EOF""", returnStdout: true).trim()
      print("device_info = ${device_info}")
      TESTBED = device_info.tokenize(",")[2]
      DUT = device_info.tokenize(",")[1]
      print("TESTBED = ${TESTBED}, DUT = ${DUT}")
    } // end of dir("script")
  } // end of withCredentials
} // end of master

pipeline {
  agent {
    label "${TESTBED}"
  }
  environment {
    repository = "https://nexus.dent.dev/content/repositories/snapshots/org/dent/dentos/"
    http_server = "192.168.3.45"
    http_server_cred = credentials('dent-image-server')
    account = credentials('laas-dent-test')
    dent_source_path = ""
    config_file = ""
    network_interfaces_file = ""
    s3_bucket = "dent-external-logs-s3-cloudfront-index"
    s3_path = "logs/${JOB_NAME}/${BUILD_NUMBER}/"
    s3_url = "external-logs.dent.dev"
  }
  options { timestamps () }
  stages {
    stage('Prerequisites') {
      steps {
        script {
          // Generate the configuration file for testing
          dent_source_path = sh(returnStdout: true, script: "find / -type d -name 'DentOsTestbed' 2>/dev/null || true").trim()
          if (!dent_source_path) {
            throw new Exception("Error: Cannot find where the dent testing project is.")
          }
          println "dent_source_path = ${dent_source_path}"
          config_file = "${dent_source_path}/configuration/testbed_config/basic/testbed.json"
          network_interfaces_file = "${dent_source_path}/configuration/testbed_config/basic/infra_sw1/infra_sw1_NETWORK_INTERFACES"
          dir("script") {
            // Pull code from repository
            checkout([$class: 'GitSCM', branches: [[name: '*/dent-aws']], doGenerateSubmoduleConfigurations: false, extensions: [[$class: 'SparseCheckoutPaths', sparseCheckoutPaths: [[path: 'dent-script/']]]], submoduleCfg: [], userRemoteConfigs: [[credentialsId: 'jenkins_gitlab', url: 'git@gitlab.edge-core.com:root/dent-auto-test.git']]])
            sh """python3 ./dent-script/dent_modify_config.py -rid ${params.reservation_id} -u ${account_USR} -op ${config_file}<< EOF
${account_PSW}
EOF"""
          } // end of dir("script")
        }
      }
    } // end of stage('Prerequisites')

    stage('Download image from repository') {
      steps {
        script {
          remote_image_url = "${repository}${params.image_version}_INSTALLED_INSTALLER"
          sh("set +x; sshpass -p '$http_server_cred_PSW' ssh -o StrictHostKeyChecking=no $http_server_cred_USR@${http_server} 'wget ${remote_image_url} -O /var/www/html/${params.image_version}_INSTALLED_INSTALLER'")
        }
      }
    } // end of stage('Download image from repository')

    stage('Deploy Image to DUT') {
      steps {
        script {
          dir("script") {
            image_url = "http://${http_server}/${params.image_version}_INSTALLED_INSTALLER"
            sh "PYTHONIOENCODING=utf-8 python3 ./dent-script/dent_auto_upgrade.py -dev ${DUT} -img ${image_url} -c ${config_file} -nf ${network_interfaces_file}"
          }
        }
      }
    } // end of stage('Deploy Image to DUT')

    stage('Run test case') {
      steps {
        script {
          def test_suite_group_list = params.test_suite_group.tokenize(',')
          for (def suite_group in test_suite_group_list) {
            sh """
              cd ${dent_source_path}
              rm -rf logs
              rm -rf reports
              mkdir -p reports
              dentos_testbed_runtests -d --stdout --test-output-dest ./test_output --config configuration/testbed_config/basic/testbed.json --config-dir configuration/testbed_config/basic/ --suite-groups ${suite_group} --discovery-reports-dir ./reports --discovery-path ../DentOsTestbedLib/src/dent_os_testbed/discovery/modules/ -l 5
              mkdir -p $WORKSPACE/archives/logs/${suite_group}/
              cp -R logs/* $WORKSPACE/archives/logs/${suite_group}/
              mv reports/* $WORKSPACE/archives/logs/${suite_group}/report_${suite_group}.json
            """
          } // end of for (def suite_group in test_suite_group_list)
        } // end of script
      } 
    } // end of stage('Run test case')
  }

  post {
    always {
      script {
        // Upload log to repository(S3 bucket)
        dir("script") {
          try {
            sh "mkdir -p $WORKSPACE/archives/"
            sh "bash ./dent-script/lftool-deploy-s3.sh /home/lftool-venv '$s3_bucket' '$s3_path' '$BUILD_URL' '$WORKSPACE'"
            echo "S3 build logs: <a href=\"https://$s3_url/$s3_path\"></a>"
            currentBuild.description = "<a href=\"https://$s3_url/$s3_path\">S3 Logs</a>"
          } catch (err_upload_log) {
            println "Error: Upload log fail. Error Message: ${err_upload_log}"
          }

          // release device from laas
          println "Send resource release message to LaaS server to release reservation ID ${params.reservation_id}."
          sh """python3 ./dent-script/laas_interface_for_jenkins.py release -u ${account_USR} ${params.reservation_id} << EOF
${account_PSW}
EOF"""
        } // end of script
      }
    }
  } // end of post
} // end of pipeline
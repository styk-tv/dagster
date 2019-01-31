'''Static scaffolding autogenerated by dagster-airflow from pipeline demo_pipeline with config:

    context:
      default:
        config: {log_level: DEBUG}
    solids:
      multiply_the_word:
        config: {factor: 2}
        inputs:
          word: {value: bar}
    

By convention, users should attempt to isolate post-codegen changes and customizations to the
"editable" demo_pipeline_editable__scaffold.py file, rather than changing the definitions in this
"static" file. Please let us know if you are encountering use cases where it is necessary to make
changes to the static file.
'''

from airflow import DAG
from airflow.operators.dagster_plugin import DagsterOperator


CONFIG = '''
    {
      context: {
        default: {
          config: {
            log_level: "DEBUG"
          }
        }
      },
      solids: {
        multiply_the_word: {
          config: {
            factor: 2
          },
          inputs: {
            word: {
              value: "bar"
            }
          }
        }
      }
    }
'''


def make_dag(
    dag_id,
    dag_description,
    dag_kwargs,
    s3_conn_id,
    modified_docker_operator_kwargs,
    host_tmp_dir
):
    dag = DAG(
        dag_id=dag_id,
        description=dag_description,
        **dag_kwargs,
    )

    multiply__the__word_word_input__thunk_task = DagsterOperator(
        step='multiply_the_word.word.input_thunk',
        config=CONFIG,
        dag=dag,
        tmp_dir='/tmp/results',
        host_tmp_dir=host_tmp_dir,
        image='dagster-airflow-demo',
        task_id='multiply__the__word_word_input__thunk',
        s3_conn_id=s3_conn_id,
        command='''-q '
            mutation {{
              startSubplanExecution(
                config: {config},
                executionMetadata: {{
                  runId: "testRun"
                }},
                pipelineName: "demo_pipeline",
                stepExecutions: [
                  {{
                    stepKey: "multiply_the_word.word.input_thunk"
                    marshalledInputs: 
                    [
                    ],
                    marshalledOutputs: 
                    [
                      {{
                        outputName: "input_thunk_output",
                        key: "/tmp/results/multiply__the__word_word_input__thunk___input__thunk__output.pickle"
                      }}
                    ],
                  }}
                ],
              ) {{
                __typename
                ... on StartSubplanExecutionSuccess {{
                  pipeline {{
                    name
                  }}
                }}
              }}
            }}
            '
        '''.format(config=CONFIG.strip('\n')),
    )

    multiply__the__word_transform_task = DagsterOperator(
        step='multiply_the_word.transform',
        config=CONFIG,
        dag=dag,
        tmp_dir='/tmp/results',
        host_tmp_dir=host_tmp_dir,
        image='dagster-airflow-demo',
        task_id='multiply__the__word_transform',
        s3_conn_id=s3_conn_id,
        command='''-q '
            mutation {{
              startSubplanExecution(
                config: {config},
                executionMetadata: {{
                  runId: "testRun"
                }},
                pipelineName: "demo_pipeline",
                stepExecutions: [
                  {{
                    stepKey: "multiply_the_word.transform"
                    marshalledInputs: 
                    [
                      {{
                        inputName: "word",
                        key: "/tmp/results/multiply__the__word_word_input__thunk___input__thunk__output.pickle"
                      }}
                    ],
                    marshalledOutputs: 
                    [
                      {{
                        outputName: "result",
                        key: "/tmp/results/multiply__the__word_transform___result.pickle"
                      }}
                    ],
                  }}
                ],
              ) {{
                __typename
                ... on StartSubplanExecutionSuccess {{
                  pipeline {{
                    name
                  }}
                }}
              }}
            }}
            '
        '''.format(config=CONFIG.strip('\n')),
    )

    count__letters_transform_task = DagsterOperator(
        step='count_letters.transform',
        config=CONFIG,
        dag=dag,
        tmp_dir='/tmp/results',
        host_tmp_dir=host_tmp_dir,
        image='dagster-airflow-demo',
        task_id='count__letters_transform',
        s3_conn_id=s3_conn_id,
        command='''-q '
            mutation {{
              startSubplanExecution(
                config: {config},
                executionMetadata: {{
                  runId: "testRun"
                }},
                pipelineName: "demo_pipeline",
                stepExecutions: [
                  {{
                    stepKey: "count_letters.transform"
                    marshalledInputs: 
                    [
                      {{
                        inputName: "word",
                        key: "/tmp/results/multiply__the__word_transform___result.pickle"
                      }}
                    ],
                    marshalledOutputs: 
                    [
                      {{
                        outputName: "result",
                        key: "/tmp/results/count__letters_transform___result.pickle"
                      }}
                    ],
                  }}
                ],
              ) {{
                __typename
                ... on StartSubplanExecutionSuccess {{
                  pipeline {{
                    name
                  }}
                }}
              }}
            }}
            '
        '''.format(config=CONFIG.strip('\n')),
    )

    multiply__the__word_word_input__thunk_task.set_downstream(multiply__the__word_transform_task)
    multiply__the__word_transform_task.set_downstream(count__letters_transform_task)

    return dag

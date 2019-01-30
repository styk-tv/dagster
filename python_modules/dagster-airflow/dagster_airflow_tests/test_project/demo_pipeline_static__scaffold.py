'''Static scaffolding autogenerated by dagster-airflow from pipeline demo_pipeline with config:

    {'context': {'default': {'config': {'log_level': 'DEBUG'}}},  'solids': {'multiply_the_word':
    {'config': {'factor': 2},                                   'inputs': {'word': {'value':
    'bar'}}}}}

By convention, users should attempt to isolate post-codegen changes and customizations to the
"editable" demo_pipeline_editable__scaffold.py file, rather than changing the definitions in this
"static" file. Please let us know if you are encountering use cases where it is necessary to make
changes to the static file.
'''

from airflow import DAG
from airflow.operators.dagster_plugin import DagsterOperator


def make_dag(dag_id, dag_description, dag_kwargs, s3_conn_id, modified_docker_operator_kwargs):
    dag = DAG(
        dag_id=dag_id,
        description=dag_description,
        **dag_kwargs,
    )

    multiply__the__word_word_input__thunk_task = DagsterOperator(
        step='multiply__the__word_word_input__thunk',
        dag=dag,
        image='dagster-airflow-demo',
        task_id='multiply__the__word_word_input__thunk',
        s3_conn_id=S3_CONN_ID,
    )

    multiply__the__word_transform_task = DagsterOperator(
        step='multiply__the__word_transform',
        dag=dag,
        image='dagster-airflow-demo',
        task_id='multiply__the__word_transform',
        s3_conn_id=S3_CONN_ID,
    )

    count__letters_transform_task = DagsterOperator(
        step='count__letters_transform',
        dag=dag,
        image='dagster-airflow-demo',
        task_id='count__letters_transform',
        s3_conn_id=S3_CONN_ID,
    )

    multiply__the__word_word_input__thunk_task.set_downstream(multiply__the__word_transform_task)
    multiply__the__word_transform_task.set_downstream(count__letters_transform_task)

    return dag